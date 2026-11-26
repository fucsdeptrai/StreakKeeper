from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from streakkeeper.core import Store
from streakkeeper.streak_video import first_video_link


class StreakVideoTests(TestCase):
    def test_first_video_link_preserves_feed_order_and_skips_non_video_entries(self):
        items = [
            {"id": "4", "author": {"uniqueId": "streamer"}},
            {"id": "3", "author": {"uniqueId": "wrong/author"}, "video": True},
            {"id": "2", "author": {"uniqueId": "first"}, "video": True},
            {"id": "1", "author": {"uniqueId": "second"}, "video": True},
        ]
        self.assertEqual(first_video_link(items), "https://www.tiktok.com/@first/video/2")
        self.assertEqual(first_video_link(items[:2]), "")

    def test_saved_video_overrides_common_text_only_when_enabled_for_its_account(self):
        with TemporaryDirectory() as directory:
            store = Store(Path(directory) / "app.sqlite3")
            url = "https://www.tiktok.com/@creator/video/123"
            store.set("streak_content", "Tin nhắn dự phòng")
            store.confirm_tiktok_account("owner")
            store.set("streak_feed_url/owner", url)
            store.save_streak_chat("owner", "common", True, "")
            store.save_streak_chat("owner", "custom", True, "Tin riêng")

            self.assertEqual(store.streak_message("owner", "common"), "Tin nhắn dự phòng")
            store.set("streak_video_enabled", "1")
            self.assertEqual(store.streak_message("owner", "common"), url)
            self.assertEqual(store.streak_message("owner", "custom"), "Tin riêng")
            self.assertEqual(store.common_streak_message(), url)

            store.confirm_tiktok_account("different")
            self.assertEqual(store.common_streak_message(), "Tin nhắn dự phòng")
