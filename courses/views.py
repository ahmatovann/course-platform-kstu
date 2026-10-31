# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from progress.services import course_progress

from .models import Certificate, Course, Enrollment, Lesson
from .services import (build_program, issue_certificate_if_completed,
                       mark_lesson_watched, next_step)

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

    # 2. Сколько всего уроков в курсе — для цифр вверху страницы
    lessons_count = Lesson.objects.filter(level__course=course).count()

    # 3. Первый урок курса — для кнопки «Начать первый урок» (Ф-7).
    #    order_by: сначала по номеру уровня, потом по номеру урока.
    first_lesson = Lesson.objects.filter(level__course=course).order_by(
        'level__order', 'order').first()

    # 4. Ф-11 (Э4). Программа курса: уровни с отметкой открыт / закрыт / пройден
    #    и уроки с отметкой «просмотрен» (courses/services.py).
    program, progress = build_program(request.user, course)
    is_enrolled = progress is not None

    # 5. Ф-12 (Э4). Курс пройден — выдаём сертификат, если его ещё нет
    certificate = None
    if is_enrolled:
        certificate = issue_certificate_if_completed(request.user, course)

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'levels': program,
        'program': program,
        'progress': progress,
        'certificate': certificate,
        'is_admin_preview': request.user.is_staff,
        'lessons_count': lessons_count,
        'first_lesson': first_lesson,
        'is_enrolled': is_enrolled,
    })


# Ф-6. Запись на курс без оплаты
# @login_required — записаться может только вошедший пользователь
@login_required
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk, is_published=True)

    # По ТЗ (п. 4.1.4) администратор курсы не проходит и не записывается
    if request.user.is_staff:
        messages.info(request, 'Администратор не записывается на курсы — только просматривает их.')
        return redirect('courses:course_detail', pk=course.pk)

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
    enrollments = list(Enrollment.objects.filter(user=request.user).select_related('course'))
    # Ф-12 (Э4). У каждого курса — процент прохождения и сертификат, если курс пройден
    for enrollment in enrollments:
        enrollment.progress = course_progress(request.user, enrollment.course)
        enrollment.certificate = issue_certificate_if_completed(request.user, enrollment.course)
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

    # Администратор (п. 4.1.4) курсы не проходит, но может посмотреть урок
    # так, как его видит обучающийся — без записи и без отметок.
    is_admin_preview = request.user.is_staff

    # 2. Урок открыт только тем, кто записан на курс (Ф-6).
    #    Иначе возвращаем на карточку курса с подсказкой.
    if not is_admin_preview and not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, 'Запишитесь на курс, чтобы смотреть уроки.')
        return redirect('courses:course_detail', pk=course.pk)

    # 3. Ф-11 (Э4). Программа курса: какие уровни открыты.
    #    Урок закрытого уровня не открывается, даже если ввести адрес вручную.
    program, progress = build_program(request.user, course)
    current = next((item for item in program if item['level'].id == lesson.level_id), None)
    if not is_admin_preview and current and not current['is_open']:
        messages.error(request, 'Этот уровень ещё закрыт: пройдите уроки и тест предыдущего уровня.')
        return redirect('courses:course_detail', pk=course.pk)

    # 4. Материалы урока: к каждому файлу добавляем его вид (pdf / audio / file)
    materials = []
    for material in lesson.materials.all():
        material.kind = material_kind(material.file.name)
        materials.append(material)

    # 5. Ф-8 (Э4). Просмотрен ли урок, и куда идти дальше
    watched = any(entry['watched'] for item in program for entry in item['lessons']
                  if entry['lesson'].id == lesson.id)
    next_label, next_url = next_step(program, lesson)

    return render(request, 'courses/lesson.html', {
        'lesson': lesson,
        'course': course,
        'materials': materials,
        'levels': program,
        'program': program,
        'is_enrolled': not is_admin_preview,
        'is_admin_preview': is_admin_preview,
        'watched': watched,
        'next_label': next_label,
        'next_url': next_url,
    })


# Ф-8 (Э4). Отметка «урок просмотрен».
# Вызывается двумя способами:
#   1) скрипт static/js/lesson.js сам отправляет запрос, когда просмотрено 90 % видео;
#   2) кнопка «Отметить как изученный», если у урока нет видео.
# @require_POST — отметить можно только POST-запросом (не простым переходом по ссылке).
@login_required
@require_POST
def lesson_watched(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related('level__course'),
        pk=pk, level__course__is_published=True,
    )
    course = lesson.level.course
    wants_json = request.headers.get('X-Requested-With') == 'fetch'

    # Отмечать могут только записанные ученики и только в открытом уровне
    allowed = (not request.user.is_staff
               and Enrollment.objects.filter(user=request.user, course=course).exists())
    if allowed:
        program, _ = build_program(request.user, course)
        allowed = any(item['is_open'] for item in program if item['level'].id == lesson.level_id)
    if not allowed:
        if wants_json:
            return JsonResponse({'ok': False}, status=403)
        messages.error(request, 'Этот урок нельзя отметить.')
        return redirect('courses:course_detail', pk=course.pk)

    # Сама отметка + проверка, не завершён ли курс (Ф-12)
    certificate = mark_lesson_watched(request.user, lesson)

    if wants_json:
        # Ответ для скрипта: урок отмечен, и есть ли уже сертификат
        return JsonResponse({
            'ok': True,
            'certificate_url': f'/certificate/{certificate.number}/' if certificate else None,
        })
    messages.success(request, 'Урок отмечен как изученный.')
    if certificate:
        messages.success(request, 'Курс пройден! Сертификат выдан.')
    return redirect('courses:lesson', pk=lesson.pk)


# Ф-12 (Э4). Сертификат о прохождении курса: /certificate/CP-XXXXXXXX/
# Видит владелец и администратор. Чужой сертификат по ссылке не откроется (404).
@login_required
def certificate_view(request, number):
    certificate = get_object_or_404(
        Certificate.objects.select_related('user', 'course'), number=number)
    if certificate.user != request.user and not request.user.is_staff:
        raise Http404('Сертификат не найден')
    return render(request, 'courses/certificate.html', {'certificate': certificate})


# Ф-12 (Э4). Проверка подлинности сертификата по номеру — доступна всем,
# даже гостю (таблица ролей в ТЗ: «Гость — … проверка сертификата»).
def certificate_check(request):
    number = request.GET.get('number', '').strip().upper()
    certificate = None
    if number:
        certificate = Certificate.objects.select_related('user', 'course').filter(
            number=number).first()
    return render(request, 'courses/certificate_check.html', {
        'number': number,
        'certificate': certificate,
    })
