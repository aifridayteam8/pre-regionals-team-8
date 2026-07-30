"""TCS GenAI Lab gateway client (OpenAI-compatible LiteLLM proxy).

Ported from incidentiq/ai/client.py. The API key is read from the
TCS_GENAILAB_API_KEY environment variable (loaded from the repo-root .env by
backend.config) and is never hardcoded.

Verified working models on the gateway:
  * azure_ai/genailab-maas-DeepSeek-R1        (reasoning / RCA)
  * azure/genailab-maas-gpt-4.1-mini          (structured JSON)
  * azure/genailab-maas-gpt-4o-mini           (prose summaries)

Note: azure_ai/genailab-maas-Llama-3.3-70B-Instruct is advertised by the
gateway but returns 404 DeploymentNotFound, so gpt-4.1-mini takes the
structured role until that deployment is provisioned.
"""

import os
import re

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.ai.base_client import BaseAIClient

GATEWAY_BASE_URL = os.getenv('TCS_GENAILAB_BASE_URL', 'https://genailab.tcs.in')
API_KEY_ENV_VAR = 'TCS_GENAILAB_API_KEY'
TIMEOUT_S = 120

MODELS = {
    'rca': 'azure_ai/genailab-maas-DeepSeek-R1',
    'structured': 'azure/genailab-maas-gpt-4.1-mini',
    'summary': 'azure/genailab-maas-gpt-4o-mini',
}

_THINK_BLOCK_RE = re.compile(r'<think>.*?</think>', re.DOTALL)

_http_client = httpx.Client(verify=False, timeout=TIMEOUT_S)
_clients: dict = {}


def _api_key() -> str:
    key = os.environ.get(API_KEY_ENV_VAR)
    if not key:
        raise RuntimeError(
            f'{API_KEY_ENV_VAR} is not set — export the gateway API key before calling the LLM.'
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
    if text.startswith('```'):
        newline = text.find('\n')
        text = text[newline + 1:] if newline != -1 else text[3:]
    if text.endswith('```'):
        text = text[:-3]
    return text.strip()


def _clean(text: str) -> str:
    return _strip_code_fence(_THINK_BLOCK_RE.sub('', text))


def generate(model: str, prompt: str, system: str = '', json_mode: bool = False) -> str:
    """Single completion against the gateway; strips think-blocks and fences."""
    client = _client_for(model)
    if json_mode:
        client = client.bind(response_format={'type': 'json_object'})

    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    return _clean(client.invoke(messages).content)


def warm_all() -> None:
    """Fire a tiny call at each routed model so the first real request is warm."""
    for model in set(MODELS.values()):
        try:
            generate(model, 'Say OK')
        except Exception:
            pass


class GenAILabClient(BaseAIClient):
    """BaseAIClient-compatible wrapper over the gateway."""

    def __init__(self, model: str = None):
        self.model = model or MODELS['summary']

    def generate(self, prompt: str, system_prompt: str = '', **kwargs) -> str:
        return generate(
            kwargs.get('model', self.model),
            prompt,
            system=system_prompt or '',
            json_mode=kwargs.get('json_mode', False),
        )

    def chat(self, messages: list) -> str:
        """Collapse a chat transcript into one gateway call."""
        system = ' '.join(
            m.get('content', '') for m in messages if m.get('role') == 'system'
        )
        prompt = '\n'.join(
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in messages if m.get('role') != 'system'
        )
        return generate(self.model, prompt, system=system)

    def is_available(self) -> bool:
        try:
            generate(self.model, 'Say OK')
            return True
        except Exception:
            return False

    def list_models(self) -> list:
        return sorted(set(MODELS.values()))
