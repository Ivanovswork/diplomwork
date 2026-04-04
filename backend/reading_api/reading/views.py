import io
from datetime import timedelta, date
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.db.models import Sum
from gigachat import GigaChat
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from PyPDF2 import PdfReader, PdfWriter
import fitz
from datetime import date, datetime

from books.models import Book, UserConnection
from transformers import AutoTokenizer, AutoModelForCausalLM

from .models import ReadingSession, PageReadingLog, UserReadingStreak, Test, Question, Answer, UserTestResult
from users.models import User


# ==================== МОДЕЛЬ ДЛЯ ГЕНЕРАЦИИ ВОПРОСОВ ====================
# def generate_questions_gigachat(content, num_questions=3):
#     """Генерация вопросов через GigaChat API"""
#     print(f"DEBUG: Генерация {num_questions} вопросов через GigaChat")
#     print(f"DEBUG: Длина текста: {len(content)} символов")
#
#     truncated_content = content[:2000]
#
#     prompt = f"""Ты --- эксперт по созданию тестов. На основе текста создай {num_questions} вопросов.
#
# Текст:
# {truncated_content}
#
# ПРАВИЛА:
# 1. Вопросы должны быть ТОЛЬКО на русском языке
# 2. Каждый вопрос должен иметь ровно 3 варианта ответа
# 3. Только один вариант ответа правильный
# 4. Используй ТОЛЬКО факты из текста
# 5. ОТВЕТЬ ТОЛЬКО В ФОРМАТЕ JSON. НИКАКОГО ДРУГОГО ТЕКСТА.
#
# Формат должен быть строго таким:
# {{
#     "questions": [
#         {{
#             "question": "текст вопроса",
#             "answers": [
#                 {{"text": "вариант 1", "is_correct": false}},
#                 {{"text": "вариант 2", "is_correct": true}},
#                 {{"text": "вариант 3", "is_correct": false}}
#             ]
#         }}
#     ]
# }}
#
# JSON:"""
#
#     try:
#         from gigachat import GigaChat
#
#         with GigaChat(
#                 credentials=settings.GIGACHAT_API_KEY,
#                 verify_ssl_certs=False,
#                 timeout=60
#         ) as giga:
#             response = giga.chat(prompt)
#             generated_text = response.choices[0].message.content
#             print(f"DEBUG: Получен ответ длиной {len(generated_text)} символов")
#             print(f"DEBUG: Ответ (первые 500 символов):\n{generated_text[:500]}")
#
#             questions = extract_json_questions(generated_text, num_questions)
#             if questions:
#                 print(f"DEBUG: Успешно получено {len(questions)} вопросов")
#                 return questions
#             else:
#                 print("DEBUG: Не удалось извлечь вопросы из ответа")
#                 return None
#
#     except Exception as e:
#         print(f"DEBUG: Ошибка GigaChat: {e}")
#         import traceback
#         traceback.print_exc()
#         return None

def generate_questions_gigachat(content, num_questions=3):
    """Генерация вопросов через GigaChat API"""
    print(f"DEBUG: Генерация {num_questions} вопросов через GigaChat")
    print(f"DEBUG: Длина текста: {len(content)} символов")

    truncated_content = content[:2000]

    prompt = f"""Ты — эксперт по созданию тестов. На основе текста создай ровно 3 вопроса.

Текст:
{truncated_content}

ПРАВИЛА:
1. Вопросы только на русском языке
2. У каждого вопроса ровно 3 варианта ответа
3. Только один вариант ответа правильный
4. Используй ТОЛЬКО факты из текста
5. ОТВЕТЬ ТОЛЬКО В ФОРМАТЕ JSON

Формат:
{{
    "questions": [
        {{
            "question": "текст вопроса 1",
            "answers": [
                {{"text": "вариант 1", "is_correct": false}},
                {{"text": "вариант 2", "is_correct": true}},
                {{"text": "вариант 3", "is_correct": false}}
            ]
        }},
        {{
            "question": "текст вопроса 2",
            "answers": [
                {{"text": "вариант 1", "is_correct": false}},
                {{"text": "вариант 2", "is_correct": true}},
                {{"text": "вариант 3", "is_correct": false}}
            ]
        }},
        {{
            "question": "текст вопроса 3",
            "answers": [
                {{"text": "вариант 1", "is_correct": false}},
                {{"text": "вариант 2", "is_correct": true}},
                {{"text": "вариант 3", "is_correct": false}}
            ]
        }}
    ]
}}

JSON:"""

    try:
        from gigachat import GigaChat

        with GigaChat(
                credentials=settings.GIGACHAT_API_KEY,
                verify_ssl_certs=False,
                timeout=90
        ) as giga:
            response = giga.chat(prompt)
            generated_text = response.choices[0].message.content
            print(f"DEBUG: Получен ответ длиной {len(generated_text)} символов")
            print(f"DEBUG: Ответ:\n{generated_text}")

            questions = extract_json_questions(generated_text)
            if questions and len(questions) == 3:
                print(f"DEBUG: Успешно получено 3 вопроса")
                return questions
            else:
                print(f"DEBUG: Получено {len(questions) if questions else 0} вопросов, ожидалось 3")
                return None

    except Exception as e:
        print(f"DEBUG: Ошибка GigaChat: {e}")
        return None

import json
import re

import json
import re


def extract_json_questions(text):
    """Надежный парсер JSON с вопросами"""
    text = text.strip()

    # 1. Пробуем найти полный JSON объект
    start = text.find('{')
    if start == -1:
        return None

    brace_count = 0
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start:i + 1]
                try:
                    data = json.loads(json_str)
                    if 'questions' in data and isinstance(data['questions'], list):
                        questions = data['questions']
                        if len(questions) == 3:
                            return questions
                except json.JSONDecodeError:
                    continue
                break

    # 2. Если не нашли, ищем отдельные объекты вопросов
    question_pattern = r'{[^{}]*"question"[^{}]*"answers"[^{}]*\[[^\]]*\][^{}]*}'
    matches = re.findall(question_pattern, text, re.DOTALL)

    if len(matches) >= 3:
        valid_questions = []
        for match in matches[:3]:
            try:
                # Исправляем возможные ошибки в JSON
                fixed_match = match
                # Добавляем недостающие кавычки
                fixed_match = re.sub(r'([{,])\s*([a-zA-Zа-яА-Я_]+)\s*:', r'\1"\2":', fixed_match)
                # Удаляем trailing commas
                fixed_match = re.sub(r',\s*}', '}', fixed_match)
                fixed_match = re.sub(r',\s*]', ']', fixed_match)

                q = json.loads(fixed_match)
                if 'question' in q and 'answers' in q:
                    if isinstance(q['answers'], list) and len(q['answers']) >= 3:
                        # Нормализуем ответы
                        for a in q['answers']:
                            if 'is_correct' not in a:
                                a['is_correct'] = False
                        # Убеждаемся, что есть правильный ответ
                        has_correct = any(a.get('is_correct', False) for a in q['answers'])
                        if not has_correct and len(q['answers']) > 0:
                            q['answers'][0]['is_correct'] = True
                        valid_questions.append(q)
            except json.JSONDecodeError:
                continue

        if len(valid_questions) == 3:
            return valid_questions

    # 3. Пробуем найти массив вопросов
    array_pattern = r'\[\s*\{[\s\S]*?\}\s*\]'
    match = re.search(array_pattern, text)
    if match:
        try:
            questions = json.loads(match.group())
            if isinstance(questions, list) and len(questions) >= 3:
                valid_questions = []
                for q in questions[:3]:
                    if 'question' in q and 'answers' in q:
                        for a in q['answers']:
                            if 'is_correct' not in a:
                                a['is_correct'] = False
                        has_correct = any(a.get('is_correct', False) for a in q['answers'])
                        if not has_correct and len(q['answers']) > 0:
                            q['answers'][0]['is_correct'] = True
                        valid_questions.append(q)
                if len(valid_questions) == 3:
                    return valid_questions
        except json.JSONDecodeError:
            pass

    # 4. Пробуем извлечь по одному вопросу из текста
    # Ищем все вхождения "question"
    question_matches = []
    for i in range(3):
        q_pattern = r'"question"\s*:\s*"([^"]+)"'
        q_matches = re.findall(q_pattern, text)
        if len(q_matches) >= i + 1:
            # Нашли вопрос, ищем к нему ответы
            q_text = q_matches[i]

            # Ищем answers
            a_pattern = r'"answers"\s*:\s*\[\s*\{[^}]*\}(?:\s*,\s*\{[^}]*\}){2}\s*\]'
            a_match = re.search(a_pattern, text)
            if a_match:
                answers_str = a_match.group()
                try:
                    answers = json.loads(answers_str.split(':', 1)[1].strip())
                    if isinstance(answers, list) and len(answers) >= 3:
                        for a in answers:
                            if 'is_correct' not in a:
                                a['is_correct'] = False
                        has_correct = any(a.get('is_correct', False) for a in answers)
                        if not has_correct:
                            answers[0]['is_correct'] = True
                        question_matches.append({
                            'question': q_text,
                            'answers': answers[:3]
                        })
                except json.JSONDecodeError:
                    pass

    if len(question_matches) == 3:
        return question_matches

    return None


def create_test_for_session(session, start_page, end_page):
    """Создать тест для сессии на основе прочитанных страниц"""
    try:
        print(f"DEBUG: Создаем тест для страниц {start_page}-{end_page}")

        # Получаем текст страниц
        content = ""
        doc = fitz.open(stream=session.book.content, filetype="pdf")
        for page_num in range(start_page - 1, end_page):
            if page_num < len(doc):
                content += doc[page_num].get_text()
        doc.close()
        print(f"DEBUG: Получен текст из {end_page - start_page + 1} страниц, длина={len(content)}")

        # Генерируем вопросы через GigaChat
        questions_data = generate_questions_gigachat(content, num_questions=3)

        if not questions_data:
            print("DEBUG: Не удалось сгенерировать вопросы, тест НЕ создается")
            return None

        # Создаем тест
        test = Test.objects.create(
            session=session,
            start_page=start_page,
            end_page=end_page,
            total_questions=len(questions_data),
            status='pending'
        )
        print(f"DEBUG: Тест создан, ID={test.id}")

        # Создаем вопросы и ответы
        for idx, q_data in enumerate(questions_data):
            question = Question.objects.create(
                test=test,
                text=q_data['question']
            )
            print(f"DEBUG:   Вопрос {idx + 1}: {q_data['question'][:50]}...")

            for a_idx, a_data in enumerate(q_data['answers']):
                Answer.objects.create(
                    question=question,
                    text=a_data['text'],
                    is_correct=a_data['is_correct']
                )
                print(f"DEBUG:     Ответ {a_idx + 1}: {a_data['text'][:30]}... (correct={a_data['is_correct']})")

        print(f"DEBUG: Тест создан успешно, ID={test.id}, вопросов={test.total_questions}")
        return test

    except Exception as e:
        print(f"DEBUG: Ошибка создания теста: {e}")
        import traceback
        traceback.print_exc()
        return None

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def format_time(seconds):
    """Форматировать время в читаемый вид"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}ч {minutes}м"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    else:
        return f"{secs}с"


def update_streak(user, read_date, daily_goal):
    """Обновить стрик пользователя (только если выполнена дневная цель)"""
    streak, created = UserReadingStreak.objects.get_or_create(user=user)

    books = Book.objects.filter(user=user, status__in=['in_progress', 'completed'])
    total_pages_read_today = 0
    for book in books:
        total_pages_read_today += PageReadingLog.objects.filter(
            session__book=book,
            completed_at__date=read_date
        ).count()

    if total_pages_read_today < daily_goal:
        return

    if not streak.last_read_date:
        streak.current_streak = 1
        streak.longest_streak = 1
    elif read_date == streak.last_read_date + timedelta(days=1):
        streak.current_streak += 1
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
    elif read_date > streak.last_read_date + timedelta(days=1):
        streak.current_streak = 1
    else:
        return

    streak.last_read_date = read_date
    streak.save()


# ==================== API VIEWS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_stats(request, book_id):
    """Получить статистику книги"""
    try:
        book = Book.objects.get(id=book_id, user=request.user, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    sessions = ReadingSession.objects.filter(book=book, status='completed')
    total_pages_read = sessions.aggregate(total=models.Sum('pages_read'))['total'] or 0
    page_logs = PageReadingLog.objects.filter(session__book=book, session__status='completed')
    total_time = page_logs.aggregate(total=models.Sum('time_spent'))['total'] or timedelta(0)
    total_seconds = total_time.total_seconds()
    avg_time_per_page = total_seconds / total_pages_read if total_pages_read > 0 else 0
    total_words = page_logs.aggregate(total=models.Sum('words_count'))['total'] or 0
    reading_speed = (total_words / (total_seconds / 60)) if total_seconds > 0 else 0
    total_sessions = sessions.count()
    active_session = ReadingSession.objects.filter(book=book, status='active').first()

    return Response({
        'book_id': book.id,
        'book_name': book.name,
        'total_pages': book.pages_count,
        'pages_read': total_pages_read,
        'progress_percent': round((total_pages_read / book.pages_count * 100), 1) if book.pages_count > 0 else 0,
        'total_time_seconds': total_seconds,
        'total_time_formatted': format_time(total_seconds),
        'avg_time_per_page_seconds': round(avg_time_per_page, 1),
        'total_words': total_words,
        'reading_speed_wpm': round(reading_speed, 0),
        'total_sessions': total_sessions,
        'has_active_session': active_session is not None,
        'active_session_id': active_session.id if active_session else None,
        'last_page_read': active_session.end_page if active_session else total_pages_read
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_stats_with_daily_goal(request, book_id):
    try:
        book = Book.objects.get(id=book_id, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    is_owner = book.user == request.user
    is_parent = UserConnection.objects.filter(
        user1=request.user,
        user2=book.user,
        connection_type='parent_child',
        is_parent_flag=True,
        is_child_flag=True
    ).exists()

    if not is_owner and not is_parent:
        return Response({"error": "Нет доступа к этой книге"}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.now().date()
    all_page_logs = PageReadingLog.objects.filter(session__book=book)

    total_pages_read = all_page_logs.count()
    pages_read_today = all_page_logs.filter(completed_at__date=today).count()

    completed_logs = all_page_logs.filter(session__status='completed')
    total_time = completed_logs.aggregate(total=Sum('time_spent'))['total'] or timedelta(0)
    total_seconds = total_time.total_seconds()

    avg_time_per_page = total_seconds / total_pages_read if total_pages_read > 0 else 0
    total_words = all_page_logs.aggregate(total=Sum('words_count'))['total'] or 0
    reading_speed = (total_words / (total_seconds / 60)) if total_seconds > 0 else 0
    total_sessions = ReadingSession.objects.filter(book=book).count()
    active_session = ReadingSession.objects.filter(book=book, status='active').first()

    daily_goal = book.daily_goal
    daily_goal_achieved = pages_read_today >= daily_goal
    daily_goal_percent = min(100, int((pages_read_today / daily_goal) * 100)) if daily_goal > 0 else 0
    daily_goal_remaining = max(0, daily_goal - pages_read_today)

    last_page_log = all_page_logs.order_by('-completed_at').first()
    last_page_read = last_page_log.page_number if last_page_log else 0
    progress_percent = round((total_pages_read / book.pages_count * 100), 1) if book.pages_count > 0 else 0

    return Response({
        'book_id': book.id,
        'book_name': book.name,
        'total_pages': book.pages_count,
        'pages_read': total_pages_read,
        'progress_percent': progress_percent,
        'total_time_seconds': total_seconds,
        'total_time_formatted': format_time(total_seconds),
        'avg_time_per_page_seconds': round(avg_time_per_page, 1),
        'total_words': total_words,
        'reading_speed_wpm': round(reading_speed, 0),
        'total_sessions': total_sessions,
        'has_active_session': active_session is not None,
        'active_session_id': active_session.id if active_session else None,
        'last_page_read': last_page_read,
        'daily_goal': daily_goal,
        'pages_read_today': pages_read_today,
        'daily_goal_achieved': daily_goal_achieved,
        'daily_goal_percent': daily_goal_percent,
        'daily_goal_remaining': daily_goal_remaining
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_or_create_session(request, book_id):
    """Получить активную сессию или создать новую"""

    try:
        book = Book.objects.get(id=book_id, user=request.user, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    active_session = ReadingSession.objects.filter(book=book, status='active').first()

    if active_session:
        inactive_time = timezone.now() - active_session.last_activity
        if inactive_time > timedelta(hours=4):
            active_session.status = 'abandoned'
            active_session.save()
            active_session = None

    if not active_session:
        last_session = ReadingSession.objects.filter(
            book=book, status='completed'
        ).order_by('-end_datetime').first()

        if last_session:
            start_page = last_session.end_page + 1
        else:
            start_page = 1

        if start_page > book.pages_count:
            # Книга полностью прочитана
            return Response({
                'session_id': None,
                'start_page': book.pages_count,
                'current_page': book.pages_count,
                'total_pages': book.pages_count,
                'is_book_finished': True,
                'message': 'Книга уже прочитана полностью'
            })

        active_session = ReadingSession.objects.create(
            book=book,
            start_page=start_page,
            end_page=start_page - 1,
            status='active'
        )

    current_page = active_session.end_page + 1 if active_session.end_page else active_session.start_page

    # Проверяем, не закончена ли книга
    if current_page > book.pages_count:
        active_session.status = 'completed'
        active_session.end_datetime = timezone.now()
        active_session.save()
        book.status = 'completed'
        book.save(update_fields=['status'])

        return Response({
            'session_id': active_session.id,
            'start_page': active_session.start_page,
            'current_page': book.pages_count,
            'total_pages': book.pages_count,
            'is_book_finished': True,
            'message': 'Книга прочитана!'
        })

    # Определяем текущий блок (по 2 страницы)
    block_number = (current_page - 1) // 2 + 1
    block_start_page = (block_number - 1) * 2 + 1
    block_end_page = min(block_number * 2, book.pages_count)

    # Проверяем, есть ли тест для этого блока
    test = Test.objects.filter(
        session__book=book,
        start_page=block_start_page,
        end_page=block_end_page
    ).first()

    has_test = False
    test_status = None
    test_id = None

    if test:
        has_test = True
        test_id = test.id
        test_status = test.status

    return Response({
        'session_id': active_session.id,
        'start_page': active_session.start_page,
        'current_page': current_page,
        'total_pages': book.pages_count,
        'is_book_finished': False,
        'block_number': block_number,
        'block_start_page': block_start_page,
        'block_end_page': block_end_page,
        'has_test': has_test,
        'test_status': test_status,
        'test_id': test_id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_page_read(request):
    """Сохранить прочитанную страницу"""

    session_id = request.data.get('session_id')
    page_number = request.data.get('page_number')
    time_spent_seconds = request.data.get('time_spent', 30)
    words_count = request.data.get('words_count', 0)

    if not session_id or not page_number:
        return Response({"error": "Нужны session_id и page_number"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = ReadingSession.objects.get(id=session_id, status='active', book__user=request.user)
    except ReadingSession.DoesNotExist:
        return Response({"error": "Активная сессия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if PageReadingLog.objects.filter(session=session, page_number=page_number).exists():
        return Response({"error": "Страница уже сохранена"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        time_spent = timedelta(seconds=float(time_spent_seconds))
    except (TypeError, ValueError):
        return Response({"error": "Неверное значение time_spent"}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()
    today = now.date()
    book = session.book
    daily_goal = book.daily_goal

    is_book_uploaded_by_parent = book.uploaded_by is not None and book.uploaded_by != book.user
    is_child_reading = book.user == request.user

    # Создаем лог страницы
    page_log = PageReadingLog.objects.create(
        session=session,
        page_number=page_number,
        time_spent=time_spent,
        words_count=words_count,
        completed_at=now
    )

    # Обновляем сессию
    session.end_page = page_number
    session.pages_read += 1
    session.last_activity = now
    session.save()

    total_pages_read = PageReadingLog.objects.filter(session__book=book).count()
    pages_read_today = PageReadingLog.objects.filter(session__book=book, completed_at__date=today).count()
    daily_goal_completed = pages_read_today >= daily_goal

    is_book_finished = page_number >= book.pages_count

    if is_book_finished:
        session.status = 'completed'
        session.end_datetime = now
        session.save()
        book.status = 'completed'
        book.save(update_fields=['status'])

    if daily_goal_completed:
        update_streak(request.user, today, daily_goal)

    # ========== СОЗДАНИЕ ТЕСТА (каждые 2 страницы) ==========
    test_created = False
    test_id = None
    block_start_page = None
    block_end_page = None

    if is_book_uploaded_by_parent and is_child_reading:
        block_number = (page_number - 1) // 2 + 1
        test_start_page = (block_number - 1) * 2 + 1
        test_end_page = min(block_number * 2, book.pages_count)

        block_start_page = test_start_page
        block_end_page = test_end_page

        pages_in_block = PageReadingLog.objects.filter(
            session__book=book,
            page_number__gte=test_start_page,
            page_number__lte=test_end_page
        ).count()

        expected_pages = test_end_page - test_start_page + 1

        if pages_in_block >= expected_pages:
            existing_test = Test.objects.filter(
                session__book=book,
                start_page=test_start_page,
                end_page=test_end_page
            ).first()

            if not existing_test:
                test = create_test_for_session(session, test_start_page, test_end_page)
                if test:
                    test_created = True
                    test_id = test.id

    response_data = {
        'success': True,
        'page_saved': page_number,
        'is_book_finished': is_book_finished,
        'pages_read_in_session': session.pages_read,
        'total_pages': book.pages_count,
        'remaining_pages': book.pages_count - page_number,
        'daily_goal_completed': daily_goal_completed,
        'pages_read_today': pages_read_today,
        'daily_goal': daily_goal,
        'test_created': test_created,
        'test_id': test_id,
        'total_pages_read': total_pages_read,
        'block_end_page': block_end_page,
        'block_start_page': block_start_page
    }

    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def continue_reading(request, session_id):
    """Продолжить чтение после паузы"""
    try:
        old_session = ReadingSession.objects.get(id=session_id, book__user=request.user)
    except ReadingSession.DoesNotExist:
        return Response({"error": "Сессия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if old_session.status == 'active':
        old_session.status = 'completed'
        old_session.end_datetime = timezone.now()
        old_session.save()

    new_session = ReadingSession.objects.create(
        book=old_session.book,
        start_page=old_session.end_page + 1,
        end_page=old_session.end_page,
        status='active'
    )

    return Response({
        'session_id': new_session.id,
        'start_page': new_session.start_page,
        'total_pages': new_session.book.pages_count
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_reading(request, session_id):
    """Завершить чтение"""
    try:
        session = ReadingSession.objects.get(id=session_id, book__user=request.user, status='active')
    except ReadingSession.DoesNotExist:
        return Response({"error": "Активная сессия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    session.status = 'completed'
    session.end_datetime = timezone.now()
    session.save()

    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_book(request, book_id):
    """Принудительно завершить книгу (если все страницы прочитаны)"""
    try:
        book = Book.objects.get(id=book_id, user=request.user)
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    total_pages_read = PageReadingLog.objects.filter(session__book=book).count()

    if total_pages_read >= book.pages_count:
        book.status = 'completed'
        book.save()

        ReadingSession.objects.filter(book=book, status='active').update(
            status='completed',
            end_datetime=timezone.now()
        )

        return Response({
            'success': True,
            'message': 'Книга отмечена как прочитанная'
        })
    else:
        return Response({
            'success': False,
            'message': f'Прочитано {total_pages_read} из {book.pages_count} страниц'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_streak(request):
    """Получить стрик пользователя"""
    streak, created = UserReadingStreak.objects.get_or_create(user=request.user)
    return Response({
        'current_streak': streak.current_streak,
        'longest_streak': streak.longest_streak,
        'last_read_date': streak.last_read_date
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reading_stats(request):
    """Получить общую статистику чтения пользователя"""
    sessions = ReadingSession.objects.filter(book__user=request.user, status='completed')
    page_logs = PageReadingLog.objects.filter(session__book__user=request.user, session__status='completed')

    total_pages = page_logs.count()
    total_time = page_logs.aggregate(total=models.Sum('time_spent'))['total'] or timedelta(0)
    total_seconds = total_time.total_seconds()
    total_words = page_logs.aggregate(total=models.Sum('words_count'))['total'] or 0
    reading_speed = (total_words / (total_seconds / 60)) if total_seconds > 0 else 0
    books_in_progress = Book.objects.filter(user=request.user, status='in_progress').count()
    books_completed = Book.objects.filter(user=request.user, status='completed').count()
    total_sessions = sessions.count()
    avg_session_duration = total_seconds / total_sessions if total_sessions > 0 else 0

    return Response({
        'total_pages': total_pages,
        'total_time_seconds': total_seconds,
        'total_time_formatted': format_time(total_seconds),
        'total_words': total_words,
        'reading_speed_wpm': round(reading_speed, 0),
        'books_in_progress': books_in_progress,
        'books_completed': books_completed,
        'total_sessions': total_sessions,
        'avg_session_duration_seconds': round(avg_session_duration, 0)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pdf_proxy(request, book_id):
    """Отдает одну страницу PDF"""
    try:
        page_num = int(request.GET.get('page', 1))
        book = Book.objects.get(id=book_id, user=request.user, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({"error": "Неверный номер страницы"}, status=status.HTTP_400_BAD_REQUEST)

    if not book.content:
        return Response({"error": "Контент книги отсутствует"}, status=status.HTTP_404_NOT_FOUND)

    if page_num < 1 or page_num > book.pages_count:
        return Response({"error": "Страница вне диапазона"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pdf_content = book.content
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)

        if page_num > len(reader.pages):
            return HttpResponse("Страница не найдена", status=404)

        writer = PdfWriter()
        writer.add_page(reader.pages[page_num - 1])

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=page_{page_num}.pdf'
        response['Access-Control-Allow-Origin'] = '*'
        writer.write(response)
        return response

    except Exception as e:
        return HttpResponse(f"Ошибка: {str(e)}", status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def read_book_web(request, book_id):
    """Отдать PDF для чтения в WebView"""
    try:
        book = Book.objects.get(id=book_id, user=request.user, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=404)

    if not book.content:
        return Response({"error": "Контент книги отсутствует"}, status=404)

    response = HttpResponse(book.content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{book.name}.pdf"'
    response['Content-Length'] = len(book.content)
    response['Access-Control-Allow-Origin'] = '*'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_test_required(request, session_id):
    """Проверить, требуется ли тест перед следующей страницей"""
    try:
        session = ReadingSession.objects.get(id=session_id, book__user=request.user)
    except ReadingSession.DoesNotExist:
        return Response({"error": "Сессия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    book = session.book

    is_child_reading = book.user == request.user
    is_book_uploaded_by_parent = book.uploaded_by is not None and book.uploaded_by != book.user

    if not is_book_uploaded_by_parent or is_child_reading:
        return Response({'requires_test': False})

    # Определяем текущий блок на основе последней сохраненной страницы
    last_page = session.end_page if session.end_page else session.start_page
    block_number = (last_page - 1) // 2 + 1
    test_start_page = (block_number - 1) * 2 + 1
    test_end_page = min(block_number * 2, book.pages_count)

    test = Test.objects.filter(
        session__book=book,
        start_page=test_start_page,
        end_page=test_end_page
    ).first()

    if test:
        if test.status == 'pending':
            return Response({
                'requires_test': True,
                'test_id': test.id,
                'message': 'Пройдите тест перед продолжением чтения',
                'start_page': test_start_page,
                'end_page': test_end_page,
                'retake': False
            })
        elif test.status == 'failed':
            return Response({
                'requires_test': True,
                'test_id': test.id,
                'message': 'Тест не пройден. Перечитайте страницы и пройдите тест заново.',
                'start_page': test_start_page,
                'end_page': test_end_page,
                'retake': True
            })

    return Response({'requires_test': False})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_test(request, test_id):
    """Получить тест для прохождения"""
    try:
        test = Test.objects.get(id=test_id, session__book__user=request.user)
    except Test.DoesNotExist:
        return Response({"error": "Тест не найден"}, status=status.HTTP_404_NOT_FOUND)

    questions_data = []
    for question in test.questions.all():
        questions_data.append({
            'id': question.id,
            'text': question.text,
            'answers': [{'id': a.id, 'text': a.text} for a in question.answers.all()]
        })

    return Response({
        'test_id': test.id,
        'status': test.status,
        'start_page': test.start_page,
        'end_page': test.end_page,
        'questions': questions_data,
        'score': test.score,
        'total': test.total_questions
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_test(request, test_id):
    """Отправить ответы на тест"""
    answers = request.data.get('answers', {})

    try:
        test = Test.objects.get(id=test_id, session__book__user=request.user)
    except Test.DoesNotExist:
        return Response({"error": "Тест не найден"}, status=status.HTTP_404_NOT_FOUND)

    if test.status != 'pending':
        return Response({"error": "Тест уже пройден"}, status=status.HTTP_400_BAD_REQUEST)

    correct_count = 0
    for question in test.questions.all():
        user_answer_id = answers.get(str(question.id))
        if user_answer_id:
            try:
                answer = Answer.objects.get(id=user_answer_id, question=question)
                if answer.is_correct:
                    correct_count += 1
            except Answer.DoesNotExist:
                pass

    test.score = correct_count
    test.status = 'passed' if correct_count >= 2 else 'failed'
    test.completed_at = timezone.now()
    test.save()

    UserTestResult.objects.create(
        user=request.user,
        book=test.session.book,
        test=test,
        correct_answers=correct_count,
        total_questions=test.total_questions
    )

    return Response({
        'correct': correct_count,
        'total': test.total_questions,
        'passed': test.status == 'passed',
        'message': f'Правильных ответов: {correct_count} из {test.total_questions}'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retake_test(request, test_id):
    """Пересдать тест (создать новый с новыми вопросами)"""
    print("=" * 50)
    print("RETAKE TEST CALLED")
    print(f"test_id: {test_id}")

    try:
        old_test = Test.objects.get(id=test_id, session__book__user=request.user)
        print(f"Old test found: id={old_test.id}, pages={old_test.start_page}-{old_test.end_page}")
    except Test.DoesNotExist:
        print("ERROR: Test not found")
        return Response({"error": "Тест не найден"}, status=status.HTTP_404_NOT_FOUND)

    # Получаем текст страниц для этого блока
    content = ""
    doc = fitz.open(stream=old_test.session.book.content, filetype="pdf")
    for page_num in range(old_test.start_page - 1, old_test.end_page):
        if page_num < len(doc):
            content += doc[page_num].get_text()
    doc.close()

    print(f"Content length: {len(content)} characters")

    # Генерируем вопросы
    questions_data = generate_questions_gigachat(content, num_questions=3)

    if not questions_data:
        print("ERROR: Failed to generate questions")
        return Response({"error": "Ошибка генерации вопросов"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    print(f"Generated {len(questions_data)} questions")

    # Создаем новый тест
    new_test = Test.objects.create(
        session=old_test.session,
        start_page=old_test.start_page,
        end_page=old_test.end_page,
        total_questions=len(questions_data),
        status='pending'
    )

    print(f"New test created: id={new_test.id}")

    # Создаем вопросы и ответы
    for idx, q_data in enumerate(questions_data):
        question = Question.objects.create(
            test=new_test,
            text=q_data['question']
        )
        print(f"  Question {idx + 1}: {q_data['question'][:50]}...")

        for a_idx, a_data in enumerate(q_data['answers']):
            Answer.objects.create(
                question=question,
                text=a_data['text'],
                is_correct=a_data['is_correct']
            )
            print(f"    Answer {a_idx + 1}: {a_data['text'][:30]}... (correct={a_data['is_correct']})")

    print(f"Test {new_test.id} created successfully")
    print("=" * 50)

    # ВАЖНО: возвращаем объект с полем test_id
    return Response({
        'test_id': new_test.id,
        'message': 'Новый тест создан'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_test_stats(request, book_id):
    """Получить статистику тестов по книге (для родителя)"""
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    is_parent = UserConnection.objects.filter(
        user1=request.user,
        user2=book.user,
        connection_type='parent_child',
        is_parent_flag=True,
        is_child_flag=True
    ).exists()

    if book.user != request.user and not is_parent:
        return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

    if book.user == request.user:
        is_book_uploaded_by_parent = book.uploaded_by is not None and book.uploaded_by != book.user
        if not is_book_uploaded_by_parent:
            return Response({
                'total_tests': 0,
                'average_score': 0,
                'passed_tests': 0,
                'results': [],
                'message': 'Тесты доступны только для книг, загруженных родителем'
            })

    results = UserTestResult.objects.filter(user=book.user, book=book).order_by('-completed_at')

    total_tests = results.count()
    if total_tests == 0:
        return Response({
            'total_tests': 0,
            'average_score': 0,
            'passed_tests': 0,
            'results': []
        })

    total_score = sum(r.score_percent for r in results)
    passed_tests = results.filter(correct_answers__gte=2).count()

    results_data = []
    for r in results:
        results_data.append({
            'id': r.id,
            'test_id': r.test.id,
            'correct_answers': r.correct_answers,
            'total_questions': r.total_questions,
            'score_percent': r.score_percent,
            'completed_at': r.completed_at.isoformat(),
            'start_page': r.test.start_page,
            'end_page': r.test.end_page
        })

    return Response({
        'total_tests': total_tests,
        'average_score': round(total_score / total_tests, 1) if total_tests > 0 else 0,
        'passed_tests': passed_tests,
        'results': results_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_block_text(request, book_id, block_number):
    """Получить текст блока страниц для перечитывания"""
    try:
        book = Book.objects.get(id=book_id, user=request.user)
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    block_start_page = (block_number - 1) * 2 + 1
    block_end_page = min(block_number * 2, book.pages_count)

    content = ""
    doc = fitz.open(stream=book.content, filetype="pdf")
    for page_num in range(block_start_page - 1, block_end_page):
        if page_num < len(doc):
            content += doc[page_num].get_text()
    doc.close()

    return Response({
        'block_number': block_number,
        'start_page': block_start_page,
        'end_page': block_end_page,
        'content': content[:5000]  # Ограничиваем для чтения
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_child_full_stats(request, child_id):
    """Полная статистика ребенка для родителя"""
    try:
        child = User.objects.get(id=child_id)
    except User.DoesNotExist:
        return Response({"error": "Ребенок не найден"}, status=status.HTTP_404_NOT_FOUND)

    # Проверка: текущий пользователь - родитель ребенка
    is_parent = UserConnection.objects.filter(
        user1=request.user,
        user2=child,
        connection_type='parent_child',
        is_parent_flag=True,
        is_child_flag=True
    ).exists()

    if not is_parent:
        return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

    # Статистика по книгам
    books = Book.objects.filter(user=child, status__in=['in_progress', 'completed'])
    books_count = books.count()
    total_pages = books.aggregate(total=models.Sum('pages_count'))['total'] or 0

    # Статистика по тестам
    test_results = UserTestResult.objects.filter(user=child)
    total_tests = test_results.count()
    passed_tests = test_results.filter(correct_answers__gte=2).count()
    avg_score = test_results.aggregate(avg=models.Avg('correct_answers'))['avg'] or 0
    avg_percent = (avg_score / 3 * 100) if total_tests > 0 else 0

    # Статистика чтения
    page_logs = PageReadingLog.objects.filter(session__book__user=child, session__status='completed')
    total_time = page_logs.aggregate(total=models.Sum('time_spent'))['total'] or timedelta(0)
    total_seconds = total_time.total_seconds()
    total_words = page_logs.aggregate(total=models.Sum('words_count'))['total'] or 0
    reading_speed = (total_words / (total_seconds / 60)) if total_seconds > 0 else 0

    return Response({
        'child_id': child.id,
        'child_name': child.name,
        'child_email': child.email,
        'books_count': books_count,
        'total_pages': total_pages,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'avg_score_percent': round(avg_percent, 1),
        'total_reading_time_seconds': total_seconds,
        'total_reading_time_formatted': format_time(total_seconds),
        'total_words': total_words,
        'reading_speed_wpm': round(reading_speed, 0)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_child_book_stats(request, child_id, book_id):
    """Статистика конкретной книги ребенка для родителя"""
    try:
        book = Book.objects.get(id=book_id, user_id=child_id, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Проверка: текущий пользователь - родитель ребенка
    is_parent = UserConnection.objects.filter(
        user1=request.user,
        user2_id=child_id,
        connection_type='parent_child',
        is_parent_flag=True,
        is_child_flag=True
    ).exists()

    if not is_parent:
        return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

    # Статистика по книге
    all_page_logs = PageReadingLog.objects.filter(session__book=book)
    total_pages_read = all_page_logs.count()
    completed_logs = all_page_logs.filter(session__status='completed')
    total_time = completed_logs.aggregate(total=models.Sum('time_spent'))['total'] or timedelta(0)
    total_seconds = total_time.total_seconds()
    avg_time_per_page = total_seconds / total_pages_read if total_pages_read > 0 else 0
    total_words = all_page_logs.aggregate(total=models.Sum('words_count'))['total'] or 0
    reading_speed = (total_words / (total_seconds / 60)) if total_seconds > 0 else 0
    total_sessions = ReadingSession.objects.filter(book=book).count()

    # Статистика тестов по этой книге
    test_results = UserTestResult.objects.filter(user_id=child_id, book=book)
    total_tests = test_results.count()
    passed_tests = test_results.filter(correct_answers__gte=2).count()
    avg_score = test_results.aggregate(avg=models.Avg('correct_answers'))['avg'] or 0
    avg_percent = (avg_score / 3 * 100) if total_tests > 0 else 0

    # Результаты тестов детально
    results_data = []
    for r in test_results.order_by('-completed_at'):
        results_data.append({
            'test_id': r.test.id,
            'correct_answers': r.correct_answers,
            'total_questions': r.total_questions,
            'score_percent': r.score_percent,
            'completed_at': r.completed_at.isoformat(),
            'start_page': r.test.start_page,
            'end_page': r.test.end_page
        })

    return Response({
        'book_id': book.id,
        'book_name': book.name,
        'total_pages': book.pages_count,
        'pages_read': total_pages_read,
        'progress_percent': round((total_pages_read / book.pages_count * 100), 1) if book.pages_count > 0 else 0,
        'total_time_seconds': total_seconds,
        'total_time_formatted': format_time(total_seconds),
        'avg_time_per_page_seconds': round(avg_time_per_page, 1),
        'total_words': total_words,
        'reading_speed_wpm': round(reading_speed, 0),
        'total_sessions': total_sessions,
        'has_active_session': ReadingSession.objects.filter(book=book, status='active').exists(),
        'last_page_read': all_page_logs.order_by('-completed_at').first().page_number if all_page_logs.exists() else 0,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'avg_test_score_percent': round(avg_percent, 1),
        'test_results': results_data
    })