import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import FrameType
from typing import IO, Any, Callable, Iterable, Literal, Optional

from rich import get_console
from rich.console import Console
from rich.markup import escape as escape_markup
from tqdm import tqdm as TQDMClass

from .get_frame import get_frame

# If we cannot import better_exceptions, we fall back to the standard traceback module
try:
    from better_exceptions import format_exception
except ImportError:
    from traceback import format_exception


class LogLevel:
    # For color options, see https://rich.readthedocs.io/en/stable/appendix/colors.html
    color_map = {
        "print": "default",
        "debug": "grey30",
        "info": "light_sky_blue3",
        "success": "dark_green",
        "warning": "dark_orange3",
        "error": "red",
    }
    repr_map = {
        "print": "PRINT",
        "debug": "DEBUG",
        "info": "INFO",
        "success": "SUCCESS",
        "warning": "WARNING",
        "error": "ERROR",
    }
    int_map = {
        "print": -1,
        "debug": 0,
        "info": 1,
        "success": 2,
        "warning": 3,
        "error": 4,
    }

    @staticmethod
    def get_color(key):
        return LogLevel.color_map[key]

    @staticmethod
    def get_repr(key):
        return LogLevel.repr_map[key]

    @staticmethod
    def get_int(key):
        return LogLevel.int_map[key]


def rich_print(
    *objects: Any,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
) -> None:
    r"""
    Adapted from https://github.com/Textualize/rich/blob/720800e6930d85ad027b1e9bd0cbb96b5e994ce3/rich/__init__.py#L53

    Disables highlighting that rich automatically does. Adds tqdm-safe printing.

    ---

    Print object(s) supplied via positional arguments.
    This function has an identical signature to the built-in print.
    For more advanced features, see the :class:`~rich.console.Console` class.

    Args:
        sep (str, optional): Separator between printed objects. Defaults to " ".
        end (str, optional): Character to write at end of output. Defaults to "\\n".
        file (IO[str], optional): File to write to, or None for stdout. Defaults to None.
        flush (bool, optional): Has no effect as Rich always flushes output. Defaults to False.
    """

    write_console = get_console() if file is None else Console(file=file)

    # Do not break tqdm bars, when using tqdm.rich it works out of the box since it uses the same console
    # (Almost) a no-op if not using tqdm
    # NOTE: debate nolock=True vs nolock=False. Let's stay with the default from reference implementation for now (nolock=False).
    with TQDMClass.external_write_mode(file=sys.stdout, nolock=False):
        return write_console.print(*objects, sep=sep, end=end, highlight=False)


def extract_frame_info(frame: FrameType):
    line_no = frame.f_lineno
    function_name = frame.f_code.co_name
    file_name = frame.f_code.co_filename
    path = frame.f_globals["__name__"]

    if path == "__main__":
        path = Path(file_name).name
    else:
        # Enable jumping to source code in IDEs
        path = f"{path.replace('.', '/')}.py"

    return line_no, function_name, file_name, path


def print_on_steroids(
    *values,
    level: str = "print",
    rank: int = None,
    rank0_only: bool = None,
    print_time: bool = False,
    print_level: bool = True,
    print_origin: bool = False,
    sep: str = " ",
    end: str = "\n",
    escape: bool = False,
    stack_offset: int = 1,
):
    if rank0_only and rank != 0:
        return
    if level == "print":
        print_level = False

    frame = get_frame(stack_offset)
    line_no, function_name, file_name, path = extract_frame_info(frame)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    level_color = LogLevel.get_color(level)
    level_name = LogLevel.get_repr(level)

    timestamp_info = f"[dim cyan]{timestamp} |[/] " if print_time else ""
    level_info = f"[b {level_color}]{level_name:<7}[/] [dim cyan]|[/] " if print_level else ""
    origin_info = f"[cyan]{path}[/]:[cyan]{line_no}[/] - [dim cyan]{function_name}[/] [dim cyan]|[/] " if print_origin else ""
    rank_info = f"[b {level_color}]Rank {rank}[/] [dim cyan]|[/]" if rank is not None and not rank0_only else ""

    info = timestamp_info + level_info + origin_info + rank_info
    info = info.strip()

    message = sep.join(str(value) for value in values)
    if escape:
        message = escape_markup(message)

    if len(info) > 0:
        message = f"{info} {message}"

    rich_print(message, end=end)


def namespace_print_on_steroids(
    *values,
    namespace: str,
    level: str | int = "info",
    rank: int = None,
    rank0_only: bool = None,
    sep=" ",
    end="\n",
    escape=False,
):
    if rank0_only and rank != 0:
        return
    level_color = LogLevel.get_color(level)
    level_name = LogLevel.get_repr(level)
    info = f"[b {level_color}]{namespace} [dim cyan]-[/] {level_name}[dim cyan]:[/]"
    message = sep.join(str(value) for value in values)
    if escape:
        message = escape_markup(message)

    rich_print(info, message, end=end)


class PrinterOnSteroids:
    def __init__(
        self,
        mode: Literal["dev", "package", "silent", "from_env"] = "dev",
        verbosity: str = "print",
        package_name: str = None,
        rank: int = None,
        print_rank0_only=False,
    ):
        if mode == "from_env":
            assert package_name is not None
            mode = os.getenv(f"{package_name.upper()}_LOG_MODE", "package")
        self.mode = mode
        self.package_name = package_name
        self.rank = rank
        self.print_rank0_only = print_rank0_only
        self.verbosity = verbosity

    def log(
        self,
        *values,
        level: str | int = "info",
        rank: int = None,
        rank0_only: bool = None,
        sep=" ",
        end="\n",
        escape=False,
        stack_offset=2,
        print_time=True,
        print_level=True,
        print_origin=True,
    ):
        if self.mode == "silent":
            return
        if self.verbosity and LogLevel.get_int(level) < LogLevel.get_int(self.verbosity):
            return
        if rank is None:
            rank = self.rank
        if rank0_only is None:
            rank0_only = self.print_rank0_only

        if self.mode == "dev":
            print_on_steroids(
                *values,
                level=level,
                rank=rank,
                rank0_only=rank0_only,
                sep=sep,
                end=end,
                escape=escape,
                stack_offset=stack_offset,
                print_time=print_time,
                print_level=print_level,
                print_origin=print_origin,
            )
        elif self.mode == "package":
            if LogLevel.get_int(level) > LogLevel.get_int("debug"):
                namespace_print_on_steroids(
                    *values, namespace=self.package_name, level=level, rank=rank, rank0_only=rank0_only, sep=sep, end=end
                )

    def print(
        self,
        *values,
        rank: int = None,
        rank0_only: bool = None,
        sep=" ",
        end="\n",
        escape=False,
        print_time=False,
        print_level=False,
        print_origin=False,
    ):
        self.log(
            *values,
            level="print",
            rank=rank,
            rank0_only=rank0_only,
            sep=sep,
            end=end,
            escape=escape,
            stack_offset=3,
            print_time=print_time,
            print_level=print_level,
            print_origin=print_origin,
        )

    def debug(
        self,
        *values,
        rank: int = None,
        rank0_only: bool = None,
        sep=" ",
        end="\n",
        escape=False,
        print_time=True,
        print_level=False,
        print_origin=True,
    ):
        self.log(
            *values,
            level="debug",
            rank=rank,
            rank0_only=rank0_only,
            sep=sep,
            end=end,
            escape=escape,
            stack_offset=3,
            print_time=print_time,
            print_level=print_level,
            print_origin=print_origin,
        )

    def info(
        self,
        *values,
        rank: int = None,
        rank0_only: bool = None,
        sep=" ",
        end="\n",
        escape=False,
        print_time=True,
        print_level=True,
        print_origin=True,
    ):
        self.log(
            *values,
            level="info",
            rank=rank,
            rank0_only=rank0_only,
            sep=sep,
            end=end,
            escape=escape,
            stack_offset=3,
            print_time=print_time,
            print_level=print_level,
            print_origin=print_origin,
        )

    def success(
        self,
        *values,
        rank: int = None,
        rank0_only: bool = None,
        sep=" ",
        end="\n",
        escape=False,
        print_time=True,
        print_level=True,
        print_origin=True,
    ):
        self.log(
            *values,
            level="success",
            rank=rank,
            rank0_only=rank0_only,
            sep=sep,
            end=end,
            escape=escape,
            stack_offset=3,
            print_time=print_time,
            print_level=print_level,
            print_origin=print_origin,
        )

    def warning(
        self,
        *values,
        rank: int = None,
        rank0_only: bool = None,
        sep=" ",
        end="\n",
        escape=False,
        print_time=True,
        print_level=True,
        print_origin=True,
    ):
        self.log(
            *values,
            level="warning",
            rank=rank,
            rank0_only=rank0_only,
            sep=sep,
            end=end,
            escape=escape,
            stack_offset=3,
            print_time=print_time,
            print_level=print_level,
            print_origin=print_origin,
        )

    def error(
        self,
        *values,
        rank: int = None,
        rank0_only: bool = None,
        sep=" ",
        end="\n",
        escape=False,
        print_time=True,
        print_level=True,
        print_origin=True,
    ):
        self.log(
            *values,
            level="error",
            rank=rank,
            rank0_only=rank0_only,
            sep=sep,
            end=end,
            escape=escape,
            stack_offset=3,
            print_time=print_time,
            print_level=print_level,
            print_origin=print_origin,
        )

    def config(
        self,
        mode: Literal["dev", "package", "silent"] = None,
        verbosity: str = None,
        package_name: str = None,
        rank: int = None,
        print_rank0_only: bool = None,
    ):
        self.rank = self.rank if rank is None else rank
        self.mode = self.mode if mode is None else mode
        self.package_name = self.package_name if package_name is None else package_name
        self.print_rank0_only = self.print_rank0_only if print_rank0_only is None else print_rank0_only
        self.verbosity = self.verbosity if verbosity is None else verbosity

    def set_rank(self, rank: int):
        self.rank = rank

    def set_mode(self, mode: Literal["dev", "package", "silent", "from_env"]):
        if mode == "from_env":
            assert self.package_name is not None
            mode = os.getenv(f"{self.package_name.upper()}_LOG_MODE", "package")
            assert mode in ["dev", "package", "silent"]
        self.mode = mode


@contextmanager
def graceful_exceptions(
    handled_exceptions: Exception | Iterable[Exception] = Exception,
    *,
    on_exception: Callable[[Exception], Any] = lambda e: None,
    exit: bool = True,
    extra_message: str = "",
):
    """
    Context manager and decorator that gracefully handles exceptions with a beautiful traceback print.

    `handled_exceptions` can be a single or list of exceptions, e.g. `ValueError` or `[ValueError, TypeError]`. All exceptions that are not a subclass of these are not handled. By default, all exceptions are handled.

    `on_exception` is an optional callback that is called after the traceback print. It is passed the exception as argument.

    If `exit=True`, we exit with `sys.exit(1)` after the traceback print (default). Otherwise, the exception is caught and the program continues.

    `extra_message` is an optional message that is printed with the traceback print, e.g. the rank of the process in a distributed setting.

    Usage as decorator:
    ```python
    @graceful_exceptions()
    def my_func(arg1, arg2):
        raise ValueError("Bad!")
    ```

    Usage as context manager:
    ```python
    def my_func(arg1, arg2):
        raise ValueError("Bad!")

    with graceful_exceptions():
        my_func(1, 2)
    ```
    """
    handled_exceptions = handled_exceptions if isinstance(handled_exceptions, Iterable) else [handled_exceptions]
    try:
        yield
    except Exception as e:
        if not any(issubclass(e.__class__, exc) for exc in handled_exceptions):
            raise e

        traceback, full_traceback = e.__traceback__, e.__traceback__
        # Loop until last frame, which is where the exception was raised
        while traceback.tb_next:
            traceback = traceback.tb_next
        line_no, function_name, file_name, name = extract_frame_info(traceback.tb_frame)
        origin_info = f"[cyan]{name}[/]:[cyan]{line_no}[/] - [dim cyan]{function_name}[/]"

        # Skip the first frame for printing, which is the context manager/decorator
        full_traceback = full_traceback.tb_next
        *formatted_traceback, formatted_exception = format_exception(type(e), e, full_traceback)
        exc_message = "".join([*formatted_traceback, formatted_exception])

        color = "red" if exit else "green"
        prefix = "Caught " if not exit else ""
        if len(extra_message):
            extra_message = f"| {extra_message} "
        get_console().rule(title=f"[b]↓[/] {prefix}{formatted_exception} | {origin_info } {extra_message}[b]↓", style=color)
        rich_print(exc_message.strip())
        get_console().rule(title=f"[b]↑[/] {prefix}{formatted_exception} | {origin_info } {extra_message}[b]↑", style=color)

        # Optional user-defined callback
        on_exception(e)

        if exit:
            # Kill like this so that we do not get duplicate Traceback print
            sys.exit(1)


# Instantiate for easy import
logger = PrinterOnSteroids(mode="dev", package_name=None)
