const API_BASE =
    import.meta.env.VITE_API_BASE || "http://localhost:5000";

const ACCESS_TOKEN_KEY = "incidentiq_access_token";
const REFRESH_TOKEN_KEY = "incidentiq_refresh_token";
const USER_KEY = "incidentiq_user";

export async function login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username,
            password
        })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Login failed");
    }

    localStorage.setItem(
        ACCESS_TOKEN_KEY,
        data.access_token
    );

    localStorage.setItem(
        REFRESH_TOKEN_KEY,
        data.refresh_token
    );

    localStorage.setItem(
        USER_KEY,
        JSON.stringify(data.user)
    );

    return data;
}

export function logout() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

export function getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getCurrentUser() {
    const user = localStorage.getItem(USER_KEY);

    if (!user) return null;

    return JSON.parse(user);
}

export async function refreshAccessToken() {

    const refresh_token = getRefreshToken();

    if (!refresh_token)
        throw new Error("Refresh token missing");

    const response = await fetch(
        `${API_BASE}/auth/refresh`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                refresh_token
            })
        }
    );

    const data = await response.json();

    if (!response.ok) {

        logout();

        throw new Error("Session expired");
    }

    localStorage.setItem(
        ACCESS_TOKEN_KEY,
        data.access_token
    );

    return data.access_token;
}

export async function authFetch(
    url,
    options = {}
) {

    let token = getAccessToken();

    let response = await fetch(
        `${API_BASE}${url}`,
        {
            ...options,
            headers: {
                ...(options.headers || {}),
                Authorization: `Bearer ${token}`
            }
        }
    );

    if (response.status !== 401)
        return response;

    token = await refreshAccessToken();

    response = await fetch(
        `${API_BASE}${url}`,
        {
            ...options,
            headers: {
                ...(options.headers || {}),
                Authorization: `Bearer ${token}`
            }
        }
    );

    return response;
}