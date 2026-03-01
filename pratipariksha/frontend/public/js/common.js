const API_BASE = "http://127.0.0.1:5000/api";

function fetchAPI(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(`${API_BASE}${endpoint}`, { ...options, headers });
}

function handleLogin(role, username, password) {
    return fetchAPI('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ role, username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('role', data.role);
            localStorage.setItem('username', data.username);
            return true;
        }
        return false;
    });
}

function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

function checkRole(role) {
    const userRole = localStorage.getItem('role');
    if (userRole !== role) {
        logout();
    }
}
