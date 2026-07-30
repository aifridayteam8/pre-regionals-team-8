import os
import re

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

GATEWAY_BASE_URL = "https://genailab.tcs.in"
API_KEY_ENV_VAR = "TCS_GENAILAB_API_KEY"
TIMEOUT_S = 120

MODELS = {
    "rca": "azure_ai/genailab-maas-DeepSeek-R1",
    "structured": "azure_ai/genailab-maas-Llama-3.3-70B-Instruct",
    "summary": "azure/genailab-maas-gpt-4o-mini",
}

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

_http_client = httpx.Client(verify=False, timeout=TIMEOUT_S)
_clients: dict[str, ChatOpenAI] = {}


def _api_key() -> str:
    key = os.environ.get(API_KEY_ENV_VAR)
    if not key:
        raise RuntimeError(
            f"{API_KEY_ENV_VAR} is not set — export the hackathon gateway API key before calling the LLM."
        )
    return key


def _client_for(model: str) -> ChatOpenAI:
    if model not in _clients:
        _clients[model] = ChatOpenAI(
            base_url=GATEWAY_BASE_URL,
            model=model,
            api_key=_api_key(),
            http_client=_http_client,
            timeout=TIMEOUT_S,
        )
    return _clients[model]


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        newline = text.find("\n")
        text = text[newline + 1 :] if newline != -1 else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _clean(text: str) -> str:
    text = _THINK_BLOCK_RE.sub("", text)
    return _strip_code_fence(text)


def generate(model: str, prompt: str, system: str = "", json_mode: bool = False) -> str:
    client = _client_for(model)
    if json_mode:
        client = client.bind(response_format={"type": "json_object"})

    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    response = client.invoke(messages)
    return _clean(response.content)


def warm_all() -> None:
    for model in set(MODELS.values()):
        try:
            generate(model, "Say OK", system="")
        except Exception:
            pass
