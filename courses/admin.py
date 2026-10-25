# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
# Регистрация моделей в стандартной админке Django (/admin/).
# Нужна, чтобы уже сейчас добавлять курсы и проверять каталог.
# Своя панель администратора (А-1 – А-6) будет на этапе Э5.
from django.contrib import admin

from .models import Course, Level, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    # Какие колонки видны в списке курсов
    list_display = ('title', 'is_published', 'created_at')
    # Галочку «Опубликован» можно ставить прямо в списке
    list_editable = ('is_published',)
    # Поиск по названию в админке
    search_fields = ('title',)


admin.site.register(Level)
admin.site.register(Lesson)
