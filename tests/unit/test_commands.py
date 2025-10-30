from unittest.mock import patch

import pytest

from commizard import commands, llm_providers


@pytest.mark.parametrize(
    "gen_message, commit_ret, expected_func, expected_arg",
    [
        (None, None, "print_warning", "No commit message detected. Skipping."),
        ("", None, "print_warning", "No commit message detected. Skipping."),
        (
            "Generated msg",
            (0, "Commit success"),
            "print_success",
            "Commit success",
        ),
        (
            "Generated msg",
            (1, "Commit failed"),
            "print_warning",
            "Commit failed",
        ),
    ],
)
@patch("commizard.commands.output.print_warning")
@patch("commizard.commands.output.print_success")
@patch("commizard.commands.git_utils.commit")
def test_handle_commit_req(
    mock_commit,
    mock_print_success,
    mock_print_warning,
    gen_message,
    commit_ret,
    expected_func,
    expected_arg,
    monkeypatch,
):
    monkeypatch.setattr(llm_providers, "gen_message", gen_message)
    if commit_ret is not None:
        mock_commit.return_value = commit_ret

    commands.handle_commit_req([])

    if expected_func == "print_success":
        mock_print_success.assert_called_once_with(expected_arg)
        mock_print_warning.assert_not_called()
    else:
        mock_print_warning.assert_called_once_with(expected_arg)
        mock_print_success.assert_not_called()


@pytest.mark.parametrize(
    "opt, expected",
    [
        (
            [],
            (
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
            ),
        ),
        (
            ["cp"],
            "Usage: cp\n\nCopies the last generated message to the clipboard.\n",
        ),
        (
            ["doesn't exist"],
            "Unknown command: doesn't exist. Use help for a list of available commands.\n",
        ),
    ],
)
def test_print_help(capsys, opt, expected):
    commands.print_help(opt)
    cap = capsys.readouterr()
    assert cap.out == expected + "\n"
    assert cap.err == ""


@pytest.mark.parametrize(
    "gen_message, opts, expect_warning",
    [
        # No message. warning only
        (None, [], True),
        # copied + success
        ("The sky is blue because of rayleigh scattering", [], False),
    ],
)
@patch("pyperclip.copy")
@patch("commizard.output.print_success")
@patch("commizard.output.print_warning")
def test_copy_command(
    mock_warn,
    mock_success,
    mock_copy,
    gen_message,
    opts,
    expect_warning,
    monkeypatch,
):
    monkeypatch.setattr(llm_providers, "gen_message", gen_message)
    commands.copy_command(opts)

    if expect_warning:
        mock_warn.assert_called_once()
        mock_success.assert_not_called()
        mock_copy.assert_not_called()
    else:
        mock_warn.assert_not_called()
        mock_success.assert_called_once()
        mock_copy.assert_called_once_with(gen_message)


@pytest.mark.parametrize(
    "available_models, opts, expect_init, expect_error, expect_select",
    [
        # init_model_list called
        (None, ["grok"], True, False, True),
        # print_error called
        (["gpt-1", "gpt-2"], ["gpt-3"], False, True, False),
        # select_model called
        (["gpt-1", "gpt-2"], ["gpt-2"], False, False, True),
        # incorrect user input
        (None, [], True, True, False),
        (["gpt-1", "gpt-2"], [], False, True, False),
    ],
)
@patch("commizard.llm_providers.output.print_error")
@patch("commizard.llm_providers.select_model")
@patch("commizard.llm_providers.init_model_list")
def test_start_model(
    mock_init,
    mock_select,
    mock_error,
    monkeypatch,
    available_models,
    opts,
    expect_init,
    expect_error,
    expect_select,
):
    # set available_models dynamically
    monkeypatch.setattr(llm_providers, "available_models", available_models)

    # mock the behavior of mock_init
    def fake_init():
        monkeypatch.setattr(llm_providers, "available_models", ["grok", "GPT"])

    mock_init.side_effect = fake_init
    commands.start_model(opts)

    assert mock_init.called == expect_init
    assert mock_error.called == expect_error

    if expect_select:
        mock_select.assert_called_once_with(opts[0])
    else:
        mock_select.assert_not_called()


@pytest.mark.parametrize(
    "available_models, opts",
    [
        ([], ["-v"]),
        (["gpt-1"], ["-q"]),
        (["gpt-1", "gpt-2", "gpt-3"], ["--all-info"]),
    ],
)
@patch("builtins.print")  # thanks chat-GPT. I never would've found this.
@patch("commizard.commands.llm_providers.init_model_list")
def test_print_available_models_correct(
    mock_init, mock_print, available_models, opts, monkeypatch
):
    mock_init.side_effect = lambda: monkeypatch.setattr(
        llm_providers, "available_models", available_models
    )
    commands.print_available_models(opts)

    mock_init.assert_called_once()

    # assert prints match number of models
    assert mock_print.call_count == len(available_models)

    for model in available_models:
        mock_print.assert_any_call(model)


@pytest.mark.parametrize(
    "available_models, expect_err",
    [
        ([], False),
        (None, True),
    ],
)
@patch("commizard.llm_providers.output.print_warning")
@patch("commizard.llm_providers.output.print_error")
@patch("builtins.print")
@patch("commizard.commands.llm_providers.init_model_list")
def test_print_available_models_error_behavior(
    mock_init, mock_print, mock_err, mock_warn, available_models, expect_err
):
    mock_init.side_effect = lambda: setattr(
        llm_providers, "available_models", available_models
    )
    commands.print_available_models([])
    mock_print.assert_not_called()
    if expect_err:
        mock_err.assert_called_once()
    else:
        mock_warn.assert_called_once()


@patch("commizard.commands.output.print_warning")
@patch("commizard.commands.git_utils.get_clean_diff")
def test_generate_message_no_diff(mock_diff, mock_output, monkeypatch):
    mock_diff.return_value = ""
    monkeypatch.setattr(commands.llm_providers, "gen_message", None)

    commands.generate_message(["--dummy"])

    mock_output.assert_called_once_with("No changes to the repository.")
    assert commands.llm_providers.gen_message is None


@patch("commizard.commands.output.print_error")
@patch("commizard.commands.git_utils.get_clean_diff")
@patch("commizard.commands.llm_providers.generate")
def test_generate_message_err(mock_gen, mock_diff, mock_output, monkeypatch):
    mock_diff.return_value = "some diff"
    mock_gen.return_value = (1, "Error happened")
    monkeypatch.setattr(commands.llm_providers, "generation_prompt", "PROMPT:")
    monkeypatch.setattr(commands.llm_providers, "gen_message", None)

    commands.generate_message(["--dummy"])

    mock_gen.assert_called_once_with("PROMPT:some diff")
    mock_output.assert_called_once_with("Error happened")
    assert commands.llm_providers.gen_message is None


@patch("commizard.commands.output.wrap_text")
@patch("commizard.commands.output.print_generated")
@patch("commizard.commands.git_utils.get_clean_diff")
@patch("commizard.commands.llm_providers.generate")
def test_generate_message_success(
    mock_gen, mock_diff, mock_output, mock_wrap, monkeypatch
):
    mock_diff.return_value = "some diff"
    mock_gen.return_value = (0, "The generated commit message")
    monkeypatch.setattr(commands.llm_providers, "generation_prompt", "PROMPT:")
    monkeypatch.setattr(commands.llm_providers, "gen_message", None)
    mock_wrap.side_effect = lambda text, width: f"WRAPPED({text})"

    commands.generate_message(["--dummy"])

    mock_gen.assert_called_once_with("PROMPT:some diff")
    mock_wrap.assert_called_once_with("The generated commit message", 72)
    mock_output.assert_called_once_with("WRAPPED(The generated commit message)")
    assert llm_providers.gen_message == "WRAPPED(The generated commit message)"


@pytest.mark.parametrize(
    "os, has_clear",
    [
        ("Windows", True),
        ("Linux", True),
        ("Darwin", True),
        ("Freebsd", True),
        ("Unix", True),
        ("Obscure chinese spyware", False),
        ("Windows", False),
    ],
)
@patch("commizard.commands.sys.stdout.flush")
@patch("commizard.commands.sys.stdout.write")
@patch("commizard.commands.os.system")
@patch("commizard.commands.platform.system")
def test_cmd_clear(mock_os, mock_exec, mock_write, mock_flush, os, has_clear):
    mock_os.return_value = os
    mock_exec.return_value = int(not has_clear)
    commands.cmd_clear([])
    cmd = "cls" if os == "Windows" else "clear"
    mock_exec.assert_called_once_with(cmd)
    if not has_clear:
        mock_write.assert_called_once()
        mock_flush.assert_called_once()


@pytest.mark.parametrize(
    "user_input, expected_args",
    [
        ("commit", []),
        ("commit arg1 arg2 arg3", ["arg1", "arg2", "arg3"]),
        ("                     commit       ", []),
        ("commit arg            ", ["arg"]),
        ("  commit                  arg1   arg2", ["arg1", "arg2"]),
    ],
)
@patch("commizard.commands.handle_commit_req")
def test_parser_commit(mock_func, user_input, expected_args):
    with patch.dict(
        "commizard.commands.supported_commands", {"commit": mock_func}
    ):
        result = commands.parser(user_input)
        assert result == 0
        mock_func.assert_called_once_with(expected_args)


@pytest.mark.parametrize(
    "user_input, expected_args",
    [
        ("help", []),
        ("help this-cmd", ["this-cmd"]),
        ("help f'ed up input 😣  😬", ["f'ed", "up", "input", "😣", "😬"]),
    ],
)
@patch("commizard.commands.print_help")
def test_parser_help(mock_func, user_input, expected_args):
    with patch.dict(
        "commizard.commands.supported_commands", {"help": mock_func}
    ):
        result = commands.parser(user_input)
        assert result == 0
        mock_func.assert_called_once_with(expected_args)


@pytest.mark.parametrize(
    "user_input, expected_args",
    [
        ("cp src dest", ["src", "dest"]),
        ("cp head", ["head"]),
        (" cp ", []),
    ],
)
@patch("commizard.commands.copy_command")
def test_parser_cp(mock_func, user_input, expected_args):
    with patch.dict("commizard.commands.supported_commands", {"cp": mock_func}):
        result = commands.parser(user_input)
        assert result == 0
        mock_func.assert_called_once_with(expected_args)


@pytest.mark.parametrize(
    "user_input, expected_args",
    [
        ("start gpt-4", ["gpt-4"]),
        ("start llama --temp=0.8", ["llama", "--temp=0.8"]),
        ("start         mistral:latest", ["mistral:latest"]),
    ],
)
@patch("commizard.commands.start_model")
def test_parser_start(mock_func, user_input, expected_args):
    with patch.dict(
        "commizard.commands.supported_commands", {"start": mock_func}
    ):
        result = commands.parser(user_input)
        assert result == 0
        mock_func.assert_called_once_with(expected_args)


@pytest.mark.parametrize(
    "user_input, expected_args",
    [
        ("list", []),
        ("list --all", ["--all"]),
        ("          list             --q", ["--q"]),
    ],
)
@patch("commizard.commands.print_available_models")
def test_parser_list(mock_func, user_input, expected_args):
    with patch.dict(
        "commizard.commands.supported_commands", {"list": mock_func}
    ):
        result = commands.parser(user_input)
        assert result == 0
        mock_func.assert_called_once_with(expected_args)


@pytest.mark.parametrize(
    "user_input, expected_args",
    [
        ("gen", []),
        ("gen --length=100", ["--length=100"]),
        ("generate --style=funny", ["--style=funny"]),
        ("generate", []),
    ],
)
@patch("commizard.commands.generate_message")
def test_parser_gen(mock_func, user_input, expected_args):
    with patch.dict(
        "commizard.commands.supported_commands",
        {"gen": mock_func, "generate": mock_func},
    ):
        result = commands.parser(user_input)
        assert result == 0
        mock_func.assert_called_once_with(expected_args)


@pytest.mark.parametrize(
    "user_input",
    [
        "nonsense",
        "blargh --x",
    ],
)
def test_parser_unrecognized(capsys, user_input):
    result = commands.parser(user_input)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err != ""
    assert result == 1


@pytest.mark.parametrize(
    "user_input, expected_err",
    [
        (
            "commir",
            "Command 'commir' not found. Use 'help' for more info\n\n"
            "The most similar command is:\n\tcommit\n",
        ),
        (
            "lits",
            "Command 'lits' not found. Use 'help' for more info\n\n"
            "The most similar command is:\n\tlist\n",
        ),
        (
            "gener",
            "Command 'gener' not found. Use 'help' for more info\n\n"
            "The most similar commands are:\n\tgenerate\n\tgen\n",
        ),
    ],
)
@patch("commizard.commands.output.print_error")
def test_parser_typo(mock_perr, user_input, expected_err):
    result = commands.parser(user_input)
    mock_perr.assert_called_once_with(expected_err)
    assert result == 1


@pytest.mark.parametrize("cmd", ["clear", "cls"])
def test_parser_clear_and_cls(monkeypatch, cmd):
    called = {"v": False}

    def fake(_=None):
        called["v"] = True

    monkeypatch.setattr(commands, "cmd_clear", fake)
    with patch.dict("commizard.commands.supported_commands", {cmd: fake}):
        result = commands.parser(cmd)
        assert result == 0
        assert called["v"] is True
