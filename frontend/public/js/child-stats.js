let childId = null;

async function loadChildStats() {
    const urlParams = new URLSearchParams(window.location.search);
    childId = urlParams.get('id');
    const childName = urlParams.get('name');

    if (!childId) {
        window.location.href = '/';
        return;
    }

    try {
        const user = await apiRequest('/users/me/', 'GET');
        document.getElementById('headerUserName').textContent = user.name || '';
    } catch (e) {}

    document.getElementById('childName').textContent = childName || 'Статистика ребенка';

    try {
        // Загружаем ПОЛНУЮ статистику ребенка
        const stats = await apiRequest(`/reading/child/${childId}/full-stats/`, 'GET');
        console.log('Child full stats:', stats);

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

        // Загружаем ВСЕ книги ребенка
        const books = await apiRequest(`/books/books/child/${childId}/`, 'GET');
        console.log('Child books:', books);

        renderChildBooks(books.child_books || []);

    } catch (error) {
        console.error('Error loading child stats:', error);
        document.getElementById('childBooksList').innerHTML = '<div class="empty-state">❌ Ошибка загрузки книг</div>';
    }
}

function renderChildBooks(books) {
    const container = document.getElementById('childBooksList');

    if (!books || books.length === 0) {
        container.innerHTML = '<div class="empty-state">📚 У ребенка пока нет книг</div>';
        return;
    }

    container.innerHTML = books.map(book => `
        <div class="child-book-item" onclick="window.location.href='/child-book-stats.html?childId=${childId}&bookId=${book.id}&bookName=${encodeURIComponent(book.name)}'">
            <div class="child-book-info">
                <div class="child-book-name">${escapeHtml(book.name)}</div>
                <div class="child-book-meta">
                    📄 ${book.pages_count} стр. • 🎯 цель: ${book.daily_goal} стр./день
                    ${book.status === 'completed' ? '<span style="color:#10b981; margin-left:8px;">✅ Завершена</span>' : '<span style="color:#3b82f6; margin-left:8px;">🟢 В процессе</span>'}
                </div>
            </div>
            <div class="child-book-arrow">→</div>
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