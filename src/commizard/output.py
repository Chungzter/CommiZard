from __future__ import annotations

import textwrap

from rich.console import Console
from rich.padding import Padding
from rich.table import Table

console: Console = Console()
error_console: Console = Console()


def init_console(color: bool):
    """
    Initialize Console instances.

    Args:
        color (bool): Whether to use color.
    """
    global console, error_console
    if color:
        error_console = Console(stderr=True, style="bold red")
    else:
        console = Console(color_system=None)
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
):
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


# fixme: this function destroys bulletin board outputs. We shouldn't blindly
#        wrap these lists into each-other.
def wrap_text(text: str, width: int = 70) -> str:
    """
    Wrap text into paragraphs of specified width, preserving paragraph breaks.
    """
    paragraphs = text.split("\n\n")
    wrapped_paragraphs = [
        textwrap.fill(
            p, width=width, break_long_words=False, break_on_hyphens=False
        )
        for p in paragraphs
    ]
    return "\n\n".join(wrapped_paragraphs)
