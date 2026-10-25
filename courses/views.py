# Ответственная: Фатима (Ф-4 – Ф-8, Ф-11, Ф-12)
from django.db.models import Count
from django.shortcuts import render

from .models import Course

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
