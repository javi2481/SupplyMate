"""Tests for boilerplate question detection in thread titles."""

from __future__ import annotations

from ui.composition.chat_titles import is_boilerplate_user_question, normalize_question


def test_normalize_question_strips_punctuation_and_case():
    assert normalize_question("¿Qué productos tengo que comprar?") == "que productos tengo que comprar"


def test_default_startup_query_is_boilerplate():
    assert is_boilerplate_user_question("¿Qué productos tengo que comprar?")
    assert is_boilerplate_user_question("que productos tengo que comprar")


def test_real_user_question_is_not_boilerplate():
    assert not is_boilerplate_user_question("¿Cuántos pañales tengo que pedir?")
