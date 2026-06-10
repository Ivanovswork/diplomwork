const API_URL = '/api';

const ICON_PATHS = {
    books: 'M18,2H6c-1.1,0 -2,0.9 -2,2v16c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V4c0,-1.1 -0.9,-2 -2,-2zM6,4h5v8l-2.5,-1.5L6,12V4z',
    bookOpen: 'M21,5c-1.11,-0.35 -2.33,-0.5 -3.5,-0.5 -1.95,0 -4.05,0.4 -5.5,1.5 -1.45,-1.1 -3.55,-1.5 -5.5,-1.5S2.45,4.9 1,6v14.65c0,0.25 0.25,0.5 0.5,0.5 0.1,0 0.15,-0.05 0.25,-0.05C3.1,20.45 5.05,20 6.5,20c1.95,0 4.05,0.4 5.5,1.5 1.35,-0.85 3.8,-1.5 5.5,-1.5 1.65,0 3.35,0.3 4.75,1.05 0.1,0.05 0.15,0.05 0.25,0.05 0.25,0 0.5,-0.25 0.5,-0.5V6c-1.65,-0.45 -3.15,-0.7 -4.75,-0.5zM21,18.5c-1.1,-0.35 -2.3,-0.5 -3.5,-0.5 -1.7,0 -4.15,0.65 -5.5,1.5V8c1.35,-0.85 3.8,-1.5 5.5,-1.5 1.2,0 2.4,0.15 3.5,0.5v11.5z',
    chart: 'M19,3H5c-1.1,0 -2,0.9 -2,2v14c0,1.1 0.9,2 2,2h14c1.1,0 2,-0.9 2,-2V5c0,-1.1 -0.9,-2 -2,-2zM9,17H7v-7h2v7zM13,17h-2V7h2v10zM17,17h-2v-4h2v4z',
    pages: 'M14,2H6c-1.1,0 -1.99,0.9 -1.99,2L4,20c0,1.1 0.89,2 1.99,2H18c1.1,0 2,-0.9 2,-2V8l-6,-6zM6,20V4h7v5h5v11H6z',
    speed: 'M20.38,8.57l-1.23,1.85a8,8 0,0 1,-0.22 7.58H5.07A8,8 0,0 1,15.58 6.85l1.85,-1.23A10,10 0,0 0,3.35 19a2,2 0,0 0,1.72 1h13.85a2,2 0,0 0,1.74 -1,10 10,0 0,0 -0.27,-10.44zM10.59,15.41a2,2 0,0 0,2.83 0l5.66,-8.49 -8.49,5.66a2,2 0,0 0,0 2.83z',
    streak: 'M13.5,0.67s0.74,2.65 0.74,4.8c0,2.06 -1.35,3.73 -3.41,3.73 -2.07,0 -3.63,-1.67 -3.63,-3.73l0.03,-0.36C5.21,7.51 4,10.62 4,14c0,4.42 3.58,8 8,8s8,-3.58 8,-8C20,8.61 17.41,3.8 13.5,0.67zM11.71,19c-1.78,0 -3.22,-1.4 -3.22,-3.14 0,-1.62 1.05,-2.76 2.81,-3.12 1.77,-0.36 3.6,-1.21 4.62,-2.58 0.39,1.29 0.59,2.65 0.59,3.72 0,2.63 -1.68,5.12 -4.8,5.12z',
    trophy: 'M12,17.27L18.18,21l-1.64,-7.03L22,9.24l-7.19,-0.61L12,2 9.19,8.63 2,9.24l5.46,4.73L5.82,21z',
    friends: 'M16,11c1.66,0 2.99,-1.34 2.99,-3S17.66,5 16,5c-1.66,0 -3,1.34 -3,3s1.34,3 3,3zM8,11c1.66,0 2.99,-1.34 2.99,-3S9.66,5 8,5C6.34,5 5,6.34 5,8s1.34,3 3,3zM8,13c-2.33,0 -7,1.17 -7,3.5L1,19h14v-2.5c0,-2.33 -4.67,-3.5 -7,-3.5zM16,13c-0.29,0 -0.62,0.02 -0.97,0.05 1.16,0.84 1.97,1.97 1.97,3.45V19h6v-2.5c0,-2.33 -4.67,-3.5 -7,-3.5z',
    family: 'M16,11c1.66,0 2.99,-1.34 2.99,-3S17.66,5 16,5c-1.66,0 -3,1.34 -3,3s1.34,3 3,3zM8,11c1.66,0 2.99,-1.34 2.99,-3S9.66,5 8,5C6.34,5 5,6.34 5,8s1.34,3 3,3zM8,13c-2.33,0 -7,1.17 -7,3.5L1,19h14v-2.5c0,-2.33 -4.67,-3.5 -7,-3.5zM16,13c-0.29,0 -0.62,0.02 -0.97,0.05 1.16,0.84 1.97,1.97 1.97,3.45V19h6v-2.5c0,-2.33 -4.67,-3.5 -7,-3.5z',
    profile: 'M12,12c2.21,0 4,-1.79 4,-4s-1.79,-4 -4,-4 -4,1.79 -4,4 1.79,4 4,4zM12,14c-2.67,0 -8,1.34 -8,4v2h16v-2c0,-2.66 -5.33,-4 -8,-4z',
    security: 'M18,8h-1L17,6c0,-2.76 -2.24,-5 -5,-5S7,3.24 7,6v2L6,8c-1.1,0 -2,0.9 -2,2v10c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V10c0,-1.1 -0.9,-2 -2,-2zM12,17c-1.1,0 -2,-0.9 -2,-2s0.9,-2 2,-2 2,0.9 2,2 -0.9,2 -2,2zM15.1,8H8.9L8.9,6c0,-1.71 1.39,-3.1 3.1,-3.1 1.71,0 3.1,1.39 3.1,3.1v2z',
    time: 'M11.99,2C6.47,2 2,6.48 2,12s4.47,10 9.99,10C17.52,22 22,17.52 22,12S17.52,2 11.99,2zM12,20c-4.42,0 -8,-3.58 -8,-8s3.58,-8 8,-8 8,3.58 8,8 -3.58,8 -8,8zM12.5,7H11v6l5.25,3.15 0.75,-1.23 -4.5,-2.67z',
    checkCircle: 'M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM10,17l-5,-5 1.41,-1.41L10,14.17l7.59,-7.59L19,8l-9,9z',
    chevronRight: 'M10,6L8.59,7.41 13.17,12l-4.58,4.59L10,18l6,-6z',
    close: 'M19,6.41L17.59,5 12,10.59 6.41,5 5,6.41 10.59,12 5,17.59 6.41,19 12,13.41 17.59,19 19,17.59 13.41,12z',
    person: 'M12,12c2.21,0 4,-1.79 4,-4s-1.79,-4 -4,-4 -4,1.79 -4,4 1.79,4 4,4zM12,14c-2.67,0 -8,1.34 -8,4v2h16v-2c0,-2.66 -5.33,-4 -8,-4z',
    plus: 'M19,11H13V5h-2v6H5v2h6v6h2v-6h6z',
    arrowLeft: 'M14,7l-5,5 5,5V7z',
    upload: 'M5,20h14v-2H5v2zM12,2l-5.5,5.5h4V16h3V7.5h4L12,2z',
    target: 'M13,17h-2v-2h2v2zM13,13h-2V7h2v6zM19,3H5c-1.1,0 -2,0.9 -2,2v14c0,1.1 0.9,2 2,2h14c1.1,0 2,-0.9 2,-2V5c0,-1.1 -0.9,-2 -2,-2z',
    file: 'M6,2h7l5,5v15H6c-1.1,0 -2,-0.9 -2,-2V4c0,-1.1 0.9,-2 2,-2zM12,3.5V8h4.5',
    trash: 'M16,9v10H8V9h8m-1.5,-6h-5l-1,1H5v2h14V4h-3.5l-1,-1z',
    mail: 'M20,4H4c-1.1,0 -2,0.9 -2,2v12c0,1.1 0.9,2 2,2h16c1.1,0 2,-0.9 2,-2V6c0,-1.1 -0.9,-2 -2,-2zM20,8l-8,5 -8,-5V6l8,5 8,-5v2z',
    words: 'M14,17H7v-2h7v2zM17,13H7v-2h10v2zM17,9H7V7h10v2z'
};

window.renderIcon = function(name, className = '', label = '') {
    const path = ICON_PATHS[name] || ICON_PATHS.profile;
    const classes = ['icon', className].filter(Boolean).join(' ');
    const aria = label ? ` role="img" aria-label="${label}"` : ' aria-hidden="true"';
    return `<svg viewBox="0 0 24 24" class="${classes}"${aria}><path d="${path}"></path></svg>`;
};

window.applyIconMarkup = function(root = document) {
    root.querySelectorAll('[data-icon]').forEach((el) => {
        const iconName = el.dataset.icon;
        if (iconName) el.innerHTML = window.renderIcon(iconName);
    });

    root.querySelectorAll('.logo-mark').forEach((el) => {
        if (!el.innerHTML.trim()) el.innerHTML = window.renderIcon('books');
    });

    root.querySelectorAll('.modal-close').forEach((el) => {
        if (!el.innerHTML.trim()) el.innerHTML = window.renderIcon('close');
    });
};

window.getToken = function() {
    const token = localStorage.getItem('token');
    console.log('getToken called, token:', token ? 'present' : 'missing');
    return token;
};

function setToken(token) {
    if (token) {
        localStorage.setItem('token', token);
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.user_id) localStorage.setItem('user_id', payload.user_id);
            if (payload.name) localStorage.setItem('user_name', payload.name);
            if (payload.email) localStorage.setItem('user_email', payload.email);
        } catch (e) {
            console.error('Error parsing token:', e);
        }
    } else {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_name');
        localStorage.removeItem('user_email');
    }
}

async function apiRequest(endpoint, method, data) {
    const token = window.getToken();
    const headers = { 'Content-Type': 'application/json' };

    if (token) {
        headers.Authorization = `Token ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined
    });

    if (!response.ok) {
        let errorMessage;
        try {
            const errorData = await response.json();
            errorMessage = errorData.error || errorData.message || `HTTP ${response.status}`;
        } catch (e) {
            errorMessage = `HTTP ${response.status}`;
        }
        return { error: errorMessage, status: response.status };
    }

    return response.json();
}

window.login = async function(email, password) {
    if (!email || !password) {
        alert('Введите email и пароль');
        return;
    }

    const data = await apiRequest('/users/login/', 'POST', { email, password });

    if (data.token) {
        setToken(data.token);
        if (data.user) {
            localStorage.setItem('user_name', data.user.name);
            localStorage.setItem('user_email', data.user.email);
            localStorage.setItem('user_id', data.user.id);
        }
        window.location.href = '/';
    } else {
        alert(data.error || 'Ошибка входа. Проверьте email и пароль.');
    }
};

window.register = async function(name, email, password, passwordConfirm) {
    if (!name || !email || !password || !passwordConfirm) {
        alert('Заполните все поля');
        return;
    }

    if (password !== passwordConfirm) {
        alert('Пароли не совпадают');
        return;
    }

    if (password.length < 6) {
        alert('Пароль должен быть не менее 6 символов');
        return;
    }

    const data = await apiRequest('/users/register/', 'POST', {
        name,
        email,
        password,
        password_confirm: passwordConfirm
    });

    if (data.token) {
        setToken(data.token);
        if (data.user) {
            localStorage.setItem('user_name', data.user.name);
            localStorage.setItem('user_email', data.user.email);
            localStorage.setItem('user_id', data.user.id);
        }
        window.location.href = '/';
    } else {
        const errorMsg = data.errors || data.error || 'Ошибка регистрации';
        alert(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg);
    }
};

window.logout = function() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
    window.location.href = '/login.html';
};

function getUserNameFromToken() {
    const token = window.getToken();
    if (!token) return 'Читатель';

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.name || 'Читатель';
    } catch (e) {
        return 'Читатель';
    }
}

window.updateHeaderUserName = function() {
    const userName = getUserNameFromToken();
    document.querySelectorAll('.user-name').forEach((el) => {
        if (el) el.textContent = userName;
    });
};

document.addEventListener('DOMContentLoaded', () => {
    window.applyIconMarkup();
});

window.getToken = window.getToken;
