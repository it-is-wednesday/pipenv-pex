# pipenv-pex
Quickly create [PEX](https://github.com/pantsbuild/pex) files out of your
Pipenv projects using this one simple command!

PEX files are an expansion upon [zipapp](https://docs.python.org/3/library/zipapp.html)s. You can bundle your application's modules along with their dependencies into one file, executable using a Python interpreter.

## Installation
Using the lovely [pipx](https://github.com/pipxproject/pipx):

`pipx install pipenv-pex`

## Usage
``` shell
cd project-with-pipfile
pipenv-pex --entry-point "epic_project:main"
python ./project-with-pipfile.pex
```
- `--entry-point` argument should have the form “pkg.mod:fn”, where “pkg.mod” is a package/module in the archive, and “fn” is a callable in the given module. (taken from[here](https://docs.python.org/3/library/zipapp.html#command-line-interface))
- All parameters except `--exclude` are passed directly to PEX, `--entry-point` being one of them.

## Why not use pex directly?
Since `pipenx-pex` piggybacks on the informaton in your `Pipfile`, some automations become possible:
- Dependencies are fetched from your Pipfile, so you don't have to update your Makefile each time you change a dependency in your Pipfile
- _(unrelated to pipenv actually)_ Irrelevant noise files are ignored when bundling the modules (such as .mypy_cache, \_\_pycache\_\_ etc.), saving a few precious MBs :) additional files and directories can be added to this list via the `--exclude` parameter.
