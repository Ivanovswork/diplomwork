from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta, date
from django.db import models
from django.db.models import Sum, Avg, Count
from books.models import Book
from .models import ReadingSession, PageReadingLog, UserReadingStreak
import fitz
from django.http import HttpResponse
from PyPDF2 import PdfWriter, PdfReader
import io


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_stats(request, book_id):
    """Получить статистику книги (общее время, страниц, скорость)"""
    try:
        book = Book.objects.get(id=book_id, user=request.user, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Все завершенные сессии по этой книге
    sessions = ReadingSession.objects.filter(book=book, status='completed')

    # Общее количество прочитанных страниц
    total_pages_read = sessions.aggregate(total=models.Sum('pages_read'))['total'] or 0

    # Все логи страниц
    page_logs = PageReadingLog.objects.filter(session__book=book, session__status='completed')

    # Общее время чтения
    total_time = page_logs.aggregate(total=models.Sum('time_spent'))['total'] or timedelta(0)
    total_seconds = total_time.total_seconds()

    # Среднее время на страницу
    avg_time_per_page = total_seconds / total_pages_read if total_pages_read > 0 else 0

    # Всего слов
    total_words = page_logs.aggregate(total=models.Sum('words_count'))['total'] or 0

    # Скорость чтения (слов в минуту)
    reading_speed = (total_words / (total_seconds / 60)) if total_seconds > 0 else 0

    # Сессий всего
    total_sessions = sessions.count()

    # Последняя активная сессия
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
def get_or_create_session(request, book_id):
    """Получить активную сессию или создать новую"""
    try:
        book = Book.objects.get(id=book_id, user=request.user, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Ищем активную сессию
    active_session = ReadingSession.objects.filter(book=book, status='active').first()

    if active_session:
        # Проверяем, не слишком ли долго не было активности (больше 4 часов)
        inactive_time = timezone.now() - active_session.last_activity
        if inactive_time > timedelta(hours=4):
            active_session.status = 'abandoned'
            active_session.save()
            active_session = None

    if not active_session:
        # Определяем стартовую страницу
        last_completed_session = ReadingSession.objects.filter(
            book=book, status='completed'
        ).order_by('-end_datetime').first()

        start_page = last_completed_session.end_page + 1 if last_completed_session else 1

        if start_page > book.pages_count:
            start_page = book.pages_count

        active_session = ReadingSession.objects.create(
            book=book,
            start_page=start_page,
            end_page=start_page - 1,
            status='active'
        )

    return Response({
        'session_id': active_session.id,
        'start_page': active_session.start_page,
        'current_page': active_session.end_page + 1 if active_session.end_page else active_session.start_page,
        'total_pages': book.pages_count
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

    # Проверяем, что страница новая (не сохранена ранее)
    if PageReadingLog.objects.filter(session=session, page_number=page_number).exists():
        return Response({"error": "Страница уже сохранена"}, status=status.HTTP_400_BAD_REQUEST)

    time_spent = timedelta(seconds=float(time_spent_seconds))

    # Создаем лог страницы
    page_log = PageReadingLog.objects.create(
        session=session,
        page_number=page_number,
        time_spent=time_spent,
        words_count=words_count
    )

    # Обновляем сессию
    session.end_page = page_number
    session.pages_read += 1
    session.last_activity = timezone.now()
    session.save()

    # Проверяем, закончена ли книга
    is_book_finished = page_number >= session.book.pages_count

    if is_book_finished:
        session.status = 'completed'
        session.end_datetime = timezone.now()
        session.save()

    # Обновляем стрик
    update_streak(request.user, page_log.completed_at.date())

    return Response({
        'success': True,
        'page_saved': page_number,
        'is_book_finished': is_book_finished,
        'pages_read_in_session': session.pages_read,
        'total_pages': session.book.pages_count
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def continue_reading(request, session_id):
    """Продолжить чтение после паузы (создать новую сессию)"""
    try:
        old_session = ReadingSession.objects.get(id=session_id, book__user=request.user)
    except ReadingSession.DoesNotExist:
        return Response({"error": "Сессия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if old_session.status == 'active':
        old_session.status = 'completed'
        old_session.end_datetime = timezone.now()
        old_session.save()

    # Создаем новую сессию
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
    """Завершить чтение (выйти на страницу книги)"""
    try:
        session = ReadingSession.objects.get(id=session_id, book__user=request.user, status='active')
    except ReadingSession.DoesNotExist:
        return Response({"error": "Активная сессия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    session.status = 'completed'
    session.end_datetime = timezone.now()
    session.save()

    return Response({'success': True})


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
    # Все завершенные сессии
    sessions = ReadingSession.objects.filter(book__user=request.user, status='completed')

    # Все логи страниц
    page_logs = PageReadingLog.objects.filter(session__book__user=request.user, session__status='completed')

    total_pages = page_logs.count()
    total_time = page_logs.aggregate(total=models.Sum('time_spent'))['total'] or timedelta(0)
    total_seconds = total_time.total_seconds()
    total_words = page_logs.aggregate(total=models.Sum('words_count'))['total'] or 0

    # Скорость чтения
    reading_speed = (total_words / (total_seconds / 60)) if total_seconds > 0 else 0

    # Книг в процессе
    books_in_progress = Book.objects.filter(user=request.user, status='in_progress').count()
    books_completed = Book.objects.filter(user=request.user, status='completed').count()

    # Сессий всего
    total_sessions = sessions.count()

    # Средняя длительность сессии
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
def read_book_web(request, book_id):
    """Отдать PDF для чтения в WebView"""
    try:
        book = Book.objects.get(id=book_id, user=request.user, status__in=['in_progress', 'completed'])
    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if not book.content:
        return Response({"error": "Контент книги отсутствует"}, status=status.HTTP_404_NOT_FOUND)

    response = HttpResponse(book.content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{book.name}.pdf"'
    response['Content-Length'] = len(book.content)
    return response


def update_streak(user, read_date):
    """Обновить стрик пользователя"""
    streak, created = UserReadingStreak.objects.get_or_create(user=user)

    today = date.today()

    if not streak.last_read_date:
        streak.current_streak = 1
        streak.longest_streak = 1
    elif read_date == today:
        # Уже обновлено сегодня
        return
    elif read_date == streak.last_read_date + timedelta(days=1):
        streak.current_streak += 1
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
    elif read_date > streak.last_read_date + timedelta(days=1):
        streak.current_streak = 1
    else:
        # Дата раньше последней (не обновляем)
        return

    streak.last_read_date = read_date
    streak.save()


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
        # Читаем PDF из binary content
        pdf_content = book.content
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)

        if page_num > len(reader.pages):
            return HttpResponse("Страница не найдена", status=404)

        # Создаем PDF только с 1 страницей
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