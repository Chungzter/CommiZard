from unittest.mock import DEFAULT, patch

import pytest

from commizard import cli


@pytest.mark.parametrize(
    "argv,expected_print,expect_exit",
    [
        (["prog"], "", False),
        (["prog", "-v"], f"CommiZard {cli.version}\n", True),
        (["prog", "--version"], f"CommiZard {cli.version}\n", True),
        (["prog", "--version", "ignored"], f"CommiZard {cli.version}\n", True),
        (["prog", "-h"], cli.help_msg.strip() + "\n", True),
        (["prog", "--help"], cli.help_msg.strip() + "\n", True),
        (
            ["prog", "not", "recognized"],
            "Unknown option: not\ntry 'commizard -h' for more information.\n",
            True,
        ),
    ],
)
@patch("commizard.cli.sys.exit")
def test_handle_args(
    mock_exit, argv, expected_print, expect_exit, capsys, monkeypatch
):
    monkeypatch.setattr(cli.sys, "argv", argv)

    cli.handle_args()

    captured = capsys.readouterr()
    assert captured.out == expected_print
    assert captured.err == ""

    if expect_exit:
        mock_exit.assert_called_once()
    else:
        mock_exit.assert_not_called()


@pytest.mark.parametrize(
    "git_installed, local_ai_avail, inside_work_tree, user_inputs, num_parse",
    [
        (False, True, True, [""], 0),
        (True, True, False, [""], 0),
        (True, True, True, [""], 0),
        (True, True, True, ["\n            \n \n"], 0),
        (True, True, True, ["exit"], 0),
        (True, False, True, ["quit"], 0),
        (True, True, True, ["cmd1", "cmd2", "cmd3"], 3),
        (True, True, True, ["cmd" for cmd in range(40)], 40),
    ],
    ids=[
        "git_not_installed",
        "not_in_work_tree",
        "empty_input",
        "whitespace_input",
        "happy_exit",
        "ai_unavailable_quit",
        "multiple_commands_then_exit",
        "very_long_session",
    ],
)
@patch("commizard.cli.start.check_git_installed")
@patch("commizard.cli.start.local_ai_available")
@patch("commizard.cli.start.is_inside_working_tree")
@patch("commizard.cli.start.print_welcome")
@patch("commizard.cli.commands.parser")
@patch("commizard.cli.input")
@patch("commizard.cli.output.print_error")
@patch("commizard.cli.output.print_warning")
@patch("commizard.cli.print")
@patch("commizard.cli.handle_args")
def test_main(
    mock_args,
    mock_print,
    mock_warning,
    mock_error,
    mock_input,
    mock_parser,
    mock_welcome,
    mock_is_inside_work_tree,
    mock_local_ai,
    mock_check_git_installed,
    git_installed,
    local_ai_avail,
    inside_work_tree,
    user_inputs,
    num_parse,
):
    mock_check_git_installed.return_value = git_installed
    mock_is_inside_work_tree.return_value = inside_work_tree
    mock_local_ai.return_value = local_ai_avail
    mock_input.side_effect = [*user_inputs, "exit"]
    out = cli.main()
    mock_args.assert_called_once()
    mock_check_git_installed.assert_called_once()

    if not git_installed:
        assert out == 1
        mock_error.assert_called_once_with("git not installed")
        mock_welcome.assert_not_called()
        mock_parser.assert_not_called()
        return
    else:
        mock_is_inside_work_tree.assert_called_once()

    if not inside_work_tree:
        mock_error.assert_called_once_with("not inside work tree")
        mock_welcome.assert_not_called()
        mock_parser.assert_not_called()
        return

    mock_welcome.assert_called_once()
    # Now we're in the loop
    if not local_ai_avail:
        mock_warning.assert_called_once_with("local AI not available")

    assert mock_parser.call_count == num_parse

    # exit the loop
    assert mock_print.call_count == 1
    assert out == 0
    mock_print.assert_called_once_with("Goodbye!")


@pytest.mark.parametrize(
    "expected_exception",
    [
        EOFError,
        KeyboardInterrupt,
    ],
)
def test_main_exception_handling(expected_exception):
    with (
        patch.multiple(
            "commizard.cli.start",
            check_git_installed=DEFAULT,
            local_ai_available=DEFAULT,
            is_inside_working_tree=DEFAULT,
            print_welcome=DEFAULT,
        ),
        patch.multiple(
            "commizard.cli.output",
            print_warning=DEFAULT,
            print_error=DEFAULT,
        ),
        patch.multiple(
            "commizard.cli",
            print=DEFAULT,
            handle_args=DEFAULT,
            input=DEFAULT,
        ) as print_mocks,
    ):
        print_mocks["print"].side_effect = None  # optional, just to be explicit
        print_mocks["input"].side_effect = expected_exception

        out = cli.main()

        assert out == 0
        print_mocks["print"].assert_called_once_with("\nGoodbye!")
