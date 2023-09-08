# print-on-steroids :weight_lifting_man:

![Build Status](https://github.com/konstantinjdobler/print-on-steroids/actions/workflows/test_publish.yml/badge.svg?branch=main) [![Conda Version](https://img.shields.io/conda/vn/conda-forge/print-on-steroids)](https://anaconda.org/conda-forge/print-on-steroids) [![PyPI Version](https://img.shields.io/pypi/v/print-on-steroids.svg)](https://pypi.python.org/pypi/print-on-steroids) ![Code Size](https://img.shields.io/github/languages/code-size/konstantinjdobler/print-on-steroids) ![Code Style](https://img.shields.io/badge/code%20style-black-black) ![Linter](https://img.shields.io/badge/linter-ruff-blue)


A lean and hackable rich logger and print function.

## Installation

```bash
pip install print-on-steroids
conda install -c conda-forge print-on-steroids
```

## Features

- Support for logging only on rank zero in distributed setups (e.g. Deep Learning)
- Gracefully handles `tqdm` and `tqdm.rich` progress bars (no annoying leftover progress bars anymore!)
- Rich meta-information for free like timestamps and originating line of code with clickable link
- Easy switching between `dev` and `package` modes when publishing packages to PyPI (cleaner logs without clutter)

## Usage

```python
from print_on_steroids import print_on_steroids as print, logger

# Enjoy enhanced print with optional log levels, timestamp, and originating line of code
print("It's like", "your regular", "Python print function", "but better", level="success")

# Logging with multiple processes - avoid terminal clutter 
print("Gets printed", rank=0, rank0=True)
print("Doesn't get printed", rank=1, rank0=True)

# Full-fledged logger object out-of-the-box
logger.log("This", "is", "cool", level="info")
# or directly:
logger.info("This", "is", "cool")
logger.warning("This", "is", "dangerous")
logger.error("This", "is", "fatal")
...

# Easy setup for distributed setting:
logger.config(rank=RANK, print_rank0_only=True)
# Afterwards, the rank is remembered and does not need to be passed again
logger.success("Dataset processing finished!") # <-- this now prints only on rank zero

# For cleaner logs when publishing a package, use this:
logger.config(mode="package", package_name="torch")

# Gracefully handles tqdm
from tqdm import tqdm
for i in tqdm(range(42), desc="This works!"):
    sleep(1)
    logger.success("Work done:", i)
    print_on_steroids("Work done:", i)
```
