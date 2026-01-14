from __future__ import annotations

from unittest.mock import MagicMock, Mock, call, patch

import pytest
import requests

from commizard import llm_providers as llm
from commizard.llm_providers import HttpResponse


@pytest.mark.parametrize(
    "method, raises",
    [
        ("get", False),
        ("DELETE", False),
        ("doesn't exist", True),
    ],
)
@patch("commizard.llm_providers.requests.request")
def test_http_request_init_method_processing(mock_request, method, raises):
    url = "https://example.com"

    if raises:
        with pytest.raises(
            ValueError, match=f"{method.upper()} is not a valid method."
        ):
            _ = llm.HttpRequest(method, url)
        mock_request.assert_not_called()
    else:
        _ = llm.HttpRequest(method, url)
        mock_request.assert_called_once_with(method.upper(), url)


@pytest.mark.parametrize(
    "is_text, resp",
    [
        (False, {"test": True, "content": "this is a JSON response"}),
        (True, "This is a text response"),
    ],
)
@patch("commizard.llm_providers.requests.request")
def test_http_request_no_raises(mock_request, is_text, resp):
    url = "https://example.com"
    method = "POST"
    mock = Mock()
    mock.status_code = 123456
    if is_text:
        mock.json.side_effect = requests.exceptions.JSONDecodeError(
            "err", "doc", 0
        )
        mock.text = resp
    else:
        mock.json.return_value = resp
    mock_request.return_value = mock

    obj = llm.HttpRequest(method, url, testkwargs="testing")
    mock_request.assert_called_once_with(method, url, testkwargs="testing")
    assert obj.response == resp
    assert obj.return_code == 123456
    assert not obj.is_error()
    assert obj.err_message() == ""


@pytest.mark.parametrize(
    "exception, expected_retval, err_str",
    [
        (requests.ConnectionError, -1, "can't connect to the server"),
        (requests.HTTPError, -2, "HTTP error occurred"),
        (requests.TooManyRedirects, -3, "too many redirects"),
        (requests.Timeout, -4, "the request timed out"),
        (requests.RequestException, -5, "There was an ambiguous error"),
    ],
)
@patch("commizard.llm_providers.requests.request")
def test_http_request_requestslib_exceptions(
    mock_request, exception, expected_retval, err_str
):
    url = "https://example.com"
    method = "PATCH"
    mock_request.side_effect = exception

    obj = llm.HttpRequest(method, url)
    mock_request.assert_called_once_with(method, url)
    assert obj.response is None
    assert obj.return_code == expected_retval
    assert obj.is_error()
    assert obj.err_message() == err_str


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


@pytest.mark.parametrize(
    "encoding, expected",
    [(None, "utf-8"), ("ANSI", "ANSI"), ("utf-8", "utf-8")],
)
@patch("commizard.llm_providers.requests.request")
def test_stream_request_init_correct_encoding(mock_request, encoding, expected):
    url = "https://test.com"
    method = "TEST"
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.encoding = encoding
    mock_request.return_value = mock_resp

    obj = llm.StreamRequest(method, url)
    mock_request.assert_called_once_with(
        method, url, timeout=(0.5, 5), stream=True
    )
    assert obj.response.encoding == expected


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


def test_stream_request_iterator_protocol_no_raises():
    stream_object = llm.StreamRequest.__new__(llm.StreamRequest)
    stream_object.response = Mock()
    data_for_test = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    stream_object.response.iter_lines.return_value = data_for_test
    stream_object.error = (False, "")

    for test, actual in zip(stream_object, data_for_test):
        assert test == actual


def test_stream_request_dunder_next_no_raises():
    stream_object = llm.StreamRequest.__new__(llm.StreamRequest)
    iterable = [1, 2, 3, 4, 5]
    stream_object.stream = iter(iterable)
    assert stream_object.__next__() == next(iter(iterable))


def test_stream_request_dunder_next_severed_connection():
    stream_object = llm.StreamRequest.__new__(llm.StreamRequest)

    class FakeStream:
        def __next__(self):
            raise requests.exceptions.ChunkedEncodingError

    stream_object.stream = FakeStream()
    with pytest.raises(
        llm.StreamError,
        match=r"The server closed the connection before the full response was"
        " received.",
    ):
        stream_object.__next__()


@pytest.mark.parametrize("error", [(False, ""), (True, "Test error")])
def test_stream_request_dunder_iter(error: tuple[bool, str]):
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


@pytest.mark.parametrize(
    "is_error, response, expected_result",
    [
        # http_request returns error
        (True, None, None),
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
        ),
        # http_request succeeds but no models
        (False, {"models": []}, []),
        # Bizzare case where There isn't any error but response is None
        (False, None, None),
    ],
)
@patch("commizard.llm_providers.HttpRequest")
def test_list_locals(
    mock_http_request,
    is_error,
    response,
    expected_result,
):
    mock_http_request.return_value.is_error.return_value = is_error
    mock_http_request.return_value.response = response

    result = llm.list_locals()
    if is_error:
        assert result is None
    else:
        assert result == expected_result
    mock_http_request.assert_called_once()


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
    "sse_events, expected_results",
    [
        # 1. Real output from OpenRouter.ai
        (
            [
                ": OPENROUTER PROCESSING",
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":"!"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                ": OPENROUTER PROCESSING",
                "",
                ": OPENROUTER PROCESSING",
                "",
                ": OPENROUTER PROCESSING",
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":" How"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":" can"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":" I"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":" help"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":" you"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":" today"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":"?"},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"system_fingerprint":""}',
                "",
                ": OPENROUTER PROCESSING",
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":"stop","native_finish_reason":"stop","logprobs":null}],"system_fingerprint":""}',
                "",
                'data: {"id":"gen-1769532074","provider":"Liquid","model":"liquid/lfm-2.5-1.2b-instruct:free","object":"chat.completion.chunk","created":1769532074,"choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null,"native_finish_reason":null,"logprobs":null}],"usage":{"prompt_tokens":15,"completion_tokens":10,"total_tokens":25,"cost":0,"is_byok":false,"prompt_tokens_details":{"cached_tokens":0,"audio_tokens":0},"cost_details":{"upstream_inference_cost":0,"upstream_inference_prompt_cost":0,"upstream_inference_completions_cost":0},"completion_tokens_details":{"reasoning_tokens":0,"audio_tokens":0}}}',
                "",
                "data: [DONE]",
                "",
            ],
            [
                "",
                "Hello",
                "!",
                " How",
                " can",
                " I",
                " help",
                " you",
                " today",
                "?",
                "",
                "",
            ],
        ),
        # 2. edge cases
        (
            [
                'data: {"choices":[{"index":0,"delta":{"content":"foo"}}]}',
                'data: {"choices":[{"index":0}]}',
                'data: {"choices":[{"index":0,"delta":{"content":"bacon"}}]}',
                'data: {"choices":[{"index":0,"delta":{"not-content":"ham"}}]}',
                "no data here, skip it",
                "data: [DONE]",
                "data: We shouldn't read these",
                '[data: {"choices":[{"index":0,"delta":{"content":"eggs"}}]}',
            ],
            ["foo", "bacon"],
        ),
    ],
)
@patch("commizard.llm_providers.output.print_token")
@patch("commizard.llm_providers.output.set_stream_print_width")
@patch("commizard.llm_providers.output.live_stream")
@patch("commizard.llm_providers.StreamRequest")
def test_stream_generate_no_error(
    mock_stream_request,
    mock_live_stream,
    mock_set_stream_print_width,
    mock_print_token,
    sse_events,
    expected_results,
    monkeypatch,
):
    monkeypatch.setattr(llm, "selected_model", "mymodel")

    stream_obj = MagicMock()
    stream_obj.__iter__.return_value = iter(sse_events)
    stream_obj.__enter__.return_value = stream_obj
    mock_stream_request.return_value = stream_obj

    res = llm.stream_generate("testing")
    mock_stream_request.assert_called_once()
    mock_live_stream.assert_called_once()
    mock_set_stream_print_width.assert_called_once_with(70)
    expected_calls = [call(i) for i in expected_results]
    mock_print_token.assert_has_calls(expected_calls)
    assert res == (0, "".join(expected_results))


@pytest.mark.parametrize(
    "sse_event, expected_return",
    [
        # 1. Incorrect JSON responses
        (
            ['data: {"not_a_correct_name":[{"delta":{"content":"foo"}}]}'],
            (1, "Couldn't find response from JSON: Invalid output"),
        ),
        (
            ['data: {"choices":{"delta":{"content":"foo"}}}'],
            (1, "Couldn't find response from JSON: Invalid output"),
        ),
        # 2. invalid response (Not JSON)
        ([": We should skip this", "no exception should raise here"], (0, "")),
        (
            ['data: "choices" : "not_correct_JSON"'],
            (1, "Couldn't decode JSON response"),
        ),
        (
            ["data: someone's messing with us!"],
            (1, "Couldn't decode JSON response"),
        ),
    ],
)
@patch("commizard.llm_providers.output.print_token")
@patch("commizard.llm_providers.output.set_stream_print_width")
@patch("commizard.llm_providers.output.live_stream")
@patch("commizard.llm_providers.StreamRequest")
def test_stream_generate_bad_response(
    mock_stream_request,
    mock_live_stream,
    mock_set_stream_print_width,
    mock_print_token,
    sse_event,
    expected_return,
    monkeypatch,
):
    monkeypatch.setattr(llm, "selected_model", "mymodel")
    stream_obj = MagicMock()
    stream_obj.__iter__.return_value = iter(sse_event)
    stream_obj.__enter__.return_value = stream_obj
    mock_stream_request.return_value = stream_obj

    res = llm.stream_generate("testing")
    mock_stream_request.assert_called_once()
    mock_live_stream.assert_called_once()
    mock_set_stream_print_width.assert_called_once_with(70)
    mock_print_token.assert_not_called()
    assert res == expected_return


@patch("commizard.llm_providers.StreamRequest")
def test_stream_generate_stream_error(
    mock_stream_request,
    monkeypatch,
):
    monkeypatch.setattr(llm, "selected_model", "mymodel")
    mock_stream_request.side_effect = llm.StreamError("test exception")
    res = llm.stream_generate("testing")
    assert res == (1, "test exception")


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
