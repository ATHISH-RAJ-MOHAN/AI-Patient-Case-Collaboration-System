const appConfig = window.APP_CONFIG || {};

export const API_BASE_URL = (appConfig.apiBaseUrl || "").replace(/\/$/, "");
export const ROUTES = {
    app: appConfig.routes?.app || "/app",
    login: appConfig.routes?.login || "/login",
    signup: appConfig.routes?.signup || "/signup",
};

export function apiUrl(path) {
    return `${API_BASE_URL}${path}`;
}

export function fileUrl(path) {
    if (!path) {
        return "#";
    }

    if (/^https?:\/\//i.test(path)) {
        return path;
    }

    return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

export function websocketUrl(path) {
    const origin = API_BASE_URL || `${window.location.protocol}//${window.location.host}`;
    return `${origin.replace(/^http/i, "ws").replace(/\/$/, "")}${path}`;
}
