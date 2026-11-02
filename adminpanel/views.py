# Ответственная: Фатима (А-1 – А-6) — этап Э5
# Панель администратора — отдельный интерфейс администратора (п. 4.1.4 ТЗ):
#   А-1 курсы · А-2 уровни · А-3 уроки и материалы · А-4 конструктор тестов
#   А-5 пользователи · А-6 прогресс пользователей
# Все страницы — по адресу /panel/… и только для администратора (staff_required).
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.emails import make_password, send_account_email
from accounts.models import User
from courses.models import Certificate, Course, Enrollment, Lesson, Level, Material
from progress.services import course_progress
from quizzes.models import Answer, Attempt, Question, Quiz

from .emails import send_new_password_email
from .forms import (CourseForm, LessonForm, LevelForm, MaterialForm, QuestionForm,
                    QuizForm, UserCreateForm)


# Доступ только администратору. Не вошёл — на страницу входа.
# Вошёл обычный ученик — на главную с сообщением (функции администратора
# недоступны пользователю, п. 4.2 ТЗ).
def staff_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Этот раздел доступен только администратору.')
            return redirect('/')
        return view(request, *args, **kwargs)
    return wrapper


# Куда вернуться после кнопки: адрес из скрытого поля next, но только
# адрес нашего же сайта — чтобы ссылкой нельзя было увести на чужой сайт
def back_to(request, default):
    target = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect(default)


# ---------------------------------------------------------------- Обзор

# Обзор: главные цифры платформы и последние попытки тестов
@staff_required
def dashboard(request):
    stats = {
        'courses': Course.objects.count(),
        'published': Course.objects.filter(is_published=True).count(),
        'lessons': Lesson.objects.count(),
        'students': User.objects.filter(is_staff=False).count(),
        'blocked': User.objects.filter(is_staff=False, is_active=False).count(),
        'enrollments': Enrollment.objects.count(),
        'certificates': Certificate.objects.count(),
        'attempts': Attempt.objects.count(),
    }
    recent = Attempt.objects.select_related('user', 'quiz__level__course')[:8]
    return render(request, 'adminpanel/dashboard.html', {'stats': stats, 'recent': recent})


# ---------------------------------------------------------------- А-1. Курсы

@staff_required
def course_list(request):
    # annotate — сразу считаем уровни, уроки и записавшихся для каждого курса
    courses = Course.objects.annotate(
        levels_count=Count('levels', distinct=True),
        lessons_count=Count('levels__lessons', distinct=True),
        students_count=Count('enrollments', distinct=True),
    )
    return render(request, 'adminpanel/course_list.html', {'courses': courses})


# Создание и редактирование курса — одна функция: pk=None — новый курс
@staff_required
def course_form(request, pk=None):
    course = get_object_or_404(Course, pk=pk) if pk else None
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        messages.success(request, f'Курс «{course.title}» сохранён.')
        return redirect('adminpanel:course_detail', pk=course.pk)
    return render(request, 'adminpanel/form.html', {
        'form': form,
        'title': 'Редактирование курса' if pk else 'Новый курс',
        'back': ('adminpanel:course_detail', course.pk) if course else ('adminpanel:course_list', None),
    })


# Опубликовать / скрыть курс одной кнопкой (А-1)
@staff_required
@require_POST
def course_toggle(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.is_published = not course.is_published
    course.save(update_fields=['is_published'])
    messages.success(request, f'Курс «{course.title}» {"опубликован" if course.is_published else "скрыт"}.')
    return back_to(request, 'adminpanel:course_list')


@staff_required
@require_POST
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    title = course.title
    course.delete()  # уровни, уроки, тесты и записи удалятся вместе с курсом (CASCADE)
    messages.success(request, f'Курс «{title}» удалён.')
    return redirect('adminpanel:course_list')


# Структура курса: уровни по порядку, в каждом уроки и тест (А-1 – А-4)
@staff_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    levels = course.levels.order_by('order').prefetch_related('lessons__materials')
    # Подсказка «Как наполнить курс»: какие шаги уже сделаны (галочка) — уровень, урок, тест, публикация
    steps = {
        'level': course.levels.exists(),
        'lesson': Lesson.objects.filter(level__course=course).exists(),
        'quiz': Question.objects.filter(quiz__level__course=course).exists(),
        'published': course.is_published,
    }
    return render(request, 'adminpanel/course_detail.html', {'course': course, 'levels': levels, 'steps': steps})


# ---------------------------------------------------------------- А-2. Уровни

@staff_required
def level_form(request, course_pk=None, pk=None):
    level = get_object_or_404(Level, pk=pk) if pk else None
    course = level.course if level else get_object_or_404(Course, pk=course_pk)
    # Новый уровень по умолчанию — следующий номер после последнего
    initial = {'order': (course.levels.count() + 1)} if not level else None
    form = LevelForm(request.POST or None, instance=level, course=course, initial=initial)
    if request.method == 'POST' and form.is_valid():
        level = form.save(commit=False)
        level.course = course
        level.save()
        messages.success(request, f'Уровень «{level.title}» сохранён.')
        return redirect('adminpanel:course_detail', pk=course.pk)
    return render(request, 'adminpanel/form.html', {
        'form': form,
        'title': f'Уровень курса «{course.title}»',
        'back': ('adminpanel:course_detail', course.pk),
    })


@staff_required
@require_POST
def level_delete(request, pk):
    level = get_object_or_404(Level, pk=pk)
    course_pk = level.course_id
    level.delete()
    messages.success(request, 'Уровень удалён.')
    return redirect('adminpanel:course_detail', pk=course_pk)


# ---------------------------------------------------------------- А-3. Уроки и материалы

@staff_required
def lesson_form(request, level_pk=None, pk=None):
    lesson = get_object_or_404(Lesson, pk=pk) if pk else None
    level = lesson.level if lesson else get_object_or_404(Level, pk=level_pk)
    initial = {'order': level.lessons.count() + 1} if not lesson else None
    # request.FILES — загружаемый видеофайл
    form = LessonForm(request.POST or None, request.FILES or None, instance=lesson, initial=initial)
    if request.method == 'POST' and form.is_valid():
        lesson = form.save(commit=False)
        lesson.level = level
        lesson.save()
        messages.success(request, f'Урок «{lesson.title}» сохранён.')
        return redirect('adminpanel:lesson_edit', pk=lesson.pk)
    materials = lesson.materials.all() if lesson else []
    return render(request, 'adminpanel/lesson_form.html', {
        'form': form,
        'lesson': lesson,
        'level': level,
        'materials': materials,
        'material_form': MaterialForm(),
    })


@staff_required
@require_POST
def lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    course_pk = lesson.level.course_id
    lesson.delete()
    messages.success(request, 'Урок удалён.')
    return redirect('adminpanel:course_detail', pk=course_pk)


# Загрузка файла-материала к уроку (PDF, презентация, аудио)
@staff_required
@require_POST
def material_add(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    form = MaterialForm(request.POST, request.FILES)
    if form.is_valid():
        material = form.save(commit=False)
        material.lesson = lesson
        material.save()
        messages.success(request, f'Материал «{material.title}» добавлен.')
    else:
        for errors in form.errors.values():
            messages.error(request, errors[0])
    return redirect('adminpanel:lesson_edit', pk=lesson.pk)


@staff_required
@require_POST
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    lesson_pk = material.lesson_id
    material.delete()
    messages.success(request, 'Материал удалён.')
    return redirect('adminpanel:lesson_edit', pk=lesson_pk)


# ---------------------------------------------------------------- А-4. Конструктор тестов

# Тест уровня: название, порог сдачи, вопросы с вариантами.
# У уровня ровно один тест (OneToOne) — если его нет, создаём при сохранении.
@staff_required
def quiz_edit(request, level_pk):
    level = get_object_or_404(Level, pk=level_pk)
    quiz = getattr(level, 'quiz', None)
    form = QuizForm(request.POST or None, instance=quiz,
                    initial=None if quiz else {'title': f'Тест: {level.title}', 'pass_score': 80})
    if request.method == 'POST' and form.is_valid():
        quiz = form.save(commit=False)
        quiz.level = level
        quiz.save()
        messages.success(request, 'Тест сохранён.')
        return redirect('adminpanel:quiz_edit', level_pk=level.pk)
    questions = quiz.questions.prefetch_related('answers') if quiz else []
    return render(request, 'adminpanel/quiz_edit.html', {
        'level': level,
        'quiz': quiz,
        'form': form,
        'questions': questions,
        'question_form': QuestionForm(),
    })


# Добавить вопрос или изменить существующий (pk — номер вопроса)
@staff_required
def question_form(request, level_pk, pk=None):
    level = get_object_or_404(Level, pk=level_pk)
    quiz = getattr(level, 'quiz', None)
    if quiz is None:
        messages.error(request, 'Сначала сохраните тест уровня.')
        return redirect('adminpanel:quiz_edit', level_pk=level.pk)
    question = get_object_or_404(Question, pk=pk, quiz=quiz) if pk else None

    initial = None
    if question:
        # Заполняем форму существующими вариантами
        initial = {'text': question.text}
        for i, answer in enumerate(question.answers.all()[:4], start=1):
            initial[f'answer_{i}'] = answer.text
            if answer.is_correct:
                initial['correct'] = str(i)
    form = QuestionForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        if question is None:
            question = Question.objects.create(quiz=quiz, text=form.cleaned_data['text'],
                                               order=quiz.questions.count() + 1)
        else:
            question.text = form.cleaned_data['text']
            question.save(update_fields=['text'])
            question.answers.all().delete()  # варианты пересоздаём заново
        for text, is_correct in form.answers():
            Answer.objects.create(question=question, text=text, is_correct=is_correct)
        messages.success(request, 'Вопрос сохранён.')
        return redirect('adminpanel:quiz_edit', level_pk=level.pk)

    return render(request, 'adminpanel/form.html', {
        'form': form,
        'title': f'{"Вопрос" if question else "Новый вопрос"} — {quiz.title}',
        'back': ('adminpanel:quiz_edit', level.pk),
    })


@staff_required
@require_POST
def question_delete(request, pk):
    question = get_object_or_404(Question.objects.select_related('quiz'), pk=pk)
    level_pk = question.quiz.level_id
    question.delete()
    messages.success(request, 'Вопрос удалён.')
    return redirect('adminpanel:quiz_edit', level_pk=level_pk)


# ---------------------------------------------------------------- А-5. Пользователи

@staff_required
def user_list(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    users = User.objects.filter(is_staff=False).annotate(
        courses_count=Count('enrollments', distinct=True)).order_by('email')
    if query:
        # Поиск без учёта больших и маленьких букв. SQLite умеет это только для
        # латиницы, поэтому сравниваем в Python через casefold() — работает и для кириллицы
        needle = query.casefold()
        users = [u for u in users if needle in u.email.casefold() or needle in u.first_name.casefold()]
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'blocked':
        users = users.filter(is_active=False)
    return render(request, 'adminpanel/user_list.html', {
        'users': users, 'query': query, 'status': status,
    })


# Создание учётной записи: сайт придумывает пароль и отправляет логин и пароль
# на почту (Ф-1 Нургуль — та же функция send_account_email из accounts/emails.py)
@staff_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.username = user.email
        password = make_password()
        user.set_password(password)
        user.save()
        if send_account_email(request, user, password):
            messages.success(request, f'Аккаунт создан. Логин и пароль отправлены на {user.email}.')
        else:
            messages.warning(request, f'Аккаунт создан, но письмо не отправилось. '
                                      f'Передайте человеку: логин {user.email}, пароль {password}')
        return redirect('adminpanel:user_list')
    return render(request, 'adminpanel/form.html', {
        'form': form,
        'title': 'Новый пользователь',
        'note': 'Пароль задавать не нужно: сайт придумает его сам и отправит на почту вместе с логином.',
        'back': ('adminpanel:user_list', None),
    })


# Блокировка / разблокировка: is_active=False — войти на сайт нельзя
@staff_required
@require_POST
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk, is_staff=False)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    messages.success(request, f'{user.email} {"разблокирован" if user.is_active else "заблокирован"}.')
    return back_to(request, 'adminpanel:user_list')


# Выдача нового пароля: новый случайный пароль уходит человеку на почту
@staff_required
@require_POST
def user_new_password(request, pk):
    user = get_object_or_404(User, pk=pk, is_staff=False)
    password = make_password()
    user.set_password(password)
    user.save(update_fields=['password'])
    if send_new_password_email(request, user, password):
        messages.success(request, f'Новый пароль отправлен на {user.email}.')
    else:
        messages.warning(request, f'Письмо не отправилось. Новый пароль для {user.email}: {password}')
    return back_to(request, 'adminpanel:user_list')


# ---------------------------------------------------------------- А-6. Прогресс

# Прогресс одного пользователя по всем его курсам и уровням
# (та же функция course_progress, что и в «Моём прогрессе» Ф-14)
@staff_required
def user_progress(request, pk):
    student = get_object_or_404(User, pk=pk, is_staff=False)
    enrollments = Enrollment.objects.filter(user=student).select_related('course')
    # к прогрессу каждого курса добавляем номер записи — для кнопки «Отчислить»
    courses = [{**course_progress(student, e.course), 'enrollment_pk': e.pk} for e in enrollments]
    certificates = Certificate.objects.filter(user=student).select_related('course')
    # Курсы, на которые ученика ещё можно записать (опубликованные, где он ещё не учится)
    available = Course.objects.filter(is_published=True).exclude(enrollments__user=student).order_by('title')
    return render(request, 'adminpanel/user_progress.html', {
        'student': student, 'courses': courses, 'certificates': certificates,
        'available': available,
    })


# Сводная таблица: все записи на курсы и процент прохождения, с фильтром по курсу
@staff_required
def progress_overview(request):
    course_id = request.GET.get('course', '')
    enrollments = Enrollment.objects.select_related('user', 'course').order_by('course__title', 'user__email')
    if course_id.isdigit():
        enrollments = enrollments.filter(course_id=int(course_id))
    rows = []
    for enrollment in enrollments:
        progress = course_progress(enrollment.user, enrollment.course)
        rows.append({'enrollment': enrollment, 'percent': progress['percent'],
                     'completed': progress['is_completed']})
    return render(request, 'adminpanel/progress.html', {
        'rows': rows, 'courses': Course.objects.order_by('title'), 'course_id': course_id,
        # для формы «Записать ученика на курс»
        'students': User.objects.filter(is_staff=False).order_by('email'),
        'published_courses': Course.objects.filter(is_published=True).order_by('title'),
    })


# ---------------------------------------------------------------- Сверх ТЗ: запись на курс администратором
# По ТЗ (Ф-6) ученик записывается на курс сам. Дополнительно администратор
# может сам записать ученика на курс (открыть ему доступ) или отчислить его.
# Записать можно только на опубликованный курс: скрытый курс ученик не увидит.

def post_int(request, name):
    # Число из формы; если пришло не число — 0 (такого id в базе нет → 404)
    value = request.POST.get(name, '')
    return int(value) if value.isdigit() else 0


@staff_required
@require_POST
def enrollment_add(request):
    student = get_object_or_404(User, pk=post_int(request, 'user'), is_staff=False)
    course = get_object_or_404(Course, pk=post_int(request, 'course'), is_published=True)
    # get_or_create — повторная запись не создаст дубль
    _, created = Enrollment.objects.get_or_create(user=student, course=course)
    if created:
        messages.success(request, f'{student.email} записан на курс «{course.title}». Курс появился у него в «Моих курсах».')
    else:
        messages.info(request, f'{student.email} уже записан на курс «{course.title}».')
    return back_to(request, 'adminpanel:progress')


# Отчислить: запись удаляется, курс пропадает из «Моих курсов» ученика.
# Просмотренные уроки и попытки тестов остаются — при новой записи прогресс вернётся.
@staff_required
@require_POST
def enrollment_remove(request, pk):
    enrollment = get_object_or_404(Enrollment.objects.select_related('user', 'course'), pk=pk)
    enrollment.delete()
    messages.success(request, f'{enrollment.user.email} отчислен с курса «{enrollment.course.title}».')
    return back_to(request, 'adminpanel:progress')
