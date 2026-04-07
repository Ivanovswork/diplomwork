let childId = null;
let bookId = null;
let currentBookName = null;
let isParent = false;  // Флаг, является ли текущий пользователь родителем

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
        
        // Проверяем, является ли текущий пользователь родителем этого ребенка
        // Для этого пробуем загрузить статистику ребенка (только родитель может)
        try {
            await apiRequest(`/reading/child/${childId}/full-stats/`, 'GET');
            isParent = true;
            console.log('Current user is parent of this child');
        } catch (e) {
            isParent = false;
            console.log('Current user is NOT parent');
        }
    } catch (e) {}

    try {
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
        document.getElementById('readingSpeed').textContent = `${stats.reading_speed_wpm || 0} слов/мин`;
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

        // Загружаем детальную статистику по страницам и тестам
        await loadPageStats();
        
        // ========== ПОКАЗЫВАЕМ КНОПКУ УДАЛЕНИЯ ТОЛЬКО ДЛЯ РОДИТЕЛЯ ==========
        const deleteBtn = document.getElementById('deleteBookBtn');
        if (deleteBtn && isParent) {
            deleteBtn.style.display = 'block';
            deleteBtn.onclick = () => showDeleteModal();
            console.log('Delete button shown for parent');
        } else if (deleteBtn) {
            deleteBtn.style.display = 'none';
        }

    } catch (error) {
        console.error('Error loading child book stats:', error);
        showErrorMessage();
    }
}

async function loadPageStats() {
    try {
        const data = await apiRequest(`/reading/child/${childId}/book/${bookId}/page-stats/`, 'GET');
        console.log('Page stats:', data);
        
        // Отображаем тесты
        if (data.tests_stats && data.tests_stats.length > 0) {
            document.getElementById('testsListCard').style.display = 'block';
            renderTestsList(data.tests_stats);
        }
        
        // Отображаем страницы
        renderPagesTable(data.pages_stats || []);
        
    } catch (error) {
        console.error('Error loading page stats:', error);
        const tbody = document.getElementById('pagesTableBody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Ошибка загрузки статистики страниц</td></tr>';
    }
}

function renderTestsList(tests) {
    const container = document.getElementById('testsList');
    if (!container) return;
    
    if (tests.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет пройденных тестов</div>';
        return;
    }
    
    container.innerHTML = tests.map(test => `
        <div class="test-item">
            <div>
                <div class="test-pages">📖 Страницы ${test.start_page}-${test.end_page}</div>
                <div class="test-date">${test.completed_at}</div>
            </div>
            <div class="test-score ${test.passed ? 'test-passed' : 'test-failed'}">
                ${test.score_percent}% (${test.correct_answers}/${test.total_questions})
            </div>
        </div>
    `).join('');
}

function renderPagesTable(pages) {
    const tbody = document.getElementById('pagesTableBody');
    if (!tbody) return;
    
    if (!pages || pages.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Нет данных о прочитанных страницах</td></tr>';
        return;
    }
    
    tbody.innerHTML = pages.map(page => `
        <tr>
            <td><strong>${page.page_number}</strong></td>
            <td>${page.time_spent_seconds} сек</td>
            <td>${page.words_count}</td>
            <td>${page.reading_speed} слов/мин</td>
            <td>${page.completed_at}</td>
        </tr>
    `).join('');
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
    
    const tbody = document.getElementById('pagesTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Ошибка загрузки</td></tr>';
}

// ==================== УДАЛЕНИЕ КНИГИ ====================

function showDeleteModal() {
    console.log('showDeleteModal called');
    const modal = document.getElementById('deleteModal');
    if (modal) modal.classList.add('active');
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) modal.classList.remove('active');
}

async function confirmDelete() {
    if (!bookId) {
        console.error('No bookId for deletion');
        return;
    }

    console.log('Deleting book:', bookId);
    const token = getToken();

    try {
        const response = await fetch(`${API_URL}/books/books/${bookId}/delete/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        console.log('Delete response:', result);

        if (response.ok) {
            alert(`Книга "${currentBookName}" успешно удалена`);
            window.location.href = `/child-stats.html?id=${childId}`;
        } else {
            alert(result.error || 'Ошибка при удалении книги');
        }
    } catch (error) {
        console.error('Error deleting book:', error);
        alert('Ошибка при удалении книги: ' + error.message);
    } finally {
        closeDeleteModal();
    }
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

document.addEventListener('DOMContentLoaded', () => {
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    loadChildBookStats();
});