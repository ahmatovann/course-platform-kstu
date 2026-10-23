# Ответственная: Нургуль (Ф-9, Ф-10)
# Тесты в стандартной админке Django (/admin/): здесь пока создаём
# тесты, вопросы и варианты ответов. Своя панель (А-1 – А-6) — на этапе Э5.
from django.contrib import admin

from .models import Answer, Attempt, Question, Quiz


# Inline — вопросы редактируются прямо на странице теста
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # одна пустая строка для нового вопроса


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'pass_score')
    inlines = [QuestionInline]


# Варианты ответов редактируются на странице вопроса.
# Галочка «Правильный» видна только администратору.
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [AnswerInline]


# Попытки только смотрим: кто, какой тест, сколько процентов
@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'passed', 'created_at')
    list_filter = ('quiz', 'passed')
