"""Thread store: snapshot, title, pin, day groups, JSON. No Streamlit."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from app.core.models import AnalyticalScope
from ui.composition.scope_label import compact_scope_line
from ui.threads import (
    SNAPSHOT_KEYS,
    Thread,
    ThreadStore,
    apply_snapshot,
    group_history_by_day,
    new_chat_should_persist,
    persist_active,
    prepare_new_chat,
    snapshot_from_session,
    switch_thread,
    title_for_thread,
)


def _session(**overrides: object) -> dict:
    base: dict = {
        "messages": [{"role": "user", "content": "¿Qué compro?", "csv_bytes": b"sku,qty\n1,2\n"}],
        "analytical_scope": AnalyticalScope(categories=["Pañales"]).model_dump(),
        "panel_mode": "explore",
        "frozen_scope": None,
        "live_list_active": True,
        "slice_data": {"dashboard": {"skus": 12}},
        "analyze_data": {"insight": {"summary": "ok"}},
        "interaction_events": [{"source": "chip", "action": "add"}],
        "root_skus": 441,
        "root_question": "¿Qué productos tengo que comprar?",
        "highlight_calc": {"recommended_quantity": 3},
        "guidance": {"action": "ask_clarification"},
        "csv_bytes": b"should-not-copy",
        "pending_prompt": "ignore-me",
    }
    base.update(overrides)
    return base


def test_snapshot_round_trip_includes_spec_fields_and_strips_csv():
    snap = snapshot_from_session(_session())
    assert set(SNAPSHOT_KEYS) <= set(snap)
    assert "csv_bytes" not in snap
    assert snap["messages"][0]["content"] == "¿Qué compro?"
    assert "csv_bytes" not in snap["messages"][0]
    assert snap["analytical_scope"]["categories"] == ["Pañales"]
    assert snap["live_list_active"] is True

    target: dict = {}
    apply_snapshot(target, snap)
    assert target["messages"][0]["content"] == "¿Qué compro?"
    assert target["panel_mode"] == "explore"
    assert "csv_bytes" not in target["messages"][0]


def test_title_uses_compact_scope_when_recorte_is_set():
    scope = AnalyticalScope(categories=["Pañales"], name_tokens=["xxg"])
    title = title_for_thread(
        scope,
        [{"role": "user", "content": "¿Qué productos tengo que comprar?"}],
    )
    assert title == compact_scope_line(scope)
    assert "comprar" not in title.lower()


def test_title_falls_back_to_truncated_first_user_message():
    long = "a" * 80
    title = title_for_thread(AnalyticalScope(), [{"role": "user", "content": long}])
    assert title == "a" * 48


def test_title_skips_default_startup_question():
    title = title_for_thread(
        AnalyticalScope(),
        [{"role": "user", "content": "¿Qué productos tengo que comprar?"}],
    )
    assert title == "Nuevo chat"


def test_title_uses_catalog_line_for_full_inventario():
    title = title_for_thread(
        AnalyticalScope(),
        [{"role": "user", "content": "¿Qué productos tengo que comprar?"}],
        snap={"root_skus": 13125, "slice_data": {"dashboard": {"skus": 13125}}},
    )
    assert title == "Catálogo · 13125 SKUs"


def test_title_uses_first_non_boilerplate_user_question():
    title = title_for_thread(
        AnalyticalScope(),
        [
            {"role": "user", "content": "¿Qué productos tengo que comprar?"},
            {"role": "user", "content": "¿Cuántos pañales tengo que pedir?"},
        ],
    )
    assert title == "¿Cuántos pañales tengo que pedir?"


def test_title_empty_home_is_nuevo_chat():
    assert title_for_thread(AnalyticalScope(), []) == "Nuevo chat"
    assert title_for_thread(AnalyticalScope(), [{"role": "assistant", "content": "hola"}]) == "Nuevo chat"


def test_pin_excludes_thread_from_history(tmp_path: Path):
    store = ThreadStore(tmp_path / "threads.json")
    t = store.upsert_session("t1", _session())
    store.set_pinned(t.id, True)
    assert [p.id for p in store.pinned_threads()] == [t.id]
    assert store.history_threads() == []
    store.set_pinned(t.id, False)
    assert store.pinned_threads() == []
    assert [h.id for h in store.history_threads()] == [t.id]


def test_group_history_by_day_labels_hoy_ayer_and_iso():
    def _thread(tid: str, day: date, hour: int = 15) -> Thread:
        return Thread(
            id=tid,
            title=tid,
            updated_at=datetime(day.year, day.month, day.day, hour, 0, tzinfo=timezone.utc).isoformat(),
            pinned=False,
            snapshot={},
        )

    today = date(2026, 9, 3)
    groups = group_history_by_day(
        [
            _thread("old", date(2026, 8, 1)),
            _thread("hoy-b", today, hour=10),
            _thread("ayer", date(2026, 9, 2)),
            _thread("hoy-a", today, hour=18),
        ],
        today=today,
    )
    labels = [label for label, _ in groups]
    assert labels == ["Hoy", "Ayer", "2026-08-01"]
    assert [t.id for t in groups[0][1]] == ["hoy-a", "hoy-b"]


def test_json_round_trip_and_corrupt_file_is_empty(tmp_path: Path):
    path = tmp_path / "threads.json"
    store = ThreadStore(path)
    t = store.upsert_session("t1", _session())
    store.active_id = t.id
    store.save()

    loaded = ThreadStore(path)
    got = loaded.get(t.id)
    assert got is not None
    assert got.title == compact_scope_line(AnalyticalScope(categories=["Pañales"]))
    assert loaded.active_id == t.id
    assert got.snapshot["root_question"].startswith("¿Qué")

    path.write_text("{not-json", encoding="utf-8")
    broken = ThreadStore(path)
    assert broken.threads == []
    assert broken.active_id is None


def test_missing_file_is_empty_index(tmp_path: Path):
    store = ThreadStore(tmp_path / "missing.json")
    assert store.threads == []


def test_cap_drops_oldest_unpinned_keeps_pinned(tmp_path: Path):
    store = ThreadStore(tmp_path / "threads.json")
    pinned = store.upsert_session(
        "pin",
        _session(analytical_scope=AnalyticalScope(categories=["Fijado"]).model_dump()),
    )
    store.set_pinned(pinned.id, True)
    for i in range(51):
        store.upsert_session(
            f"h{i}",
            _session(
                analytical_scope=AnalyticalScope(categories=[f"Cat{i}"]).model_dump(),
                messages=[{"role": "user", "content": f"m{i}"}],
            ),
        )
    history = store.history_threads()
    assert len(history) == 50
    assert store.get("pin") is not None
    assert store.get("pin").pinned is True
    assert store.get("h0") is None


def test_new_chat_should_persist_dirty_not_empty_home():
    assert new_chat_should_persist(messages=[{"role": "user", "content": "x"}], live_list_active=False)
    assert new_chat_should_persist(messages=[], live_list_active=True)
    assert not new_chat_should_persist(messages=[], live_list_active=False)


def test_search_matches_title_and_subtitle_case_insensitively(tmp_path: Path):
    store = ThreadStore(tmp_path / "threads.json")
    store.upsert_session(
        "cabello",
        _session(
            analytical_scope=AnalyticalScope(categories=["Cuidado del Cabello"]).model_dump(),
            slice_data={"dashboard": {"skus": 2430}, "purchase_list": [{}] * 25},
        ),
    )
    store.upsert_session(
        "panales",
        _session(
            analytical_scope=AnalyticalScope(categories=["Pañales"], subcategories=["Bebé"]).model_dump(),
            slice_data={"dashboard": {"skus": 120}, "purchase_list": [{}] * 4},
            messages=[{"role": "user", "content": "Reposición urgente"}],
        ),
    )
    assert [thread.id for thread in store.search("cabello")] == ["cabello"]
    assert [thread.id for thread in store.search("2430 skus")] == ["cabello"]
    assert [thread.id for thread in store.search("bebé")] == ["panales"]
    assert {thread.id for thread in store.search("")} == {"cabello", "panales"}


def test_search_matches_without_accent(tmp_path: Path):
    store = ThreadStore(tmp_path / "threads.json")
    store.upsert_session(
        "panales",
        _session(
            analytical_scope=AnalyticalScope(categories=["Pañales"], subcategories=["Bebé"]).model_dump(),
            messages=[{"role": "user", "content": "Reposición urgente"}],
        ),
    )
    assert [thread.id for thread in store.search("bebe")] == ["panales"]


def test_prepare_new_chat_persists_dirty_and_skips_empty_home(tmp_path: Path):
    store = ThreadStore(tmp_path / "threads.json")
    empty: dict = {
        "messages": [],
        "live_list_active": False,
        "analytical_scope": AnalyticalScope().model_dump(),
    }
    prepare_new_chat(store, empty)
    assert store.threads == []

    dirty = _session()
    dirty["active_thread_id"] = None
    prepare_new_chat(store, dirty)
    assert len(store.threads) == 1
    assert dirty["messages"] == []
    assert dirty["live_list_active"] is False
    assert dirty["active_thread_id"] is None
    assert store.active_id is None


def test_switch_thread_restores_commit_frozen_scope(tmp_path: Path):
    store = ThreadStore(tmp_path / "threads.json")
    frozen = AnalyticalScope(categories=["Pañales"]).model_dump()
    commit = store.upsert_session(
        "c1",
        _session(
            panel_mode="commit",
            frozen_scope=frozen,
            live_list_active=True,
        ),
    )
    current: dict = {
        "messages": [{"role": "user", "content": "otro"}],
        "live_list_active": False,
        "analytical_scope": AnalyticalScope().model_dump(),
        "panel_mode": "explore",
        "frozen_scope": None,
        "active_thread_id": None,
    }
    switch_thread(store, current, commit.id)
    assert current["panel_mode"] == "commit"
    assert current["frozen_scope"] == frozen
    assert current["messages"][0]["content"] == "¿Qué compro?"
    assert current["active_thread_id"] == commit.id

