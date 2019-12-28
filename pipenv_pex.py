import tempfile
from pathlib import Path
from typing import List

import click as c
from pex.bin.pex import main as pex_main
from pipenv.project import Project  # type: ignore

FILES_IRRELEVANT_TO_PEX = [
    "Pipfile", "Pipfile.lock", ".mypy_cache", "__pycache__"
]


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
    def __init__(self, origin, predicate: List[str]):
        self.predicate = predicate
        self.origin = Path(origin)

    def __enter__(self):
        # using home dir instead of /tmp becuase it's impossible to truly move
        # files between different filesystems - moving a file pointer around is
        # only possible within the same filesystem. since all we want is to
        # hide these files for a moment, meaning moving a pointer, we'll have
        # to pick a directory within the same filesystem we're currently on.
        self.tmpdir = tempfile.TemporaryDirectory(dir=str(Path.home()))
        for f in self.origin.iterdir():
            if f.name in self.predicate:
                f.rename(f"{self.tmpdir.name}/{f.name}")

    def __exit__(self, type, value, traceback):
        for f in Path(self.tmpdir.name).iterdir():
            f.rename(f"{self.origin}/{f.name}")


@c.command(context_settings={"ignore_unknown_options": True})
@c.option("-x",
          "--exclude",
          multiple=True,
          help="Don't include these files/directories in the resulting .pex "
          "file. In addition to files/dirs added using this option, these are "
          "excluded by deafult:\n{}.".format(
              ", ".join(FILES_IRRELEVANT_TO_PEX)))
@c.argument("pex_args", nargs=-1, type=c.UNPROCESSED)
def main(exclude: List[str], pex_args):
    project = Project()
    proj_dir = project.project_directory

    # add inferred output filename if none were found in pex params
    if not ("-o" in pex_args or "--output" in pex_args):
        output = f"{proj_dir}/{project.name}.pex"
        pex_args += ("--output", output)

    deps = [
        f"{key}{value['version']}"
        for key, value in project.get_or_create_lockfile()["default"].items()
    ]

    irrelevant = FILES_IRRELEVANT_TO_PEX + list(exclude)
    with StashAwayFiles(proj_dir, irrelevant):
        pex_main([*deps, "--sources-directory", proj_dir, *pex_args])


if __name__ == '__main__':
    main()
