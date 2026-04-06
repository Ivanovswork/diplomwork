console.log('=== reading.js loaded ===');

let bookId = null;
let bookName = null;
let sessionId = null;
let currentPage = 1;
let totalPages = 1;
let startTime = null;
let timerInterval = null;
let isPageLoaded = false;
let isWaitingForTest = false;
let isInReviewMode = false;
let pendingTestId = null;
let blockStartPage = 1;
let blockEndPage = 2;
let isReadingFinished = false;

// Проверяем URL параметры при загрузке
const urlParams = new URLSearchParams(window.location.search);
const reviewMode = urlParams.get('review') === 'true';
const reviewStartPage = parseInt(urlParams.get('startPage'));
const reviewEndPage = parseInt(urlParams.get('endPage'));
const oldTestId = urlParams.get('testId');

// ==================== ЗАГРУЗКА PDF ====================

async function loadPDFPage() {
    console.log('=== loadPDFPage START ===');
    console.log('Loading page:', currentPage);
    
    const viewer = document.getElementById('pdfViewer');
    let loadingOverlay = document.getElementById('loadingOverlay');
    
    if (!viewer) {
        console.error('pdfViewer element not found!');
        return;
    }
    
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loadingOverlay';
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<div class="spinner"></div><div>Загрузка страницы...</div>';
        viewer.appendChild(loadingOverlay);
    }
    
    loadingOverlay.style.display = 'flex';
    loadingOverlay.innerHTML = '<div class="spinner"></div><div>Загрузка страницы...</div>';
    isPageLoaded = false;

    try {
        const token = getToken();
        if (!token) throw new Error('Токен не найден');

        const pdfUrl = `${API_URL}/reading/pdf-proxy/${bookId}/?page=${currentPage}`;
        console.log('PDF URL:', pdfUrl);

        const response = await fetch(pdfUrl, {
            headers: { 'Authorization': `Token ${token}` }
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);

        viewer.innerHTML = '';
        
        const newLoadingOverlay = document.createElement('div');
        newLoadingOverlay.id = 'loadingOverlay';
        newLoadingOverlay.className = 'loading-overlay';
        newLoadingOverlay.innerHTML = '<div class="spinner"></div><div>Загрузка страницы...</div>';
        viewer.appendChild(newLoadingOverlay);
        
        loadingOverlay = newLoadingOverlay;

        const embed = document.createElement('embed');
        embed.src = blobUrl;
        embed.type = 'application/pdf';
        embed.style.width = '100%';
        embed.style.height = '100%';
        
        embed.setAttribute('toolbar', '0');
        embed.setAttribute('navpanes', '0');
        embed.setAttribute('scrollbar', '0');
        embed.setAttribute('statusbar', '0');
        embed.setAttribute('view', 'FitH');
        embed.setAttribute('zoom', '100%');

        embed.onload = () => {
            console.log('PDF embed loaded');
            if (loadingOverlay) loadingOverlay.style.display = 'none';
            isPageLoaded = true;
            if (!isInReviewMode && !isWaitingForTest) startTimer();
        };

        embed.onerror = (err) => {
            console.error('Embed error:', err);
            if (loadingOverlay) loadingOverlay.innerHTML = '<div>Ошибка отображения PDF</div>';
        };

        viewer.appendChild(embed);
    } catch (error) {
        console.error('loadPDFPage error:', error);
        if (loadingOverlay) {
            loadingOverlay.innerHTML = `<div>Ошибка: ${error.message}</div>`;
        }
    }
}

// ==================== СЕССИЯ ====================

async function getOrCreateSession() {
    console.log('--- getOrCreateSession ---');
    try {
        const data = await apiRequest(`/reading/session/${bookId}/`, 'GET');
        console.log('Session data:', data);

        sessionId = data.session_id;
        
        if (isInReviewMode && reviewStartPage && reviewEndPage) {
            currentPage = reviewStartPage;
            blockStartPage = reviewStartPage;
            blockEndPage = reviewEndPage;
            totalPages = data.total_pages;
            pendingTestId = oldTestId;
            console.log('Review mode - using pages:', { currentPage, blockStartPage, blockEndPage });
        } else {
            currentPage = data.current_page;
            totalPages = data.total_pages;
            blockStartPage = data.block_start_page || 1;
            blockEndPage = data.block_end_page || 2;
        }

        document.getElementById('pageInfo').textContent = `Страница ${currentPage} / ${totalPages}`;
        
        if (!isInReviewMode) {
            await checkTestForCurrentBlock();
        }
        
        await loadPDFPage();
    } catch (error) {
        console.error('Session error:', error);
        alert('Ошибка загрузки сессии: ' + (error.message || ''));
    }
}

async function checkTestForCurrentBlock() {
    console.log('--- checkTestForCurrentBlock ---');
    try {
        const check = await apiRequest(`/reading/test/check/${sessionId}/`, 'GET');
        console.log('Test check:', check);
        if (check.requires_test) {
            isWaitingForTest = true;
            pendingTestId = check.test_id;
            showTestDialog();
        }
    } catch (error) {
        console.error('Test check error:', error);
    }
}

function showTestDialog() {
    if (!pendingTestId) return;
    const confirmAction = confirm('Пройдите тест, чтобы продолжить чтение?');
    if (confirmAction) {
        window.location.href = `/test.html?testId=${pendingTestId}&bookId=${bookId}&bookName=${encodeURIComponent(bookName)}&sessionId=${sessionId}&startPage=${blockStartPage}&endPage=${blockEndPage}`;
    } else {
        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) nextBtn.disabled = true;
        isWaitingForTest = true;
    }
}

// ==================== ТАЙМЕР ====================

function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    startTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const timerEl = document.getElementById('timer');
        if (timerEl) {
            timerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

// ==================== СОХРАНЕНИЕ ====================

async function saveCurrentPage() {
    console.log('=== saveCurrentPage START ===');
    
    if (isInReviewMode) {
        console.log('Review mode - skipping save');
        return;
    }
    
    if (!isPageLoaded) {
        alert('Подождите, страница загружается');
        return;
    }

    if (currentPage >= totalPages) {
        finishReading();
        return;
    }

    stopTimer();
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    if (!isInReviewMode && timeSpent < 5) {
        alert('Прочитайте страницу хотя бы 5 секунд');
        startTimer();
        return;
    }

    const wordsCount = 250 + Math.floor(Math.random() * 200);
    const request = {
        session_id: sessionId,
        page_number: currentPage,
        time_spent: timeSpent,
        words_count: wordsCount
    };
    
    console.log('Save request body:', request);

    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) {
        nextBtn.disabled = true;
        nextBtn.textContent = 'Сохранение...';
    }

    try {
        const result = await apiRequest('/reading/page/save/', 'POST', request);
        console.log('Save result:', result);
        
        if (result.success === true) {
            currentPage++;
            const pageInfoEl = document.getElementById('pageInfo');
            if (pageInfoEl) {
                pageInfoEl.textContent = `Страница ${currentPage} / ${totalPages}`;
            }

            if (result.test_created && result.test_id) {
                console.log('Test created! test_id:', result.test_id);
                isWaitingForTest = true;
                pendingTestId = result.test_id;
                showTestDialog();
                if (nextBtn) {
                    nextBtn.disabled = false;
                    nextBtn.textContent = 'Далее';
                }
                return;
            }

            if (currentPage > blockEndPage) {
                blockStartPage = ((currentPage - 1) / 2) * 2 + 1;
                blockEndPage = Math.min(blockStartPage + 1, totalPages);
                console.log('New block:', blockStartPage, '-', blockEndPage);
            }

            await loadPDFPage();
        } else {
            alert(result.error || 'Ошибка сохранения страницы');
            startTimer();
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('Ошибка сохранения: ' + (error.message || 'Неизвестная ошибка'));
        startTimer();
    } finally {
        if (nextBtn) {
            nextBtn.disabled = false;
            nextBtn.textContent = 'Далее';
        }
    }
}

// ==================== КНОПКА ДАЛЕЕ ====================

async function onNextPageClick() {
    console.log('onNextPageClick - isInReviewMode:', isInReviewMode, 'isWaitingForTest:', isWaitingForTest);

    if (isInReviewMode) {
        if (currentPage < blockEndPage) {
            currentPage++;
            const pageInfoEl = document.getElementById('pageInfo');
            if (pageInfoEl) {
                pageInfoEl.textContent = `Страница ${currentPage} / ${totalPages}`;
            }
            await loadPDFPage();
        } else {
            await createNewTestAfterReview();
        }
        return;
    }

    if (isWaitingForTest) {
        alert('Сначала пройдите тест!');
        return;
    }

    await saveCurrentPage();
}

async function createNewTestAfterReview() {
    console.log('--- createNewTestAfterReview ---');
    
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) {
        nextBtn.disabled = true;
        nextBtn.textContent = 'Создание теста...';
    }

    try {
        let result;
        if (pendingTestId) {
            result = await apiRequest(`/reading/test/${pendingTestId}/retake/`, 'POST', {});
        } else {
            result = { test_id: null };
        }
        
        console.log('Retake result:', result);
        
        if (result.test_id) {
            pendingTestId = result.test_id;
            isWaitingForTest = true;
            isInReviewMode = false;
            setTimeout(() => {
                window.location.href = `/test.html?testId=${pendingTestId}&bookId=${bookId}&bookName=${encodeURIComponent(bookName)}&sessionId=${sessionId}&startPage=${blockStartPage}&endPage=${blockEndPage}`;
            }, 300);
        } else {
            alert('Ошибка создания теста');
            isInReviewMode = false;
            window.location.reload();
        }
    } catch (error) {
        console.error('Create test error:', error);
        alert('Ошибка создания теста');
        isInReviewMode = false;
        window.location.reload();
    } finally {
        if (nextBtn) {
            nextBtn.disabled = false;
            nextBtn.textContent = 'Далее';
        }
    }
}

// ==================== ЗАВЕРШЕНИЕ СЕССИИ ====================

async function finishSession() {
    if (isReadingFinished) return;
    isReadingFinished = true;
    
    try {
        await apiRequest(`/reading/session/${sessionId}/finish/`, 'POST', {});
        console.log('Session finished successfully');
        return true;
    } catch (error) {
        console.error('Error finishing session:', error);
        return false;
    }
}

async function goBackToBookStats() {
    console.log('=== goBackToBookStats ===');
    stopTimer();
    
    if (confirm('Выйти из чтения? Прогресс будет сохранен.')) {
        await finishSession();
        window.location.href = `/book-stats.html?id=${bookId}`;
    }
}

async function finishReading() {
    console.log('=== finishReading ===');
    stopTimer();
    
    if (confirm('Завершить чтение книги?')) {
        await finishSession();
        window.location.href = `/book-stats.html?id=${bookId}`;
    }
}

function closeReading() {
    goBackToBookStats();
}

// Обработчик закрытия вкладки/браузера
window.addEventListener('beforeunload', () => {
    if (sessionId && !isReadingFinished) {
        // Используем sendBeacon для асинхронного запроса, который выполнится даже при закрытии
        const url = `${API_URL}/reading/session/${sessionId}/finish/`;
        const token = getToken();
        navigator.sendBeacon(url, JSON.stringify({}));
    }
});

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

async function initReading() {
    console.log('=== INIT READING START ===');
    bookId = urlParams.get('id');
    bookName = urlParams.get('name') || 'Книга';
    
    if (reviewMode && reviewStartPage && reviewEndPage) {
        isInReviewMode = true;
        isWaitingForTest = false;
        console.log('Review mode enabled - pages:', reviewStartPage, '-', reviewEndPage);
    }

    if (!bookId) {
        alert('ID книги не указан');
        window.location.href = '/';
        return;
    }

    const titleEl = document.getElementById('bookTitle');
    if (titleEl) titleEl.textContent = bookName;
    
    await getOrCreateSession();
    
    const nextBtn = document.getElementById('nextBtn');
    if (nextBtn) nextBtn.addEventListener('click', onNextPageClick);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded in reading.js');
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    initReading();
});