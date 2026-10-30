# Ответственная: Нургуль (Ф-14)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from courses.models import Enrollment

from .services import course_progress

# Ф-14 Мой прогресс — Нургуль


# Ф-14. «Мой прогресс»: процент прохождения по каждому курсу и результаты тестов
@login_required
def my_progress(request):
    # По ТЗ (п. 4.1.4) у администратора раздела «Мой прогресс» нет:
    # он курсы не проходит, а прогресс учеников смотрит в своей панели (А-6).
    if request.user.is_staff:
        messages.info(request, 'У администратора нет раздела «Мой прогресс».')
        return redirect('/admin/')

    # 1. Курсы, на которые записан пользователь (Ф-6), сначала новые записи
    enrollments = (Enrollment.objects.filter(user=request.user)
                   .select_related('course').order_by('-enrolled_at'))

    # 2. Для каждого курса считаем прогресс (progress/services.py):
    #    процент, уровни, просмотренные уроки, результаты тестов
    courses = [course_progress(request.user, e.course) for e in enrollments]

    return render(request, 'progress/my_progress.html', {'courses': courses})
