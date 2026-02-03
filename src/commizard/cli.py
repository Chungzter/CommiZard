from __future__ import annotations

import concurrent.futures
import sys

from . import __version__ as version
from . import commands, config, output, start

help_msg = """
Commit writing wizard

Usage:
  commizard [-v | --version] [-h | --help] [--no-color] [--no-banner]

Options:
  -h, --help       Show help for commizard
  -v, --version    Show version information
  --no-color       Don't colorize output
  --no-banner      Disable the ASCII welcome banner
  --stream         Stream generated prompt to stdout
"""


# Fixme: This function doesn't check for all possible arguments passed: if there
#        are many arguments like: --no-color --no-banner --stream, it will just
#        disable colors, but still print the banner and not stream the output.
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
        "--stream",
    ]
    if sys.argv[1] not in supported_args:
        print(f"Unknown option: {sys.argv[1]}")
        print("try 'commizard -h' for more information.")
        sys.exit(2)
    if sys.argv[1] in ("-v", "--version"):
        print(f"CommiZard {version}")
        sys.exit(0)
    elif sys.argv[1] in ("-h", "--help"):
        print(help_msg.strip(), end="\n")
        sys.exit(0)
    elif sys.argv[1] == "--no-banner":
        config.SHOW_BANNER = False
    elif sys.argv[1] == "--no-color":
        config.USE_COLOR = False
    elif sys.argv[1] == "--stream":
        config.STREAM = True


def main() -> int:
    """
    This is the entry point of the program. calls some functions at the start,
    then jumps into an infinite loop.

    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    # TODO: we're losing performance. We should take a look at better options to
    #       parallelize this. right now there's a 40-50 ms regression on
    #       startups with the ollama server both on and off
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
