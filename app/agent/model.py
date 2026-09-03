from __future__ import annotations

from agents import set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from app.core import config

_model_cache: OpenAIChatCompletionsModel | str | None = None


def get_model() -> OpenAIChatCompletionsModel | str:
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    if config.LLM_PROVIDER == "groq":
        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
            )
        set_tracing_disabled(True)
        client = AsyncOpenAI(
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
        )
        _model_cache = OpenAIChatCompletionsModel(
            model=config.GROQ_MODEL,
            openai_client=client,
        )
        return _model_cache

    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    _model_cache = config.OPENAI_MODEL
    return _model_cache
