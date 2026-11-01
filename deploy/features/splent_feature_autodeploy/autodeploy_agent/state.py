"""The agent's memory, on the /data volume.

``state.json`` is what the agent is doing and what it has decided: paused or
not, the images it will not deploy again, the deploy in progress (so a
restart halfway through can finish or undo it), the last check. It is
rewritten atomically on every change.

``history.jsonl`` is one JSON object per finished deploy, appended and never
rewritten.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import threading
from collections import deque
from pathlib import Path

logger = logging.getLogger("autodeploy.state")

#: Results that mean the image must not be deployed again.
BAD_RESULTS = frozenset({"rolled_back", "rollback_failed", "failed"})

#: How many bad image ids are remembered. Older ones are images the channel
#: has long moved past.
MAX_BAD_IMAGES = 50

DEFAULT_STATE = {
    "status": "idle",
    "detail": "",
    "paused": False,
    "bad_images": [],
    "last_check": None,
    "pending_image": None,
    "running_image": None,
    "running_versions": None,
    "in_progress": None,
    "last_deploy": None,
}


class StateStore:
    def __init__(self, data_dir: str | os.PathLike):
        self.data_dir = Path(data_dir)
        self.backups_dir = self.data_dir / "backups"
        self.state_path = self.data_dir / "state.json"
        self.history_path = self.data_dir / "history.jsonl"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._state = self._load()

    # ── state.json ──────────────────────────────────────────────────────

    def _load(self) -> dict:
        state = copy.deepcopy(DEFAULT_STATE)
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raw = None
        except (OSError, ValueError) as exc:
            # Kept for a person to look at, and the agent starts afresh.
            logger.error("state.json is unreadable (%s); starting from defaults", exc)
            try:
                self.state_path.replace(
                    self.state_path.with_name("state.json.unreadable")
                )
            except OSError:
                pass
            raw = None
        if isinstance(raw, dict):
            state.update({k: v for k, v in raw.items() if k in DEFAULT_STATE})
            return state

        # No usable state.json. The images the history says failed stay
        # refused, so losing the file cannot start the loop again. With the
        # file in place its list is the truth, which is what lets an operator
        # take an image off it by hand.
        bad: list[str] = []
        for entry in reversed(self.history(limit=MAX_BAD_IMAGES)):
            image = entry.get("to_image")
            if entry.get("result") in BAD_RESULTS and image and image not in bad:
                bad.append(image)
        state["bad_images"] = bad
        return state

    def _save(self) -> None:
        tmp = self.state_path.with_name("state.json.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(self._state, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, self.state_path)

    def snapshot(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._state)

    def get(self, key: str):
        with self._lock:
            return copy.deepcopy(self._state.get(key))

    def update(self, **changes) -> dict:
        with self._lock:
            self._state.update(changes)
            self._save()
            return copy.deepcopy(self._state)

    def mark_bad(self, image_id: str) -> None:
        if not image_id:
            return
        with self._lock:
            bad = list(self._state.get("bad_images") or [])
            if image_id not in bad:
                bad.append(image_id)
            self._state["bad_images"] = bad[-MAX_BAD_IMAGES:]
            self._save()

    def is_bad(self, image_id: str) -> bool:
        with self._lock:
            return image_id in (self._state.get("bad_images") or [])

    # ── history.jsonl ───────────────────────────────────────────────────

    def append_history(self, entry: dict) -> None:
        line = json.dumps(entry, sort_keys=True).encode("utf-8") + b"\n"
        with self._lock:
            with open(self.history_path, "a+b") as handle:
                # A line a crash cut short has no newline; without one here
                # this entry would be glued to it and lost with it.
                handle.seek(0, os.SEEK_END)
                if handle.tell() > 0:
                    handle.seek(-1, os.SEEK_END)
                    if handle.read(1) != b"\n":
                        line = b"\n" + line
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())

    def history(self, limit: int = 20) -> list[dict]:
        """The newest ``limit`` entries, newest first. A line that does not
        parse (a write cut short by a crash) is skipped."""
        if limit <= 0:
            return []
        try:
            with open(self.history_path, encoding="utf-8") as handle:
                lines = deque(handle, maxlen=limit)
        except FileNotFoundError:
            return []
        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if isinstance(entry, dict):
                entries.append(entry)
        entries.reverse()
        return entries
