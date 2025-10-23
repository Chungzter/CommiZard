from __future__ import annotations

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
    try:
        if method.upper() == "GET":
            r = requests.get(url, **kwargs)  # noqa: S113
        elif method.upper() == "POST":
            r = requests.post(url, **kwargs)  # noqa: S113

        else:
            if method.upper() in ("PUT", "DELETE", "PATCH"):
                raise NotImplementedError(f"{method} is not implemented.")
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


def init_model_list() -> None:
    """
    Initialize the list of available models inside the available_models global
    variable.
    """
    global available_models
    available_models = list_locals()


# TODO: see issue #10
def list_locals() -> list[str] | None:
    """
    return a list of available local AI models
    """
    url = config.LLM_URL + "api/tags"
    r = http_request("GET", url, timeout=0.3)
    if r.is_error():
        return None
    r = r.response["models"]
    return [model["name"] for model in r]


def select_model(select_str: str) -> None:
    """
    Prepare the local model for use
    """
    global selected_model
    selected_model = select_str
    load_res = load_model(selected_model)
    if load_res.get("done_reason") == "load":
        output.print_success(f"{selected_model} loaded.")


def load_model(model_name: str) -> dict:
    """
    Load the local model into RAM
    Args:
        model_name: name of the model to load

    Returns:
        a dict of the POST request
    """
    print("Loading local model...")
    payload = {"model": selected_model}
    url = config.gen_request_url()
    out = http_request("POST", url, json=payload)
    if out.is_error():
        output.print_error(f"Failed to load {model_name}. Is ollama running?")
        return {}
    return out.response


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


# TODO: see issues #11 and #15
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
            "No model selected. You must use the start command to specify"
            "which model to use before generating.\nExample: start model_name"
        )
    payload = {"model": selected_model, "prompt": prompt, "stream": False}
    r = http_request("POST", url, json=payload)
    if r.is_error():
        return 1, r.err_message()
    elif r.return_code == 200:
        return 0, r.response.get("response").strip()
    else:
        error_msg = get_error_message(r.return_code)
        return r.return_code, error_msg


def regenerate(prompt: str) -> None:
    """
    regenerate commit message based on prompt
    """
