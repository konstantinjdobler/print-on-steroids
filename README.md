# print-on-steroids :weight_lifting_man:

[![PyPI Version](https://img.shields.io/pypi/v/print-on-steroids.svg)](https://pypi.python.org/pypi/print-on-steroids) ![Code Size](https://img.shields.io/github/languages/code-size/konstantinjdobler/print-on-steroids) ![Code Style](https://img.shields.io/badge/code%20style-black-black)

A lean and hackable rich logger and print function.

## Installation

```bash
pip install print-on-steroids
```

## Features

- Easy switching between dev and prod modes for logging and an extra logging mode for publishing packages
- Rich meta-information for free like timestamps and originating line of code with clickable link
- Support for logging only on rank zero in distributed setups (e.g. Deep Learning)

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

# Dev logs can be turned on again like this:
logger.config(mode="dev")
```
