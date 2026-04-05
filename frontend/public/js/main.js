const API_URL = '/api';

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  if (token) {
    localStorage.setItem('token', token);
  } else {
    localStorage.removeItem('token');
  }
}

async function apiRequest(endpoint, method, data, isFormData = false) {
  const token = getToken();
  const headers = {};
  
  if (token) {
    headers['Authorization'] = `Token ${token}`;
  }
  
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  
  const options = {
    method,
    headers,
    body: isFormData ? data : (data ? JSON.stringify(data) : undefined)
  };
  
  try {
    const response = await fetch(`${API_URL}${endpoint}`, options);
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    return { error: 'Ошибка соединения' };
  }
}

async function login(email, password) {
  const data = await apiRequest('/users/login/', 'POST', { email, password });
  
  if (data.token) {
    setToken(data.token);
    if (data.user) {
      localStorage.setItem('user_name', data.user.name);
      localStorage.setItem('user_email', data.user.email);
    }
    window.location.href = '/';
  } else {
    alert(data.error || 'Ошибка входа');
  }
}

async function register(name, email, password, passwordConfirm) {
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
    }
    window.location.href = '/';
  } else {
    alert(data.errors || data.error || 'Ошибка регистрации');
  }
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user_name');
  localStorage.removeItem('user_email');
  window.location.href = '/login.html';
}

async function updateHeaderUserName() {
  const token = getToken();
  if (!token) return;
  
  try {
    const user = await apiRequest('/users/me/', 'GET');
    const userNameElements = document.querySelectorAll('.user-name');
    userNameElements.forEach(el => {
      if (el) el.textContent = user.name || '';
    });
  } catch (e) {
    console.error('Error updating user name:', e);
  }
}

function formatTime(seconds) {
  if (!seconds) return '0с';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins > 0) return `${mins}м ${secs}с`;
  return `${secs}с`;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  const path = window.location.pathname;
  
  const publicPages = ['/login.html', '/register.html'];
  
  if (!token && !publicPages.includes(path)) {
    window.location.href = '/login.html';
    return;
  }
  
  if (token && !publicPages.includes(path)) {
    updateHeaderUserName();
  }
});