from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

from streakkeeper.streak_browser import active_login_pid, chrome_session


def check_chrome(profile: Path):
    # Use a temporary profile and a test cookie. No TikTok account is involved.
    cookie = {
        "name": "streakkeeper_smoke", "value": "persisted", "url": "http://localhost/",
        "expires": time.time() + 3600,
    }
    with chrome_session(profile) as page:
        assert active_login_pid(profile) is None, "Headless Chrome was mistaken for the setup browser"
        page.goto("data:text/html,<title>StreakKeeper smoke test</title>")
        assert page.title() == "StreakKeeper smoke test"
        assert page.evaluate("new Date('2026-01-01T00:00:00Z').getHours()") == 7
        page.context.add_cookies([cookie])
    with chrome_session(profile) as page:
        assert any(item["name"] == cookie["name"] and item["value"] == cookie["value"]
                   for item in page.context.cookies(cookie["url"])), "Chrome profile did not persist"


def check_executable(executable: Path, data_dir: Path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    windows = Path(os.environ["SystemRoot"])
    env["PATH"] = os.pathsep.join((str(windows / "System32"), str(windows)))
    node = executable.parent / "_internal" / "playwright" / "driver" / "node.exe"
    subprocess.run([node, "--version"], env=env, check=True, timeout=10)

    args = [executable, "--data-dir", data_dir]
    process = subprocess.Popen(args, cwd=data_dir.parent, env=env)
    try:
        database = data_dir / "app.sqlite3"
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline and process.poll() is None:
            if database.is_file():
                with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
                    result = db.execute("SELECT 1 FROM sqlite_master WHERE name = 'settings'").fetchone()
                if result:
                    break
            time.sleep(0.2)
        else:
            raise RuntimeError(f"Packaged app did not start (exit {process.poll()})")

        duplicate = subprocess.run(args, cwd=data_dir.parent, env=env, timeout=10)
        assert duplicate.returncode == 1 and process.poll() is None, "The app accepted a duplicate instance"
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    with TemporaryDirectory(prefix="streakkeeper smoke ") as directory:
        data = Path(directory)
        check_chrome(data / "browser" / "headless-chrome")
        check_executable(Path(sys.argv[1]).resolve(), data / "application")
    print("Windows executable, single-instance lock and persistent Chrome profile passed")
