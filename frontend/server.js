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
  console.log('REGISTER request:', req.body);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/users/register/`, req.body);
    res.json(response.data);
  } catch (error) {
    console.error('Register error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/users/login/', async (req, res) => {
  console.log('LOGIN request:', req.body.email);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/users/login/`, req.body);
    res.json(response.data);
  } catch (error) {
    console.error('Login error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/users/me/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('ME request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/users/me/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('ME error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== СТАТИСТИКА ====================

app.get('/api/books/stats/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('BOOKS STATS request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Books stats error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/streak/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('STREAK request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/streak/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Streak error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/stats/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('READING STATS request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Reading stats error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/leaderboard/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('LEADERBOARD request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/leaderboard/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Leaderboard error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== ДРУЗЬЯ ====================

app.get('/api/books/friends/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('FRIENDS list request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/friends/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Friends list error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/friends/requests/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('FRIEND REQUESTS request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/friends/requests/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Friend requests error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/add-by-email/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('ADD FRIEND BY EMAIL:', req.body.email);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/add-by-email/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Add friend error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/confirm/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('CONFIRM FRIEND request');
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/confirm/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Confirm friend error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/reject/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('REJECT FRIEND request');
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/reject/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Reject friend error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/friends/remove/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('REMOVE FRIEND request');
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/friends/remove/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Remove friend error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== РОДИТЕЛЬСКИЙ КОНТРОЛЬ ====================

app.get('/api/books/parent/children/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('CHILDREN list request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/parent/children/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Children list error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/parent/parents/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('PARENTS list request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/parent/parents/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Parents list error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/connections/parent-requests/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('PARENT REQUESTS request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/connections/parent-requests/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Parent requests error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/parent/request-by-email/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('REQUEST PARENT BY EMAIL:', req.body.email);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/parent/request-by-email/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Request parent error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/confirm/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('CONFIRM PARENT request');
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/confirm/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Confirm parent error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/reject/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('REJECT PARENT request');
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/reject/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Reject parent error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/unlink-child/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('UNLINK CHILD request');
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/unlink-child/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Unlink child error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/connections/unlink-parent/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('UNLINK PARENT request');
  try {
    const response = await axios.post(`${DJANGO_API_URL}/books/connections/unlink-parent/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Unlink parent error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/connections/requests-count/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('REQUESTS COUNT request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/connections/requests-count/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Requests count error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== КНИГИ ====================

app.get('/api/books/my/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('MY BOOKS request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/my/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('My books error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/books/:bookId/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  console.log('BOOK DETAILS request:', bookId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/${bookId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Book details error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/books/books/', upload.single('file'), async (req, res) => {
  const token = req.headers.authorization;
  console.log('UPLOAD BOOK request:', req.body.name);
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
    console.error('Upload error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка загрузки книги' });
  }
});

app.post('/api/books/books/child/', upload.single('file'), async (req, res) => {
  const token = req.headers.authorization;
  console.log('UPLOAD BOOK TO CHILD request:', req.body.name);
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
    console.error('Upload to child error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка загрузки книги' });
  }
});

app.delete('/api/books/books/:bookId/delete/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  console.log('DELETE BOOK request:', bookId);
  try {
    const response = await axios.delete(`${DJANGO_API_URL}/books/books/${bookId}/delete/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Delete book error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/books/child/:childId/', async (req, res) => {
  const token = req.headers.authorization;
  const { childId } = req.params;
  console.log('CHILD BOOKS request:', childId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/child/${childId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Child books error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.put('/api/books/books/:bookId/daily-goal/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  console.log('UPDATE DAILY GOAL request:', bookId);
  try {
    const response = await axios.put(`${DJANGO_API_URL}/books/books/${bookId}/daily-goal/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Update daily goal error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/books/limit/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('BOOK LIMIT request');
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/limit/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Book limit error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/books/books/child-limit/:childId/', async (req, res) => {
  const token = req.headers.authorization;
  const { childId } = req.params;
  console.log('CHILD BOOK LIMIT request:', childId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/books/books/child-limit/${childId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Child book limit error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== СТАТИСТИКА КНИГ ====================

app.get('/api/reading/book/:bookId/stats-with-daily/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  console.log('BOOK STATS WITH DAILY request:', bookId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/book/${bookId}/stats-with-daily/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Book stats error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/child/:childId/full-stats/', async (req, res) => {
  const token = req.headers.authorization;
  const { childId } = req.params;
  console.log('CHILD FULL STATS request:', childId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/child/${childId}/full-stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Child full stats error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/child/:childId/book/:bookId/stats/', async (req, res) => {
  const token = req.headers.authorization;
  const { childId, bookId } = req.params;
  console.log('CHILD BOOK STATS request:', childId, bookId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/child/${childId}/book/${bookId}/stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Child book stats error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/book/:bookId/refresh-stats/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  console.log('REFRESH BOOK STATS request:', bookId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/book/${bookId}/refresh-stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Refresh stats error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== ЧТЕНИЕ КНИГ ====================

app.get('/api/reading/session/:bookId/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  console.log('GET SESSION request for book:', bookId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/session/${bookId}/`, {
      headers: { Authorization: token }
    });
    console.log('Session response:', response.data);
    res.json(response.data);
  } catch (error) {
    console.error('Session error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/session/progress/:sessionId/', async (req, res) => {
  const token = req.headers.authorization;
  const { sessionId } = req.params;
  console.log('SESSION PROGRESS request:', sessionId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/session/progress/${sessionId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Session progress error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/reading/session/:sessionId/continue/', async (req, res) => {
  const token = req.headers.authorization;
  const { sessionId } = req.params;
  console.log('CONTINUE SESSION request:', sessionId);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/reading/session/${sessionId}/continue/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Continue session error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/reading/page/save/', async (req, res) => {
  const token = req.headers.authorization;
  console.log('SAVE PAGE request:', req.body);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/reading/page/save/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Save page error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== PDF PROXY (ВАЖНЫЙ ЭНДПОИНТ) ====================

app.get('/api/reading/pdf-proxy/:bookId/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  const page = req.query.page || 1;

  console.log('========================================');
  console.log('PDF PROXY CALLED!');
  console.log('bookId:', bookId);
  console.log('page:', page);
  console.log('token:', token ? 'present' : 'MISSING');
  console.log('========================================');

  try {
    const djangoUrl = `${DJANGO_API_URL}/reading/pdf-proxy/${bookId}/?page=${page}`;
    console.log('Calling Django:', djangoUrl);

    const response = await axios.get(djangoUrl, {
      headers: { Authorization: token },
      responseType: 'arraybuffer'
    });

    console.log('Django response status:', response.status);
    console.log('Response size:', response.data.length, 'bytes');

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Disposition', `inline; filename=page_${page}.pdf`);
    res.send(response.data);

    console.log('PDF sent to client successfully');
  } catch (error) {
    console.error('PDF PROXY ERROR:', error.message);
    console.error('Status:', error.response?.status);
    res.status(error.response?.status || 500).send(error.response?.data || 'Ошибка загрузки PDF');
  }
});

// ==================== ТЕСТЫ ====================

app.get('/api/reading/test/check/:sessionId/', async (req, res) => {
  const token = req.headers.authorization;
  const { sessionId } = req.params;
  console.log('CHECK TEST request for session:', sessionId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/test/check/${sessionId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Check test error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/test/:testId/', async (req, res) => {
  const token = req.headers.authorization;
  const { testId } = req.params;
  console.log('GET TEST request:', testId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/test/${testId}/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Get test error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/reading/test/:testId/submit/', async (req, res) => {
  const token = req.headers.authorization;
  const { testId } = req.params;
  console.log('SUBMIT TEST request:', testId);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/reading/test/${testId}/submit/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Submit test error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.post('/api/reading/test/:testId/retake/', async (req, res) => {
  const token = req.headers.authorization;
  const { testId } = req.params;
  console.log('RETAKE TEST request:', testId);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/reading/test/${testId}/retake/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Retake test error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

app.get('/api/reading/book/:bookId/test-stats/', async (req, res) => {
  const token = req.headers.authorization;
  const { bookId } = req.params;
  console.log('BOOK TEST STATS request:', bookId);
  try {
    const response = await axios.get(`${DJANGO_API_URL}/reading/book/${bookId}/test-stats/`, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Book test stats error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// ==================== ЗАВЕРШЕНИЕ СЕССИИ ====================

app.post('/api/reading/session/:sessionId/finish/', async (req, res) => {
  const token = req.headers.authorization;
  const { sessionId } = req.params;
  console.log('FINISH SESSION request:', sessionId);
  try {
    const response = await axios.post(`${DJANGO_API_URL}/reading/session/${sessionId}/finish/`, req.body, {
      headers: { Authorization: token }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Finish session error:', error.response?.data);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
  }
});

// Детальная статистика по страницам книги ребенка
app.get('/api/reading/child/:childId/book/:bookId/page-stats/', async (req, res) => {
    const token = req.headers.authorization;
    const { childId, bookId } = req.params;
    try {
        const response = await axios.get(`${DJANGO_API_URL}/reading/child/${childId}/book/${bookId}/page-stats/`, {
            headers: { Authorization: token }
        });
        res.json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
    }
});

// Получение количества слов на странице
app.get('/api/reading/book/:bookId/page/:pageNumber/words/', async (req, res) => {
    const token = req.headers.authorization;
    const { bookId, pageNumber } = req.params;
    try {
        const response = await axios.get(`${DJANGO_API_URL}/reading/book/${bookId}/page/${pageNumber}/words/`, {
            headers: { Authorization: token }
        });
        res.json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { error: 'Ошибка сервера' });
    }
});

// ==================== ЗАПУСК СЕРВЕРА ====================

app.listen(PORT, () => {
  console.log(`========================================`);
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Proxying to Django API: ${DJANGO_API_URL}`);
  console.log(`========================================`);
});