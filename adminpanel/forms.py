# Ответственная: Фатима (А-1 – А-6) — этап Э5
# Формы панели администратора. ModelForm строится по модели и сама
# проверяет поля (пустое название, неверная ссылка, неподходящий файл)
# и сохраняет данные в базу.
from django import forms

from accounts.models import User
from courses.models import Course, Lesson, Level, Material
from quizzes.models import Quiz


# А-1. Курс: название, описание, опубликован или скрыт
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'description', 'is_published')
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


# А-2. Уровень: название и порядок (уровни открываются по порядку, Ф-11)
class LevelForm(forms.ModelForm):
    class Meta:
        model = Level
        fields = ('title', 'order')
        help_texts = {'order': 'Номер уровня: 1, 2, 3… Уровни открываются по порядку.'}

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.course = course

    # Два уровня с одним номером в одном курсе запутают порядок — запрещаем
    def clean_order(self):
        order = self.cleaned_data['order']
        if order < 1:
            raise forms.ValidationError('Номер уровня начинается с 1.')
        same = Level.objects.filter(course=self.course, order=order).exclude(pk=self.instance.pk)
        if same.exists():
            raise forms.ValidationError('Уровень с таким номером в курсе уже есть.')
        return order


# А-3. Урок: название, порядок, описание, видео файлом или ссылкой
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('title', 'order', 'description', 'video', 'video_url')
        widgets = {'description': forms.Textarea(attrs={'rows': 6})}
        help_texts = {
            'video': 'Файл .mp4 или .webm. Урок отметится просмотренным после 90 % видео.',
            'video_url': 'Или ссылка: YouTube или прямая ссылка на .mp4.',
        }

    # Видеофайл должен быть видео, а не, например, картинкой
    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video and hasattr(video, 'name') and not video.name.lower().endswith(('.mp4', '.webm', '.ogg', '.mov')):
            raise forms.ValidationError('Загрузите видео в формате .mp4, .webm, .ogg или .mov.')
        return video


# А-3. Материал к уроку: PDF, презентация, аудио
class MaterialForm(forms.ModelForm):
    ALLOWED = ('.pdf', '.ppt', '.pptx', '.doc', '.docx', '.mp3', '.wav', '.ogg', '.m4a', '.zip', '.txt')

    class Meta:
        model = Material
        fields = ('title', 'file')

    # п. 4.2 ТЗ: неподдерживаемый тип файла отклоняется с понятным сообщением
    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith(self.ALLOWED):
            raise forms.ValidationError('Можно загрузить PDF, презентацию, документ, аудио или архив.')
        return file


# А-2, А-4. Тест уровня: название и порог сдачи (по ТЗ по умолчанию 80 %)
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ('title', 'pass_score')


# А-4. Конструктор вопроса: текст, до 4 вариантов, отметка правильного.
# Обычная форма (не ModelForm): один вопрос + несколько вариантов ответа сразу.
class QuestionForm(forms.Form):
    text = forms.CharField(label='Текст вопроса', widget=forms.Textarea(attrs={'rows': 3}))
    answer_1 = forms.CharField(label='Вариант 1', max_length=300)
    answer_2 = forms.CharField(label='Вариант 2', max_length=300)
    answer_3 = forms.CharField(label='Вариант 3', max_length=300, required=False)
    answer_4 = forms.CharField(label='Вариант 4', max_length=300, required=False)
    correct = forms.ChoiceField(
        label='Правильный вариант',
        choices=[('1', 'Вариант 1'), ('2', 'Вариант 2'), ('3', 'Вариант 3'), ('4', 'Вариант 4')],
        widget=forms.RadioSelect,
    )

    # Правильным нельзя отметить пустой вариант
    def clean(self):
        data = super().clean()
        correct = data.get('correct')
        if correct and not data.get(f'answer_{correct}'):
            raise forms.ValidationError('Правильный вариант не может быть пустым.')
        return data

    # Список вариантов: [(текст, правильный ли), …] без пустых
    def answers(self):
        return [(self.cleaned_data[f'answer_{i}'], self.cleaned_data['correct'] == str(i))
                for i in range(1, 5) if self.cleaned_data.get(f'answer_{i}')]


# А-5. Новый пользователь: только почта и имя, пароль сайт придумает сам
class UserCreateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name')
        labels = {'first_name': 'Имя'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
