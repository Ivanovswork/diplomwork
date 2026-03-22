from django.contrib import admin
from .models import (
    ReadingSession, PageReadingLog, Test, Question, Answer,
    Achievement, UserAchievement
)

class PageReadingLogInline(admin.TabularInline):
    model = PageReadingLog
    extra = 0

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2

class TestInline(admin.TabularInline):
    model = Test
    extra = 0
    inlines = [QuestionInline, AnswerInline]

@admin.register(ReadingSession)
class ReadingSessionAdmin(admin.ModelAdmin):
    list_display = ['book', 'start_page', 'end_page', 'status', 'start_datetime']
    list_filter = ['status', 'start_datetime', 'book__status']
    inlines = [PageReadingLogInline, TestInline]
    raw_id_fields = ['book']

@admin.register(PageReadingLog)
class PageReadingLogAdmin(admin.ModelAdmin):
    list_display = ['session', 'page_number', 'time_spent', 'words_count']
    list_filter = ['session__book', 'session__status']
    raw_id_fields = ['session']

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['session', 'test_status', 'formation_time']
    list_filter = ['test_status']
    inlines = [QuestionInline]
    raw_id_fields = ['session']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['test', 'text']
    inlines = [AnswerInline]
    raw_id_fields = ['test']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'text', 'is_correct']
    raw_id_fields = ['question']

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement']
    raw_id_fields = ['user', 'achievement']
    list_filter = ['achievement']
