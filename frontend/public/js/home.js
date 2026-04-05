// ==================== ЗАГРУЗКА ГЛАВНОЙ СТРАНИЦЫ ====================

async function loadHomePage() {
  try {
    console.log('Loading home page...');
    
    showLoadingIndicators();
    
    const [
      user, 
      stats, 
      streak, 
      books, 
      leaderboard, 
      readingStats, 
      friends, 
      friendRequests, 
      children, 
      parentRequests
    ] = await Promise.all([
      apiRequest('/users/me/', 'GET'),
      apiRequest('/books/stats/', 'GET'),
      apiRequest('/reading/streak/', 'GET'),
      apiRequest('/books/my/', 'GET'),
      apiRequest('/reading/leaderboard/', 'GET'),
      apiRequest('/reading/stats/', 'GET'),
      apiRequest('/books/friends/', 'GET'),
      apiRequest('/books/friends/requests/', 'GET'),
      apiRequest('/books/parent/children/', 'GET'),
      apiRequest('/books/connections/parent-requests/', 'GET')
    ]);
    
    console.log('Friends:', friends);
    console.log('Children:', children);
    console.log('Books:', books);
    
    updateUserInfo(user);
    updateStreak(streak);
    updateReadingStats(readingStats);
    renderBooks(books.my_books || []);
    renderLeaderboard(leaderboard.leaderboard || []);
    renderFriends(friends.friends || []);
    renderFriendRequests(friendRequests.friend_requests || []);
    renderChildren(children.children || []);
    renderParentRequests(parentRequests.parent_requests || []);
    
  } catch (error) {
    console.error('Error loading home page:', error);
    showErrorMessage();
  }
}

function showLoadingIndicators() {
  const elements = ['booksList', 'friendsList', 'childrenList', 'leaderboardList'];
  elements.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '<div class="loading-placeholder">Загрузка...</div>';
  });
}

function showErrorMessage() {
  const elements = ['booksList', 'friendsList', 'childrenList', 'leaderboardList'];
  elements.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '<div class="error-placeholder">Ошибка загрузки</div>';
  });
}

function updateUserInfo(user) {
  const userNameElements = document.querySelectorAll('.user-name');
  userNameElements.forEach(el => {
    if (el) el.textContent = user.name || '';
  });
}

function updateStreak(streak) {
  document.getElementById('streakCount').textContent = streak.current_streak || 0;
  document.getElementById('longestStreak').textContent = streak.longest_streak || 0;
}

function updateReadingStats(stats) {
  document.getElementById('totalPagesAll').textContent = stats.total_pages || 0;
  document.getElementById('totalTimeAll').textContent = stats.total_time_formatted || '0';
  document.getElementById('totalWordsAll').textContent = stats.total_words || 0;
  document.getElementById('readingSpeedAll').textContent = `${stats.reading_speed_wpm || 0} слов/мин`;
  document.getElementById('booksInProgress').textContent = stats.books_in_progress || 0;
  document.getElementById('booksCompleted').textContent = stats.books_completed || 0;
  document.getElementById('totalSessionsAll').textContent = stats.total_sessions || 0;
  
  const avgSecs = stats.avg_session_duration_seconds || 0;
  const avgMins = Math.floor(avgSecs / 60);
  const avgSecsRem = Math.floor(avgSecs % 60);
  document.getElementById('avgSessionTime').textContent = avgMins > 0 ? `${avgMins}м ${avgSecsRem}с` : `${avgSecsRem}с`;
}

// ==================== КНИГИ ====================

function renderBooks(books) {
  const container = document.getElementById('booksList');
  
  if (!books || books.length === 0) {
    container.innerHTML = '<div class="empty-state">У вас пока нет активных книг</div>';
    return;
  }
  
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

// ==================== ДРУЗЬЯ ====================

function renderFriends(friends) {
  const container = document.getElementById('friendsList');
  
  if (!friends || friends.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет друзей</div>';
    return;
  }
  
  container.innerHTML = friends.map(friend => `
    <div class="social-item">
      <div class="social-avatar">👤</div>
      <div class="social-info">
        <div class="social-name">${escapeHtml(friend.name)}</div>
        <div class="social-email">${escapeHtml(friend.email)}</div>
      </div>
      <div class="social-actions">
        <button class="social-action-btn" onclick="viewFriendStats(${friend.id}, '${escapeHtml(friend.name)}')">Статистика</button>
      </div>
    </div>
  `).join('');
}

async function viewFriendStats(userId, userName) {
  alert(`Статистика друга ${userName} будет доступна в следующей версии`);
}

function renderFriendRequests(requests) {
  const container = document.getElementById('friendRequestsList');
  const card = document.getElementById('friendRequestsCard');
  
  if (!requests || requests.length === 0) {
    if (card) card.style.display = 'none';
    return;
  }
  
  if (card) card.style.display = 'block';
  container.innerHTML = requests.map(req => `
    <div class="social-item request-item">
      <div class="social-avatar">👤</div>
      <div class="social-info">
        <div class="social-name">${escapeHtml(req.user1_data?.name || 'Пользователь')}</div>
        <div class="social-email">${escapeHtml(req.user1_data?.email || '')}</div>
      </div>
      <div class="request-buttons">
        <button class="request-accept" onclick="acceptFriendRequest(${req.id})">Принять</button>
        <button class="request-reject" onclick="rejectFriendRequest(${req.id})">Отклонить</button>
      </div>
    </div>
  `).join('');
}

async function acceptFriendRequest(connectionId) {
  try {
    const result = await apiRequest('/books/friends/confirm/', 'POST', { target_user_id: connectionId });
    if (result.message) {
      alert('Запрос принят!');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при принятии запроса');
    }
  } catch (error) {
    alert('Ошибка при принятии запроса');
  }
}

async function rejectFriendRequest(connectionId) {
  try {
    const result = await apiRequest('/books/friends/reject/', 'POST', { target_user_id: connectionId });
    if (result.message) {
      alert('Запрос отклонен');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отклонении запроса');
    }
  } catch (error) {
    alert('Ошибка при отклонении запроса');
  }
}

// ==================== ДЕТИ ====================

function renderChildren(children) {
  const container = document.getElementById('childrenList');
  
  if (!children || children.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет детей</div>';
    return;
  }
  
  container.innerHTML = children.map(child => `
    <div class="social-item child-item">
      <div class="social-avatar">👶</div>
      <div class="social-info">
        <div class="social-name">${escapeHtml(child.name)}</div>
        <div class="social-email">${escapeHtml(child.email)}</div>
      </div>
      <div class="social-actions">
        <button class="social-action-btn" onclick="viewChildStats(${child.id}, '${escapeHtml(child.name)}')">Статистика</button>
        <button class="social-action-btn add-book" onclick="showUploadChildBookModal(${child.id}, '${escapeHtml(child.name)}')">Добавить книгу</button>
      </div>
    </div>
  `).join('');
}

function viewChildStats(childId, childName) {
  window.location.href = `/child-stats.html?id=${childId}&name=${encodeURIComponent(childName)}`;
}

function renderParentRequests(requests) {
  const container = document.getElementById('parentRequestsList');
  const card = document.getElementById('parentRequestsCard');
  
  if (!requests || requests.length === 0) {
    if (card) card.style.display = 'none';
    return;
  }
  
  if (card) card.style.display = 'block';
  container.innerHTML = requests.map(req => `
    <div class="social-item request-item">
      <div class="social-avatar">👨‍👩‍👧</div>
      <div class="social-info">
        <div class="social-name">${escapeHtml(req.user1_data?.name || 'Родитель')}</div>
        <div class="social-email">${escapeHtml(req.user1_data?.email || '')}</div>
      </div>
      <div class="request-buttons">
        <button class="request-accept" onclick="acceptParentRequest(${req.id})">Принять</button>
        <button class="request-reject" onclick="rejectParentRequest(${req.id})">Отклонить</button>
      </div>
    </div>
  `).join('');
}

async function acceptParentRequest(connectionId) {
  try {
    const result = await apiRequest('/books/connections/confirm/', 'POST', { target_parent_id: connectionId });
    if (result.message) {
      alert('Запрос принят!');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при принятии запроса');
    }
  } catch (error) {
    alert('Ошибка при принятии запроса');
  }
}

async function rejectParentRequest(connectionId) {
  try {
    const result = await apiRequest('/books/connections/reject/', 'POST', { target_parent_id: connectionId });
    if (result.message) {
      alert('Запрос отклонен');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отклонении запроса');
    }
  } catch (error) {
    alert('Ошибка при отклонении запроса');
  }
}

// ==================== ЛИДЕРБОРД ====================

function renderLeaderboard(leaderboard) {
  const container = document.getElementById('leaderboardList');
  
  if (!leaderboard || leaderboard.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет данных</div>';
    return;
  }
  
  container.innerHTML = leaderboard.map((user, idx) => {
    const rank = idx + 1;
    let rankDisplay = rank;
    let rankClass = '';
    
    if (rank === 1) {
      rankDisplay = '🥇';
      rankClass = 'rank-1';
    } else if (rank === 2) {
      rankDisplay = '🥈';
      rankClass = 'rank-2';
    } else if (rank === 3) {
      rankDisplay = '🥉';
      rankClass = 'rank-3';
    }
    
    return `
      <div class="leaderboard-item ${user.is_current_user ? 'current-user' : ''}">
        <div class="leaderboard-rank ${rankClass}">${rankDisplay}</div>
        <div class="leaderboard-info">
          <div class="leaderboard-name">${escapeHtml(user.name)}${user.is_current_user ? ' <span class="current-badge">(Вы)</span>' : ''}</div>
          <div class="leaderboard-stats">
            <span class="streak">🔥 ${user.current_streak}</span>
            <span class="pages">📄 ${user.total_pages}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ==================== ДОБАВЛЕНИЕ ДРУГА ====================

function showAddFriendModal() {
  document.getElementById('addFriendModal').classList.add('active');
}

function closeAddFriendModal() {
  document.getElementById('addFriendModal').classList.remove('active');
  document.getElementById('friendEmail').value = '';
}

async function addFriend() {
  const email = document.getElementById('friendEmail').value;
  
  if (!email) {
    alert('Введите email друга');
    return;
  }
  
  try {
    const result = await apiRequest('/books/friends/add-by-email/', 'POST', { email });
    if (result.status) {
      alert('Запрос в друзья отправлен!');
      closeAddFriendModal();
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отправке запроса');
    }
  } catch (error) {
    alert('Ошибка при отправке запроса');
  }
}

// ==================== ДОБАВЛЕНИЕ РЕБЕНКА ====================

function showAddChildModal() {
  document.getElementById('addChildModal').classList.add('active');
}

function closeAddChildModal() {
  document.getElementById('addChildModal').classList.remove('active');
  document.getElementById('childEmail').value = '';
}

async function addChild() {
  const email = document.getElementById('childEmail').value;
  
  if (!email) {
    alert('Введите email ребенка');
    return;
  }
  
  try {
    const result = await apiRequest('/books/parent/request-by-email/', 'POST', { email });
    if (result.status) {
      alert('Запрос на добавление ребенка отправлен!');
      closeAddChildModal();
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отправке запроса');
    }
  } catch (error) {
    alert('Ошибка при отправке запроса');
  }
}

// ==================== ЗАГРУЗКА КНИГИ ====================

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

// ==================== ЗАГРУЗКА КНИГИ РЕБЕНКУ ====================

let currentChildId = null;
let currentChildName = null;

function showUploadChildBookModal(childId, childName) {
  currentChildId = childId;
  currentChildName = childName;
  document.getElementById('targetChildId').value = childId;
  document.getElementById('targetChildName').value = childName;
  document.getElementById('uploadChildBookModal').classList.add('active');
}

function closeUploadChildBookModal() {
  document.getElementById('uploadChildBookModal').classList.remove('active');
  document.getElementById('childBookName').value = '';
  document.getElementById('childDailyGoal').value = '10';
  document.getElementById('childBookFile').value = '';
  document.getElementById('childFileInfo').innerHTML = '';
  currentChildId = null;
  currentChildName = null;
}

async function uploadChildBook() {
  const name = document.getElementById('childBookName').value;
  const dailyGoal = document.getElementById('childDailyGoal').value;
  const file = document.getElementById('childBookFile').files[0];
  
  if (!name || !file) {
    alert('Заполните название книги и выберите файл');
    return;
  }
  
  const token = getToken();
  const formData = new FormData();
  formData.append('child_id', currentChildId);
  formData.append('name', name);
  formData.append('daily_goal', dailyGoal);
  formData.append('file', file);
  
  const submitBtn = document.querySelector('#uploadChildBookForm button[type="submit"]');
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Загрузка...';
  submitBtn.disabled = true;
  
  try {
    const response = await fetch(`${API_URL}/books/books/child/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`
      },
      body: formData
    });
    
    if (response.ok) {
      alert('Книга успешно добавлена ребенку!');
      closeUploadChildBookModal();
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

// ==================== ФАЙЛЫ ====================

function setupFileInputs() {
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
  
  const childFileInput = document.getElementById('childBookFile');
  if (childFileInput) {
    childFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const fileInfo = document.getElementById('childFileInfo');
      if (file) {
        fileInfo.innerHTML = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        fileInfo.style.color = '#10b981';
      } else {
        fileInfo.innerHTML = '';
      }
    });
  }
}

// ==================== ЗАКРЫТИЕ МОДАЛЬНЫХ ОКОН ====================

function setupModalClose() {
  const modals = ['uploadModal', 'addFriendModal', 'addChildModal', 'uploadChildBookModal'];
  modals.forEach(modalId => {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          if (modalId === 'uploadModal') closeUploadModal();
          if (modalId === 'addFriendModal') closeAddFriendModal();
          if (modalId === 'addChildModal') closeAddChildModal();
          if (modalId === 'uploadChildBookModal') closeUploadChildBookModal();
        }
      });
    }
  });
}

// ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

function setupEventListeners() {
  document.getElementById('showAddFriendBtn')?.addEventListener('click', showAddFriendModal);
  document.getElementById('showAddChildBtn')?.addEventListener('click', showAddChildModal);
  document.getElementById('showUploadBtn')?.addEventListener('click', showUploadModal);
  
  document.getElementById('addFriendForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    addFriend();
  });
  
  document.getElementById('addChildForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    addChild();
  });
  
  document.getElementById('uploadForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    uploadBook();
  });
  
  document.getElementById('uploadChildBookForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    uploadChildBook();
  });
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (!token) {
    window.location.href = '/login.html';
    return;
  }
  
  loadHomePage();
  setupFileInputs();
  setupModalClose();
  setupEventListeners();
});