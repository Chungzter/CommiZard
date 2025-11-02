from unittest.mock import patch

import pytest

from commizard.output import (
    init_console,
    print_error,
    print_generated,
    print_success,
    print_warning,
    wrap_text,
)


@pytest.mark.parametrize(
    "arg",
    [
        True,
        False,
    ],
)
@patch("commizard.output.Console")
def test_init_console(mock_console, arg):
    init_console(arg)
    mock_console.assert_called()


@patch("commizard.output.console.print")
def test_print_success(mock_print):
    print_success("All good")
    mock_print.assert_called_once_with("[green]All good[/green]")


@patch("commizard.output.error_console.print")
def test_print_error(mock_err):
    print_error("Something went wrong")
    mock_err.assert_called_once_with("Error: Something went wrong")


@patch("commizard.output.console.print")
def test_print_warning(mock_print):
    print_warning("Careful!")
    mock_print.assert_called_once_with("[yellow]Warning: Careful![/yellow]")


@patch("commizard.output.console.print")
def test_print_generated(mock_print):
    print_generated("Auto-created file")
    mock_print.assert_called_once_with("[blue]Auto-created file[/blue]")


@pytest.mark.parametrize(
    "text,width,expected",
    [
        ("short line", 10, "short line"),
        ("a long line that should wrap", 10, "a long\nline that\nshould\nwrap"),
        ("para1\n\npara2", 10, "para1\n\npara2"),
        (
            "This is a simple sentence that should wrap neatly.",
            10,
            "This is a\nsimple\nsentence\nthat\nshould\nwrap\nneatly.",
        ),
        (
            "First paragraph here with some text.\n\nSecond paragraph is also here.",
            15,
            "First paragraph\nhere with some\ntext.\n\nSecond\nparagraph is\nalso here.",
        ),
        ("\n\nHello world\n\n", 5, "\n\nHello\nworld\n\n"),
        ("Extraordinarilylongword", 5, "Extraordinarilylongword"),
        ("", 10, ""),
    ],
)
def test_wrap_text(text, width, expected):
    result = wrap_text(text, width=width)
    assert result == expected
