/* Ответственная: Фатима (Ф-8) — этап Э4 */
/* Ф-8. Урок отмечается просмотренным автоматически после 90 % видео.
   Считаем не позицию ползунка, а сколько видео реально проиграно.
   Браузер сам запоминает проигранные куски в video.played (список отрезков
   «с какой по какую секунду»). Перемотанные куски туда не попадают,
   поэтому перемотка в конец не засчитается — нужно действительно посмотреть.
   Когда набралось 90 % длины видео, отправляем POST на сервер (courses/views.py,
   функция lesson_watched), а сервер сохраняет отметку в базу (LessonProgress). */
(function () {
    var video = document.getElementById('lesson-video');
    // Нет видео или урок уже отмечен (нет data-watched-url) — ничего не делаем
    if (!video || !video.dataset.watchedUrl) return;

    var sent = false;   // отметку отправляем только один раз

    // csrftoken — защита Django от подделки запросов: берём его из cookie
    function csrfToken() {
        var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function send() {
        sent = true;
        fetch(video.dataset.watchedUrl, {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken(), 'X-Requested-With': 'fetch'},
            credentials: 'same-origin'
        }).then(function (response) { return response.json(); })
          .then(function (data) {
              if (!data.ok) return;
              // Показываем «Урок просмотрен» без перезагрузки страницы
              document.getElementById('watched-badge').hidden = false;
              var hint = document.getElementById('watched-hint');
              if (hint) hint.hidden = true;
              // Ф-12: если этим уроком курс пройден — ссылка на сертификат
              if (data.certificate_url) {
                  document.getElementById('certificate-link').href = data.certificate_url;
                  document.getElementById('certificate-badge').hidden = false;
              }
          })
          .catch(function () { sent = false; }); // нет сети — попробуем ещё раз
    }

    // Сколько секунд видео реально проиграно: сумма отрезков из video.played
    function playedSeconds() {
        var total = 0;
        for (var i = 0; i < video.played.length; i++) {
            total += video.played.end(i) - video.played.start(i);
        }
        return total;
    }

    function check() {
        if (!sent && video.duration && playedSeconds() / video.duration >= 0.9) send();
    }

    // timeupdate срабатывает несколько раз в секунду, пока видео играет;
    // ended — когда видео закончилось
    video.addEventListener('timeupdate', check);
    video.addEventListener('ended', check);
})();
