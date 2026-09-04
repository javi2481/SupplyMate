"""Local chat-thread index. Streamlit-free."""

from __future__ import annotations

import json
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from app.core.models import AnalyticalScope
from ui.composition.chat_titles import is_boilerplate_user_question
from ui.composition.scope_label import compact_scope_line

SNAPSHOT_KEYS = (
    "messages",
    "analytical_scope",
    "panel_mode",
    "frozen_scope",
    "live_list_active",
    "slice_data",
    "analyze_data",
    "interaction_events",
    "root_skus",
    "root_question",
    "highlight_calc",
    "guidance",
)

UNPINNED_CAP = 50
DEFAULT_TITLE = "Nuevo chat"
DEFAULT_STORE_PATH = Path.home() / ".supplymate" / "threads.json"

_SNAPSHOT_DEFAULTS: dict[str, Any] = {
    "messages": [],
    "analytical_scope": AnalyticalScope().model_dump(),
    "panel_mode": "explore",
    "frozen_scope": None,
    "live_list_active": False,
    "slice_data": None,
    "analyze_data": None,
    "interaction_events": [],
    "root_skus": None,
    "root_question": "",
    "highlight_calc": None,
    "guidance": None,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_search_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.casefold()


def _strip_csv(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_csv(v) for k, v in value.items() if k != "csv_bytes"}
    if isinstance(value, list):
        return [_strip_csv(item) for item in value]
    return value


def snapshot_from_session(session: Mapping[str, Any]) -> dict[str, Any]:
    snap: dict[str, Any] = {}
    for key in SNAPSHOT_KEYS:
        if key in session:
            snap[key] = _strip_csv(session[key])
        else:
            snap[key] = _strip_csv(_SNAPSHOT_DEFAULTS[key])
    return snap


def apply_snapshot(target: MutableMapping[str, Any], snapshot: Mapping[str, Any]) -> None:
    for key in SNAPSHOT_KEYS:
        if key in snapshot:
            target[key] = _strip_csv(snapshot[key])
        else:
            target[key] = _strip_csv(_SNAPSHOT_DEFAULTS[key])


def _as_scope(scope: AnalyticalScope | Mapping[str, Any] | None) -> AnalyticalScope:
    if isinstance(scope, AnalyticalScope):
        return scope
    if scope is None:
        return AnalyticalScope()
    return AnalyticalScope.model_validate(scope)


def _catalog_sku_count(snap: Mapping[str, Any] | None) -> int | None:
    if not snap:
        return None
    root = snap.get("root_skus")
    if isinstance(root, int):
        return root
    dash = (snap.get("slice_data") or {}).get("dashboard") or {}
    skus = dash.get("skus")
    return skus if isinstance(skus, int) else None


def _first_non_boilerplate_question(messages: list[Mapping[str, Any]] | None) -> str:
    for msg in messages or []:
        if msg.get("role") != "user":
            continue
        text = str(msg.get("content") or "").strip()
        if not text or is_boilerplate_user_question(text):
            continue
        return text[:48]
    return ""


def title_for_thread(
    scope: AnalyticalScope | Mapping[str, Any] | None,
    messages: list[Mapping[str, Any]] | None,
    *,
    snap: Mapping[str, Any] | None = None,
) -> str:
    line = compact_scope_line(_as_scope(scope))
    if line != "Inventario":
        return line
    catalog_skus = _catalog_sku_count(snap)
    if catalog_skus is not None and catalog_skus > 0:
        return "Inventario general"
    question = _first_non_boilerplate_question(messages)
    if question:
        return question
    return DEFAULT_TITLE


def new_chat_should_persist(
    *,
    messages: list[Any] | None,
    live_list_active: bool,
) -> bool:
    return bool(messages) or bool(live_list_active)


def _parse_dt(iso: str) -> datetime:
    raw = iso.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def group_history_by_day(
    threads: list[Thread],
    *,
    today: date | None = None,
) -> list[tuple[str, list[Thread]]]:
    today = today or datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    buckets: dict[str, list[Thread]] = {}
    order: list[str] = []
    sorted_threads = sorted(threads, key=lambda t: _parse_dt(t.updated_at), reverse=True)
    for thread in sorted_threads:
        day = _parse_dt(thread.updated_at).date()
        if day == today:
            label = "Hoy"
        elif day == yesterday:
            label = "Ayer"
        elif week_start <= day <= week_end:
            label = "Esta semana"
        else:
            label = day.isoformat()
        if label not in buckets:
            buckets[label] = []
            order.append(label)
        buckets[label].append(thread)
    return [(label, buckets[label]) for label in order]


@dataclass
class Thread:
    id: str
    title: str
    updated_at: str
    pinned: bool = False
    subtitle: str = ""
    snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "updated_at": self.updated_at,
            "pinned": self.pinned,
            "snapshot": self.snapshot,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Thread:
        return cls(
            id=str(raw.get("id") or uuid.uuid4()),
            title=str(raw.get("title") or DEFAULT_TITLE),
            subtitle=str(raw.get("subtitle") or ""),
            updated_at=str(raw.get("updated_at") or _now_iso()),
            pinned=bool(raw.get("pinned")),
            snapshot=dict(raw.get("snapshot") or {}),
        )


def _subtitle_from_snap(snap: dict[str, Any]) -> str:
    """Subtítulo de reconocimiento: contexto mínimo, sin SKUs ni totales de catálogo."""
    scope = _as_scope(snap.get("analytical_scope"))
    if compact_scope_line(scope) == "Inventario":
        catalog_skus = _catalog_sku_count(snap)
        if catalog_skus is not None and catalog_skus > 0:
            return "Todos los productos"
        return ""
    purchase_list = (snap.get("slice_data") or {}).get("purchase_list") or []
    if purchase_list:
        return f"{len(purchase_list)} para reponer"
    return ""


def _refresh_thread_labels(thread: Thread) -> None:
    snap = thread.snapshot
    thread.title = title_for_thread(
        snap.get("analytical_scope"),
        snap.get("messages") or [],
        snap=snap,
    )
    thread.subtitle = _subtitle_from_snap(snap)


def _disambiguate_clone_subtitles(threads: list[Thread]) -> None:
    """Same UTC day + same title/subtitle → use non-boilerplate question as subtitle."""
    buckets: dict[tuple[date, str, str], list[Thread]] = {}
    for thread in threads:
        day = _parse_dt(thread.updated_at).date()
        key = (day, thread.title, thread.subtitle)
        buckets.setdefault(key, []).append(thread)
    for group in buckets.values():
        if len(group) < 2:
            continue
        for thread in group:
            question = _first_non_boilerplate_question(thread.snapshot.get("messages") or [])
            if question:
                thread.subtitle = question


class ThreadStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_STORE_PATH
        self.threads: list[Thread] = []
        self.active_id: str | None = None
        self.load()

    def load(self) -> None:
        self.threads = []
        self.active_id = None
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return
        if not isinstance(payload, dict):
            return
        raw_threads = payload.get("threads") or []
        if not isinstance(raw_threads, list):
            return
        for item in raw_threads:
            if isinstance(item, dict):
                thread = Thread.from_dict(item)
                _refresh_thread_labels(thread)
                self.threads.append(thread)
        _disambiguate_clone_subtitles(self.threads)
        active = payload.get("active_id")
        self.active_id = str(active) if active else None

    def refresh_all_labels(self) -> None:
        for thread in self.threads:
            _refresh_thread_labels(thread)
        _disambiguate_clone_subtitles(self.threads)

    def search(self, query: str) -> list[Thread]:
        """Filter threads by title/subtitle. Presentation-free; rail owns copy and layout."""
        raw = query.strip()
        if not raw:
            return list(self.threads)
        needle = _normalize_search_text(raw)
        matches: list[Thread] = []
        for thread in self.threads:
            haystack = _normalize_search_text(
                " ".join(part for part in (thread.title, thread.subtitle) if part)
            )
            if needle in haystack:
                matches.append(thread)
        return matches

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "active_id": self.active_id,
            "threads": [t.to_dict() for t in self.threads],
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, thread_id: str) -> Thread | None:
        return next((t for t in self.threads if t.id == thread_id), None)

    def pinned_threads(self) -> list[Thread]:
        pinned = [t for t in self.threads if t.pinned]
        return sorted(pinned, key=lambda t: _parse_dt(t.updated_at), reverse=True)

    def history_threads(self) -> list[Thread]:
        history = [t for t in self.threads if not t.pinned]
        return sorted(history, key=lambda t: _parse_dt(t.updated_at), reverse=True)

    def set_pinned(self, thread_id: str, pinned: bool) -> Thread | None:
        thread = self.get(thread_id)
        if thread is None:
            return None
        thread.pinned = pinned
        thread.updated_at = _now_iso()
        self.save()
        return thread

    def upsert_session(self, thread_id: str | None, session: Mapping[str, Any]) -> Thread:
        snap = snapshot_from_session(session)
        title = title_for_thread(snap.get("analytical_scope"), snap.get("messages") or [], snap=snap)
        subtitle = _subtitle_from_snap(snap)
        existing = self.get(thread_id) if thread_id else None
        if existing is None:
            thread = Thread(
                id=thread_id or str(uuid.uuid4()),
                title=title,
                subtitle=subtitle,
                updated_at=_now_iso(),
                pinned=False,
                snapshot=snap,
            )
            self.threads.append(thread)
        else:
            existing.title = title
            existing.subtitle = subtitle
            existing.updated_at = _now_iso()
            existing.snapshot = snap
            self.threads = [t for t in self.threads if t.id != existing.id]
            self.threads.append(existing)
            thread = existing
        _disambiguate_clone_subtitles(self.threads)
        self.active_id = thread.id
        self._cap_unpinned()
        self.save()
        return thread

    def _cap_unpinned(self) -> None:
        unpinned_ids = [t.id for t in self.threads if not t.pinned]
        overflow = len(unpinned_ids) - UNPINNED_CAP
        if overflow <= 0:
            return
        drop = set(unpinned_ids[:overflow])
        self.threads = [t for t in self.threads if t.id not in drop]


def empty_home_snapshot() -> dict[str, Any]:
    return snapshot_from_session({})


def persist_active(store: ThreadStore, session: MutableMapping[str, Any]) -> Thread | None:
    messages = session.get("messages") or []
    live = bool(session.get("live_list_active"))
    thread_id = session.get("active_thread_id")
    if not thread_id and not new_chat_should_persist(messages=messages, live_list_active=live):
        return None
    thread = store.upsert_session(thread_id, session)
    session["active_thread_id"] = thread.id
    return thread


def prepare_new_chat(store: ThreadStore, session: MutableMapping[str, Any]) -> None:
    persist_active(store, session)
    apply_snapshot(session, empty_home_snapshot())
    session["active_thread_id"] = None
    session["pending_prompt"] = None
    session["pending_unfreeze"] = None
    session["last_analyze_key"] = ""
    store.active_id = None
    store.save()


def switch_thread(
    store: ThreadStore,
    session: MutableMapping[str, Any],
    thread_id: str,
) -> Thread | None:
    persist_active(store, session)
    thread = store.get(thread_id)
    if thread is None:
        return None
    apply_snapshot(session, thread.snapshot)
    session["active_thread_id"] = thread.id
    session["pending_prompt"] = None
    session["pending_unfreeze"] = None
    store.active_id = thread.id
    store.save()
    return thread
