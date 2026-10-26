# Совместно: настройки проекта
# Главный список адресов сайта. Каждое приложение подключает свои адреса.
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Стандартная админка Django
    path('admin/', admin.site.urls),
    # Ф-9, Ф-10. Тесты в конце уровня (Нургуль)
    path('quizzes/', include('quizzes.urls')),
    # Ф-1, Ф-2, Ф-3. Регистрация, вход, выход, восстановление пароля (Нургуль)
    path('accounts/', include('accounts.urls')),
    # Ф-4. Каталог курсов — на главной странице (Фатима)
    path('', include('courses.urls')),
]

# В режиме разработки отдаём загруженные файлы (видео, PDF, аватары) из media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
