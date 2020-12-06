import shutil
import tempfile
from pathlib import Path
from sys import stderr
from typing import Container, Iterable, List

import click as c
from colorama import Fore, Style  # type: ignore
from pex.bin.pex import main as pex_main  # type: ignore
from pipenv.project import Project  # type: ignore

FILES_IRRELEVANT_TO_PEX = [
    "Pipfile",
    "Pipfile.lock",
    ".mypy_cache",
    "__pycache__",
    ".git*",
    ".idea"
]


def info(object):
    print(f"{Fore.GREEN}{object}{Style.RESET_ALL}")


def warning(object):
    print(f"{Fore.LIGHTYELLOW_EX}{object}{Style.RESET_ALL}")


def error(object):
    print(f"{Fore.RED}{object}{Style.RESET_ALL}", file=stderr)


class TempProjDir:
    """
    Context manager the creates a temp dir and copies current contents,
    minus excluded patterns
    """

    def __init__(self, origin, patterns: List[str]):
        self.patterns = patterns
        self.origin = Path(origin)

    def __enter__(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmpdir.name) / 'tmp_proj'
        shutil.copytree(self.origin, self.dest, ignore=shutil.ignore_patterns(*self.patterns))
        return self.dest

    def __exit__(self, type, value, traceback):
        self.tmpdir.cleanup()


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
               "excluded by default:\n{}.".format(
              ", ".join(FILES_IRRELEVANT_TO_PEX)))
@c.version_option()
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
                    output = pex_args[pex_args.index(flag) + 1]
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
    info("Copying files to temp project directory...")

    outpath = Path(output)
    if outpath.exists():
        warning(f"{outpath.name} already exists, deleting it...")
        outpath.unlink()

    with TempProjDir(proj_dir, irrelevant) as d:
        info("Running pex...")
        pex_main([*deps, "--sources-directory", d, *pex_args])
        info("Cleaning up temp project directory...")

    print(Fore.GREEN + "Done!")


if __name__ == '__main__':
    main()
