// public/js/test.js
let testId = null;
let bookId = null;
let bookName = null;
let startPage = null;
let endPage = null;
let sessionId = null;
let questions = [];
let selectedAnswers = {};

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function initTest() {
    const urlParams = new URLSearchParams(window.location.search);
    testId = urlParams.get('testId');
    bookId = urlParams.get('bookId');
    bookName = urlParams.get('bookName');
    startPage = urlParams.get('startPage');
    endPage = urlParams.get('endPage');
    sessionId = urlParams.get('sessionId');

    console.log('Test init:', { testId, bookId, bookName, startPage, endPage, sessionId });

    if (!testId) {
        alert('Тест не найден');
        window.location.href = '/';
        return;
    }

    document.getElementById('testInfo').textContent = `Книга: ${bookName || ''} | Страницы ${startPage}-${endPage}`;

    await loadTest();
}

async function loadTest() {
    try {
        const data = await apiRequest(`/reading/test/${testId}/`, 'GET');
        console.log('Test data:', data);
        questions = data.questions;
        renderQuestions();
    } catch (error) {
        console.error('Error loading test:', error);
        alert('Ошибка загрузки теста');
    }
}

function renderQuestions() {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';

    questions.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'question-card';
        card.innerHTML = `
            <div class="question-text">${idx + 1}. ${escapeHtml(q.text)}</div>
            <div class="answers">
                ${q.answers.map((a, aIdx) => `
                    <label class="answer-option">
                        <input type="radio" name="q_${q.id}" value="${a.id}">
                        ${escapeHtml(a.text)}
                    </label>
                `).join('')}
            </div>
        `;
        container.appendChild(card);
    });

    document.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const name = e.target.name;
            const qId = parseInt(name.split('_')[1]);
            selectedAnswers[qId] = parseInt(e.target.value);
            console.log('Selected answers:', selectedAnswers);
        });
    });
}

async function submitTest() {
    if (Object.keys(selectedAnswers).length !== questions.length) {
        alert('Ответьте на все вопросы');
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Отправка...';

    try {
        const result = await apiRequest(`/reading/test/${testId}/submit/`, 'POST', { answers: selectedAnswers });
        console.log('Submit result:', result);
        
        const resultDiv = document.getElementById('resultMessage');
        resultDiv.style.display = 'block';
        resultDiv.textContent = result.message;
        resultDiv.className = `result-message ${result.passed ? 'result-passed' : 'result-failed'}`;

        if (result.passed) {
            submitBtn.style.display = 'none';
            setTimeout(() => {
                window.location.href = `/reading.html?id=${bookId}&name=${encodeURIComponent(bookName)}`;
            }, 2000);
        } else {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Отправить ответы';
            document.getElementById('retakeBtn').style.display = 'block';
            document.getElementById('retakeBtn').onclick = () => {
                // Переход в режим перечитывания с теми же страницами
                window.location.href = `/reading.html?id=${bookId}&name=${encodeURIComponent(bookName)}&review=true&startPage=${startPage}&endPage=${endPage}&testId=${testId}`;
            };
        }
    } catch (error) {
        console.error('Error submitting test:', error);
        alert('Ошибка отправки');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Отправить ответы';
    }
}

document.getElementById('submitBtn').addEventListener('click', submitTest);

document.addEventListener('DOMContentLoaded', () => {
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    initTest();
});