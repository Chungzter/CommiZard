from __future__ import annotations

import os
import platform
import sys
from difflib import get_close_matches
from typing import TYPE_CHECKING

import pyperclip

from . import config, git_utils, llm_providers, output

if TYPE_CHECKING:
    from collections.abc import Callable


def handle_commit_req(opts: list[str]) -> None:
    """
    commits the generated prompt. prints an error message if commiting fails
    """
    if llm_providers.gen_message is None or llm_providers.gen_message == "":
        output.print_warning("No commit message detected. Skipping.")
        return
    out, msg = git_utils.commit(llm_providers.gen_message)
    if out == 0:
        output.print_success(msg)
    else:
        output.print_warning(msg)


def print_help(opts: list[str]) -> None:
    """
    print general or command specific help.
    """
    command_help = {
        "start": (
            "Usage: start <model>\n\n"
            "Selects the model to generate commit messages with.\n"
        ),
        "gen": (
            "Usage: gen\n\n"
            "Generates a commit message from the current Git diff.\n"
        ),
        "cp": (
            "Usage: cp\n\nCopies the last generated message to the clipboard.\n"
        ),
        "commit": (
            "Usage: commit\n\nCommits using the last generated message.\n"
        ),
        "list": "Usage: list\n\nLists all installed models.\n",
        "cls": "Usage: cls | clear\n\nClears the terminal screen.\n",
        "clear": "Usage: cls | clear\n\nClears the terminal screen.\n",
        "exit": "Usage: exit | quit\n\nExits the program.\n",
        "quit": "Usage: exit | quit\n\nExits the program.\n",
    }
    if opts == []:
        help_msg = (
            "\nThe following commands are available:\n\n"
            "  start             Select a model to generate for you.\n"
            "  list              List all available models.\n"
            "  gen               Generate a new commit message.\n"
            "  cp                Copy the last generated message to the clipboard.\n"
            "  commit            Commit the last generated message.\n"
            "  cls  | clear      Clear the terminal screen.\n"
            "  exit | quit       Exit the program.\n"
            "\nTo view help for a command, type help, followed by a space, and the\n"
            "command's name.\n"
        )
    else:
        cmd = opts[0]
        help_msg = command_help.get(
            cmd,
            f"Unknown command: {cmd}. Use help for a list of available commands.\n",
        )
    print(help_msg)


def copy_command(opts: list[str]) -> None:
    """
    copies the generated prompt to clipboard according to options passed.

    Args:
        opts: list of options following the command
    """
    if llm_providers.gen_message is None:
        output.print_warning(
            "No generated message found. Please run 'generate' first."
        )
        return

    pyperclip.copy(llm_providers.gen_message)
    output.print_success("Copied to clipboard.")


def start_model(opts: list[str]) -> None:
    """
    Get the model (either local or online) ready for generation based on the
    options passed.
    """
    if opts == []:
        output.print_error("Please specify a model.")
        return

    if llm_providers.available_models is None:
        llm_providers.init_model_list()

    # TODO: see issue #42
    model_name = opts[0]

    if (
        llm_providers.available_models
        and model_name not in llm_providers.available_models
    ):
        output.print_error(f"{model_name} Not found.")
        return
    print("Loading model...")
    ret_stat, msg = llm_providers.select_model(model_name)
    if ret_stat == 0:
        output.print_success(msg)
    else:
        output.print_error(msg)


def print_available_models(opts: list[str]) -> None:
    """
    prints the available models according to options passed.
    """
    llm_providers.init_model_list()

    models = llm_providers.list_locals()
    if models is None:
        output.print_error(
            "failed to list available local AI models. Is ollama running?"
        )
        return
    elif not models:
        output.print_warning("No local AI models found.")
        return
    output.print_table(["Model name", "Parameter size"], models)


def generate_message(opts: list[str]) -> None:
    """
    Generate a message based on the current Git repository changes.
    """
    diff = git_utils.get_clean_diff()
    if diff == "":
        output.print_warning("No changes to the repository.")
        return

    prompt = llm_providers.generation_prompt + diff
    if config.STREAM:
        stat, res = llm_providers.stream_generate(prompt)
    else:
        stat, res = llm_providers.generate(prompt)

    if stat != 0:
        output.print_error(res)
        return

    # separate the title and the body and wrap them
    res_paragraphs = res.strip().split("\n\n", 1)
    title = output.wrap_text(res_paragraphs[0], 50)
    body = (
        output.wrap_text(res_paragraphs[1], 72)
        if len(res_paragraphs) > 1
        else ""
    )

    wrapped_res = title + ("\n\n" + body if len(res_paragraphs) > 1 else "")
    llm_providers.gen_message = wrapped_res

    if not config.STREAM:
        output.print_generated(wrapped_res)


def cmd_clear(opts: list[str]) -> None:
    """
    Clear terminal screen (Windows/macOS/Linux).
    """
    cmd = "cls" if platform.system().lower().startswith("win") else "clear"
    rc = os.system(cmd)  # noqa: S605
    if rc != 0:  # fallback to ANSI if shell command failed
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


supported_commands: dict[str, Callable[[list[str]], None]] = {
    "commit": handle_commit_req,
    "help": print_help,
    "cp": copy_command,
    "start": start_model,
    "list": print_available_models,
    "gen": generate_message,
    "generate": generate_message,
    "clear": cmd_clear,
    "cls": cmd_clear,
}


def parser(user_input: str) -> int:
    """
    Parse the user input and call appropriate functions

    Args:
        user_input: The user input to be parsed

    Returns:
        a status code: 0 for success, 1 for unrecognized command
    """
    commands = user_input.split()
    if commands[0] in supported_commands:
        # call the function from the dictionary with the rest of the commands
        # passed as arguments to it
        cmd_func = supported_commands[commands[0]]
        cmd_func(commands[1:])
        return 0
    else:
        err_str = (
            f"Command '{commands[0]}' not found. Use 'help' for more info\n"
        )
        match = get_close_matches(
            commands[0], [*supported_commands.keys(), "exit", "quit"], n=2
        )
        if match != []:
            is_are = (" is" if len(match) == 1 else "s are") + ":\n"
            err_str += "\nThe most similar command" + is_are

            for i in match:
                err_str += f"\t{i}\n"
        output.print_error(err_str)

        return 1
