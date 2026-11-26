from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from enum import StrEnum
import os
from pathlib import Path
import sqlite3
from typing import Protocol
from zoneinfo import ZoneInfo


VIETNAM = ZoneInfo("Asia/Ho_Chi_Minh")


class Status(StrEnum):
    NO_OUTGOING = "Chưa có tin đi"
    HAS_OUTGOING = "Đã có tin đi"
    UNKNOWN = "Chưa xác minh được"
    SENDER_UNVERIFIED = "Chưa xác minh được người gửi"
    LOGIN_REQUIRED = "Cần đăng nhập lại"
    VERIFICATION_REQUIRED = "Cần xác minh bảo mật"
    SENT = "Đã gửi"
    APP_SENT_TODAY = "App đã gửi hôm nay"
    UNCONFIRMED = "Chưa xác nhận được kết quả gửi"
    LIMIT = "Đã hết lượt gửi hôm nay"


class Sender(Protocol):
    def send(self, target: str, content: str, day: str) -> bool | Status: ...


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                os.fchmod(descriptor, 0o600)
            finally:
                os.close(descriptor)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS targets (name TEXT PRIMARY KEY, enabled INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS streak_chats (
                    conversation_id TEXT PRIMARY KEY, enabled INTEGER NOT NULL, message TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS account_streak_chats (
                    owner TEXT NOT NULL, conversation_id TEXT NOT NULL,
                    enabled INTEGER NOT NULL, message TEXT NOT NULL,
                    PRIMARY KEY (owner, conversation_id)
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    target TEXT, day TEXT, count INTEGER NOT NULL,
                    started TEXT NOT NULL, confirmed INTEGER NOT NULL,
                    PRIMARY KEY (target, day)
                );
                CREATE TABLE IF NOT EXISTS activity (
                    time TEXT NOT NULL, target TEXT NOT NULL, status TEXT NOT NULL
                );
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, key: str, default: str = "") -> str:
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set(self, key: str, value: str):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))

    def targets(self):
        with self.connect() as db:
            return db.execute("SELECT name, enabled FROM targets ORDER BY name").fetchall()

    def save_target(self, name: str, enabled: bool):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO targets VALUES (?, ?)", (name, enabled))

    def confirm_tiktok_account(self, owner: str):
        if not owner:
            raise ValueError("Thiếu tài khoản TikTok đã xác nhận.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            settings = dict(db.execute("SELECT key, value FROM settings"))
            if settings.get("tiktok_inbox_owner") == owner and not settings.get("legacy_streak_chats_imported"):
                db.execute(
                    "INSERT OR IGNORE INTO account_streak_chats "
                    "SELECT ?, conversation_id, enabled, message FROM streak_chats",
                    (owner,),
                )
                db.execute("INSERT OR REPLACE INTO settings VALUES ('legacy_streak_chats_imported', '1')")
            db.execute("INSERT OR REPLACE INTO settings VALUES ('tiktok_headless_owner', ?)", (owner,))

    def streak_chats(self, owner: str):
        with self.connect() as db:
            return {
                conversation_id: (bool(enabled), message)
                for conversation_id, enabled, message in db.execute(
                    "SELECT conversation_id, enabled, message FROM account_streak_chats WHERE owner = ?",
                    (owner,),
                )
            }

    def save_streak_chat(self, owner: str, conversation_id: str, enabled: bool, message: str):
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO account_streak_chats VALUES (?, ?, ?, ?)",
                (owner, conversation_id, enabled, message.strip()),
            )

    def streak_message(self, owner: str, conversation_id: str, connection=None) -> str | None:
        if connection is None:
            with self.connect() as db:
                return self.streak_message(owner, conversation_id, db)
        row = connection.execute(
            "SELECT message "
            "FROM account_streak_chats WHERE owner = ? AND conversation_id = ? AND enabled = 1",
            (owner, conversation_id),
        ).fetchone()
        return (row[0] or self.common_streak_message(connection, owner=owner)) if row else None

    def common_streak_message(self, connection=None, *, owner=None) -> str:
        if connection is None:
            with self.connect() as db:
                return self.common_streak_message(db, owner=owner)
        settings = dict(connection.execute("SELECT key, value FROM settings"))
        owner = owner or settings.get("tiktok_headless_owner")
        if settings.get("streak_video_enabled") == "1" and owner:
            cached = settings.get(f"streak_feed_url/{owner}")
            if cached:
                return cached
        return settings.get("streak_content") or "."

    def confirmed_streak_chats(self, owner: str, day: str) -> set[str]:
        prefix = f"{owner}/"
        with self.connect() as db:
            rows = db.execute(
                "SELECT target FROM attempts WHERE day = ? AND confirmed = 1 AND "
                "(substr(target, 1, ?) = ? OR (? = "
                "(SELECT value FROM settings WHERE key = 'tiktok_inbox_owner') "
                "AND instr(target, '/') = 0))",
                (day, len(prefix), prefix, owner),
            )
            return {target.removeprefix(prefix) for (target,) in rows}

    def record(self, now: datetime, target: str, status: Status, *, owner=None):
        with self.connect() as db:
            key = f"{owner}/{target}" if owner else target
            db.execute("INSERT INTO activity VALUES (?, ?, ?)", (now.isoformat(), key, status.value))

    def activity(self, owner=None):
        with self.connect() as db:
            if owner:
                prefix = f"{owner}/"
                rows = db.execute(
                    "SELECT time, target, status FROM activity "
                    "WHERE substr(target, 1, ?) = ? OR (? = "
                    "(SELECT value FROM settings WHERE key = 'tiktok_inbox_owner') "
                    "AND instr(target, '/') = 0) ORDER BY rowid DESC LIMIT 100",
                    (len(prefix), prefix, owner),
                )
                return [(time, target.removeprefix(prefix), status) for time, target, status in rows]
            return db.execute("SELECT * FROM activity ORDER BY rowid DESC LIMIT 100").fetchall()

    def completed_today(self, now: datetime):
        midnight = now.astimezone(VIETNAM).replace(hour=0, minute=0, second=0, microsecond=0)
        with self.connect() as db:
            rows = db.execute(
                "SELECT DISTINCT target FROM activity WHERE datetime(time) >= datetime(?) "
                "AND datetime(time) <= datetime(?) AND status IN (?, ?)",
                (midnight.isoformat(), now.isoformat(), Status.SENT, Status.HAS_OUTGOING),
            )
            return {target for (target,) in rows}


def check(store: Store, messages, clock=lambda: datetime.now(UTC), *,
          owner=None, on_result=None, cancelled=lambda: False, only=None):
    if store.get("paused") == "1":
        return

    targets = [(target, config[0]) for target, config in store.streak_chats(owner).items()] if owner else store.targets()
    for target, enabled in targets:
        if cancelled() or store.get("paused") == "1":
            break
        if not enabled or (only is not None and target not in only):
            continue
        now = clock()
        day = now.astimezone(VIETNAM).date().isoformat()
        result = Status.NO_OUTGOING
        if not owner:
            try:
                result = messages.inspect(target, day)
            except OSError:
                result = Status.UNKNOWN
        if cancelled():
            break
        if result == Status.NO_OUTGOING:
            result = attempt(store, messages, target, now, day, clock, owner=owner)
        store.record(now, target, result, owner=owner)
        if on_result is not None:
            on_result(target, result)
        if result in (Status.LOGIN_REQUIRED, Status.VERIFICATION_REQUIRED):
            return result


def attempt(store: Store, messages: Sender, target: str, now: datetime, day: str, clock, *, owner=None) -> Status:
    attempt_target = f"{owner}/{target}" if owner else target
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        settings = dict(db.execute("SELECT key, value FROM settings"))
        if settings.get("paused") == "1":
            return Status.UNKNOWN
        if owner:
            content = store.streak_message(owner, target, db)
            if content is None:
                return Status.UNKNOWN
        else:
            enabled = db.execute("SELECT enabled FROM targets WHERE name = ?", (target,)).fetchone()
            if enabled != (1,):
                return Status.UNKNOWN
            content = settings.get("content", ".")
        if clock().astimezone(VIETNAM).date().isoformat() != day:
            return Status.UNKNOWN
        row = db.execute(
            "SELECT count, started, confirmed FROM attempts WHERE target = ? AND day = ?",
            (attempt_target, day),
        ).fetchone()
        if row is None and owner and settings.get("tiktok_inbox_owner") == owner:
            row = db.execute(
                "SELECT count, started, confirmed FROM attempts WHERE target = ? AND day = ?",
                (target, day),
            ).fetchone()
        if row:
            count, started, confirmed = row
            if confirmed:
                return Status.APP_SENT_TODAY if owner else Status.HAS_OUTGOING
            if not owner:
                if count >= 2:
                    return Status.LIMIT
                if (now - datetime.fromisoformat(started)).total_seconds() < 3600:
                    return Status.UNCONFIRMED
        else:
            count = 0
        db.execute(
            "INSERT OR REPLACE INTO attempts VALUES (?, ?, ?, ?, 0)",
            (attempt_target, day, count + 1, clock().isoformat()),
        )

    try:
        sent = messages.send(target, content, day)
    except OSError:
        sent = False
    if isinstance(sent, Status):
        return sent
    if not sent:
        return Status.UNCONFIRMED
    with store.connect() as db:
        db.execute("UPDATE attempts SET confirmed = 1 WHERE target = ? AND day = ?", (attempt_target, day))
    return Status.SENT


class DemoMessages:
    def __init__(self, store: Store):
        self.store = store

    def inspect(self, target: str, day: str) -> Status:
        return Status(self.store.get("demo_status", Status.NO_OUTGOING))

    def send(self, target: str, content: str, day: str) -> bool:
        return self.store.get("demo_uncertain") != "1"
