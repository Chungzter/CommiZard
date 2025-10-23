from __future__ import annotations

import os
import platform
import sys
from typing import TYPE_CHECKING

import pyperclip

from . import git_utils, llm_providers, output

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


# TODO: implement
def print_help(opts: list[str]) -> None:
    """
    prints a list of all commands and a brief description

    Args:
        opts: a specific command that the user needs help with

    Returns:
        None
    """


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
    if llm_providers.available_models is None:
        llm_providers.init_model_list()

    if opts == []:
        output.print_error("Please specify a model.")
        return

    # TODO: see issue #42
    model_name = opts[0]

    if (
        llm_providers.available_models
        and model_name not in llm_providers.available_models
    ):
        output.print_error(f"{model_name} Not found.")
        return
    llm_providers.select_model(model_name)


def print_available_models(opts: list[str]) -> None:
    """
    prints the available models according to options passed.
    """
    llm_providers.init_model_list()
    if llm_providers.available_models is None:
        output.print_error(
            "failed to list available local AI models. Is ollama running?"
        )
        return
    elif not llm_providers.available_models:
        output.print_warning("No local AI models found.")
        return
    for model in llm_providers.available_models:
        print(model)


def generate_message(opts: list[str]) -> None:
    """
    Generate a message based on the current Git repository changes.
    """
    diff = git_utils.get_clean_diff()
    if diff == "":
        output.print_warning("No changes to the repository.")
        return

    prompt = llm_providers.generation_prompt + diff
    stat, res = llm_providers.generate(prompt)

    if stat != 0:
        output.print_error(res)
        return

    wrapped_res = output.wrap_text(res, 72)
    llm_providers.gen_message = wrapped_res
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
    if commands[0] in list(supported_commands.keys()):
        # call the function from the dictionary with the rest of the commands
        # passed as arguments to it
        cmd_func = supported_commands[commands[0]]
        cmd_func(commands[1:])
        return 0
    else:
        return 1
