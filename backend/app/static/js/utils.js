const conversationTimeFormatter = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
});

const messageTimeFormatter = new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
});

const fullDateFormatter = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
});

export function escapeHtml(value = "") {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#39;");
}

export function truncateText(value = "", maxLength = 88) {
    if (value.length <= maxLength) {
        return value;
    }

    return `${value.slice(0, maxLength - 1)}…`;
}

export function formatConversationTime(value) {
    if (!value) {
        return "";
    }

    const date = new Date(value);
    const now = new Date();
    const isToday = now.toDateString() === date.toDateString();

    return isToday ? messageTimeFormatter.format(date) : conversationTimeFormatter.format(date);
}

export function formatMessageTime(value) {
    if (!value) {
        return "";
    }

    return messageTimeFormatter.format(new Date(value));
}

export function formatFullDateTime(value) {
    if (!value) {
        return "";
    }

    return fullDateFormatter.format(new Date(value));
}

export function getInitials(value = "") {
    const tokens = value
        .trim()
        .split(/\s+/)
        .filter(Boolean);

    if (!tokens.length) {
        return "CC";
    }

    return tokens
        .slice(0, 2)
        .map((token) => token[0].toUpperCase())
        .join("");
}

export function autoResizeTextarea(textarea) {
    if (!textarea) {
        return;
    }

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
}

export function isNearBottom(element, threshold = 120) {
    if (!element) {
        return true;
    }

    const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
    return distance < threshold;
}

export function scrollToBottom(element) {
    if (!element) {
        return;
    }

    window.requestAnimationFrame(() => {
        element.scrollTop = element.scrollHeight;
    });
}
