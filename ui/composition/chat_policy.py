"""Commit chat must not silently drop frozen_scope."""


def chat_would_unfreeze(panel_mode: str, response_mode: str) -> bool:
    return panel_mode == "commit" and response_mode in ("list", "explore")
