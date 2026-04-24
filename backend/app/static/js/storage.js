const TOKEN_KEY = "carecollab.accessToken";
const USER_KEY = "carecollab.currentUser";
const ACTIVE_CASE_KEY = "carecollab.activeCaseId";

export function getToken() {
    return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
    window.localStorage.setItem(TOKEN_KEY, token);
}

export function getCurrentUser() {
    const raw = window.localStorage.getItem(USER_KEY);
    if (!raw) {
        return null;
    }

    try {
        return JSON.parse(raw);
    } catch (_error) {
        window.localStorage.removeItem(USER_KEY);
        return null;
    }
}

export function setCurrentUser(user) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getActiveCaseId() {
    const raw = window.localStorage.getItem(ACTIVE_CASE_KEY);
    return raw ? Number(raw) : null;
}

export function setActiveCaseId(caseId) {
    if (caseId === null || caseId === undefined) {
        window.localStorage.removeItem(ACTIVE_CASE_KEY);
        return;
    }

    window.localStorage.setItem(ACTIVE_CASE_KEY, String(caseId));
}

export function clearSession() {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
    window.localStorage.removeItem(ACTIVE_CASE_KEY);
}
