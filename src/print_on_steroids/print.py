import os
import sys
import time
from pathlib import Path
from typing import IO, Any, Literal, Optional

from rich import get_console
from rich.console import Console
from rich.markup import escape as escape_markup
from tqdm import tqdm as TQDMClass

from .get_frame import get_frame


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


def print_on_steroids(
    *values,
    level: str = "info",
    rank: int = None,
    rank0: bool = None,
    sep=" ",
    end="\n",
    escape=False,
    stack_offset=1,
    print_time=True,
    print_level=True,
    print_origin=True,
):
    if rank0 and rank != 0:
        return
    frame = get_frame(stack_offset)

    line_no = frame.f_lineno
    function_name = frame.f_code.co_name
    file_name = frame.f_code.co_filename
    name = frame.f_globals["__name__"]

    if name == "__main__":
        name = Path(file_name).name
    else:
        # Enable jumping to source code in IDEs
        name = f"{name.replace('.', '/')}.py"

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    level_color = LogLevel.get_color(level)
    level_name = LogLevel.get_repr(level)

    timestamp_info = f"[dim cyan]{timestamp} |[/] " if print_time else ""
    level_info = f"[b {level_color}]{level_name:<7}[/] [dim cyan]|[/] " if print_level else ""
    origin_info = f"[cyan]{name}[/]:[cyan]{line_no}[/] - [dim cyan]{function_name}[/] [dim cyan]|[/] " if print_origin else ""
    rank_info = f"[b {level_color}]Rank {rank}[/] [dim cyan]|[/]" if rank is not None and not rank0 else ""

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
    rank0: bool = None,
    sep=" ",
    end="\n",
    escape=False,
):
    if rank0 and rank != 0:
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
        rank0: bool = None,
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
        if rank0 is None:
            rank0 = self.print_rank0_only

        if self.mode == "dev":
            print_on_steroids(
                *values,
                level=level,
                rank=rank,
                rank0=rank0,
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
                    *values, namespace=self.package_name, level=level, rank=rank, rank0=rank0, sep=sep, end=end
                )

    def print(
        self,
        *values,
        rank: int = None,
        rank0: bool = None,
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
            rank0=rank0,
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
        rank0: bool = None,
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
            rank0=rank0,
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
        rank0: bool = None,
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
            rank0=rank0,
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
        rank0: bool = None,
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
            rank0=rank0,
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
        rank0: bool = None,
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
            rank0=rank0,
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
        rank0: bool = None,
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
            rank0=rank0,
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


logger = PrinterOnSteroids(mode="dev", package_name=None)
