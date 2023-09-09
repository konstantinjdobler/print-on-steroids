# print-on-steroids :weight_lifting_man:

![Build Status](https://github.com/konstantinjdobler/print-on-steroids/actions/workflows/test_publish.yml/badge.svg?branch=main) [![Conda Version](https://img.shields.io/conda/vn/conda-forge/print-on-steroids)](https://anaconda.org/conda-forge/print-on-steroids) [![PyPI Version](https://img.shields.io/pypi/v/print-on-steroids.svg)](https://pypi.python.org/pypi/print-on-steroids) ![Code Size](https://img.shields.io/github/languages/code-size/konstantinjdobler/print-on-steroids) ![Code Style](https://img.shields.io/badge/code%20style-black-black) ![Linter](https://img.shields.io/badge/linter-ruff-blue)

A lean and hackable rich logger and drop-in enhanced replacement for the native `print` function.

## Installation

```bash
pip install print-on-steroids
conda install -c conda-forge print-on-steroids
```

If installing from `conda`, you need to `pip install better-exceptions` manually if you want better traceback formatting.

## Features

- Support for logging only on rank zero in distributed setups (e.g. DistributedDataParallel or sharded training in Deep Learning)
- Gracefully handles `tqdm` and `tqdm.rich` progress bars (logs during training do not interrupt the progress bar!)
- A context manager and decorator for beautiful and enriched exception printing
- Rich meta-information for free like timestamps and originating line of code (turned into a clickable deeplink by VS Code)
- Easy switching between `dev` and `package` modes when publishing packages to PyPI (cleaner logs without clutter)

## Usage

`print_on_steroids` - like `print` but on steroids!

```python
from print_on_steroids import print_on_steroids as print

# Enjoy enhanced print with optional log levels, timestamp, and originating line of code
print("Enhanced", "print!", level="success", print_time=True, print_origin=True)

# Logging with multiple processes - avoid terminal clutter
print("Gets printed", rank=0, rank0_only=True)
print("Doesn't get printed", rank=1, rank0_only=True)
```

Use `logger` for more advanced use cases:

```python
from print_on_steroids import logger

# Full-fledged logger object out-of-the-box
logger.log("This", "is", "cool", level="info")
# or give the log level directly:
logger.info("This", "is", "cool")
logger.warning("This", "is", "dangerous")
logger.error("This", "is", "fatal")
...

# Easy setup for distributed setting:
logger.config(rank=RANK, print_rank0_only=True)
# Afterwards, the rank is remembered and does not need to be passed agai
logger.success("Dataset processing finished!") # <-- this now prints only on rank zero

# For cleaner logs when publishing a package, use this:
logger.config(mode="package", package_name="MyPackage")
```

All methods gracefully handle `tqdm` - no interrupted progress bars:

```python
from print_on_steroids import logger, print_on_steroids as print
from tqdm import tqdm

for i in tqdm(range(42), desc="This works!"):
    sleep(1)
    logger.success("Work done:", i)
    print_on_steroids("Work done:", i)
```

Beautifully formatted Exception and traceback printing:

```python
from print_on_steroids import graceful_exceptions

# As a context manager:
with graceful_exceptions():
    # Do stuff...

# As a decorator:
@graceful_exceptions()
def do_stuff():
    # Do stuff...
```
