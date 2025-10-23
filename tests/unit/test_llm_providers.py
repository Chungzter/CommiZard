from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from commizard import llm_providers as llm


@pytest.mark.parametrize(
    "response, return_code, expected_is_error, expected_err_message",
    [
        # Non-error responses
        ("ok", 200, False, ""),
        ("created", 201, False, ""),
        ("empty", 0, False, ""),
        ({"reason": "not found"}, 404, False, ""),
        # Error cases
        ("404", -1, True, "can't connect to the server"),
        ("success", -2, True, "HTTP error occurred"),
        ({1: "found"}, -3, True, "too many redirects"),
        ("", -4, True, "the request timed out"),
    ],
)
def test_http_response(
    response, return_code, expected_is_error, expected_err_message
):
    http_resp = llm.HttpResponse(response, return_code)

    assert http_resp.response == response
    assert http_resp.return_code == return_code
    assert http_resp.is_error() == expected_is_error
    assert http_resp.err_message() == expected_err_message


@pytest.mark.parametrize(
    "method, return_value, side_effect, expected_response, expected_code,"
    "expected_exception",
    [
        # --- Success cases ---
        (
            "GET",
            {"json": {"key": "val"}, "status": 200},
            None,
            {"key": "val"},
            200,
            None,
        ),
        (
            "GET",
            {
                "json": requests.exceptions.JSONDecodeError("err", "doc", 0),
                "text": "plain text",
                "status": 200,
            },
            None,
            "plain text",
            200,
            None,
        ),
        (
            "POST",
            {"json": {"ok": True}, "status": 201},
            None,
            {"ok": True},
            201,
            None,
        ),
        (
            "GET",
            {"json": {"key": "val"}, "status": 503},
            None,
            {"key": "val"},
            503,
            None,
        ),
        # --- Error branches ---
        ("GET", None, requests.ConnectionError, None, -1, None),
        ("GET", None, requests.HTTPError, None, -2, None),
        ("GET", None, requests.TooManyRedirects, None, -3, None),
        ("GET", None, requests.Timeout, None, -4, None),
        ("GET", None, requests.RequestException, None, -5, None),
        # --- Invalid methods ---
        ("PUT", None, None, None, None, NotImplementedError),
        ("FOO", None, None, None, None, ValueError),
    ],
)
@patch("requests.get")
@patch("requests.post")
def test_http_request(
    mock_post,
    mock_get,
    method,
    return_value,
    side_effect,
    expected_response,
    expected_code,
    expected_exception,
):
    # pick which mock to configure
    mock_target = None
    if method.upper() == "GET":
        mock_target = mock_get
    elif method.upper() == "POST":
        mock_target = mock_post

    # setup mock_target based on the return_value dict
    if mock_target:
        if side_effect:
            mock_target.side_effect = side_effect
        else:
            mock_resp = Mock()
            mock_resp.status_code = return_value["status"]
            if isinstance(return_value.get("json"), Exception):
                mock_resp.json.side_effect = return_value["json"]
            else:
                mock_resp.json.return_value = return_value.get("json")
            mock_resp.text = return_value.get("text")
            mock_target.return_value = mock_resp

    if expected_exception:
        with pytest.raises(expected_exception):
            llm.http_request(method, "https://test.com")
    else:
        result = llm.http_request(method, "https://test.com")
        assert isinstance(result, llm.HttpResponse)
        assert result.response == expected_response
        assert result.return_code == expected_code


@patch("commizard.llm_providers.list_locals")
def test_init_model_list(mock_list, monkeypatch):
    monkeypatch.setattr(llm, "available_models", None)
    llm.init_model_list()
    mock_list.assert_called_once()


@pytest.mark.parametrize(
    "is_error, response, expected_result, expect_error",
    [
        # http_request returns error
        (True, None, [], True),
        # http_request succeeds with models
        (
            False,
            {"models": [{"name": "model1"}, {"name": "model2"}]},
            ["model1", "model2"],
            False,
        ),
        # http_request succeeds but no models
        (False, {"models": []}, [], False),
    ],
)
@patch("commizard.llm_providers.http_request")
def test_list_locals(
    mock_http_request,
    is_error,
    response,
    expected_result,
    expect_error,
):
    fake_response = Mock()
    fake_response.is_error.return_value = is_error
    fake_response.response = response
    mock_http_request.return_value = fake_response

    result = llm.list_locals()
    if expect_error:
        assert result is None
    else:
        assert result == expected_result
    mock_http_request.assert_called_once()


@pytest.mark.parametrize(
    "is_error, response, expect_error, expected_result",
    [
        (True, None, True, {}),
        (False, {"done_reason": "load"}, False, {"done_reason": "load"}),
    ],
)
@patch("commizard.llm_providers.output.print_error")
@patch("commizard.llm_providers.http_request")
def test_load_model(
    mock_http_request,
    mock_print_error,
    monkeypatch,
    is_error,
    response,
    expect_error,
    expected_result,
):
    fake_response = Mock()
    fake_response.is_error.return_value = is_error
    fake_response.response = response
    mock_http_request.return_value = fake_response
    monkeypatch.setattr(llm, "selected_model", "patched_model")
    result = llm.load_model("test_model")

    mock_http_request.assert_called_once()
    if expect_error:
        mock_print_error.assert_called_once_with(
            "Failed to load test_model. Is ollama running?"
        )
    else:
        mock_print_error.assert_not_called()
    assert result == expected_result


@pytest.mark.parametrize(
    "initial_model, response_is_error, expected_model_after, should_call_success, should_call_error",
    [
        # No model loaded
        (None, False, None, False, False),
        # Unload succeeds
        ("llama3", False, None, True, False),
        # Unload fails
        ("mistral", True, "mistral", False, True),
    ],
)
@patch("commizard.llm_providers.output.print_success")
@patch("commizard.llm_providers.output.print_error")
@patch("commizard.llm_providers.http_request")
def test_unload_model(
    mock_http_request,
    mock_print_error,
    mock_print_success,
    initial_model,
    response_is_error,
    expected_model_after,
    should_call_success,
    should_call_error,
    monkeypatch,
):
    monkeypatch.setattr(llm, "selected_model", initial_model)
    mock_response = Mock()
    mock_response.is_error.return_value = response_is_error
    mock_response.err_message.return_value = "Connection failed"
    mock_http_request.return_value = mock_response

    llm.unload_model()

    if initial_model is None:
        mock_http_request.assert_not_called()
        mock_print_error.assert_not_called()
        mock_print_success.assert_not_called()
    else:
        mock_http_request.assert_called_once()
        assert mock_print_error.called == should_call_error
        assert mock_print_success.called == should_call_success

    # Verify global state
    assert llm.selected_model == expected_model_after


@pytest.mark.parametrize(
    "error_code, expected_result",
    [
        (
            503,
            "Error 503: Service Unavailable - Ollama service is not responding.\n"
            "Please do let the dev team know if this keeps happening.\n",
        ),
        (
            499,
            "Error 499: Client Error - This appears to be a configuration or request issue.\n"
            "Suggestions:\n"
            "  • Verify your request parameters and model name\n"
            "  • Check Ollama documentation: https://github.com/ollama/ollama/blob/main/docs/api.md\n"
            "  • Review your commizard configuration",
        ),
        (
            599,
            "Error 599: Server Error - This appears to be an issue with the Ollama service.\n"
            "Suggestions:\n"
            "  • Try restarting Ollama: ollama serve\n"
            "  • Check Ollama logs for more information\n"
            "  • Wait a moment and try again",
        ),
        (
            999,
            "Error 999: Unexpected response.\n"
            "Check the Ollama documentation or server logs for more details.",
        ),
    ],
)
def test_get_error_message(error_code, expected_result):
    assert llm.get_error_message(error_code) == expected_result


@pytest.mark.parametrize(
    "is_error, return_code, response_dict, err_msg, expected",
    [
        (
            True,
            -1,
            None,
            "can't connect to the server",
            (1, "can't connect to the server"),
        ),
        (False, 200, {"response": "Hello world"}, None, (0, "Hello world")),
        (False, 200, {"response": "  Hello world\n"}, None, (0, "Hello world")),
        (
            False,
            500,
            {"error": "ignored"},
            None,
            (
                500,
                "Error 500: Internal Server Error - Ollama encountered an unexpected error.\nSuggestions:\n  • The model may have run out of memory (RAM/VRAM)\n  • Try restarting Ollama: ollama serve\n  • Check Ollama logs for detailed error information\n  • Consider using a smaller model if resources are limited",
            ),
        ),
    ],
)
@patch("commizard.llm_providers.http_request")
def test_generate(
    mock_http_request,
    is_error,
    return_code,
    response_dict,
    err_msg,
    expected,
    monkeypatch,
):
    fake_response = MagicMock()
    fake_response.is_error.return_value = is_error
    fake_response.return_code = return_code
    fake_response.response = response_dict
    fake_response.err_message.return_value = err_msg
    mock_http_request.return_value = fake_response

    monkeypatch.setattr(llm, "selected_model", "mymodel")

    result = llm.generate("Test prompt")

    mock_http_request.assert_called_once()
    assert result == expected


@patch("commizard.llm_providers.http_request")
def test_generate_none_selected(mock_http_request, monkeypatch):
    monkeypatch.setattr(llm, "selected_model", None)
    err_str = (
        "No model selected. You must use the start command to specify"
        "which model to use before generating.\nExample: start model_name"
    )
    res = llm.generate("Test prompt")
    mock_http_request.assert_not_called()
    assert res == (1, err_str)


@pytest.mark.parametrize(
    "select_str, load_val, should_print",
    [
        ("modelA", {"done_reason": "load"}, True),
        ("modelB", {"done_reason": "error"}, False),
        ("modelC", {}, False),
    ],
)
@patch("commizard.llm_providers.load_model")
@patch("commizard.llm_providers.output.print_success")
def test_select_model(
    mock_print, mock_load, select_str, load_val, should_print, monkeypatch
):
    monkeypatch.setattr(llm, "selected_model", None)

    mock_load.return_value = load_val

    llm.select_model(select_str)
    assert llm.selected_model == select_str
    mock_load.assert_called_once_with(select_str)

    if should_print:
        mock_print.assert_called_once_with(f"{llm.selected_model} loaded.")
    else:
        mock_print.assert_not_called()
