import subprocess
from unittest.mock import MagicMock, patch

import pytest

from commizard import git_utils


# TODO: add valid test cases that mock actual returns or subprocess.run
@pytest.mark.parametrize(
    "args, mock_result, raised_exception",
    [
        # successful git commands
        (
            ["status"],
            subprocess.CompletedProcess(
                args=["git", "status"],
                returncode=0,
                stdout="On branch main\n",
                stderr="",
            ),
            None,
        ),
        (
            ["log", "--oneline"],
            subprocess.CompletedProcess(
                args=["git", "log", "--oneline"],
                returncode=0,
                stdout="abc123 Initial commit\n",
                stderr="",
            ),
            None,
        ),
        # git command failure
        (
            ["push"],
            subprocess.CompletedProcess(
                args=["git", "push"],
                returncode=1,
                stdout="",
                stderr="Authentication failed",
            ),
            None,
        ),
        # exceptions
        (["status"], None, FileNotFoundError("git not found")),
        (
            ["push"],
            None,
            subprocess.TimeoutExpired(cmd=["git", "push"], timeout=5),
        ),
    ],
)
@patch("commizard.git_utils.subprocess.run")
def test_run_git_command(mock_run, args, mock_result, raised_exception):
    if raised_exception:
        mock_run.side_effect = raised_exception
        with pytest.raises(
            type(raised_exception)
        ):  # ensure the right exception is raised
            git_utils.run_git_command(args)
        mock_run.assert_called_once_with(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        return

    # success path
    mock_run.return_value = mock_result
    result = git_utils.run_git_command(args)
    mock_run.assert_called_once_with(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    assert result is mock_result


@pytest.mark.parametrize(
    "mock_val, expected_result",
    [
        (
            subprocess.CompletedProcess(
                args=["git", "rev-parse", "--is-inside-work-tree"],
                returncode=128,
                stdout="",
                stderr="fatal: not a git repository (or any of the parent directories): .git\n",
            ),
            False,
        ),
        (
            subprocess.CompletedProcess(
                args=["git", "rev-parse", "--is-inside-work-tree"],
                returncode=0,
                stdout="true\n",
                stderr="",
            ),
            True,
        ),
        (
            subprocess.CompletedProcess(
                args=["git", "rev-parse", "--is-inside-work-tree"],
                returncode=0,
                stdout="false\n",
                stderr="",
            ),
            False,
        ),
    ],
)
@patch("commizard.git_utils.run_git_command")
def test_is_inside_working_tree(mock_run, mock_val, expected_result):
    mock_run.return_value = mock_val
    res = git_utils.is_inside_working_tree()
    mock_run.assert_called_once_with(["rev-parse", "--is-inside-work-tree"])
    assert res == expected_result


@pytest.mark.parametrize(
    "mock_val, expected",
    [
        # This shouldn't happen based on the code's structure of running
        # is_inside_working_tree at start.
        (
            subprocess.CompletedProcess(
                args=["git", "diff", "--name-only"],
                returncode=128,
                stdout="",
                stderr="fatal: this operation must be run in a work tree\n",
            ),
            False,
        ),
        (
            subprocess.CompletedProcess(
                args=["git", "diff", "--name-only"],
                returncode=0,
                stdout="tests/test_git_utils.py\n",
                stderr="",
            ),
            True,
        ),
        (
            subprocess.CompletedProcess(
                args=["git", "diff", "--name-only"],
                returncode=0,
                stdout="",
                stderr="",
            ),
            False,
        ),
    ],
)
@patch("commizard.git_utils.run_git_command")
def test_is_changed(mock_run, mock_val, expected):
    mock_run.return_value = mock_val
    res = git_utils.is_changed()
    mock_run.assert_called_once_with(["diff", "--name-only"])
    assert res == expected


@pytest.mark.parametrize(
    "is_changed_return, run_git_returncode, run_git_stdout, expected_output",
    [
        # No changes detected
        (False, 0, "some diff", ""),
        # Changes detected, git diff succeeds
        (
            True,
            0,
            "diff --git a/file.py b/file.py\n+new line\n-old line\n\n",
            "diff --git a/file.py b/file.py\n+new line\n-old line",
        ),
        # Changes detected, git diff fails (non-zero return code)
        (True, 1, "error output", None),
        # Changes detected, git diff succeeds but stdout is empty
        (True, 0, "", ""),
        # Changes detected, git diff succeeds with whitespace-only output
        (True, 0, "   \n\t  ", ""),
    ],
)
@patch("commizard.git_utils.run_git_command")
@patch("commizard.git_utils.is_changed")
def test_get_diff(
    mock_is_changed,
    mock_run_git_command,
    is_changed_return,
    run_git_returncode,
    run_git_stdout,
    expected_output,
):
    mock_is_changed.return_value = is_changed_return
    mock_result = MagicMock()
    mock_result.returncode = run_git_returncode
    mock_result.stdout = run_git_stdout
    mock_run_git_command.return_value = mock_result

    result = git_utils.get_diff()

    if is_changed_return:
        mock_run_git_command.assert_called_once_with(
            ["--no-pager", "diff", "--no-color"]
        )
    else:
        mock_run_git_command.assert_not_called()

    assert result == expected_output


@pytest.mark.parametrize(
    "stdout, stderr, expected_ret",
    [
        ("Commit successful\n", "", "Commit successful"),
        ("   \n", "Some error\n", "Some error"),
        ("   \n", "   \n", ""),
    ],
)
@patch("commizard.git_utils.run_git_command")
def test_commit(mock_run_git_command, stdout, stderr, expected_ret):
    # arrange: directly configure the mock return value
    mock_run_git_command.return_value.stdout = stdout
    mock_run_git_command.return_value.stderr = stderr
    mock_run_git_command.return_value.returncode = 42

    code, output = git_utils.commit("test message")

    mock_run_git_command.assert_called_once_with(
        ["commit", "-a", "-m", "test message"]
    )
    assert code == 42
    assert output == expected_ret


@pytest.mark.parametrize(
    "input_diff, expected_output",
    [
        (
            "diff --git a/file.py b/file.py\nindex abc..def\n+added line\n"
            "-removed line",
            "+added line\n-removed line",
        ),
        ("+added line\n-removed line", "+added line\n-removed line"),
        ("", ""),
        (
            "diff --git a/file.py b/file.py\nindex abc..def\n"
            "warning: something",
            "",
        ),
        (None, ""),
    ],
)
def test_clean_diff(input_diff, expected_output):
    result = git_utils.clean_diff(input_diff)
    assert result == expected_output


@patch("commizard.git_utils.clean_diff")
@patch("commizard.git_utils.get_diff")
def test_get_clean_diff(mock_diff, mock_clean_diff):
    git_utils.get_clean_diff()
    mock_clean_diff.assert_called_once_with(mock_diff.return_value)
