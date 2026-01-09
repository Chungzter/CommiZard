from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from commizard import llm_providers as llm
from commizard.llm_providers import HttpResponse


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
            "get",
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
            "PUT",
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
        ("FOO", None, ValueError, None, None, ValueError),
    ],
)
@patch("commizard.llm_providers.requests.request")
def test_http_request(
    mock_request,
    method,
    return_value,
    side_effect,
    expected_response,
    expected_code,
    expected_exception,
):
    # setup mock_target based on the return_value dict
    if side_effect:
        mock_request.side_effect = side_effect
    else:
        mock_resp = Mock()
        mock_resp.status_code = return_value["status"]
        if isinstance(return_value.get("json"), Exception):
            mock_resp.json.side_effect = return_value["json"]
        else:
            mock_resp.json.return_value = return_value.get("json")
        mock_resp.text = return_value.get("text")
        mock_request.return_value = mock_resp

    if expected_exception:
        with pytest.raises(expected_exception):
            llm.http_request(method, "https://test.com")
    else:
        result = llm.http_request(method, "https://test.com")
        assert isinstance(result, llm.HttpResponse)
        assert result.response == expected_response
        assert result.return_code == expected_code


@pytest.mark.parametrize(
    "kwargs, expected_kwargs, error, status_code",
    [
        # 1. test kwarg passing correctly
        (
            {"data": "test"},
            {"data": "test", "stream": True, "timeout": (0.5, 5)},
            [(False, ""), None],
            200,
        ),
        (
            {"json": 1234, "stream": True},
            {"json": 1234, "stream": True, "timeout": (0.5, 5)},
            [(False, ""), None],
            200,
        ),
        (
            {"data": "test", "timeout": (1, 2)},
            {"data": "test", "timeout": (1, 2), "stream": True},
            [(False, ""), None],
            200,
        ),
        (
            {"test": [1, 2, 3], "timeout": (69, 420), "stream": False},
            {"test": [1, 2, 3], "timeout": (69, 420), "stream": False},
            [(False, ""), None],
            200,
        ),
        # 2. test error status code (404, 503, etc.)
        (
            {"data": "test"},
            {"data": "test", "stream": True, "timeout": (0.5, 5)},
            [(True, llm.get_error_message(404)), None],
            404,
        ),
        # 3. test exceptions thrown by requests
        (
            {"stream": True, "timeout": (0.5, 5)},
            {"stream": True, "timeout": (0.5, 5)},
            [(True, "Cannot connect to the server"), requests.ConnectionError],
            69,
        ),
        (
            {"stream": True, "timeout": (0.5, 5)},
            {"stream": True, "timeout": (0.5, 5)},
            [(True, "HTTP error occurred"), requests.HTTPError],
            69,
        ),
        (
            {"stream": True, "timeout": (0.5, 5)},
            {"stream": True, "timeout": (0.5, 5)},
            [(True, "Too many redirects"), requests.TooManyRedirects],
            69,
        ),
        (
            {"stream": True, "timeout": (0.5, 5)},
            {"stream": True, "timeout": (0.5, 5)},
            [(True, "request timed out"), requests.Timeout],
            69,
        ),
        (
            {"stream": True, "timeout": (0.5, 5)},
            {"stream": True, "timeout": (0.5, 5)},
            [(True, "There was an ambiguous error"), requests.RequestException],
            69,
        ),
    ],
)
@patch("commizard.llm_providers.requests.request")
def test_stream_request_init(
    mock_request, kwargs, expected_kwargs, error, status_code
):
    url = "https://test.com"
    method = "TEST"
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_request.return_value = mock_resp
    mock_request.side_effect = error[1]

    obj = llm.StreamRequest(method, url, **kwargs)
    mock_request.assert_called_once_with(method, url, **expected_kwargs)
    assert obj.error == error[0]

    if error[0][0]:
        assert obj.response is None
    else:
        assert obj.response == mock_resp


@pytest.mark.parametrize("exception", [ValueError, llm.StreamError, None])
def test_stream_request_context_manager(exception):
    stream_object = llm.StreamRequest.__new__(llm.StreamRequest)
    stream_object.response = Mock()
    stream_object.error = ("doesn't", "matter")

    if exception is None:
        with stream_object as obj:
            assert obj is stream_object
    else:
        with pytest.raises(exception), stream_object as obj:
            assert obj is stream_object
            raise exception()

    stream_object.response.close.assert_called_once()


def test_stream_request_context_manager_none_response():
    """
    In here, we just check that the close method doesn't get called on None type
    If it does, the function will raise the following exception:
    AttributeError: 'NoneType' object has no attribute 'close'
    """
    stream_object = llm.StreamRequest.__new__(llm.StreamRequest)
    stream_object.response = None

    with stream_object as obj:
        assert obj is stream_object


def test_stream_request_exit_propagates_exceptions_and_allows_normal_exit():
    stream_object = llm.StreamRequest.__new__(llm.StreamRequest)
    stream_object.response = Mock()

    # 1. correctly propagates exceptions
    result = stream_object.__exit__(ValueError, ValueError(), None)
    assert result is False

    # 2. correctly returns on no exception
    result = stream_object.__exit__(None, None, None)
    assert result is None

@pytest.mark.parametrize("error", [(False, ""), (True, "Test error")])
def test_stream_request_iter(error: tuple[bool, str]):
    stream_object = llm.StreamRequest.__new__(llm.StreamRequest)
    stream_object.error = error
    stream_object.stream = None

    if error[0]:
        with pytest.raises(llm.StreamError, match=error[1]):
            stream_object.__iter__()
        assert stream_object.stream is None
    else:
        stream_object.response = Mock()
        # make a mock iterable return value
        stream_object.response.iter_lines.return_value = [1, 2, 3]

        obj = stream_object.__iter__()

        stream_object.response.iter_lines.assert_called_once_with(
            decode_unicode=True
        )
        assert obj is stream_object
        assert type(stream_object.stream) is type(iter([]))


@patch("commizard.llm_providers.list_locals")
def test_init_model_list(mock_list, monkeypatch):
    monkeypatch.setattr(llm, "available_models", None)

    # first case: None returned by list_locals()
    mock_list.return_value = None
    llm.init_model_list()
    mock_list.assert_called_once()
    assert llm.available_models is None

    # second case: correct output from list_locals()
    monkeypatch.setattr(llm, "available_models", None)
    mock_list.return_value = [["gpt-1", "10b"], ["gpt-2", "5b"]]
    llm.init_model_list()
    mock_list.assert_called()
    assert llm.available_models == ["gpt-1", "gpt-2"]


@pytest.mark.parametrize(
    "is_error, response, expected_result, expect_error",
    [
        # http_request returns error
        (True, None, [], True),
        # http_request succeeds with models
        (
            False,
            {
                "models": [
                    {
                        "name": "model1",
                        "details": {1: "bacon", "parameter_size": "5b"},
                    },
                    {
                        "name": "model2",
                        "details": {"happy": False, "parameter_size": "135m"},
                    },
                ]
            },
            [["model1", "5b"], ["model2", "135m"]],
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


@patch("commizard.llm_providers.http_request")
def test_request_load_model(mock_http_request, monkeypatch):
    monkeypatch.setattr(llm.config, "LLM_URL", "TEST/")
    retval = HttpResponse("response", 420)
    mock_http_request.return_value = retval
    assert llm.request_load_model("gpt") == retval
    mock_http_request.assert_called_once_with(
        "POST", "TEST/api/generate", json={"model": "gpt"}, timeout=(0.3, 600)
    )


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
        (
            False,
            200,
            {
                "choices": [
                    {"message": {"role": "user", "content": "Hello world"}}
                ]
            },
            None,
            (0, "Hello world"),
        ),
        (
            False,
            200,
            {
                "choices": [
                    {"message": {"role": "user", "content": "  Hello world\n"}}
                ]
            },
            None,
            (0, "  Hello world\n"),
        ),
        (
            False,
            500,
            {"error": "ignored"},
            None,
            (
                500,
                "Error 500: Internal Server Error - Ollama encountered an "
                "unexpected error.\nSuggestions:\n  • The model may have run"
                " out of memory (RAM/VRAM)\n  • Try restarting Ollama: ollama "
                "serve\n  • Check Ollama logs for detailed error information\n "
                " • Consider using a smaller model if resources are limited",
            ),
        ),
        # real world test case
        (
            False,
            200,
            {
                "id": "chatcmpl-406",
                "object": "chat.completion",
                "created": 1767616167,
                "model": "smollm:135m",
                "system_fingerprint": "fp_ollama",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello! How can I help you today?",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 10,
                    "total_tokens": 21,
                },
            },
            None,
            (0, "Hello! How can I help you today?"),
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
        "No model selected. You must use the start command to specify "
        "which model to use before generating.\nExample: start model_name"
    )
    res = llm.generate("Test prompt")
    mock_http_request.assert_not_called()
    assert res == (1, err_str)


@pytest.mark.parametrize(
    "model_name, load_res, expected_return, selected_model_result",
    [
        (
            "gpt",
            HttpResponse("test", -1),
            (
                1,
                f"failed to load gpt: {HttpResponse(str(1), -1).err_message()}",
            ),
            None,
        ),
        (
            "llama",
            HttpResponse("404", 404),
            (1, llm.get_error_message(404)),
            None,
        ),
        (
            "smollm",
            HttpResponse({"done_reason": "load"}, 200),
            (0, "smollm loaded."),
            "smollm",
        ),
        (
            "fara",
            HttpResponse({"done_reason": "spooky error"}, 200),
            (
                1,
                "There was an unknown problem loading the model.\n"
                " Please report this issue.",
            ),
            None,
        ),
    ],
)
@patch("commizard.llm_providers.request_load_model")
def test_select_model(
    mock_load,
    model_name,
    load_res,
    expected_return,
    selected_model_result,
    monkeypatch,
):
    monkeypatch.setattr(llm, "selected_model", None)
    mock_load.return_value = load_res
    assert llm.select_model(model_name) == expected_return
    assert llm.selected_model == selected_model_result
