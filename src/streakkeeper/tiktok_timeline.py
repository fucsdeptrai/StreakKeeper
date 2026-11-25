# TikTok renders each message in its own wrapper. Date separators can sit in an
# earlier wrapper, so a message's previous sibling alone cannot identify its group.
TIMELINE_JS = r"""
function readTimeline(list) {
    const rowSelector = '[data-e2e="dm-new-chat-item"]';
    const markerSelector = '[class*="DivTimeContainer"]';
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const months = 'January February March April May June July August September October November December'.split(' ');
    const now = Date.now();

    function markerTime(label) {
        if (!['Asia/Ho_Chi_Minh', 'Asia/Saigon'].includes(timezone)) return NaN;
        const parts = label.match(/^([A-Za-z]+) (\d{1,2}), (\d{4}) (\d{1,2}):(\d{2})$/);
        if (!parts) return NaN;
        const [, monthName, day, year, hour, minute] = parts;
        const month = months.indexOf(monthName);
        if (month < 0 || +hour > 23 || +minute > 59) return NaN;
        const value = new Date(+year, month, +day, +hour, +minute);
        return value.getMonth() === month && value.getDate() === +day ? value.getTime() : NaN;
    }

    const messages = [];
    let group = null;
    for (const element of list.querySelectorAll(rowSelector + ', ' + markerSelector)) {
        if (element.matches(markerSelector)) {
            if (element.closest(rowSelector)) continue;
            const label = element.querySelector('span')?.textContent.trim() || '';
            const time = markerTime(label);
            if (group) group.to = time;
            group = {label, from: time, to: now, marker: element};
            continue;
        }
        const datetime = element.querySelector(':scope > time[datetime]')?.getAttribute('datetime');
        const exact = datetime && /(?:Z|[+-]\d{2}:\d{2})$/i.test(datetime) ? Date.parse(datetime) : NaN;
        messages.push({row: element, exact, datetime, group});
    }
    return messages.map(({row, exact, datetime, group}) => {
        if (Number.isFinite(exact)) return {row, from: exact, to: exact, label: datetime, grouped: false};
        // Chrome's observed chat markup puts a new date separator and its
        // first message together, as adjacent children of the same wrapper.
        const startsGroup = group && row.previousElementSibling === group.marker;
        const latest = startsGroup ? Math.min(group.from + 59999, now) : group?.to ?? NaN;
        return {row, from: group?.from ?? NaN, to: latest, label: group?.label ?? '', grouped: !startsGroup};
    });
}
"""
