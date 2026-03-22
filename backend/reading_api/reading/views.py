from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from books.models import Book


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def read_book(request, book_id):
    """Чтение своей книги (только свои книги!)"""
    try:
        # Только свои книги!
        book = Book.objects.get(
            id=book_id,
            user=request.user,
            status__in=['in_progress', 'completed']
        )

        # PDF stream
        response = HttpResponse(
            book.content,
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{book.name}.pdf"'
        response['Content-Length'] = len(book.content)

        return response

    except Book.DoesNotExist:
        return Response({"error": "Книга не найдена или нет доступа"}, status=404)