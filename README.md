# pipenv-pex
Quickly create [PEX](https://github.com/pantsbuild/pex) files out of your
Pipenv projects using this one simple command!

PEX files are an expansion upon [zipapp](https://docs.python.org/3/library/zipapp.html)s, meaning you can bundle your application's modules along with their dependencies into one file that can be executes using a Python interpreter.

## Usage
``` shell
cd project-with-pipfile
pipenv-pex
python ./project-with-pipfile.pex
```

## Features
- Dependencies are fetched from your Pipfile, so you don't have to update your Makefile each time you change a dependency in your Pipfile
- Irrelevant noise files are ignored when bundling the modules (such as .mypy_cache, __pycache__ etc.), saving a few precious MBs :)
