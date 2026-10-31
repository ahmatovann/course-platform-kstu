# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
# Регистрация моделей в стандартной админке Django (/admin/).
# Нужна, чтобы уже сейчас добавлять курсы, уровни и уроки и проверять сайт.
# Своя панель администратора (А-1 – А-6) будет на этапе Э5.
from django.contrib import admin

from .models import Certificate, Course, Enrollment, Lesson, LessonProgress, Level, Material


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


# Ф-7. Файлы урока (PDF, презентации, аудио) — прямо на странице урока
class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'order')
    list_filter = ('level__course',)
    inlines = [MaterialInline]


# Ф-6. Записи на курсы — только просмотр, кто куда записан
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')


# Ф-8 (Э4). Просмотры уроков — администратор видит, кто что посмотрел
@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'watched_at')
    list_filter = ('lesson__level__course',)


# Ф-12 (Э4). Выданные сертификаты — только просмотр, подделать нельзя:
# сертификат выдаёт сам сайт, когда курс пройден полностью
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('number', 'user', 'course', 'issued_at')
    search_fields = ('number', 'user__email')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
