let childId = null;

function childBookStatus(book) {
    if (book.status === 'completed') {
        return '<span style="color:#10b981; margin-left:8px; font-weight:700;">Завершена</span>';
    }
    return '<span style="color:#2563eb; margin-left:8px; font-weight:700;">В процессе</span>';
}

async function loadChildStats() {
    const urlParams = new URLSearchParams(window.location.search);
    childId = urlParams.get('id');
    const childName = urlParams.get('name');

    if (!childId) {
        window.location.href = '/';
        return;
    }

    window.applyIconMarkup();

    try {
        const user = await apiRequest('/users/me/', 'GET');
        document.getElementById('headerUserName').textContent = user.name || '';
    } catch (e) {}

    document.getElementById('childName').textContent = childName || 'Статистика ребёнка';

    try {
        const stats = await apiRequest(`/reading/child/${childId}/full-stats/`, 'GET');
        if (stats) {
            document.getElementById('childBooksCount').textContent = stats.books_count || 0;
            document.getElementById('childPagesCount').textContent = stats.total_pages || 0;
            document.getElementById('childTotalTests').textContent = stats.total_tests || 0;
            document.getElementById('childPassedTests').textContent = `${stats.passed_tests || 0} / ${stats.total_tests || 0}`;
            document.getElementById('childAvgScore').textContent = `${stats.avg_score_percent || 0}%`;
            document.getElementById('childReadingTime').textContent = stats.total_reading_time_formatted || '0';
            document.getElementById('childReadingSpeed').textContent = `${stats.reading_speed_wpm || 0} слов/мин`;
            document.getElementById('childTotalWords').textContent = stats.total_words || 0;
        }

        const books = await apiRequest(`/books/books/child/${childId}/`, 'GET');
        renderChildBooks(books.child_books || []);
    } catch (error) {
        console.error('Error loading child stats:', error);
        document.getElementById('childBooksList').innerHTML = '<div class="empty-state">Ошибка загрузки книг</div>';
    }
}

function renderChildBooks(books) {
    const container = document.getElementById('childBooksList');

    if (!books || books.length === 0) {
        container.innerHTML = '<div class="empty-state">У ребёнка пока нет книг</div>';
        return;
    }

    container.innerHTML = books.map((book) => `
        <div class="child-book-item" onclick="window.location.href='/child-book-stats.html?childId=${childId}&bookId=${book.id}&bookName=${encodeURIComponent(book.name)}'">
            <div class="child-book-info">
                <div class="child-book-name">${escapeHtml(book.name)}</div>
                <div class="child-book-meta">
                    ${window.renderIcon('pages')} ${book.pages_count} стр. • ${window.renderIcon('target')} цель: ${book.daily_goal} стр./день
                    ${childBookStatus(book)}
                </div>
            </div>
            <div class="child-book-arrow">${window.renderIcon('chevronRight')}</div>
        </div>
    `).join('');
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
    loadChildStats();
});
