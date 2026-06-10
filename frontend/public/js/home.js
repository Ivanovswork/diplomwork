function iconChip(name, extraClass = '') {
  return `<span class="${extraClass ? `${extraClass} ` : ''}icon-badge">${window.renderIcon(name)}</span>`;
}

function iconInline(name, extraClass = '') {
  return window.renderIcon(name, extraClass);
}

async function loadHomePage() {
  try {
    showLoadingIndicators();

    const [
      stats,
      streak,
      books,
      leaderboard,
      readingStats,
      friends,
      friendRequests,
      children,
      parentRequests,
      parents
    ] = await Promise.all([
      apiRequest('/books/stats/', 'GET'),
      apiRequest('/reading/streak/', 'GET'),
      apiRequest('/books/my/', 'GET'),
      apiRequest('/reading/leaderboard/', 'GET'),
      apiRequest('/reading/stats/', 'GET'),
      apiRequest('/books/friends/', 'GET'),
      apiRequest('/books/friends/requests/', 'GET'),
      apiRequest('/books/parent/children/', 'GET'),
      apiRequest('/books/connections/parent-requests/', 'GET'),
      apiRequest('/books/parent/parents/', 'GET')
    ]);

    updateHeaderUserName();
    updateStreak(streak);
    updateReadingStats(readingStats);
    renderBooks(books.my_books || []);
    renderLeaderboard(leaderboard.leaderboard || []);
    renderFriends(friends.friends || []);
    renderFriendRequests(friendRequests.friend_requests || []);
    renderChildren(children.children || []);
    renderParentRequests(parentRequests.parent_requests || []);
    renderParents(parents.parents || []);
    window.applyIconMarkup();
  } catch (error) {
    console.error('Error loading home page:', error);
    showErrorMessage();
  }
}

function showLoadingIndicators() {
  const elements = [
    'booksList',
    'friendsList',
    'childrenList',
    'parentsList',
    'leaderboardList',
    'friendRequestsList',
    'parentRequestsList'
  ];

  elements.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '<div class="loading-placeholder">Загрузка...</div>';
  });
}

function showErrorMessage() {
  const elements = ['booksList', 'friendsList', 'childrenList', 'parentsList', 'leaderboardList'];
  elements.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '<div class="error-placeholder">Ошибка загрузки</div>';
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

function renderBooks(books) {
  const container = document.getElementById('booksList');

  if (!books || books.length === 0) {
    container.innerHTML = '<div class="empty-state">У вас пока нет активных книг</div>';
    return;
  }

  const activeBooks = books.filter((book) => book.status === 'in_progress');
  if (activeBooks.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет активных книг</div>';
    return;
  }

  container.innerHTML = activeBooks.map((book) => `
    <div class="book-item" onclick="window.location.href='/book-stats.html?id=${book.id}'">
      <div class="book-info">
        <div class="book-name">${escapeHtml(book.name)}</div>
        <div class="book-meta">${book.pages_count} стр. • цель: ${book.daily_goal} стр./день</div>
      </div>
      <div class="book-arrow">${iconInline('chevronRight')}</div>
    </div>
  `).join('');
}

function renderFriends(friends) {
  const container = document.getElementById('friendsList');

  if (!friends || friends.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет друзей</div>';
    return;
  }

  container.innerHTML = friends.map((friend) => `
    <div class="social-item">
      <div class="social-avatar">${iconInline('friends')}</div>
      <div class="social-info">
        <div class="social-name">${escapeHtml(friend.name)}</div>
        <div class="social-email">${escapeHtml(friend.email)}</div>
      </div>
      <div class="social-actions">
        <button class="social-action-btn" onclick="viewFriendStats(${friend.id}, '${escapeHtml(friend.name)}')">Статистика</button>
        <button class="social-action-btn delete-btn" onclick="removeFriend(${friend.id}, '${escapeHtml(friend.name)}')">Удалить</button>
      </div>
    </div>
  `).join('');
}

async function viewFriendStats(userId, userName) {
  alert(`Статистика друга ${userName} будет доступна в следующей версии`);
}

async function removeFriend(userId, friendName) {
  if (!confirm(`Вы уверены, что хотите удалить друга "${friendName}"?`)) return;

  const token = getToken();
  const url = `${API_URL}/books/friends/remove/`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Token ${token}`
      },
      body: JSON.stringify({ target_user_id: userId })
    });

    const result = await response.json();
    if (response.ok && (result.message || result.success)) {
      alert('Друг удалён');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при удалении друга');
    }
  } catch (error) {
    console.error('Error removing friend:', error);
    alert('Ошибка при удалении друга');
  }
}

function renderFriendRequests(requests) {
  const container = document.getElementById('friendRequestsList');
  const card = document.getElementById('friendRequestsCard');

  if (!requests || requests.length === 0) {
    if (card) card.style.display = 'none';
    return;
  }

  if (card) card.style.display = 'block';
  container.innerHTML = requests.map((req) => `
    <div class="request-item">
      <div class="request-header">
        <div class="request-avatar">${iconInline('person')}</div>
        <div class="request-info">
          <div class="request-name">${escapeHtml(req.user1_data?.name || 'Пользователь')}</div>
          <div class="request-email">${escapeHtml(req.user1_data?.email || '')}</div>
        </div>
      </div>
      <div class="request-type">${iconInline('mail')}<span>Запрос в друзья</span></div>
      <div class="request-buttons">
        <button class="request-accept" onclick="acceptFriendRequest(${req.user1_data.id}, ${req.id})">Принять</button>
        <button class="request-reject" onclick="rejectFriendRequest(${req.user1_data.id}, ${req.id})">Отклонить</button>
      </div>
    </div>
  `).join('');
}

async function acceptFriendRequest(userId) {
  try {
    const result = await apiRequest('/books/friends/confirm/', 'POST', { target_user_id: userId });
    if (result.message) {
      alert('Запрос принят');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при принятии запроса');
    }
  } catch (error) {
    alert('Ошибка при принятии запроса');
  }
}

async function rejectFriendRequest(userId) {
  try {
    const result = await apiRequest('/books/friends/reject/', 'POST', { target_user_id: userId });
    if (result.message) {
      alert('Запрос отклонён');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отклонении запроса');
    }
  } catch (error) {
    alert('Ошибка при отклонении запроса');
  }
}

function renderChildren(children) {
  const container = document.getElementById('childrenList');

  if (!children || children.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет детей</div>';
    return;
  }

  container.innerHTML = children.map((child) => `
    <div class="social-item child-item">
      <div class="social-avatar">${iconInline('person')}</div>
      <div class="social-info">
        <div class="social-name">${escapeHtml(child.name)}</div>
        <div class="social-email">${escapeHtml(child.email)}</div>
      </div>
      <div class="social-actions">
        <button class="social-action-btn" onclick="viewChildStats(${child.id}, '${escapeHtml(child.name)}')">Статистика</button>
        <button class="social-action-btn add-book" onclick="showUploadChildBookModal(${child.id}, '${escapeHtml(child.name)}')">Добавить книгу</button>
        <button class="social-action-btn delete-btn" onclick="unlinkChild(${child.id}, '${escapeHtml(child.name)}')">Отвязать</button>
      </div>
    </div>
  `).join('');
}

function viewChildStats(childId, childName) {
  window.location.href = `/child-stats.html?id=${childId}&name=${encodeURIComponent(childName)}`;
}

async function unlinkChild(childId, childName) {
  if (!confirm(`Вы уверены, что хотите отвязать ребёнка "${childName}"?`)) return;

  const token = getToken();
  const url = `${API_URL}/books/connections/unlink-parent/`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Token ${token}`
      },
      body: JSON.stringify({ target_child_id: childId })
    });

    const result = await response.json();
    if (response.ok && result.message) {
      alert('Ребёнок отвязан');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отвязке ребёнка');
    }
  } catch (error) {
    console.error('Error unlinking child:', error);
    alert('Ошибка при отвязке ребёнка');
  }
}

function renderParentRequests(requests) {
  const container = document.getElementById('parentRequestsList');
  const card = document.getElementById('parentRequestsCard');

  if (!requests || requests.length === 0) {
    if (card) card.style.display = 'none';
    return;
  }

  if (card) card.style.display = 'block';
  container.innerHTML = requests.map((req) => `
    <div class="request-item">
      <div class="request-header">
        <div class="request-avatar">${iconInline('family')}</div>
        <div class="request-info">
          <div class="request-name">${escapeHtml(req.user1_data?.name || 'Родитель')}</div>
          <div class="request-email">${escapeHtml(req.user1_data?.email || '')}</div>
        </div>
      </div>
      <div class="request-type">${iconInline('security')}<span>Запрос на родительский контроль</span></div>
      <div class="request-buttons">
        <button class="request-accept" onclick="acceptParentRequest(${req.user1_data.id}, ${req.id})">Принять</button>
        <button class="request-reject" onclick="rejectParentRequest(${req.user1_data.id}, ${req.id})">Отклонить</button>
      </div>
    </div>
  `).join('');
}

async function acceptParentRequest(parentUserId) {
  try {
    const result = await apiRequest('/books/connections/confirm/', 'POST', { target_parent_id: parentUserId });
    if (result.message) {
      alert('Запрос принят');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при принятии запроса');
    }
  } catch (error) {
    alert('Ошибка при принятии запроса');
  }
}

async function rejectParentRequest(parentUserId) {
  try {
    const result = await apiRequest('/books/connections/reject/', 'POST', { target_parent_id: parentUserId });
    if (result.message) {
      alert('Запрос отклонён');
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отклонении запроса');
    }
  } catch (error) {
    alert('Ошибка при отклонении запроса');
  }
}

function renderParents(parents) {
  const container = document.getElementById('parentsList');

  if (!parents || parents.length === 0) {
    container.innerHTML = '<div class="empty-state">Нет родителей</div>';
    return;
  }

  container.innerHTML = parents.map((parent) => `
    <div class="social-item parent-item">
      <div class="social-avatar">${iconInline('family')}</div>
      <div class="social-info">
        <div class="social-name">${escapeHtml(parent.name)}</div>
        <div class="social-email">${escapeHtml(parent.email)}</div>
      </div>
    </div>
  `).join('');
}

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
      rankDisplay = '1';
      rankClass = 'rank-1';
    } else if (rank === 2) {
      rankDisplay = '2';
      rankClass = 'rank-2';
    } else if (rank === 3) {
      rankDisplay = '3';
      rankClass = 'rank-3';
    }

    return `
      <div class="leaderboard-item ${user.is_current_user ? 'current-user' : ''}">
        <div class="leaderboard-rank ${rankClass}">${rankDisplay}</div>
        <div class="leaderboard-info">
          <div class="leaderboard-name">${escapeHtml(user.name)}${user.is_current_user ? ' <span class="current-badge">(Вы)</span>' : ''}</div>
          <div class="leaderboard-stats">
            <span class="streak">${iconInline('streak')}<span>${user.current_streak}</span></span>
            <span class="pages">${iconInline('bookOpen')}<span>${user.total_pages}</span></span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

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
      alert('Запрос в друзья отправлен');
      closeAddFriendModal();
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отправке запроса');
    }
  } catch (error) {
    alert('Ошибка при отправке запроса');
  }
}

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
    alert('Введите email ребёнка');
    return;
  }

  try {
    const result = await apiRequest('/books/parent/request-by-email/', 'POST', { email });
    if (result.status) {
      alert('Запрос на добавление ребёнка отправлен');
      closeAddChildModal();
      loadHomePage();
    } else {
      alert(result.error || 'Ошибка при отправке запроса');
    }
  } catch (error) {
    alert('Ошибка при отправке запроса');
  }
}

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
      headers: { Authorization: `Token ${token}` },
      body: formData
    });

    if (response.ok) {
      alert('Книга успешно добавлена');
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

let currentChildId = null;

function showUploadChildBookModal(childId, childName) {
  currentChildId = childId;
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
      headers: { Authorization: `Token ${token}` },
      body: formData
    });

    if (response.ok) {
      alert('Книга успешно добавлена ребёнку');
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

function setupFileInputs() {
  const fileInput = document.getElementById('bookFile');
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const fileInfo = document.getElementById('fileInfo');
      fileInfo.innerHTML = file ? `${iconInline('file')} ${file.name} (${(file.size / 1024).toFixed(1)} KB)` : '';
      fileInfo.style.color = file ? '#2563eb' : '';
    });
  }

  const childFileInput = document.getElementById('childBookFile');
  if (childFileInput) {
    childFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const fileInfo = document.getElementById('childFileInfo');
      fileInfo.innerHTML = file ? `${iconInline('file')} ${file.name} (${(file.size / 1024).toFixed(1)} KB)` : '';
      fileInfo.style.color = file ? '#2563eb' : '';
    });
  }
}

function setupModalClose() {
  const modals = ['uploadModal', 'addFriendModal', 'addChildModal', 'uploadChildBookModal'];
  modals.forEach((modalId) => {
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

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (!token) {
    window.location.href = '/login.html';
    return;
  }

  window.applyIconMarkup();
  loadHomePage();
  setupFileInputs();
  setupModalClose();
  setupEventListeners();
});
