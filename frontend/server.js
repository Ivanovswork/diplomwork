const express = require('express');
const cors = require('cors');
const path = require('path');
const axios = require('axios');
const multer = require('multer');
const FormData = require('form-data');

const app = express();
const PORT = process.env.PORT || 3000;

const DJANGO_API_URL = 'http://localhost:8000/api';

const upload = multer({ storage: multer.memoryStorage() });

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Логирование всех запросов
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

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

// ==================== ДРУЗЬЯ ====================

app.get('/api/books/friends/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/friends/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/friends/requests/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/friends/requests/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/add-by-email/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/add-by-email/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/confirm/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/confirm/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/reject/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/reject/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/remove/', async (req, res) => {
  const token = req.headers.authorization;
  const { target_user_id } = req.body;
  console.log('Remove friend - target_user_id:', target_user_id);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/remove/`, 
      { target_user_id: target_user_id },
      { headers: { Authorization: token } }
    );
    console.log('Remove friend response:', response.data);
    res.json(response.data);
  } catch (error) {
    console.error('Remove friend error:', error.response?.status, error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== РОДИТЕЛЬСКИЙ КОНТРОЛЬ ====================

app.get('/api/books/parent/children/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/parent/children/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/parent/parents/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/parent/parents/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/connections/parent-requests/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/connections/parent-requests/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/parent/request-by-email/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/parent/request-by-email/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/confirm/', async (req, res) => {
  const token = req.headers.authorization;
  const { target_parent_id } = req.body;
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/confirm/`, 
      { target_parent_id: target_parent_id },
      { headers: { Authorization: token } }
    );
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/reject/', async (req, res) => {
  const token = req.headers.authorization;
  const { target_parent_id } = req.body;
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/reject/`, 
      { target_parent_id: target_parent_id },
      { headers: { Authorization: token } }
    );
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/unlink-child/', async (req, res) => {
  const token = req.headers.authorization;
  const { target_parent_id } = req.body;
  console.log('Unlink child - target_parent_id:', target_parent_id);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/unlink-child/`, 
      { target_parent_id: target_parent_id },
      { headers: { Authorization: token } }
    );
    console.log('Unlink child response:', response.data);
    res.json(response.data);
  } catch (error) {
    console.error('Unlink child error:', error.response?.status, error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/unlink-parent/', async (req, res) => {
  const token = req.headers.authorization;
  const { target_child_id } = req.body;
  console.log('Unlink parent - target_child_id:', target_child_id);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/unlink-parent/`, 
      { target_child_id: target_child_id },
      { headers: { Authorization: token } }
    );
    console.log('Unlink parent response:', response.data);
    res.json(response.data);
  } catch (error) {
    console.error('Unlink parent error:', error.response?.status, error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/connections/requests-count/', async (req, res) => {
  const token = req.headers.authorization;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/connections/requests-count/`, {
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

app.get('/api/books/books/:bookId/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/${bookId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

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

app.post('/api/books/books/child/', upload.single('file'), async (req, res) => {
  const token = req.headers.authorization;
  
  try {
    const formData = new FormData();
    formData.append('child_id', req.body.child_id);
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
    
    const response = await axios.post(`${DJANGO_API_URL}/books/books/child/`, formData, {
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

// ==================== КНИГИ РЕБЕНКА ====================

app.get('/api/books/books/child/:childId/', async (req, res) => {
  const token = req.headers.authorization;
  const { childId } = req.params;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/child/${childId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== СТАТИСТИКА КНИГ ====================

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

// ==================== СТАТИСТИКА РЕБЕНКА ====================

app.get('/api/reading/child/:childId/full-stats/', async (req, res) => {
  const token = req.headers.authorization;
  const { childId } = req.params;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/child/${childId}/full-stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/child/:childId/book/:bookId/stats/', async (req, res) => {
  const token = req.headers.authorization;
  const { childId, bookId } = req.params;
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/child/${childId}/book/${bookId}/stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== ЗАПУСК СЕРВЕРА ====================

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Proxying to Django API: ${DJANGO_API_URL}`);
});