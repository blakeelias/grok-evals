import os
from typing import Dict, Any, List, Optional, Type, TypeVar
from dotenv import load_dotenv
from pydantic import BaseModel

# OpenAI-compatible client
try:
    from openai import AsyncOpenAI, OpenAI
except Exception:
    OpenAI = None  # type: ignore
    AsyncOpenAI = None  # type: ignore

load_dotenv()

T = TypeVar('T', bound=BaseModel)

DEFAULT_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai")
DEFAULT_MODEL = os.getenv("XAI_MODEL", "grok-4")
DEFAULT_TEMPERATURE = float(os.getenv("XAI_TEMPERATURE", "0.2"))
DEFAULT_TOP_P = float(os.getenv("XAI_TOP_P", "1.0"))
DEFAULT_SEED = int(os.getenv("XAI_SEED", "7"))
DEFAULT_MAX_TOKENS = int(os.getenv("XAI_MAX_OUTPUT_TOKENS", "1024"))

class GrokClient:
    """Sync Grok API client (legacy, prefer AsyncGrokClient for new code)."""

    def __init__(self,
                 api_key: Optional[str] = None,
                 base_url: str = DEFAULT_BASE_URL,
                 model: str = DEFAULT_MODEL,
                 temperature: float = DEFAULT_TEMPERATURE,
                 top_p: float = DEFAULT_TOP_P,
                 seed: int = DEFAULT_SEED,
                 max_tokens: int = DEFAULT_MAX_TOKENS):
        if OpenAI is None:
            raise ImportError("openai>=1.40 required. pip install -r requirements.txt")
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set. Put it in environment or .env")
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.seed = seed
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def complete(self,
                 user_content: str,
                 system_content: Optional[str] = None,
                 stop: Optional[List[str]] = None,
                 extra: Optional[Dict[str, Any]] = None) -> str:
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        params: Dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            seed=self.seed,
            max_tokens=self.max_tokens,
        )
        if stop:
            params["stop"] = stop
        if extra:
            params.update(extra)
        resp = self.client.chat.completions.create(**params)  # type: ignore
        return resp.choices[0].message.content or ""


class AsyncGrokClient:
    """Async Grok API client with structured output support."""

    def __init__(self,
                 api_key: Optional[str] = None,
                 base_url: str = DEFAULT_BASE_URL,
                 model: str = DEFAULT_MODEL,
                 temperature: float = DEFAULT_TEMPERATURE,
                 top_p: float = DEFAULT_TOP_P,
                 seed: int = DEFAULT_SEED,
                 max_tokens: int = DEFAULT_MAX_TOKENS):
        if AsyncOpenAI is None:
            raise ImportError("openai>=1.40 required. pip install -r requirements.txt")
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set. Put it in environment or .env")
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.seed = seed
        self.max_tokens = max_tokens
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def complete(self,
                       user_content: str,
                       system_content: Optional[str] = None,
                       stop: Optional[List[str]] = None,
                       extra: Optional[Dict[str, Any]] = None) -> str:
        """Async text completion."""
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        params: Dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            seed=self.seed,
            max_tokens=self.max_tokens,
        )
        if stop:
            params["stop"] = stop
        if extra:
            params.update(extra)
        resp = await self.client.chat.completions.create(**params)
        return resp.choices[0].message.content or ""

    async def complete_structured(self,
                                  prompt: str,
                                  response_model: Type[T],
                                  system_content: Optional[str] = None) -> T:
        """
        Async structured output completion using Pydantic models.

        Uses the beta.chat.completions.parse API for structured outputs.
        See: https://docs.x.ai/docs/guides/structured-outputs
        """
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": prompt})

        completion = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_model,
            temperature=self.temperature,
            top_p=self.top_p,
            seed=self.seed,
            max_tokens=self.max_tokens,
        )

        return completion.choices[0].message.parsed
