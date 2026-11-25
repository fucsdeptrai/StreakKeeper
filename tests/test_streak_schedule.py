from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from streakkeeper.core import Store, VIETNAM, check
from streakkeeper.streak_schedule import next_streak_run, pending_streak_chats


class ConfirmingSender:
    def send(self, target, content, day):
        return True


class StreakScheduleTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = Store(Path(directory.name) / "test.sqlite3")
        self.now = datetime(2026, 11, 25, 8, tzinfo=VIETNAM)

    def test_default_runs_now_and_retries_after_fifteen_minutes(self):
        self.assertEqual(next_streak_run(self.now), self.now)
        last = (self.now - timedelta(minutes=4)).isoformat()
        self.assertEqual(next_streak_run(self.now, last), self.now + timedelta(minutes=11))

    def test_custom_start_repeats_each_day_without_previous_cadence(self):
        last = (self.now - timedelta(days=1)).isoformat()
        self.assertEqual(next_streak_run(self.now, last, "09:30"), self.now.replace(hour=9, minute=30))
        after = self.now.replace(hour=10)
        self.assertEqual(next_streak_run(after, last, "09:30"), after)

    def test_queue_empties_when_complete_and_refills_on_selection_or_new_day(self):
        self.store.save_streak_chat("account", "first", True, ".")
        self.store.save_streak_chat("account", "disabled", False, ".")
        self.assertEqual(pending_streak_chats(self.store, "account", self.now), {"first"})
        check(self.store, ConfirmingSender(), lambda: self.now, owner="account", only={"first"})
        self.assertEqual(pending_streak_chats(self.store, "account", self.now), set())

        self.store.save_streak_chat("account", "new", True, "")
        self.assertEqual(pending_streak_chats(self.store, "account", self.now), {"new"})
        self.assertEqual(
            pending_streak_chats(self.store, "account", self.now + timedelta(days=1)),
            {"first", "new"},
        )
