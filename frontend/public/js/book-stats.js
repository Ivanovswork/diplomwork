let currentBookId = null;
let currentBookName = null;

async function loadBookStats() {
  const urlParams = new URLSearchParams(window.location.search);
  const bookId = urlParams.get('id');
  
  if (!bookId) {
    window.location.href = '/';
    return;
  }
  
  currentBookId = bookId;
  
  try {
    const user = await apiRequest('/users/me/', 'GET');
    document.getElementById('headerUserName').textContent = user.name || '';
  } catch (e) {}
  
  try {
    const stats = await apiRequest(`/reading/book/${bookId}/stats-with-daily/`, 'GET');
    
    currentBookName = stats.book_name;
    document.getElementById('bookTitle').textContent = stats.book_name;
    document.getElementById('deleteBookName').textContent = stats.book_name;
    
    // Прогресс
    document.getElementById('pagesRead').textContent = stats.pages_read;
    document.getElementById('totalPages').textContent = stats.total_pages;
    const progressPercent = stats.progress_percent || 0;
    document.getElementById('progressFill').style.width = `${progressPercent}%`;
    document.getElementById('progressPercent').textContent = `${progressPercent}%`;
    
    // Дневная цель
    document.getElementById('pagesReadToday').textContent = stats.pages_read_today;
    document.getElementById('dailyGoal').textContent = stats.daily_goal;
    const dailyPercent = stats.daily_goal_percent || 0;
    document.getElementById('dailyGoalFill').style.width = `${dailyPercent}%`;
    
    const goalStatus = document.getElementById('goalStatus');
    if (stats.daily_goal_achieved) {
      goalStatus.innerHTML = '✅ Дневная цель выполнена!';
      goalStatus.className = 'goal-status success';
    } else {
      goalStatus.innerHTML = `⏳ Осталось: ${stats.daily_goal_remaining} стр.`;
      goalStatus.className = 'goal-status pending';
    }
    
    // Статистика
    document.getElementById('totalTime').textContent = stats.total_time_formatted || '0';
    document.getElementById('totalWords').textContent = stats.total_words || 0;
    document.getElementById('readingSpeed').textContent = `${stats.reading_speed_wpm || 0}`;
    document.getElementById('avgTimePerPage').textContent = formatTime(stats.avg_time_per_page_seconds);
    document.getElementById('totalSessions').textContent = stats.total_sessions || 0;
    document.getElementById('hasActiveSession').textContent = stats.has_active_session ? 'Да' : 'Нет';
    document.getElementById('lastPageRead').textContent = stats.last_page_read || 0;
    
    // Тесты
    if (stats.total_tests > 0) {
      document.getElementById('testStatsCard').style.display = 'block';
      document.getElementById('totalTests').textContent = stats.total_tests;
      document.getElementById('passedTests').textContent = `${stats.passed_tests} / ${stats.total_tests}`;
      document.getElementById('avgTestScore').textContent = `${stats.avg_test_score_percent || 0}%`;
    }
    
    // Кнопка начала чтения
    const startBtn = document.getElementById('startReadingBtn');
    if (startBtn) {
      startBtn.onclick = () => {
        window.location.href = `/reading.html?id=${bookId}`;
      };
    }
    
    // Кнопка удаления
    const deleteBtn = document.getElementById('deleteBookBtn');
    if (deleteBtn) {
      deleteBtn.onclick = () => showDeleteModal();
    }
    
  } catch (error) {
    console.error('Error loading book stats:', error);
  }
}

function formatTime(seconds) {
  if (!seconds) return '0с';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins > 0) return `${mins}м ${secs}с`;
  return `${secs}с`;
}

function showDeleteModal() {
  document.getElementById('deleteModal').classList.add('active');
}

function closeDeleteModal() {
  document.getElementById('deleteModal').classList.remove('active');
}

async function confirmDelete() {
  if (!currentBookId) return;
  
  const token = getToken();
  
  try {
    const response = await fetch(`${API_URL}/books/books/${currentBookId}/delete/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      alert(`Книга "${currentBookName}" успешно удалена`);
      window.location.href = '/';
    } else {
      const error = await response.json();
      alert(error.error || 'Ошибка при удалении книги');
    }
  } catch (error) {
    alert('Ошибка при удалении книги');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (!token) {
    window.location.href = '/login.html';
    return;
  }
  loadBookStats();
});