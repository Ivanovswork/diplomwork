let childId = null;
let bookId = null;
let currentBookName = null;
let isParentBook = false;

async function loadChildBookStats() {
  const urlParams = new URLSearchParams(window.location.search);
  childId = urlParams.get('childId');
  bookId = urlParams.get('bookId');
  const bookName = urlParams.get('bookName');
  
  console.log('Loading child book stats - childId:', childId, 'bookId:', bookId);
  
  if (!childId || !bookId) {
    window.location.href = '/';
    return;
  }
  
  currentBookName = bookName || 'Книга';
  document.getElementById('bookTitle').textContent = currentBookName;
  document.getElementById('deleteBookName').textContent = currentBookName;
  
  try {
    const user = await apiRequest('/users/me/', 'GET');
    document.getElementById('headerUserName').textContent = user.name || '';
  } catch (e) {}
  
  try {
    // Получаем информацию о книге (кто загрузил)
    const bookInfo = await apiRequest(`/books/books/${bookId}/`, 'GET');
    console.log('Book info:', bookInfo);
    
    // Проверяем, загружена ли книга родителем
    isParentBook = bookInfo.uploaded_by_id && bookInfo.uploaded_by_id !== childId;
    console.log('Is parent book:', isParentBook);
    
    // Получаем статистику книги
    const stats = await apiRequest(`/reading/book/${bookId}/stats-with-daily/`, 'GET');
    console.log('Stats response:', stats);
    
    if (!stats) {
      showErrorMessage();
      return;
    }
    
    // Прогресс чтения
    const pagesRead = stats.pages_read || 0;
    const totalPages = stats.total_pages || 0;
    const progressPercent = totalPages > 0 ? (pagesRead / totalPages * 100) : 0;
    
    document.getElementById('pagesRead').textContent = pagesRead;
    document.getElementById('totalPages').textContent = totalPages;
    document.getElementById('progressFill').style.width = `${progressPercent}%`;
    document.getElementById('progressPercent').textContent = `${Math.round(progressPercent)}%`;
    
    // Дневная цель
    const pagesReadToday = stats.pages_read_today || 0;
    const dailyGoal = stats.daily_goal || 0;
    const dailyGoalRemaining = stats.daily_goal_remaining !== undefined ? stats.daily_goal_remaining : (dailyGoal - pagesReadToday);
    const dailyGoalPercent = stats.daily_goal_percent !== undefined ? stats.daily_goal_percent : (dailyGoal > 0 ? (pagesReadToday / dailyGoal * 100) : 0);
    const dailyGoalAchieved = stats.daily_goal_achieved || (pagesReadToday >= dailyGoal);
    
    document.getElementById('pagesReadToday').textContent = pagesReadToday;
    document.getElementById('dailyGoal').textContent = dailyGoal;
    document.getElementById('dailyGoalFill').style.width = `${Math.min(dailyGoalPercent, 100)}%`;
    
    const goalStatus = document.getElementById('goalStatus');
    if (dailyGoalAchieved && dailyGoal > 0) {
      goalStatus.innerHTML = '✅ Дневная цель выполнена! Отличная работа!';
      goalStatus.className = 'goal-status success';
    } else if (dailyGoal > 0) {
      goalStatus.innerHTML = `⏳ Осталось прочитать ${Math.max(0, dailyGoalRemaining)} страниц из ${dailyGoal}`;
      goalStatus.className = 'goal-status pending';
    } else {
      goalStatus.innerHTML = `📖 Прочитано ${pagesReadToday} страниц сегодня`;
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
    
    // СТАТИСТИКА ТЕСТОВ - показываем только если книга загружена родителем
    const testStatsCard = document.getElementById('testStatsCard');
    if (isParentBook) {
      testStatsCard.style.display = 'block';
      document.getElementById('totalTests').textContent = stats.total_tests || 0;
      document.getElementById('passedTests').textContent = `${stats.passed_tests || 0} / ${stats.total_tests || 0}`;
      document.getElementById('avgTestScore').textContent = `${stats.avg_test_score_percent || 0}%`;
      
      // Цвета для статистики тестов
      const avgScore = stats.avg_test_score_percent || 0;
      const avgScoreEl = document.getElementById('avgTestScore');
      if (avgScore >= 70) {
        avgScoreEl.style.color = '#10b981';
      } else if (avgScore >= 40) {
        avgScoreEl.style.color = '#f59e0b';
      } else {
        avgScoreEl.style.color = '#ef4444';
      }
    } else {
      testStatsCard.style.display = 'none';
    }
    
    // Показываем кнопку удаления для родителя
    const deleteBtn = document.getElementById('deleteBookBtn');
    if (deleteBtn) {
      deleteBtn.style.display = 'block';
    }
    
  } catch (error) {
    console.error('Error loading child book stats:', error);
    showErrorMessage();
  }
}

function formatTime(seconds) {
  if (!seconds || seconds === 0) return '0с';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins > 0) return `${mins}м ${secs}с`;
  return `${secs}с`;
}

function showErrorMessage() {
  document.getElementById('pagesRead').textContent = '—';
  document.getElementById('totalPages').textContent = '—';
  document.getElementById('progressFill').style.width = '0%';
  document.getElementById('progressPercent').textContent = '0%';
  
  document.getElementById('pagesReadToday').textContent = '—';
  document.getElementById('dailyGoal').textContent = '—';
  document.getElementById('dailyGoalFill').style.width = '0%';
  document.getElementById('goalStatus').innerHTML = '❌ Ошибка загрузки данных';
  
  document.getElementById('totalTime').textContent = '—';
  document.getElementById('totalWords').textContent = '—';
  document.getElementById('readingSpeed').textContent = '—';
  document.getElementById('avgTimePerPage').textContent = '—';
  document.getElementById('totalSessions').textContent = '—';
  document.getElementById('hasActiveSession').textContent = '—';
  document.getElementById('lastPageRead').textContent = '—';
}

function showDeleteModal() {
  document.getElementById('deleteModal').classList.add('active');
}

function closeDeleteModal() {
  document.getElementById('deleteModal').classList.remove('active');
}

async function confirmDelete() {
  if (!bookId) return;
  
  const token = getToken();
  
  try {
    const response = await fetch(`${API_URL}/books/books/${bookId}/delete/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      alert(`Книга "${currentBookName}" успешно удалена`);
      window.location.href = `/child-stats.html?id=${childId}`;
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
  loadChildBookStats();
});