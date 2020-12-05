import tempfile
from pathlib import Path
from sys import stderr
from typing import Container, Iterable, List

import click as c
from colorama import Fore, Style  # type: ignore
from pex.bin.pex import main as pex_main  # type: ignore
from pipenv.project import Project  # type: ignore

FILES_IRRELEVANT_TO_PEX = [
    "Pipfile", "Pipfile.lock", ".mypy_cache", "__pycache__"
]


def info(object):
    print(f"{Fore.GREEN}{object}{Style.RESET_ALL}")


def warning(object):
    print(f"{Fore.LIGHTYELLOW_EX}{object}{Style.RESET_ALL}")


def error(object):
    print(f"{Fore.RED}{object}{Style.RESET_ALL}", file=stderr)


class StashAwayFiles:
    """
    Context manager for temporarily moving away certain file in a directory.
    On exit, the files are moved back to their original home <3

        >>> from pathlib import Path; import os
        >>> Path("test").mkdir(exist_ok=True)
        >>> Path("test/in").touch()
        >>> Path("test/bad").touch()
        >>> with StashAwayFiles(origin="test", ["bad"]):
                os.listdir()
        ...
        ['test/in']
        >>> os.listdir()
        ['test/in', 'test/bad']

    """

    def __init__(self, origin, patterns: List[str]):
        self.patterns = patterns
        self.origin = Path(origin)

    def __enter__(self):
        # using home dir instead of /tmp becuase it's impossible to truly move
        # files between different filesystems - moving a file pointer around is
        # only possible within the same filesystem. since all we want is to
        # hide these files for a moment, meaning moving a pointer, we'll have
        # to pick a directory within the same filesystem we're currently on.
        self.tmpdir = tempfile.TemporaryDirectory(dir=str(Path.home()))
        for pattern in self.patterns:
            for f in self.origin.glob(pattern):
                f.rename(f"{self.tmpdir.name}/{f.name}")

    def __exit__(self, type, value, traceback):
        for f in Path(self.tmpdir.name).iterdir():
            f.rename(f"{self.origin}/{f.name}")


def contains_any(container: Container, items: Iterable) -> bool:
    "Check whether any if the items in @items exist in @container"
    return any(item in container for item in items)


@c.command(context_settings={
    "help_option_names": ["-h", "--help"],
    "ignore_unknown_options": True,
})
@c.option("-x",
          "--exclude",
          multiple=True,
          help="Don't include these files/directories in the resulting .pex "
          "file. In addition to files/dirs added using this option, these are "
          "excluded by deafult:\n{}.".format(
              ", ".join(FILES_IRRELEVANT_TO_PEX)))
@c.argument("pex_args", nargs=-1, type=c.UNPROCESSED)
def main(exclude: List[str], pex_args: tuple):
    project = Project()
    proj_dir = project.project_directory

    # check whether entry point was given
    if not contains_any(pex_args, ["-m", "-e", "--entry-point"]):
        error("No entry point (--entry-point) given!")
        return

    # Check for -o and --output in pex_args and set 'output' variable to
    # value that follows the -o or --output flag
    output = None
    output_flags = ["-o", "--output"]
    if contains_any(pex_args, output_flags):
        try:
            for flag in output_flags:
                try:
                    output = pex_args[pex_args.index(flag)+1]
                    break  # just return first hit
                except ValueError:
                    # flag not present
                    pass
        except IndexError:
            # no value following the flag, e.g. someone entered 'pipenv-pex -e <something> -o'
            pass

    # if output flags were not found, set to default value
    if output is None:
        output = f"{proj_dir}/{project.name}.pex"
        pex_args += ("--output", output)
        warning(f"Output is {output} since --output wasn't explicitly passed")

    deps = [
        f"{name}{props['version']}"
        for name, props in project.get_or_create_lockfile()["default"].items()
        if props.get("editable") is None  # ignore packages installed with -e
    ]
    info("Dependencies found:{}\n- {}".format(Fore.WHITE, "\n- ".join(deps)))

    irrelevant = FILES_IRRELEVANT_TO_PEX + list(exclude)
    info("Stashing away excluded files...")

    outpath = Path(output)
    if outpath.exists():
        warning(f"{outpath.name} already exists, deleting it...")
        outpath.unlink()

    with StashAwayFiles(proj_dir, irrelevant):
        info("Running pex...")
        pex_main([*deps, "--sources-directory", proj_dir, *pex_args])
        info("Popping back stashed files...")

    print(Fore.GREEN + "Done!")


if __name__ == '__main__':
    main()
