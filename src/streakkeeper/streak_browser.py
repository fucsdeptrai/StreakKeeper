import json
from contextlib import contextmanager
import fcntl
from datetime import date, datetime, time, timedelta
from pathlib import Path
import subprocess
from threading import Event
import time as clock
from uuid import uuid4

from playwright.sync_api import Error as PlaywrightError, sync_playwright

from .core import Status, VIETNAM
from .tiktok import SNAPSHOT, TIKTOK_INBOX, TIKTOK_OWNER_JS

CHROME_EXECUTABLE = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

STREAK_ACTION = r"""
(() => {
    const action = __ACTION__;
    const data = name => '[data-e2e="' + name + '"]';
    const text = node => node?.textContent.trim() || '';
    const result = status => JSON.stringify({status});
    const pending = () => JSON.stringify({error: 'pending'});
    if (location.origin !== 'https://www.tiktok.com' ||
        !/^\/messages(?:\/|$)/.test(location.pathname)) return pending();
    if (Date.now() < action.start || Date.now() >= action.end) return result('unknown');

    const sidebar = document.querySelector(data('dm-new-conversation-list'));
    const rows = [...document.querySelectorAll(data('dm-new-conversation-item'))];
    if (!sidebar && !rows.length) return pending();
    const state = window.__streakKeeperAction?.id === action.id
        ? window.__streakKeeperAction : (window.__streakKeeperAction = {id: action.id});
    const row = rows.find(element => element.getAttribute('data-conv-id') === action.target);
    if (!row) {
        let scroller = rows[0]?.parentElement;
        while (scroller && !(scroller.scrollHeight > scroller.clientHeight + 10 &&
               /auto|scroll/.test(getComputedStyle(scroller).overflowY))) scroller = scroller.parentElement;
        if (!scroller) return rows.length ? result('unknown') : pending();
        if (!state.scanning) {
            state.scanning = true;
            scroller.scrollTop = 0;
            return pending();
        }
        if (scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 2) return result('unknown');
        scroller.scrollTop += scroller.clientHeight;
        return pending();
    }
    if (row.getAttribute('aria-selected') !== 'true') {
        if (!state.selected) {
            state.selected = true;
            row.click();
        }
        return pending();
    }
    const box = document.querySelector(data('dm-new-chatbox'));
    const list = box?.querySelector(data('dm-new-message-list'));
    const name = text(row.querySelector(data('dm-new-conversation-nickname')));
    if (!list || !name || name !== text(box.querySelector(data('dm-new-chat-nickname')))) return pending();
    if (rows.filter(entry => text(entry.querySelector(data('dm-new-conversation-nickname'))) === name).length !== 1) {
        return result('unknown');
    }

    function account(link) {
        const href = link?.getAttribute('href');
        if (!href) return '';
        const url = new URL(href, location.origin);
        return url.origin === location.origin
            ? url.pathname.match(/^\/@([^/]+)\/?$/)?.[1].toLowerCase() || ''
            : '';
    }
    const profile = document.querySelector(data('nav-profile'));
    const own = account(profile?.closest('a') ?? profile?.querySelector('a'));
    if (!own || action.owner !== own) return result('sender_unverified');

    // Confirm only a new matching outgoing message after our click.
    const matching = [...list.querySelectorAll(data('dm-new-chat-item'))].filter(row =>
        account(row.querySelector(data('chat-avatar'))?.closest('a')) === own &&
        text(row.querySelector(data('dm-new-message-text'))) === action.content
    ).length;
    if (state.clicked) return matching > state.matchingBefore ? result('sent') : pending();
    const editor = box.querySelector(data('dm-new-chat-bottom') + ' [contenteditable="true"]');
    if (!editor || !editor.getClientRects().length) return result('unknown');
    if (!state.filled) {
        if (text(editor)) return result('unknown');
        state.filled = true;
        editor.focus();
        const data = new DataTransfer();
        data.setData('text/plain', action.content);
        editor.dispatchEvent(new ClipboardEvent('paste', {clipboardData: data, bubbles: true, cancelable: true}));
        return pending();
    }
    if (text(editor) !== action.content) return pending();
    const buttons = [...box.querySelectorAll(data('dm-new-chat-bottom') + ' [aria-label="Send"], ' +
        data('dm-new-chat-bottom') + ' [aria-label="Gửi"]')].filter(e =>
        e.getClientRects().length && !e.disabled && e.getAttribute('aria-disabled') !== 'true');
    if (buttons.length !== 1) return pending();
    state.matchingBefore = matching;
    state.clicked = true;
    buttons[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, composed: true, button: 0}));
    return pending();
})()
"""

@contextmanager
def chrome_session(profile: Path):
    profile.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (profile.parent / "streak-chrome.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Hồ sơ TikTok riêng đang được dùng. Hãy đợi lượt đăng nhập hoặc giữ chuỗi kết thúc.") from exc
        with sync_playwright() as playwright:
            try:
                context = playwright.chromium.launch_persistent_context(
                    profile, channel="chrome", headless=True, chromium_sandbox=True,
                    timezone_id=str(VIETNAM), timeout=12000,
                    # The visible setup browser saves its session using Chrome
                    # and macOS Keychain. Open that same profile the same way.
                    ignore_default_args=["--use-mock-keychain", "--password-store=basic"],
                )
            except PlaywrightError as exc:
                raise ValueError("Không khởi động được Chrome cho StreakKeeper. Kiểm tra Chrome đã được cài.") from exc
            try:
                yield context.pages[0] if context.pages else context.new_page()
            finally:
                if context.browser is None or context.browser.is_connected():
                    context.close()


def open_inbox(page):
    page.goto(TIKTOK_INBOX, wait_until="domcontentloaded", timeout=15000)


def login_required(page) -> bool:
    return page.url.startswith("https://www.tiktok.com/login")


def open_login_chrome(profile: Path):
    profile.mkdir(mode=0o700, parents=True, exist_ok=True)
    return subprocess.Popen(
        [CHROME_EXECUTABLE, f"--user-data-dir={profile}", "--no-first-run", TIKTOK_INBOX],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def active_login_pid(profile: Path) -> int | None:
    rows = subprocess.check_output(["/bin/ps", "-axo", "pid=,args="], text=True, timeout=2)
    prefix = CHROME_EXECUTABLE + " "
    profile_argument = f" --user-data-dir={profile} "
    matches = []
    for line in rows.splitlines():
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2:
            continue
        pid, command = fields
        if command.startswith(prefix) and profile_argument in command + " " and " --headless" not in command:
            matches.append(int(pid))
    if len(matches) > 1:
        raise ValueError("Có nhiều cửa sổ thiết lập đang dùng cùng hồ sơ. Thoát các cửa sổ thiết lập rồi thử lại.")
    return matches[0] if matches else None


def close_login_chrome(profile: Path):
    pid = active_login_pid(profile)
    if pid is None:
        return
    script = """
ObjC.import('AppKit');
function run(argv) {
    const app = $.NSRunningApplication.runningApplicationWithProcessIdentifier(Number(argv[0]));
    return Boolean(app.terminate);
}
"""
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", "-", str(pid)],
            input=script, text=True, capture_output=True, check=True, timeout=5,
        )
        deadline = clock.monotonic() + 12
        while clock.monotonic() < deadline:
            if active_login_pid(profile) is None:
                return
            clock.sleep(0.2)
        raise ValueError("Cửa sổ thiết lập chưa thoát. Đóng Chrome của hồ sơ riêng rồi bấm Kiểm tra đăng nhập lại.")
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("Hãy thoát cửa sổ Chrome dùng để đăng nhập rồi bấm Kiểm tra đăng nhập lại.") from exc


def inbox_owner(page) -> str:
    if not (page.url == TIKTOK_INBOX or page.url.startswith((TIKTOK_INBOX + "?", TIKTOK_INBOX + "/", TIKTOK_INBOX + "#"))):
        return ""
    return page.evaluate(
        "() => document.querySelector('[data-e2e=dm-new-conversation-list],[data-e2e=dm-new-conversation-item]') "
        "? (" + TIKTOK_OWNER_JS + ") : ''"
    ) or ""


def wait_for_owner(page, cancelled: Event, seconds: float) -> str:
    deadline = clock.monotonic() + seconds
    while not cancelled.is_set() and not page.is_closed() and clock.monotonic() < deadline:
        try:
            owner = inbox_owner(page)
        except PlaywrightError:
            # A login redirect may replace the document while evaluating.
            owner = ""
        if owner:
            return owner
        cancelled.wait(0.5)
    return ""


def read_inbox_snapshot(page, cancelled: Event, target: str = "") -> dict:
    deadline = clock.monotonic() + 10
    previous_count = None
    latest = {}
    selected = False
    while not cancelled.is_set() and clock.monotonic() < deadline:
        if login_required(page):
            raise ValueError("TikTok yêu cầu đăng nhập cho hồ sơ nền. Mở Settings để kiểm tra phiên.")
        result = json.loads(page.evaluate(SNAPSHOT))
        if result.get("owner"):
            latest = result
            conversations = result["conversations"]
            if target:
                if result["selectedId"] == target and result["current"]:
                    return result
                if not selected and any(chat["id"] == target for chat in conversations):
                    page.evaluate(
                        """target => [...document.querySelectorAll('[data-e2e=dm-new-conversation-item]')]
                            .find(row => row.getAttribute('data-conv-id') === target)?.click()""",
                        target,
                    )
                    selected = True
            elif len(conversations) and len(conversations) == previous_count:
                return result
            previous_count = len(conversations)
        cancelled.wait(0.35)
    if not latest:
        raise ValueError("Không đọc được hộp thư trong Chrome headless. Kiểm tra phiên trong Settings.")
    if target and (latest.get("selectedId") != target or not latest.get("current")):
        raise ValueError("Chưa đọc được cuộc trò chuyện đã chọn. Mở hộp thư rồi thử lại.")
    return latest


class HeadlessMessages:
    def __init__(self, page, owner: str, cancelled: Event):
        self.page = page
        self.owner = owner
        self.cancelled = cancelled

    def send(self, target: str, content: str, day: str) -> bool | Status:
        result = self.run(target, day, content)
        if result.get("error") == "login_required":
            return Status.LOGIN_REQUIRED
        if result.get("status") == "sender_unverified":
            return Status.SENDER_UNVERIFIED
        return result.get("status") == "sent"

    def run(self, target: str, day: str, content: str) -> dict:
        start = datetime.combine(date.fromisoformat(day), time(), VIETNAM)
        action = {
            "id": uuid4().hex,
            "target": target, "start": int(start.timestamp() * 1000),
            "end": int((start + timedelta(days=1)).timestamp() * 1000),
            "owner": self.owner, "content": content,
        }
        source = STREAK_ACTION.replace("__ACTION__", json.dumps(action)).strip()
        script = "() => (" + source + ")"
        deadline = clock.monotonic() + 8
        try:
            while not self.cancelled.is_set() and clock.monotonic() < deadline:
                if self.page.url.startswith("https://www.tiktok.com/login"):
                    return {"error": "login_required"}
                result = json.loads(self.page.evaluate(script))
                if result.get("error") != "pending":
                    return result
                self.cancelled.wait(0.35)
        except (PlaywrightError, ValueError):
            pass
        return {}
