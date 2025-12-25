from __future__ import annotations

import textwrap

from rich.console import Console
from rich.live import Live
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

console: Console = Console()
error_console: Console = Console(stderr=True)
stream_console: Console = Console(width=70)
stream_txt = Text(style="blue")


def init_console(color: bool) -> None:
    """
    Initialize Console instances.

    Args:
        color (bool): Whether to use color.
    """
    global console, error_console, stream_console
    if color:
        error_console = Console(stderr=True, style="bold red")
    else:
        console = Console(color_system=None)
        stream_console = Console(color_system=None, width=70)
        error_console = Console(stderr=True, color_system=None)


def print_success(message: str) -> None:
    """
    prints success message in green color
    """
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """
    prints error message bold red
    """
    error_console.print(f"Error: {message}")


def print_warning(message: str) -> None:
    """
    prints warning message in yellow color
    """
    console.print(f"[yellow]Warning: {message}[/yellow]")


def print_generated(message: str) -> None:
    """
    prints generated message in blue color
    """
    console.print(f"[blue]{message}[/blue]")


def print_table(
    cols: list[str], rows: list[list[str]], title: str | None = None
) -> None:
    """
    prints a table with given columns and rows.
    Args:
        cols: A list of column names.
        rows: A list of rows to print.
        title (optional): The title of the table.
    """
    table = Table(title=title)

    for col in cols:
        table.add_column(col, justify="center")

    for row in rows:
        table.add_row(*row)

    console.print(Padding(table, 1), end="")


def wrap_text(text: str, width: int = 70) -> str:
    """
    Wrap text into a specified width, preserving line breaks.
    """
    lines = text.splitlines()
    wrapped_lines = [
        textwrap.fill(
            line, width=width, break_long_words=False, break_on_hyphens=False
        )
        for line in lines
    ]
    # preserve the last \n if the texts contains it.
    return "\n".join(wrapped_lines) + ("\n" if text.endswith("\n") else "")


# TODO: Streaming wrap currently handled by Rich Live. This should be replaced
#       with a stream wrapper for a more efficient execution
def live_stream() -> Live:
    return Live(
        stream_txt,
        console=stream_console,
        vertical_overflow="visible",
        refresh_per_second=30,
    )


def set_width(width: int) -> None:
    stream_console.width = width


def print_token(tok: str) -> None:
    stream_txt.append(tok)
