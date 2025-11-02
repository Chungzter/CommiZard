from __future__ import annotations

import shutil

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

# Gradient colors
start_color = Color.parse("#535147")
end_color = Color.parse("#8F00FF")


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
    result_lines = []
    if not start_color.triplet or not end_color.triplet:
        return text  # Return original text if colors are not valid
    for line in lines:
        colored_line = ""
        for i, char in enumerate(line):
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
            colored_line += f"[#{r:02x}{g:02x}{b:02x}]{char}"
        result_lines.append(colored_line)
    return "\n".join(result_lines)


# TODO: see issue #5
def print_welcome(color: bool) -> None:
    """
    Print the welcome screen. Right now it's the ASCII art of the project's
    name.
    """
    console = Console(color_system="auto" if color else None)
    if console.color_system in ("truecolor", "256"):
        console.print(gradient_text(text_banner, start_color, end_color))

    # don't use the gradient function for terminals that don't support it:
    else:
        console.print(f"[bold purple]{text_banner}[/bold purple]")


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
    r = llm_providers.http_request("get", url, timeout=0.3)
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
