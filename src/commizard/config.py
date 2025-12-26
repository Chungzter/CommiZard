from __future__ import annotations

OLLAMA_DEFAULT_URL: str = "http://127.0.0.1:11434/"
OLLAMA_DEFAULT_GEN_ENDPOINT: str = "api/generate"
GEN_ENDPOINT: str = OLLAMA_DEFAULT_GEN_ENDPOINT
# url selection to be implemented in the future, this is just a placeholder
# right now.
LLM_URL: str = OLLAMA_DEFAULT_URL

USE_COLOR: bool = True
SHOW_BANNER: bool = True
STREAM: bool = False


def set_url(url: str):
    """
    Set the LLM's URL to use
    """
    global LLM_URL
    LLM_URL = url


def gen_request_url() -> str:
    """
    Returns Complete URL for requesting generation
    """
    return LLM_URL + GEN_ENDPOINT
