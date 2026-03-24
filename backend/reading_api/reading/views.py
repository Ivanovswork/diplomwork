from datetime import timedelta

import fitz  # PyMuPDF
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from books.models import Book
from .models import ReadingSession, PageReadingLog, Test, Question, Answer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_book_session(request, book_id):
    """
    Вернуть информацию по книге и страницу, с которой продолжать чтение.
    """
    try:
        book = Book.objects.get(
            id=book_id,
            user=request.user,
            status__in=['inprogress', 'completed']
        )

        last_session = ReadingSession.objects.filter(
            book=book,
            status__in=['active', 'completed']
        ).order_by('-enddatetime').first()

        if last_session:
            start_page = last_session.endpage + 1
        else:
            start_page = 1

        if start_page > book.pagescount:
            start_page = book.pagescount

        return Response({
            'book_id': book.id,
            'name': book.name,
            'total_pages': book.pagescount,
            'start_page': start_page,
            'session_id': None
        })

    except Book.DoesNotExist:
        return Response(
            {'error': 'Книга не найдена или недоступна'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request):
    """
    Начать новую сессию чтения с указанной страницы.
    """
    book_id = request.data.get('book_id')
    start_page = request.data.get('start_page', 1)

    if book_id is None:
        return Response(
            {'error': 'Не указан book_id'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        book = Book.objects.get(id=book_id, user=request.user)
    except Book.DoesNotExist:
        return Response(
            {'error': 'Книга не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )

    session = ReadingSession.objects.create(
        book=book,
        startpage=start_page,
        endpage=start_page,
        status='active'
    )

    return Response({
        'session_id': session.id,
        'current_page': start_page
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def next_page(request):
    """
    Обработка нажатия кнопки "Прочитано, дальше":
    - логирует текущую страницу,
    - при предпоследней странице создаёт тест,
    - при последней завершает сессию и отдаёт test_id.
    """
    session_id = request.data.get('session_id')
    current_page = request.data.get('current_page')
    time_spent_seconds = request.data.get('time_spent', 30)

    if session_id is None or current_page is None:
        return Response(
            {'error': 'Нужны session_id и current_page'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        current_page = int(current_page)
        time_spent = timedelta(seconds=int(time_spent_seconds))
    except (TypeError, ValueError):
        return Response(
            {'error': 'Некорректные значения current_page или time_spent'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        session = ReadingSession.objects.get(
            id=session_id,
            status='active',
            book__user=request.user
        )
    except ReadingSession.DoesNotExist:
        return Response(
            {'error': 'Активная сессия не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )

    book = session.book

    if current_page < 1 or current_page > book.pagescount:
        return Response(
            {'error': 'Страница вне диапазона'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # лог чтения страницы
    PageReadingLog.objects.create(
        session=session,
        pagenumber=current_page,
        timespent=time_spent,
        wordscount=0  # при желании можно считать через PyMuPDF
    )

    session.endpage = current_page
    session.save()

    # предпоследняя страница → генерируем тест, но не показываем
    if current_page == book.pagescount - 1:
        test_id = create_dummy_test(session.id)
        return Response({
            'next_page': book.pagescount,
            'test_created': True,
            'test_id': test_id,
            'message': 'Тест сформирован. Прочитайте последнюю страницу.'
        })

    # последняя страница → завершаем сессию и возвращаем test_id
    if current_page == book.pagescount:
        session.status = 'completed'
        session.enddatetime = timezone.now()
        session.save()

        test = Test.objects.filter(session=session).first()
        if not test:
            test_id = create_dummy_test(session.id)
        else:
            test_id = test.id

        return Response({
            'completed': True,
            'message': 'Книга прочитана. Тест готов к прохождению.',
            'test_id': test_id
        })

    # обычный случай: просто следующая страница
    next_page_num = current_page + 1
    return Response({
        'next_page': next_page_num,
        'session_id': session.id
    })


def create_dummy_test(session_id: int) -> int:
    """
    Заглушка генерации теста:
    3 вопроса, по 3 ответа, один правильный.
    """
    start_time = timezone.now()

    session = ReadingSession.objects.get(id=session_id)
    test = Test.objects.create(
        session=session,
        teststatus='failed'
    )

    questions_data = [
        {
            'question': 'Что такое Django?',
            'answers': [
                ('Веб‑фреймворк на Python', True),
                ('База данных', False),
                ('Операционная система', False),
            ],
        },
        {
            'question': 'Сколько страниц было прочитано в этой сессии?',
            'answers': [
                (f'{session.endpage - session.startpage + 1}', True),
                ('Всегда 100', False),
                ('Меньше 5', False),
            ],
        },
        {
            'question': 'Зачем нужны сессии чтения?',
            'answers': [
                ('Чтобы отслеживать прогресс пользователя', True),
                ('Чтобы ломать приложение', False),
                ('Чтобы хранить пароли', False),
            ],
        },
    ]

    for q in questions_data:
        question = Question.objects.create(test=test, text=q['question'])
        for answer_text, is_correct in q['answers']:
            Answer.objects.create(
                question=question,
                text=answer_text,
                iscorrect=is_correct
            )

    test.formationtime = timezone.now() - start_time
    test.save()
    return test.id


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_test(request, session_id):
    """
    Отдать тест по сессии (после того, как он был создан).
    """
    try:
        session = ReadingSession.objects.get(
            id=session_id,
            book__user=request.user
        )
        test = Test.objects.get(session=session)
    except (ReadingSession.DoesNotExist, Test.DoesNotExist):
        return Response(
            {'error': 'Тест не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    data = {
        'id': test.id,
        'teststatus': test.teststatus,
        'formationtime': str(test.formationtime),
        'solutiontime': str(test.solutiontime) if test.solutiontime else None,
        'questions': []
    }

    for question in test.question_set.all():
        q_data = {
            'id': question.id,
            'text': question.text,
            'answers': []
        }
        for answer in question.answer_set.all():
            q_data['answers'].append({
                'id': answer.id,
                'text': answer.text,
                'iscorrect': answer.iscorrect
            })
        data['questions'].append(q_data)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_single_page(request, book_id, page_num):
    """
    Вернуть РОВНО одну страницу PDF книги как отдельный PDF‑документ.
    """
    try:
        book = Book.objects.get(
            id=book_id,
            user=request.user,
            status__in=['inprogress', 'completed']
        )
    except Book.DoesNotExist:
        return Response(
            {'error': 'Книга не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        return Response(
            {'error': 'Некорректный номер страницы'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if page_num < 1 or page_num > book.pagescount:
        return Response(
            {'error': 'Страница вне диапазона'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # открываем весь PDF из BinaryField
        doc = fitz.open("pdf", book.content)

        # создаём новый документ из одной страницы
        single_page_doc = fitz.open()
        single_page_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)
        pdf_bytes = single_page_doc.tobytes("pdf")

        # для статистики можем посчитать слова на этой странице
        page = doc[page_num - 1]
        words_count = len(page.get_text().split())

        single_page_doc.close()
        doc.close()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="page_{page_num}.pdf"'
        response['X-Page-Number'] = str(page_num)
        response['X-Total-Pages'] = str(book.pagescount)
        response['X-Word-Count'] = str(words_count)
        return response

    except Exception:
        return Response(
            {'error': 'Ошибка при обработке PDF'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
