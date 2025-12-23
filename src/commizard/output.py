from __future__ import annotations

import textwrap
import re
from rich.console import Console
from rich.padding import Padding
from rich.table import Table

console: Console = Console()
error_console: Console = Console(stderr=True)


def init_console(color: bool) -> None:
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


def wrap_token(
    token: str, pending: str, curr_len: int, width: int = 70
) -> tuple[list[str], str, int]:
    """
    Processes a single token from the LLM stream and determines which characters
    can be safely emitted without breaking words or exceeding the specified line
    width.
    Incomplete words are retained in the pending buffer until they can be
    emitted safely.

    Args:
        token: LLM's response token
        pending: Current uncommited buffer, which is guaranteed to be smaller
        than the width(len(pending) < width).
        curr_len: Length of the current line.
        width(default=70): The maximum length of wrapped lines

    Returns:
        result: Ordered chunks safe to append or print.
        pending: Remaining uncommitted trailing text
        curr_len: Updated current line length
    """
    res = []
    work_buf = pending + token

    # split the text into words, preserving whitespace characters as words
    words = re.split(r"(\s+)",work_buf)

    for word in words[:-1]:
        word_len = len(word)
        if curr_len+word_len <= width:
            res.append(word)
            if word == "\n":
                curr_len = 0
            # override last char if it's a space
            elif word == " " and curr_len+word_len == width:
                res[-1] = "\n"
                curr_len = 0
            else:
                curr_len += word_len
        else:
            res.append("\n")
            if word != " ":
                res.append(word)
                curr_len = word_len
            # don't append space
            else:
                curr_len =0

    return res, words[-1], curr_len
