# Ответственная: Фатима (Ф-12) — этап Э4
# Сигнал — это «подписка на событие» в Django: когда сохраняется попытка
# теста (модель Attempt из части Нургуль), Django сам вызывает нашу функцию.
# Так завершение курса (Ф-12) срабатывает и после сдачи последнего теста,
# а код теста (quizzes/views.py) менять не нужно.
from django.db.models.signals import post_save
from django.dispatch import receiver

from quizzes.models import Attempt

from .services import issue_certificate_if_completed


@receiver(post_save, sender=Attempt)
def certificate_after_test(sender, instance, created, **kwargs):
    # Интересуют только новые и сданные попытки
    if created and instance.passed:
        issue_certificate_if_completed(instance.user, instance.quiz.level.course)
