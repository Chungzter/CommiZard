from __future__ import annotations

import json
import textwrap

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


def curate_stream(resp: str, buff: str, width: int = 70) -> str:
    """
    curates response sent from an LLM in the NDJSON format, finds the token,
    processes it to a valid token to be added to buff.

    Args:
        resp: NDJSON response.
        buff: Current buffer.
        width(default: 80): The maximum length of wrapped lines

    Returns:
        the updated buffer.
    """
    token = json.loads(resp)["response"]

    curr_line = buff.split("\n")[-1]
    curr_len = len(curr_line)

    if (curr_len + len(token)) <= width:
        # Do nothing if there's no problem
        return buff + token
    else:
        last_token = curr_line.split(" ")[-1]

        if last_token == "":
            return buff.rstrip() + "\n" + token
        else:
            # every valid token except the last one that's incomplete
            words = curr_line.split(" ")[:-1]

            res = " ".join(words) + last_token + token
            return res
