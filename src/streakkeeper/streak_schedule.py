from datetime import datetime, time, timedelta

from .core import Store, VIETNAM


RETRY_INTERVAL = timedelta(minutes=15)


def pending_streak_chats(store: Store, owner: str, now: datetime) -> set[str]:
    if not owner:
        return set()
    selected = {target for target, (enabled, _) in store.streak_chats(owner).items() if enabled}
    if not selected:
        return set()
    day = now.astimezone(VIETNAM).date().isoformat()
    return selected - store.confirmed_streak_chats(owner, day)


def next_streak_run(now: datetime, last_started: str = "", start_time: str = "") -> datetime:
    now = now.astimezone(VIETNAM)
    due = now
    if start_time:
        due = max(due, datetime.combine(now.date(), time.fromisoformat(start_time), VIETNAM))
    if last_started:
        last = datetime.fromisoformat(last_started).astimezone(VIETNAM)
        if last.date() == now.date():
            due = max(due, last + RETRY_INTERVAL)
    return due
