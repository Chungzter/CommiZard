from __future__ import annotations

import json

import requests

from . import config, output

available_models: list[str] | None = None
selected_model: str | None = None
gen_message: str | None = None

# Ironically enough, I've used Chat-GPT to write a prompt to prompt other
# Models (or even itself in the future!)
generation_prompt = """
You are an assistant that generates good, professional Git commit messages.

Guidelines:
- Write a concise, descriptive commit title in **imperative mood** (e.g., "fix
parser bug").
- Keep the title under 50 characters if possible.
- If needed, add a commit body separated by a blank line:
  - Explain *what* changed and *why* (not how).
- Do not include anything except the commit message itself (no commentary or
formatting).
- Do not include Markdown formatting, code blocks, quotes, or symbols such as
``` or **.

Here is the diff:
"""


class HttpResponse:
    def __init__(self, response, return_code):
        self.response = response
        # if the value is less than zero, there's something wrong.
        self.return_code = return_code

    def is_error(self) -> bool:
        return self.return_code < 0

    def err_message(self) -> str:
        if not self.is_error():
            return ""
        err_dict = {
            -1: "can't connect to the server",
            -2: "HTTP error occurred",
            -3: "too many redirects",
            -4: "the request timed out",
        }
        return err_dict[self.return_code]


def http_request(method: str, url: str, **kwargs) -> HttpResponse:
    resp = None
    method = method.upper()  # All methods are upper case
    try:
        if method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            r = requests.request(method, url, **kwargs)  # noqa: S113
        else:
            raise ValueError(f"{method} is not a valid method.")
        try:
            resp = r.json()
        except requests.exceptions.JSONDecodeError:
            resp = r.text
        ret_val = r.status_code
    except requests.ConnectionError:
        ret_val = -1
    except requests.HTTPError:
        ret_val = -2
    except requests.TooManyRedirects:
        ret_val = -3
    except requests.Timeout:
        ret_val = -4
    except requests.RequestException:
        ret_val = -5
    return HttpResponse(resp, ret_val)


class StreamError(Exception):
    pass


class StreamRequest:
    """
    Streams an HTTP request.
    This class is intended to be used as an iterator.

    Example usage:
        for l in StreamRequest("GET", "https://example.com"):
            print(l)
    """

    def __init__(self, method: str, url: str, **kwargs):
        # set default values if the kwargs don't provide it
        if kwargs.get("stream") is None:
            kwargs["stream"] = True
        elif kwargs.get("timeout") is None:
            kwargs["timeout"] = (0.5, 5)
        self.response = None
        try:
            r = requests.request(method, url, **kwargs)  # noqa: S113
            if r.encoding is None:
                r.encoding = "utf-8"

            # Skip initialization if the status code was wrong
            if r.status_code != 200:
                self.error = (True, get_error_message(r.status_code))
                return

            self.response = r
            self.error = (False, "")
        except requests.ConnectionError:
            self.error = (True, "Cannot connect to the server")
        except requests.HTTPError:
            self.error = (True, "HTTP error occurred")
        except requests.TooManyRedirects:
            self.error = (True, "Too many redirects")
        except requests.Timeout:
            self.error = (True, "request timed out")
        except requests.RequestException:
            self.error = (True, "There was an ambiguous error")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.response is not None:
            self.response.close()

        # Don't catch any exceptions and let them propagate
        if exc_type is not None:
            return False
        return None

    def __iter__(self):
        # throw an exception if there was an error in the initial request
        if self.error[0]:
            raise StreamError(self.error[1])

        # convert the response to an iterator
        self.stream = iter(self.response.iter_lines(decode_unicode=True))

        return self

    def __next__(self):
        try:
            return next(self.stream)
        except requests.exceptions.ChunkedEncodingError:
            raise StreamError(
                "The server closed the connection before "
                "the full response was received."
            ) from None


def init_model_list() -> None:
    """
    Initialize the list of available models inside the available_models global
    variable.
    """
    global available_models
    models = list_locals()
    if models is None:
        available_models = None
    else:
        available_models = [member[0] for member in models]


def list_locals() -> list[list[str]] | None:
    """
    return a list of available local AI models
    """
    url = config.LLM_URL + "api/tags"
    r = http_request("GET", url, timeout=0.3)
    if r.is_error():
        return None
    r = r.response["models"]
    return [[model["name"], model["details"]["parameter_size"]] for model in r]


def select_model(select_str: str) -> tuple[int, str]:
    """
    Select the local model for use
    Returns:
        a tuple of the return code and the response. The return code is 0 if the
        model was selected, 1 if there were an error. The response is the result
        message
    """
    load_res = request_load_model(select_str)
    if load_res.is_error():
        return 1, f"failed to load {select_str}: {load_res.err_message()}"
    elif load_res.return_code != 200:
        return 1, get_error_message(load_res.return_code)
    elif load_res.response.get("done_reason") == "load":
        global selected_model
        selected_model = select_str
        return 0, f"{select_str} loaded."
    else:
        return (
            1,
            "There was an unknown problem loading the model.\n"
            " Please report this issue.",
        )


def request_load_model(model_name: str) -> HttpResponse:
    """
    Send a request to load the local model into RAM
    Args:
        model_name: name of the model to load

    Returns:
        a HttpResponse object
    """
    payload = {"model": model_name}
    url = config.gen_request_url()
    return http_request("POST", url, json=payload, timeout=(0.3, 600))


def unload_model() -> None:
    """
    Unload the local model from RAM
    """
    global selected_model
    if selected_model is None:
        print("No model to unload.")
        return
    url = config.gen_request_url()
    payload = {"model": selected_model, "keep_alive": 0}
    response = http_request("POST", url, json=payload)
    if response.is_error():
        output.print_error(f"Failed to unload model: {response.err_message()}")
    else:
        selected_model = None
        output.print_success("Model unloaded successfully.")


def get_error_message(status_code: int) -> str:
    """
    Return user-friendly error message for Ollama HTTP status codes.

    Ollama follows standard REST API conventions with these common responses:
    - 200/201: Success / Can be ignored
    - 400: Bad Request (malformed request)
    - 403: Forbidden (access denied, check OLLAMA_ORIGINS)
    - 404: Not Found (model doesn't exist)
    - 500: Internal Server Error (model crashed or out of memory)
    - 503: Service Unavailable (Ollama not running)

    Args:
        status_code: HTTP status code from Ollama API

    Returns:
        User-friendly error message with troubleshooting suggestions
    """
    error_messages = {
        400: (
            "Bad Request - The request was malformed or contains invalid parameters.\n"
        ),
        403: (
            "Forbidden - Access to Ollama was denied.\n"
            "Suggestions:\n"
            "  • Check OLLAMA_ORIGINS environment variable\n"
            "  • Verify Ollama accepts requests from your application\n"
            "  • Ensure proper permissions to access the service"
        ),
        404: (
            "Model Not Found - The requested model doesn't exist.\n"
            "Suggestions:\n"
            "  • Install the model: ollama pull <model-name>\n"
            "  • Check available models with the 'list' command\n"
            "  • Verify the model name spelling"
        ),
        500: (
            "Internal Server Error - Ollama encountered an unexpected error.\n"
            "Suggestions:\n"
            "  • The model may have run out of memory (RAM/VRAM)\n"
            "  • Try restarting Ollama: ollama serve\n"
            "  • Check Ollama logs for detailed error information\n"
            "  • Consider using a smaller model if resources are limited"
        ),
        503: (
            "Service Unavailable - Ollama service is not responding.\n"
            "Please do let the dev team know if this keeps happening.\n"
        ),
    }

    if status_code in error_messages:
        return f"Error {status_code}: {error_messages[status_code]}"

    if 400 <= status_code < 500:
        # Client errors (4xx)
        return (
            f"Error {status_code}: Client Error - This appears to be a configuration or request issue.\n"
            "Suggestions:\n"
            "  • Verify your request parameters and model name\n"
            "  • Check Ollama documentation: https://github.com/ollama/ollama/blob/main/docs/api.md\n"
            "  • Review your commizard configuration"
        )
    elif 500 <= status_code < 600:
        # Server errors (5xx)
        return (
            f"Error {status_code}: Server Error - This appears to be an issue with the Ollama service.\n"
            "Suggestions:\n"
            "  • Try restarting Ollama: ollama serve\n"
            "  • Check Ollama logs for more information\n"
            "  • Wait a moment and try again"
        )
    else:
        # Really unexpected codes (like 3xx redirects or 1xx info codes)
        return (
            f"Error {status_code}: Unexpected response.\n"
            "Check the Ollama documentation or server logs for more details."
        )


# TODO: see issue #15
def stream_generate(prompt: str) -> tuple[int, str]:
    url = config.gen_request_url()
    payload = {"model": selected_model, "prompt": prompt, "stream": True}
    res = ""
    try:
        with (
            StreamRequest("POST", url, json=payload) as stream,
            output.live_stream(),
        ):
            output.set_width(70)
            for s in stream:
                resp = json.loads(s)["response"]
                res += resp
                output.print_token(resp)

    except KeyError:
        return 1, "couldn't find respond from JSON"

    except json.decoder.JSONDecodeError:
        return 1, "couldn't decode JSON response"

    except StreamError as e:
        return 1, str(e)

    return (0, res)


def generate(prompt: str) -> tuple[int, str]:
    """
    generates a response by prompting the selected_model.
    Args:
        prompt: the prompt to send to the LLM.
    Returns:
        a tuple of the return code and the response. The return code is 0 if the
        response is ok, 1 otherwise. The response is the error message if the
        request fails and the return code is 1.
    """
    url = config.gen_request_url()
    if selected_model is None:
        return 1, (
            "No model selected. You must use the start command to specify "
            "which model to use before generating.\nExample: start model_name"
        )
    payload = {"model": selected_model, "prompt": prompt, "stream": False}
    r = http_request("POST", url, json=payload)
    if r.is_error():
        return 1, r.err_message()
    elif r.return_code == 200:
        return 0, r.response.get("response")
    else:
        error_msg = get_error_message(r.return_code)
        return r.return_code, error_msg


def regenerate(prompt: str) -> None:
    """
    regenerate commit message based on prompt
    """
