from __future__ import annotations

import concurrent.futures
import sys

from . import __version__ as version
from . import config, output, start

help_msg = """
Commit writing wizard

Usage:
  commizard [-v | --version] [-h | --help] [--no-color] [--no-banner]
            [--no-stream]

Options:
  -h, --help       Show help for commizard
  -v, --version    Show version information
  --no-color       Don't colorize output
  --no-banner      Disable the ASCII welcome banner
  --no-stream      Disable streaming and return the full response at once
"""


def handle_args():
    if len(sys.argv) < 2:
        return
    supported_args = [
        "-v",
        "--version",
        "-h",
        "--help",
        "--no-banner",
        "--no-color",
        "--no-stream",
    ]
    for arg in sys.argv[1:]:
        if arg not in supported_args:
            print(f"Unknown option: {arg}", file=sys.stderr)
            print("try 'commizard -h' for more information.", file=sys.stderr)
            sys.exit(2)
        if arg in ("-v", "--version"):
            print(f"CommiZard {version}")
            sys.exit(0)
        elif arg in ("-h", "--help"):
            print(help_msg.strip(), end="\n")
            sys.exit(0)
        elif arg == "--no-banner":
            config.SHOW_BANNER = False
        elif arg == "--no-color":
            config.USE_COLOR = False
        elif arg == "--no-stream":
            config.STREAM = False


def main() -> int:
    """
    This is the entry point of the program. calls some functions at the start,
    then jumps into an infinite loop.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    handle_args()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(output.init_console, config.USE_COLOR)
        fut_ai = executor.submit(start.local_ai_available)
        fut_git = executor.submit(start.check_git_installed)

        git_ok = fut_git.result()

    if not git_ok:
        output.print_error("git not installed")
        return 1
    if not start.is_inside_working_tree():
        output.print_error("not inside work tree")
        return 1

    if config.SHOW_BANNER:
        start.print_welcome(config.USE_COLOR)

    local_ai_ok = fut_ai.result()
    if not local_ai_ok:
        output.print_warning("local AI not available")

    from . import commands

    try:
        while True:
            user_input = input("CommiZard> ").strip()
            if user_input in ("exit", "quit"):
                print("Goodbye!")
                break
            elif user_input == "":
                continue
            commands.parser(user_input)
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")

    return 0


if __name__ == "__main__":  # pragma: no cover
    main()
