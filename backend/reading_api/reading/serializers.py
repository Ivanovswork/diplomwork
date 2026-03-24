from rest_framework import serializers
from .models import ReadingSession, PageReadingLog, Test, Question, Answer
from books.models import Book


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'iscorrect']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'answers']


class TestSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = ['id', 'teststatus', 'formationtime', 'solutiontime', 'questions']


class BookSessionSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    start_page = serializers.IntegerField()
    session_id = serializers.IntegerField(allow_null=True)


class PageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageReadingLog
        fields = ['pagenumber', 'timespent', 'wordscount'][file:1]
