import { apiUrl } from "./config.js";

export class ApiError extends Error {
    constructor(message, status, payload) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.payload = payload;
    }
}

async function readPayload(response) {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        return response.json();
    }

    const text = await response.text();
    return text ? { detail: text } : {};
}

async function request(path, options = {}) {
    const {
        method = "GET",
        token,
        body,
        formData,
        headers = {},
        timeoutMs = 0,
        timeoutMessage = "Request timed out.",
    } = options;

    const requestHeaders = new Headers(headers);

    if (token) {
        requestHeaders.set("Authorization", `Bearer ${token}`);
    }

    const requestInit = {
        method,
        headers: requestHeaders,
    };

    let timeoutId = null;
    let controller = null;

    if (timeoutMs > 0) {
        controller = new AbortController();
        requestInit.signal = controller.signal;
        timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
    }

    if (formData) {
        requestInit.body = formData;
    } else if (body !== undefined) {
        requestHeaders.set("Content-Type", "application/json");
        requestInit.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(apiUrl(path), requestInit);
        const payload = await readPayload(response);

        if (!response.ok) {
            const message = payload.detail || payload.message || payload.error || "Request failed.";
            throw new ApiError(message, response.status, payload);
        }

        return payload;
    } catch (error) {
        if (error?.name === "AbortError") {
            throw new ApiError(timeoutMessage, 408, { detail: timeoutMessage });
        }
        throw error;
    } finally {
        if (timeoutId) {
            window.clearTimeout(timeoutId);
        }
    }
}

export function login(credentials) {
    return request("/auth/login", {
        method: "POST",
        body: credentials,
    });
}

export function signup(payload) {
    return request("/auth/signup", {
        method: "POST",
        body: payload,
    });
}

export function logout(token) {
    return request("/auth/logout", {
        method: "POST",
        token,
    });
}

export function fetchMe(token) {
    return request("/auth/me", { token });
}

export function searchUsers(query, token) {
    return request(`/auth/users/search?q=${encodeURIComponent(query)}`, { token });
}

export function fetchCaseSummaries(token) {
    return request("/cases/summary", { token });
}

export function createCase(payload, token) {
    return request("/cases/", {
        method: "POST",
        token,
        body: payload,
    });
}

export function fetchCaseMessages(caseId, token) {
    return request(`/cases/${caseId}/messages`, { token });
}

export function sendCaseMessage(caseId, payload, token) {
    return request(`/cases/${caseId}/messages`, {
        method: "POST",
        token,
        body: payload,
    });
}

export function fetchCaseMembers(caseId, token) {
    return request(`/cases/${caseId}/members`, { token });
}

export function addCaseMember(caseId, payload, token) {
    return request(`/cases/${caseId}/members`, {
        method: "POST",
        token,
        body: payload,
    });
}

export function fetchCaseDocuments(caseId, token) {
    return request(`/documents/case/${caseId}`, { token });
}

export function uploadDocument(caseId, file, token) {
    const formData = new FormData();
    formData.append("file", file);

    return request(`/documents/upload/${caseId}`, {
        method: "POST",
        token,
        formData,
    });
}

export function queryAi(payload, token) {
    return request("/ai/query", {
        method: "POST",
        token,
        body: payload,
        timeoutMs: 45000,
        timeoutMessage: "AI is taking longer than expected. If this is the first question after uploading documents, wait a moment and try again.",
    });
}
