from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from streakkeeper.core import Status, Store, check


class FakeMessages:
    status = Status.NO_OUTGOING
    confirmed = True

    def __init__(self):
        self.calls = []

    def inspect(self, target, day):
        return self.status

    def send(self, target, content, day):
        self.calls.append((target, content, day))
        return self.confirmed


class CheckTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "test.sqlite3"
        self.store = Store(self.path)
        self.store.save_target("enabled", True)
        self.store.save_target("disabled", False)
        self.messages = FakeMessages()
        self.now = datetime(2026, 11, 23, 16, tzinfo=UTC)

    def run_check(self):
        return check(self.store, self.messages, lambda: self.now)

    def test_date_rolls_over_at_midnight_in_vietnam(self):
        self.run_check()
        self.run_check()
        self.now += timedelta(hours=1)
        self.run_check()
        self.assertEqual(self.messages.calls, [
            ("enabled", ".", "2026-11-23"),
            ("enabled", ".", "2026-11-24"),
        ])

    def test_skip_when_outgoing_or_unknown(self):
        for status in (Status.HAS_OUTGOING, Status.UNKNOWN):
            with self.subTest(status=status):
                self.messages.status = status
                self.run_check()
                self.assertEqual(self.store.activity()[0][2], status)
        self.assertEqual(self.messages.calls, [])

    def test_streak_content_only_applies_to_selected_conversations(self):
        self.store.save_streak_chat("account", "unselected", False, "Tin riêng chưa bật")
        self.store.save_streak_chat("account", "custom", True, "  Tin riêng  ")
        self.store.save_streak_chat("account", "default", True, "")
        self.assertIsNone(self.store.streak_message("account", "missing"))
        self.assertIsNone(self.store.streak_message("account", "unselected"))
        self.assertEqual(self.store.streak_message("account", "default"), ".")
        self.store.set("streak_content", "Tin chung")
        reopened = Store(self.path)
        self.assertEqual(reopened.streak_message("account", "custom"), "Tin riêng")
        self.assertEqual(reopened.streak_message("account", "default"), "Tin chung")
        reopened.save_streak_chat("account", "custom", False, "Tin riêng")
        self.assertIsNone(reopened.streak_message("account", "custom"))
        self.assertEqual(reopened.streak_chats("account")["custom"], (False, "Tin riêng"))

    def test_first_confirmed_account_starts_without_other_accounts_chats(self):
        self.store.set("tiktok_inbox_owner", "previous")
        with self.store.connect() as db:
            db.execute("INSERT INTO streak_chats VALUES (?, ?, ?)", ("shared-id", True, "Tin cũ"))
        self.store.record(self.now, "shared-id", Status.SENT)
        self.store.confirm_tiktok_account("new")
        self.assertEqual(self.store.get("tiktok_headless_owner"), "new")
        self.assertEqual(self.store.streak_chats("new"), {})
        self.assertEqual(self.store.activity("new"), [])
        self.assertIsNone(self.store.streak_message("new", "shared-id"))

        self.store.confirm_tiktok_account("previous")
        self.assertEqual(self.store.streak_message("previous", "shared-id"), "Tin cũ")
        self.assertEqual(len(self.store.activity("previous")), 1)
        self.store.save_streak_chat("previous", "shared-id", False, "Tin cũ")
        self.store.confirm_tiktok_account("previous")
        self.assertIsNone(self.store.streak_message("previous", "shared-id"))

    def test_live_run_uses_only_selected_ids_and_local_confirmations(self):
        self.store.save_streak_chat("account", "selected", True, "Riêng")
        self.store.save_streak_chat("account", "off", False, "Không gửi")
        def unexpected_inspection(_target, _day):
            self.fail("Live send should not check TikTok message history")
        self.messages.inspect = unexpected_inspection
        reported = []
        for _ in range(2):
            check(self.store, self.messages, lambda: self.now, owner="account",
                  on_result=lambda target, status: reported.append((target, status)))
        self.assertEqual(self.messages.calls, [("selected", "Riêng", "2026-11-23")])
        self.assertEqual(reported, [("selected", Status.SENT), ("selected", Status.APP_SENT_TODAY)])
        self.assertEqual(self.store.confirmed_streak_chats("account", "2026-11-23"), {"selected"})
        self.assertEqual(self.store.confirmed_streak_chats("another-account", "2026-11-23"), set())
        self.assertEqual(self.store.confirmed_streak_chats("account", "2026-11-24"), set())

    def test_live_run_retries_unconfirmed_send_and_starts_again_at_midnight(self):
        self.store.save_streak_chat("account", "selected", True, "")
        self.messages.confirmed = False
        check(self.store, self.messages, lambda: self.now, owner="account")
        self.messages.confirmed = True
        check(self.store, self.messages, lambda: self.now, owner="account")
        check(self.store, self.messages, lambda: self.now, owner="account")
        check(self.store, self.messages, lambda: self.now + timedelta(days=1), owner="account")
        self.assertEqual(self.messages.calls, [
            ("selected", ".", "2026-11-23"), ("selected", ".", "2026-11-23"),
            ("selected", ".", "2026-11-24"),
        ])

    def test_dashboard_counts_today_even_beyond_recent_history(self):
        self.store.record(self.now - timedelta(hours=24), "yesterday", Status.SENT)
        self.store.record(self.now, "completed", Status.SENT)
        for _ in range(100):
            self.store.record(self.now, "unknown", Status.UNKNOWN)
        self.assertEqual(self.store.completed_today(self.now), {"completed"})

    def test_pause_persists_and_custom_content_is_used_after_resuming(self):
        self.store.set("paused", "1")
        self.store.set("content", "Xin chào")
        self.store = Store(self.path)
        self.run_check()
        self.assertEqual(self.messages.calls, [])
        self.store.set("paused", "0")
        self.run_check()
        self.assertEqual(self.messages.calls, [("enabled", "Xin chào", "2026-11-23")])

    def test_unknown_send_retries_once_after_fresh_check_across_restart(self):
        self.now -= timedelta(hours=4)
        self.messages.confirmed = False
        self.run_check()
        self.run_check()
        self.assertEqual(len(self.messages.calls), 1)
        self.store = Store(self.path)
        self.now += timedelta(hours=1)
        self.messages.status = Status.UNKNOWN
        self.run_check()
        self.assertEqual(len(self.messages.calls), 1)
        self.messages.status = Status.NO_OUTGOING
        self.now += timedelta(hours=1)
        self.run_check()
        self.now += timedelta(hours=1)
        self.run_check()
        self.assertEqual(len(self.messages.calls), 2)
        self.assertEqual(self.store.activity()[0][2], Status.LIMIT)

    def test_outgoing_after_uncertain_send_prevents_retry(self):
        self.now -= timedelta(hours=2)
        self.messages.confirmed = False
        self.run_check()
        self.now += timedelta(hours=1)
        self.messages.status = Status.HAS_OUTGOING
        self.run_check()
        self.assertEqual(len(self.messages.calls), 1)

    def test_expired_session_and_security_challenge_stop_account(self):
        self.store.save_target("second", True)
        for status in (Status.LOGIN_REQUIRED, Status.VERIFICATION_REQUIRED):
            with self.subTest(status=status):
                self.messages.status = status
                self.assertEqual(self.run_check(), status)
        self.assertEqual(len(self.store.activity()), 2)
        self.assertEqual(self.messages.calls, [])
