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


def test_print_success(capsys):
    print_success("All good")
    captured = capsys.readouterr()

    assert "All good" in captured.out
    assert "[green]" not in captured.out  # markup should be rendered
    assert captured.err == ""


def test_print_error(capsys):
    print_error("Something went wrong")
    captured = capsys.readouterr()
    assert "Error: Something went wrong" in captured.err
    assert captured.out == ""


def test_print_warning(capsys):
    print_warning("Careful!")
    captured = capsys.readouterr()
    assert "Warning: Careful!" in captured.out
    assert captured.err == ""


def test_print_generated(capsys):
    print_generated("Auto-created file")
    captured = capsys.readouterr()
    assert "Auto-created file" in captured.out
    assert captured.err == ""


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
