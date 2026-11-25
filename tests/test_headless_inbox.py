import json
from threading import Event
from unittest import TestCase
from unittest.mock import Mock

from streakkeeper.streak_browser import read_inbox_snapshot
from streakkeeper.tiktok import TIKTOK_INBOX


class HeadlessInboxTests(TestCase):
    def test_redirect_requires_login_instead_of_returning_an_empty_inbox(self):
        page = Mock(url="https://www.tiktok.com/login")
        with self.assertRaisesRegex(ValueError, "yêu cầu đăng nhập"):
            read_inbox_snapshot(page, Event())
        page.evaluate.assert_not_called()

    def test_returns_list_after_two_matching_snapshots(self):
        page = Mock(url=TIKTOK_INBOX)
        snapshot = {"owner": "fixture", "conversations": [{"id": "42", "name": "Test"}]}
        page.evaluate.side_effect = [json.dumps(snapshot), json.dumps(snapshot)]
        self.assertEqual(read_inbox_snapshot(page, Event()), snapshot)

    def test_selects_requested_chat_in_background(self):
        page = Mock(url=TIKTOK_INBOX)
        snapshot = {"owner": "fixture", "conversations": [{"id": "42", "name": "Test"}]}
        selected = {**snapshot, "selectedId": "42", "current": {"count": 2}}
        page.evaluate.side_effect = [json.dumps({**snapshot, "selectedId": None}), None, json.dumps(selected)]
        self.assertEqual(read_inbox_snapshot(page, Event(), "42"), selected)
        self.assertEqual(page.evaluate.call_args_list[1].args[1], "42")
