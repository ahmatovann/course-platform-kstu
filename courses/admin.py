# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
# Регистрация моделей в стандартной админке Django (/admin/).
# Нужна, чтобы уже сейчас добавлять курсы, уровни и уроки и проверять сайт.
# Своя панель администратора (А-1 – А-6) будет на этапе Э5.
from django.contrib import admin

from .models import Course, Enrollment, Lesson, Level


# Inline — уровни редактируются прямо на странице курса
class LevelInline(admin.TabularInline):
    model = Level
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    # Какие колонки видны в списке курсов
    list_display = ('title', 'is_published', 'created_at')
    # Галочку «Опубликован» можно ставить прямо в списке
    list_editable = ('is_published',)
    # Поиск по названию в админке
    search_fields = ('title',)
    inlines = [LevelInline]


# Уроки редактируются прямо на странице уровня
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'order')
    list_filter = ('level__course',)


# Ф-6. Записи на курсы — только просмотр, кто куда записан
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
