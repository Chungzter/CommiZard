from __future__ import annotations

import textwrap

from rich.console import Console

console: Console | None = None
error_console: Console | None = None


def init_console(color: bool = True):
    global console, error_console
    console = Console()
    error_console = Console(stderr=True)


def print_success(message: str) -> None:
    """
    prints success message in green color
    """
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """
    prints error message bold red
    """
    error_console = Console(stderr=True, style="bold red")
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
