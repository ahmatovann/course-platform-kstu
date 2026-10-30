# Ответственная: Нургуль (Ф-13)
# Автоматический аватар в стиле пиксель-арт, если человек не загрузил свой.
# Рисуется прямо на сервере, без интернета и без сторонних сайтов.
import hashlib

# Палитра: цвет пикселей подбирается из этого списка
COLORS = ['#2533D9', '#E0457B', '#1F9D6B', '#F08A24', '#7C4DFF', '#0E8FB0']


def pixel_avatar_svg(seed, size=96):
    # 1. Из почты получаем «отпечаток» — длинное число (хеш MD5).
    #    Одна и та же почта всегда даёт один и тот же рисунок.
    digest = hashlib.md5(seed.lower().encode('utf-8')).digest()

    # 2. Цвет выбираем по первому байту отпечатка
    color = COLORS[digest[0] % len(COLORS)]

    # 3. Рисуем сетку 8×8 клеток. Левую половину (4 столбца) заполняем
    #    по битам отпечатка, правую делаем зеркальной — получается
    #    симметричный «персонаж», как в старых 8-битных играх.
    cells = []
    for row in range(8):
        for col in range(4):
            bit = (digest[1 + row] >> col) & 1
            if bit:
                cells.append((col, row))
                cells.append((7 - col, row))

    # 4. Собираем картинку в формате SVG: фон и квадратики-пиксели
    rects = ''.join(
        f'<rect x="{x}" y="{y}" width="1" height="1"/>' for x, y in cells
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 10 10" '
        f'width="{size}" height="{size}" shape-rendering="crispEdges" '
        f'role="img" aria-label="Аватар">'
        f'<rect x="-1" y="-1" width="10" height="10" fill="#FFD84D"/>'
        f'<g fill="{color}">{rects}</g></svg>'
    )
