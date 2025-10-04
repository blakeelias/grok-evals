"""
Async Grok API client using the official xAI SDK.

This module provides a unified client for making async API calls with
structured output support via Pydantic models.
"""

import os
from typing import Type, TypeVar, Optional
from dotenv import load_dotenv
from pydantic import BaseModel

try:
    from xai_sdk import AsyncClient
    from xai_sdk.chat import user, system
except ImportError:
    AsyncClient = None  # type: ignore

load_dotenv()

T = TypeVar('T', bound=BaseModel)

DEFAULT_MODEL = os.getenv("XAI_MODEL", "grok-beta")
DEFAULT_TEMPERATURE = float(os.getenv("XAI_TEMPERATURE", "0.2"))
DEFAULT_TOP_P = float(os.getenv("XAI_TOP_P", "1.0"))
DEFAULT_MAX_TOKENS = int(os.getenv("XAI_MAX_OUTPUT_TOKENS", "4096"))
DEFAULT_TIMEOUT = int(os.getenv("XAI_TIMEOUT", "300"))  # 5 minutes


class GrokClient:
    """
    Async Grok API client using the official xAI SDK.

    Uses AsyncClient from xai_sdk for native async support with automatic
    prompt caching and structured outputs via Pydantic models.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL,
                 temperature: float = DEFAULT_TEMPERATURE,
                 top_p: float = DEFAULT_TOP_P,
                 max_tokens: int = DEFAULT_MAX_TOKENS,
                 timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the Grok client.

        Args:
            api_key: xAI API key (defaults to XAI_API_KEY env var)
            model: Model to use (default: grok-beta)
            temperature: Sampling temperature (default: 0.2)
            top_p: Nucleus sampling parameter (default: 1.0)
            max_tokens: Maximum output tokens (default: 4096)
            timeout: Request timeout in seconds (default: 300)
        """
        if AsyncClient is None:
            raise ImportError("xai-sdk required. Run: pip install xai-sdk")

        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set. Put it in environment or .env")

        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        # Initialize xAI AsyncClient
        self.client = AsyncClient(api_key=self.api_key, timeout=timeout)

    async def complete(self,
                       prompt: str,
                       system_prompt: Optional[str] = None) -> str:
        """
        Async text completion.

        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append(system(system_prompt))
        messages.append(user(prompt))

        # Create chat
        chat = self.client.chat.create(
            model=self.model,
            messages=messages
        )

        # Sample response
        response = await chat.sample(
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens
        )

        return response

    async def complete_structured(self,
                                  prompt: str,
                                  response_model: Type[T],
                                  system_prompt: Optional[str] = None) -> T:
        """
        Async structured output completion using Pydantic models.

        This uses xAI's native structured output support, which ensures
        the model's response conforms to the provided Pydantic schema.

        Args:
            prompt: User prompt text
            response_model: Pydantic BaseModel class defining output structure
            system_prompt: Optional system prompt

        Returns:
            Instance of response_model with parsed structured output
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append(system(system_prompt))
        messages.append(user(prompt))

        # Create chat
        chat = self.client.chat.create(
            model=self.model,
            messages=messages
        )

        # Sample with structured output
        response = await chat.sample(
            output_model=response_model,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens
        )

        return response


# Legacy alias for backward compatibility
AsyncGrokClient = GrokClient
