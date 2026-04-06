// Глобальная константа API
const API_URL = '/api';

// ==================== ТОКЕНЫ ====================

window.getToken = function() {
    const token = localStorage.getItem('token');
    console.log('getToken called, token:', token ? 'present' : 'missing');
    return token;
};

function setToken(token) {
    if (token) {
        localStorage.setItem('token', token);
        // Сохраняем информацию из токена
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

// ==================== API ЗАПРОСЫ ====================

async function apiRequest(endpoint, method, data) {
    const token = window.getToken();
    const headers = { 'Content-Type': 'application/json' };

    if (token) {
        headers['Authorization'] = `Token ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined
    });

    // Для ошибок возвращаем объект с error, а не выбрасываем исключение
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

// ==================== АУТЕНТИФИКАЦИЯ ====================

window.login = async function(email, password) {
    console.log('Login called with:', email);
    
    if (!email || !password) {
        alert('Введите email и пароль');
        return;
    }
    
    const data = await apiRequest('/users/login/', 'POST', { email, password });
    console.log('Login response:', data);

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
    console.log('Register called for:', email);
    
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
    
    console.log('Register response:', data);

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
        if (typeof errorMsg === 'object') {
            alert(JSON.stringify(errorMsg));
        } else {
            alert(errorMsg);
        }
    }
};

window.logout = function() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
    window.location.href = '/login.html';
};

// ==================== ИМЯ ИЗ ТОКЕНА ====================

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
    document.querySelectorAll('.user-name').forEach(el => {
        if (el) el.textContent = userName;
    });
};

// Для совместимости с reading.js
window.getToken = window.getToken;