import shutil
from unittest.mock import patch

import pytest
from rich.color import Color

from commizard import start


@pytest.mark.parametrize(
    "text, start_color, end_color, expected_substrings",
    [
        (
            "Hi",
            Color.from_rgb(255, 0, 0),  # red
            Color.from_rgb(0, 0, 255),  # blue
            ["[#ff0000]H", "[#7f007f]i"],
        ),
        (
            "OK",
            Color.from_rgb(0, 255, 0),  # green
            Color.from_rgb(0, 255, 0),  # same color
            ["[#00ff00]O", "[#00ff00]K"],
        ),
        (
            "X",
            Color.from_rgb(0, 0, 0),  # black
            Color.from_rgb(255, 255, 255),  # white
            ["[#000000]X"],
        ),
        (
            "Yo\nHi",
            Color.from_rgb(0, 0, 255),  # blue
            Color.from_rgb(255, 0, 0),  # red
            ["[#0000ff]Y", "[#7f007f]o", "[#0000ff]H", "[#7f007f]i"],
            # checks gradient + newline preserved
        ),
        # Case 6: Longer string gradient black → white
        (
            "ABCDE",
            Color.from_rgb(0, 0, 0),  # black
            Color.from_rgb(255, 255, 255),  # white
            [
                "[#000000]A",
                "[#333333]B",
                "[#666666]C",
                "[#999999]D",
                "[#cccccc]E",
            ],
        ),
    ],
)
def test_gradient_text(text, start_color, end_color, expected_substrings):
    result = start.gradient_text(text, start_color, end_color)

    # Ensure all expected substrings appear in the result
    for substring in expected_substrings:
        assert substring in result

    # Check result structure: every char should be wrapped
    for char in text:
        if char != "\n":
            assert "[#" in result
            assert f"]{char}" in result


def test_gradient_text_none_triplet():
    text = "Some text"
    end_color = Color.default()
    start_color = Color.default()
    substr = ["S", "o", "m", "e", " ", "t", "e", "x", "t"]
    result = start.gradient_text(text, start_color, end_color)

    for substring in substr:
        assert substring in result

    # Check result structure: every char should be wrapped
    for char in text:
        if char != "\n":
            assert "[#" not in result
            assert f"]{char}" not in result


@pytest.mark.parametrize(
    "color_sys, expect_gradient, should_colorize",
    [
        ("truecolor", True, True),
        ("256", True, True),
        ("windows", False, True),
        (None, False, True),
        ("truecolor", False, False),
        ("256", False, False),
    ],
)
def test_print_welcome(
    monkeypatch, capsys, color_sys, expect_gradient, should_colorize
):
    # class to patch instead of rich.Console() class
    class DummyConsole:
        def __init__(self, color_system):
            if color_system == "auto":
                self.color_system = color_sys
            else:
                self.color_system = color_system

        def print(self, msg):
            print(msg)

    monkeypatch.setattr(start, "Console", DummyConsole)

    start.print_welcome(should_colorize)

    # Hook to stdout
    captured = capsys.readouterr().out

    if should_colorize:
        if expect_gradient:
            assert "[#" in captured
        else:
            # Should contain fallback purple markup
            assert "[bold purple]" in captured
    else:
        assert "[#" not in captured


@pytest.mark.parametrize(
    "git_path, expected",
    [
        ("/usr/bin/git", True),
        ("C:\\Program Files\\Git\\cmd\\git.EXE", True),
        (None, False),
        ("some/other/path/maybe/in/macOS", True),
    ],
)
def test_check_git_installed(monkeypatch, git_path, expected):
    # Monkeypatch shutil.which to simulate environment
    monkeypatch.setattr(
        shutil, "which", lambda cmd: git_path if cmd == "git" else None
    )

    assert start.check_git_installed() is expected


@pytest.mark.parametrize(
    "ret_code, resp, expected",
    [
        (200, {"version": "something"}, True),
        (
            200,
            {"version": "something", 123: 456, "another_key": "Owlama", 2: 5},
            True,
        ),
        (404, {"error": "something"}, False),
        (200, {"version": 3.1415}, True),
        (200, {"another_api_result": 3.1415}, False),
        (-5, {"version": "something"}, False),
        (-1, {"version": "something"}, False),
        (200, "not a dict", False),
        (69420, 12345, False),
    ],
)
@patch("commizard.start.llm_providers.http_request")
def test_local_ai_available(mock_req, ret_code, resp, expected):
    mock_req.return_value.return_code = ret_code
    mock_req.return_value.response = resp
    out = start.local_ai_available()
    assert out == expected


@patch("commizard.start.git_utils.is_inside_working_tree")
def test_is_inside_working_tree(mock):
    start.is_inside_working_tree()
    mock.assert_called_once()
