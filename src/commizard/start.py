from __future__ import annotations

import shutil
import random as rand

from rich.color import Color
from rich.console import Console

from . import git_utils, llm_providers

text_banner = r"""
 ██████╗ ██████╗ ███╗   ███╗███╗   ███╗██╗███████╗ █████╗ ██████╗ ██████╗
██╔════╝██╔═══██╗████╗ ████║████╗ ████║██║╚══███╔╝██╔══██╗██╔══██╗██╔══██╗
██║     ██║   ██║██╔████╔██║██╔████╔██║██║  ███╔╝ ███████║██████╔╝██║  ██║
██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██║ ███╔╝  ██╔══██║██╔══██╗██║  ██║
╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║███████╗██║  ██║██║  ██║██████╔╝
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝

"""


def gradient_text(text: str, start_color: Color, end_color: Color) -> str:
    """
    Apply a horizontal gradient across the given ASCII art text.

    Args:
        text: The ASCII art or banner text.
        start_color: The starting Rich color object.
        end_color: The ending Rich color object.

    Returns:
        str: The ASCII text wrapped in Rich markup with gradient colors.
    """
    lines = text.splitlines()
    total_chars = max(len(line) for line in lines)
    result_lines = ["" for _ in lines]

    if not start_color.triplet or not end_color.triplet:
        return text  # Return original text if colors are not valid

    for i in range(total_chars):
        # Calculate RGB gradient values
        r = int(
            start_color.triplet[0]
            + (end_color.triplet[0] - start_color.triplet[0])
            * (i / total_chars)
        )
        g = int(
            start_color.triplet[1]
            + (end_color.triplet[1] - start_color.triplet[1])
            * (i / total_chars)
        )
        b = int(
            start_color.triplet[2]
            + (end_color.triplet[2] - start_color.triplet[2])
            * (i / total_chars)
        )
        color_str = f"[#{r:02x}{g:02x}{b:02x}]"
        for j in range(len(lines)):
            # Don't index into shorter lines
            if i >= len(lines[j]):
                continue
            result_lines[j] += (
                lines[j][i]
                if lines[j][i].isspace()  # don't add RGB string for whitespace
                else (color_str + lines[j][i])
            )
    return "\n".join(result_lines)


def print_welcome(color: bool) -> None:
    """
    Print the welcome screen. Right now it's the ASCII art of the project's
    name.
    """
    console = Console(color_system="auto" if color else None)
    if console.color_system in ("truecolor", "256"):
        colors = [
            ["#1A0D2E", "#2E1B4A", "#FF5E00", "#FF7518", "#FF8C42"],
            ["#0F001A", "#331A4D", "#00F2FE", "#01FFFF", "#FF00FE"],
            ["#2E1B4A", "#1F0F2E", "#FF4500", "#F6287D", "#FF00FF"],
            ["#0A1A3A", "#1A0D2E", "#FF6B00", "#00F2FE", "#FF00FE"]
            ]
        theme = rand.choice(colors)
        s, e = rand.sample(theme, 2)
        start_color = Color.parse(s)
        end_color = Color.parse(e)
        console.print(gradient_text(text_banner, start_color, end_color))

    # don't use the gradient function for terminals that don't support it:
    else:
        color = rand.choice(["grey", "purple", "magenta", "orange", "blue"])
        console.print(f"[bold {color}]{text_banner}[/bold {color}]")


def check_git_installed() -> bool:
    """
    Check if the git package is installed.
    """
    return shutil.which("git") is not None


def local_ai_available() -> bool:
    """
    Check if there's an ollama server running.
    """
    # Very rare for a server to run on this port AND have this api endpoint.
    url = "http://localhost:11434/api/version"
    r = llm_providers.HttpRequest("GET", url, timeout=0.3)
    return (
        (r.return_code == 200)
        and (isinstance(r.response, dict))
        and ("version" in r.response)
    )


def is_inside_working_tree() -> bool:
    """
    Check if we're inside a working directory (can execute commit and diff
    commands)
    """
    return git_utils.is_inside_working_tree()
