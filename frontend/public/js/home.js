async function loadHomePage() {
  try {
    const [user, stats, streak, books, leaderboard, readingStats] = await Promise.all([
      apiRequest('/users/me/', 'GET'),
      apiRequest('/books/stats/', 'GET'),
      apiRequest('/reading/streak/', 'GET'),
      apiRequest('/books/my/', 'GET'),
      apiRequest('/reading/leaderboard/', 'GET'),
      apiRequest('/reading/stats/', 'GET')
    ]);
    
    // Имя пользователя
    document.getElementById('userName').textContent = user.name || 'Читатель';
    
    // СТРИК
    document.getElementById('streakCount').textContent = streak.current_streak || 0;
    document.getElementById('longestStreak').textContent = streak.longest_streak || 0;
    
    // ДЕТАЛЬНАЯ СТАТИСТИКА
    document.getElementById('totalPagesAll').textContent = readingStats.total_pages || 0;
    document.getElementById('totalTimeAll').textContent = readingStats.total_time_formatted || '0';
    document.getElementById('totalWordsAll').textContent = readingStats.total_words || 0;
    document.getElementById('readingSpeedAll').textContent = `${readingStats.reading_speed_wpm || 0}`;
    document.getElementById('booksInProgress').textContent = readingStats.books_in_progress || 0;
    document.getElementById('booksCompleted').textContent = readingStats.books_completed || 0;
    document.getElementById('totalSessionsAll').textContent = readingStats.total_sessions || 0;
    
    // Среднее время сессии
    const avgSecs = readingStats.avg_session_duration_seconds || 0;
    const avgMins = Math.floor(avgSecs / 60);
    const avgSecsRem = Math.floor(avgSecs % 60);
    document.getElementById('avgSessionTime').textContent = avgMins > 0 ? `${avgMins}м ${avgSecsRem}с` : `${avgSecsRem}с`;
    
    // АКТИВНЫЕ КНИГИ
    renderBooks(books.my_books || []);
    
    // ЛИДЕРБОРД
    renderLeaderboard(leaderboard.leaderboard || []);
    
  } catch (error) {
    console.error('Error:', error);
  }
}

function renderBooks(books) {
  const container = document.getElementById('booksList');
  
  if (!books || books.length === 0) {
    container.innerHTML = '<div class="empty-state">У вас пока нет активных книг</div>';
    return;
  }
  
  // Показываем только книги со статусом in_progress
  const activeBooks = books.filter(book => book.status === 'in_progress');
  
  if (activeBooks.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет активных книг</div>';
    return;
  }
  
  container.innerHTML = activeBooks.map(book => `
    <div class="book-item" onclick="window.location.href='/book-stats.html?id=${book.id}'">
      <div class="book-info">
        <div class="book-name">${escapeHtml(book.name)}</div>
        <div class="book-meta">${book.pages_count} стр. • цель: ${book.daily_goal} стр./день</div>
      </div>
      <div class="book-arrow">→</div>
    </div>
  `).join('');
}

function renderLeaderboard(leaderboard) {
  const container = document.getElementById('leaderboardList');
  
  if (!leaderboard || leaderboard.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет данных для отображения</div>';
    return;
  }
  
  container.innerHTML = leaderboard.map((user, idx) => {
    const rank = idx + 1;
    let rankClass = '';
    let rankDisplay = rank;
    
    if (rank === 1) {
      rankClass = 'rank-1';
      rankDisplay = '🥇';
    } else if (rank === 2) {
      rankClass = 'rank-2';
      rankDisplay = '🥈';
    } else if (rank === 3) {
      rankClass = 'rank-3';
      rankDisplay = '🥉';
    }
    
    return `
      <div class="leaderboard-item ${user.is_current_user ? 'current-user' : ''}">
        <div class="leaderboard-rank ${rankClass}">${rankDisplay}</div>
        <div class="leaderboard-info">
          <div class="leaderboard-name">${escapeHtml(user.name)}${user.is_current_user ? ' <span style="font-size:11px; color:#3b82f6;">(Вы)</span>' : ''}</div>
          <div class="leaderboard-stats">
            <span class="streak">🔥 ${user.current_streak}</span>
            <span class="pages">📄 ${user.total_pages}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Модальное окно загрузки
function showUploadModal() {
  document.getElementById('uploadModal').classList.add('active');
}

function closeUploadModal() {
  document.getElementById('uploadModal').classList.remove('active');
  document.getElementById('bookName').value = '';
  document.getElementById('dailyGoal').value = '10';
  document.getElementById('bookFile').value = '';
  document.getElementById('fileInfo').innerHTML = '';
}

// Отображение информации о выбранном файле
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('bookFile');
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const fileInfo = document.getElementById('fileInfo');
      if (file) {
        fileInfo.innerHTML = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        fileInfo.style.color = '#10b981';
      } else {
        fileInfo.innerHTML = '';
      }
    });
  }
});

// Загрузка книги
async function uploadBook() {
  const name = document.getElementById('bookName').value;
  const dailyGoal = document.getElementById('dailyGoal').value;
  const file = document.getElementById('bookFile').files[0];
  
  if (!name || !file) {
    alert('Заполните название книги и выберите файл');
    return;
  }
  
  const token = getToken();
  const formData = new FormData();
  formData.append('name', name);
  formData.append('daily_goal', dailyGoal);
  formData.append('file', file);
  
  const submitBtn = document.querySelector('#uploadForm button[type="submit"]');
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Загрузка...';
  submitBtn.disabled = true;
  
  try {
    const response = await fetch(`${API_URL}/books/books/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`
      },
      body: formData
    });
    
    if (response.ok) {
      alert('Книга успешно добавлена!');
      closeUploadModal();
      loadHomePage();
    } else {
      const error = await response.json();
      alert(error.error || 'Ошибка загрузки книги');
    }
  } catch (error) {
    alert('Ошибка загрузки книги');
  } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
}

// Обработчики событий
document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (!token) {
    window.location.href = '/login.html';
    return;
  }
  
  loadHomePage();
  
  // Кнопка показа модального окна
  const showUploadBtn = document.getElementById('showUploadBtn');
  if (showUploadBtn) {
    showUploadBtn.addEventListener('click', showUploadModal);
  }
  
  // Форма загрузки
  const uploadForm = document.getElementById('uploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', (e) => {
      e.preventDefault();
      uploadBook();
    });
  }
  
  // Закрытие модального окна по клику вне его
  const modal = document.getElementById('uploadModal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeUploadModal();
      }
    });
  }
});