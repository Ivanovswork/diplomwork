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
  
  const response = await fetch(`${API_URL}${endpoint}`, options);
  return response.json();
}

async function login(email, password) {
  const data = await apiRequest('/users/login/', 'POST', { email, password });
  
  if (data.token) {
    setToken(data.token);
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
    window.location.href = '/';
  } else {
    alert(data.errors || data.error || 'Ошибка регистрации');
  }
}

function logout() {
  localStorage.removeItem('token');
  window.location.href = '/login.html';
}

function formatTime(seconds) {
  if (!seconds) return '0с';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins > 0) return `${mins}м ${secs}с`;
  return `${secs}с`;
}