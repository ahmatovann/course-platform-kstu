# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .models import Course, Enrollment, Lesson

# Ф-4 Каталог курсов и поиск — Фатима
# Ф-5 Карточка курса — Фатима
# Ф-6 Запись на курс — Фатима
# Ф-7 Просмотр урока — Фатима
# Ф-8 Отметка о просмотре (90 % видео) — Фатима
# Ф-11 Открытие следующего уровня — Фатима
# Ф-12 Завершение курса и сертификат — Фатима


# Ф-4. Каталог курсов: главная страница со всеми опубликованными курсами
# и поиском по названию.
def catalog(request):
    # 1. Берём из базы только опубликованные курсы (is_published=True).
    #    annotate + Count сразу считают для каждого курса число уровней
    #    и уроков — они показываются внизу карточки («Уровней: 2 · Уроков: 4»).
    #    distinct=True — чтобы при подсчёте уроки не посчитались дважды.
    courses = Course.objects.filter(is_published=True).annotate(
        levels_count=Count('levels', distinct=True),
        lessons_count=Count('levels__lessons', distinct=True),
    )

    # 2. Читаем текст из строки поиска: адрес вида /?q=python
    #    .get('q', '') — если поиска не было, будет пустая строка.
    #    .strip() — убираем пробелы по краям.
    query = request.GET.get('q', '').strip()

    # 3. Если что-то ввели — оставляем курсы, в названии которых есть этот текст.
    #    icontains — «содержит», без учёта больших и маленьких букв.
    if query:
        courses = courses.filter(title__icontains=query)

    # 4. Отдаём данные в шаблон courses/catalog.html
    return render(request, 'courses/catalog.html', {
        'courses': courses,
        'query': query,
    })


# Ф-5. Карточка курса: описание, список уровней и уроков, кнопка «Записаться»
def course_detail(request, pk):
    # 1. Находим опубликованный курс по номеру из адреса /course/<pk>/.
    #    Неопубликованный или несуществующий курс — страница 404.
    course = get_object_or_404(Course, pk=pk, is_published=True)

    # 2. Уровни курса сразу вместе с уроками (prefetch_related —
    #    чтобы не делать отдельный запрос к базе на каждый уровень).
    levels = course.levels.prefetch_related('lessons')

    # 3. Сколько всего уроков в курсе — для цифр вверху страницы
    lessons_count = Lesson.objects.filter(level__course=course).count()

    # 4. Первый урок курса — для кнопки «Начать первый урок» (Ф-7).
    #    order_by: сначала по номеру уровня, потом по номеру урока.
    first_lesson = Lesson.objects.filter(level__course=course).order_by(
        'level__order', 'order').first()

    # 5. Записан ли уже человек на этот курс? От этого зависит,
    #    что показать: кнопку «Записаться» или «Вы записаны».
    is_enrolled = (
        request.user.is_authenticated
        and Enrollment.objects.filter(user=request.user, course=course).exists()
    )

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'levels': levels,
        'lessons_count': lessons_count,
        'first_lesson': first_lesson,
        'is_enrolled': is_enrolled,
    })


# Ф-6. Запись на курс без оплаты
# @login_required — записаться может только вошедший пользователь
@login_required
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk, is_published=True)

    # Запись только по кнопке (POST), а не простым переходом по ссылке
    if request.method == 'POST':
        # get_or_create — создаёт запись, если её ещё нет.
        # Повторное нажатие не создаст дубль (в модели есть UniqueConstraint).
        _, created = Enrollment.objects.get_or_create(user=request.user, course=course)
        if created:
            messages.success(request, 'Вы записались на курс. Он появился в «Моих курсах».')

    return redirect('courses:course_detail', pk=course.pk)


# Ф-6. «Мои курсы»: курсы, на которые записан пользователь
@login_required
def my_courses(request):
    # select_related('course') — сразу берём данные курса вместе с записью
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    return render(request, 'courses/my_courses.html', {'enrollments': enrollments})


# Ф-7. Какого вида файл материала: PDF, аудио или другой (презентация и т. п.).
# Смотрим по расширению имени файла. От вида зависит, как показать файл:
# аудио — сразу плеер на странице, остальное — ссылка «Открыть / скачать».
def material_kind(filename):
    name = filename.lower()
    if name.endswith('.pdf'):
        return 'pdf'
    if name.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
        return 'audio'
    return 'file'


# Ф-7. Просмотр урока: видео, текстовое описание и файлы материалов
@login_required
def lesson_view(request, pk):
    # 1. Находим урок. select_related сразу подтягивает уровень и курс.
    lesson = get_object_or_404(
        Lesson.objects.select_related('level__course'),
        pk=pk, level__course__is_published=True,
    )
    course = lesson.level.course

    # 2. Урок открыт только тем, кто записан на курс (Ф-6).
    #    Иначе возвращаем на карточку курса с подсказкой.
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, 'Запишитесь на курс, чтобы смотреть уроки.')
        return redirect('courses:course_detail', pk=course.pk)

    # 3. Материалы урока: к каждому файлу добавляем его вид (pdf / audio / file)
    materials = []
    for material in lesson.materials.all():
        material.kind = material_kind(material.file.name)
        materials.append(material)

    # 4. Уровни и уроки курса — для панели «Программа» справа,
    #    где текущий урок подсвечен.
    levels = course.levels.prefetch_related('lessons')

    # Открытие уровней по порядку (Ф-11) и отметка о просмотре
    # после 90 % видео (Ф-8) — этап Э4.
    return render(request, 'courses/lesson.html', {
        'lesson': lesson,
        'course': course,
        'materials': materials,
        'levels': levels,
        'is_enrolled': True,
    })
