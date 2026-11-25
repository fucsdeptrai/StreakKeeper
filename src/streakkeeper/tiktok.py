from .tiktok_timeline import TIMELINE_JS


TIKTOK_INBOX = "https://www.tiktok.com/messages"
TIKTOK_OWNER_JS = r"""
(() => {
    const profile = document.querySelector('[data-e2e="nav-profile"]');
    const href = (profile?.closest('a') ?? profile?.querySelector('a'))?.getAttribute('href');
    if (!href) return '';
    const url = new URL(href, location.origin);
    if (url.origin !== 'https://www.tiktok.com') return '';
    return url.pathname.match(/^\/@([^/]+)\/?$/)?.[1].toLowerCase() || '';
})()
"""

SNAPSHOT = '() => {\n' + TIMELINE_JS + '\nfunction tikTokOwner() { return ' + TIKTOK_OWNER_JS.strip() + '; }\n' + r'''
return (() => {
    if (location.origin !== 'https://www.tiktok.com' ||
        !/^\/messages(?:\/|$)/.test(location.pathname)) {
        return JSON.stringify({error: 'no_tab'});
    }
    const selector = name => '[data-e2e="' + name + '"]';
    const node = (root, name) => root?.querySelector(selector(name));
    const nodes = (root, name) => [...(root?.querySelectorAll(selector(name)) ?? [])];
    const label = element => element?.textContent.trim() || null;
    const sidebar = node(document, 'dm-new-conversation-list');
    const rows = nodes(document, 'dm-new-conversation-item');
    if (!sidebar && !rows.length) return JSON.stringify({error: 'inbox_unavailable'});
    const conversations = rows.map(row => ({
        id: row.getAttribute('data-conv-id'),
        name: label(node(row, 'dm-new-conversation-nickname')),
        selected: row.getAttribute('aria-selected') === 'true',
    })).filter(row => row.id && row.name);

    const chat = node(document, 'dm-new-chatbox');
    const list = node(chat, 'dm-new-message-list');
    const selected = conversations.filter(row => row.selected);
    const name = label(node(chat, 'dm-new-chat-nickname'));
    let current = null;
    if (selected.length === 1 && selected[0].name === name && list) {
        const messages = nodes(list, 'dm-new-chat-item');
        const text = messages.filter(row => node(row, 'dm-new-message-text')).length;
        const videos = messages.filter(row =>
            !node(row, 'dm-new-message-text') && node(row, 'dm-new-shared-video')).length;
        const recipient = label(node(chat, 'chat-uniqueid'))?.replace(/^@/, '').toLowerCase();
        let incoming = 0;
        let otherProfile = 0;
        for (const message of messages) {
            const link = node(message, 'chat-avatar')?.closest('a');
            const href = link?.getAttribute('href');
            const match = href && new URL(href, location.origin).pathname.match(/^\/@([^/]+)\/?$/);
            if (!match || !recipient) continue;
            if (match[1].toLowerCase() === recipient) incoming++;
            else otherProfile++;
        }
        const editor = node(chat, 'dm-new-chat-bottom')?.querySelector(
            '[contenteditable="true"]:not([aria-disabled="true"]), textarea:not(:disabled)'
        );
        const latestTime = readTimeline(list).at(-1);
        current = {
            latestTime: latestTime?.label || null, latestTimeGrouped: latestTime?.grouped ?? false,
            name, handle: label(node(chat, 'chat-uniqueid')),
            count: messages.length, text, videos, incoming, otherProfile,
            composer: Boolean(editor?.getClientRects().length),
        };
    }
    return JSON.stringify({conversations, current, owner: tikTokOwner(), selectedId: selected[0]?.id ?? null});
})();
}
'''
