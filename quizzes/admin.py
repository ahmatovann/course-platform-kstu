# Ответственная: Нургуль (Ф-9, Ф-10)
# Тесты в стандартной админке Django (/admin/): здесь пока создаём
# тесты, вопросы и варианты ответов. Своя панель (А-1 – А-6) — на этапе Э5.
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

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
# Проверка при сохранении вопроса: у вопроса должен быть ровно один
# правильный вариант. Ученик выбирает один ответ (radio-кнопки), поэтому
# без правильного варианта тест нельзя сдать, а с двумя — непонятно, какой верный.
class AnswerFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        answers = [f for f in self.forms
                   if f.cleaned_data and not f.cleaned_data.get('DELETE')]
        if not answers:
            return
        correct = sum(1 for f in answers if f.cleaned_data.get('is_correct'))
        if correct != 1:
            raise ValidationError('Отметьте ровно один правильный вариант ответа.')


class AnswerInline(admin.TabularInline):
    model = Answer
    formset = AnswerFormSet
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [AnswerInline]


# Попытки только смотрим: кто, какой тест, сколько процентов
@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'correct', 'total', 'score', 'passed', 'created_at')
    list_filter = ('quiz', 'passed')

    # Попытки создаёт только сайт после проверки теста. Админ их смотрит,
    # но не добавляет и не меняет — чтобы результаты нельзя было подделать.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
