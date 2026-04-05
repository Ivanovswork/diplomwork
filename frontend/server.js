const express = require('express');
const cors = require('cors');
const path = require('path');
const axios = require('axios');
const multer = require('multer');
const FormData = require('form-data');
const { Readable } = require('stream');

const app = express();
const PORT = process.env.PORT || 3000;

const DJANGO_API_URL = 'http://localhost:8000/api';

// Настройка multer для обработки файлов в памяти
const upload = multer({ storage: multer.memoryStorage() });

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// ==================== АУТЕНТИФИКАЦИЯ ====================

app.post('/api/users/register/', async (req, res) => {
  try {
    const response = await axios.post(`${DJANGO_API_URL}/users/register/`, req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/users/login/', async (req, res) => {
  try {
    const response = await axios.post(`${DJANGO_API_URL}/users/login/`, req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/users/me/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/users/me/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== СТАТИСТИКА ====================

app.get('/api/books/stats/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/streak/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/streak/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/stats/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/leaderboard/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/leaderboard/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== КНИГИ ====================

app.get('/api/books/my/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/my/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ЗАГРУЗКА КНИГИ (с обработкой файла)
app.post('/api/books/books/', upload.single('file'), async (req, res) => {
  const token = req.headers.authorization;
  
  try {
    const formData = new FormData();
    formData.append('name', req.body.name);
    formData.append('daily_goal', req.body.daily_goal);
    
    if (req.file) {
      formData.append('file', req.file.buffer, {
        filename: req.file.originalname,
        contentType: req.file.mimetype
      });
    } else {
      return res.status(400).json({ error: 'Файл не выбран' });
    }
    
    const response = await axios.post(`${DJANGO_API_URL}/books/books/`, formData, {
      headers: {
        Authorization: token,
        ...formData.getHeaders()
      }
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('Upload error:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка загрузки книги' });
  }
});

// СТАТИСТИКА КНИГИ
app.get('/api/reading/book/:bookId/stats-with-daily/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/book/${bookId}/stats-with-daily/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// УДАЛЕНИЕ КНИГИ
app.delete('/api/books/books/:bookId/delete/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  try {
    const response = await axios.delete(`${DJANGO_API_URL}/books/books/${bookId}/delete/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ЗАПУСК СЕРВЕРА
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Proxying to Django API: ${DJANGO_API_URL}`);
});