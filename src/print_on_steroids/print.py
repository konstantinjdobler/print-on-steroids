import os
import time
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.markup import escape as escape_markup

from .get_frame import get_frame


class LogLevel:
    color_map = {
        "debug": "grey30",
        "info": "light_sky_blue3",
        "success": "dark_green",
        "warning": "dark_orange3",
        "error": "red",
    }
    repr_map = {
        "debug": "DEBUG",
        "info": "INFO",
        "success": "SUCCESS",
        "warning": "WARNING",
        "error": "ERROR",
    }
    int_map = {
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


rich_console = Console(highlight=False, log_time_format="[%Y-%m-%d %H:%M:%S]")


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
    origin_info = f"[cyan]{name}[/]:[cyan]{line_no}[/] - [dim cyan]{function_name}[/] " if print_origin else ""
    rank_info = f"[dim cyan]|[/] [b {level_color}]Rank {rank}[/] " if rank is not None and not rank0 else ""

    info = timestamp_info + level_info + origin_info + rank_info
    info = info.strip()

    message = sep.join(str(value) for value in values)
    if escape:
        message = escape_markup(message)

    rich_console.print(info, "[dim cyan]|[/]", message, end=end)


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
    rich_console.print(info, message, end=end)


class PrinterOnSteroids:
    def __init__(
        self,
        mode: Literal["dev", "package", "silent", "from_env"] = "dev",
        verbosity: str = "debug",
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
                *values, level=level, rank=rank, rank0=rank0, sep=sep, end=end, escape=escape, stack_offset=stack_offset
            )
        else:
            if LogLevel.get_int(level) > LogLevel.get_int("debug"):
                namespace_print_on_steroids(
                    *values, namespace=self.package_name, level=level, rank=rank, rank0=rank0, sep=sep, end=end
                )

    def debug(self, *values, rank: int = None, rank0: bool = None, sep=" ", end="\n", escape=False):
        self.log(*values, level="debug", rank=rank, rank0=rank0, sep=sep, end=end, escape=escape, stack_offset=3)

    def info(self, *values, rank: int = None, rank0: bool = None, sep=" ", end="\n", escape=False):
        self.log(*values, level="info", rank=rank, rank0=rank0, sep=sep, end=end, escape=escape, stack_offset=3)

    def success(self, *values, rank: int = None, rank0: bool = None, sep=" ", end="\n", escape=False):
        self.log(*values, level="success", rank=rank, rank0=rank0, sep=sep, end=end, escape=escape, stack_offset=3)

    def warning(self, *values, rank: int = None, rank0: bool = None, sep=" ", end="\n", escape=False):
        self.log(*values, level="warning", rank=rank, rank0=rank0, sep=sep, end=end, escape=escape, stack_offset=3)

    def error(self, *values, rank: int = None, rank0: bool = None, sep=" ", end="\n", escape=False):
        self.log(*values, level="error", rank=rank, rank0=rank0, sep=sep, end=end, escape=escape, stack_offset=3)

    def config(
        self,
        mode: Literal["dev", "package", "silent"] = None,
        verbosity: str = None,
        package_name: str = None,
        rank: int = None,
        print_rank0_only: bool = None,
    ):
        self.rank = rank or self.rank
        self.mode = mode or self.mode
        self.package_name = package_name or self.package_name
        self.print_rank0_only = print_rank0_only or self.print_rank0_only
        self.verbosity = verbosity or self.verbosity

    def set_rank(self, rank: int):
        self.rank = rank

    def set_mode(self, mode: Literal["dev", "package", "silent", "from_env"]):
        if mode == "from_env":
            assert self.package_name is not None
            mode = os.getenv(f"{self.package_name.upper()}_LOG_MODE", "package")
            assert mode in ["dev", "package", "silent"]
        self.mode = mode


logger = PrinterOnSteroids(mode="dev", package_name=None)
