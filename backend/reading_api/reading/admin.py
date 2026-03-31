from django.contrib import admin
from .models import ReadingSession, PageReadingLog, Test, Question, Answer, UserReadingStreak, UserTestResult


class PageReadingLogInline(admin.TabularInline):
    model = PageReadingLog
    extra = 0
    fields = ['page_number', 'time_spent', 'words_count', 'completed_at']
    readonly_fields = ['completed_at']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['text']


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2
    fields = ['text', 'is_correct']


@admin.register(ReadingSession)
class ReadingSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'start_page', 'end_page', 'pages_read', 'status', 'start_datetime',
                    'is_daily_goal_completed']
    list_filter = ['status', 'is_daily_goal_completed', 'start_datetime']
    search_fields = ['book__name']
    readonly_fields = ['start_datetime', 'last_activity']
    raw_id_fields = ['book']
    inlines = [PageReadingLogInline]


@admin.register(PageReadingLog)
class PageReadingLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'page_number', 'time_spent', 'words_count', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['session__book__name']
    raw_id_fields = ['session']
    readonly_fields = ['completed_at']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'start_page', 'end_page', 'status', 'score', 'total_questions', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['session__book__name']
    raw_id_fields = ['session']
    readonly_fields = ['created_at', 'completed_at']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'test', 'text']
    search_fields = ['text']
    raw_id_fields = ['test']
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'text', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['text']
    raw_id_fields = ['question']


@admin.register(UserReadingStreak)
class UserReadingStreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak', 'longest_streak', 'last_read_date']
    list_filter = ['last_read_date']
    search_fields = ['user__email', 'user__name']
    raw_id_fields = ['user']


@admin.register(UserTestResult)
class UserTestResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'test', 'correct_answers', 'total_questions', 'score_percent', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['user__email', 'book__name']
    raw_id_fields = ['user', 'book', 'test']

    def score_percent(self, obj):
        return f"{obj.score_percent}%"

    score_percent.short_description = "Процент"