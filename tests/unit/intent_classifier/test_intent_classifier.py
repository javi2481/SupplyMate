from unittest.mock import AsyncMock, patch

import pytest

from app.agent.intent_classifier import classify_intent


@pytest.mark.asyncio
async def test_classify_intent_parses_model_output():
    class Result:
        final_output = "purchase_list\nporque pregunta por quiebre"

    with (
        patch("app.agent.runner.get_model", return_value="mock-model"),
        patch("app.agent.intent_classifier.Runner.run", new=AsyncMock(return_value=Result())),
    ):
        assert await classify_intent("qué me está faltando") == "purchase_list"


@pytest.mark.asyncio
async def test_classify_intent_unavailable_returns_none():
    with patch("app.agent.runner.get_model", side_effect=RuntimeError("no key")):
        assert await classify_intent("qué me está faltando") is None
