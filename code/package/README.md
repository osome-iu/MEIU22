# Introduction

This package contains some common code to facilitate the MEIU22 project.

## How to install

After moving to the directory that contains the `setup.py` file, install the package locally with `pip`.
`e` stands for editable. This basically means the package is editable and any changes to is
immediately availbale when it is re-imported.

```sh
pip install -e ./
```

## How to use

```py
import midterm

logger = midterm.get_logger(log_dir, full_log_dir)
```