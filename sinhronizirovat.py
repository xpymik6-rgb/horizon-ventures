# -*- coding: utf-8 -*-
"""
Приводит сайт в порядок после добавления нового продукта или статьи.

    python sinhronizirovat.py            # проверить и починить
    python sinhronizirovat.py --tolko-proverka   # только показать дырки

Что делает:
  1. находит все страницы продуктов (файлы вида имя.html с разметкой SoftwareApplication
     или перечисленные в СПИСКЕ ниже) и строит из них единое меню;
  2. подставляет это меню и общий подвал на КАЖДУЮ страницу сайта;
  3. проверяет, что у каждой страницы продукта есть машинная разметка с ценой;
  4. проверяет, что у каждого продукта есть блок на главной и живое демо;
  5. пересобирает карту сайта;
  6. сообщает, чего не хватает, вместо того чтобы молча пропустить.

Порядок добавления нового продукта описан в скилле `produkt-na-sajt`.
"""
import io, os, re, sys, json, datetime

ПАПКА = os.path.dirname(os.path.abspath(__file__))
САЙТ = "https://horizonventures.app/"

# Продукты в том порядке, в каком они стоят в меню.
# Добавляя новый, впишите его сюда одной строкой.
ПРОДУКТЫ = [
    ("clickable-svg.html", "Clickable SVG"),
    ("smart-search.html",  "Smart Search"),
    ("table-export.html",  "Table Export"),
    ("word-import.html",   "Word Import"),
]

ТЕГ_GOOGLE = 'gtag/js?id=AW-18433232021'
СЧЁТЧИК = 'data-goatcounter="https://horizonventures.goatcounter.com/count"'


def меню(префикс):
    строки = ['      <a href="%s%s">%s</a>' % (префикс, ф, и) for ф, и in ПРОДУКТЫ]
    строки.append('      <a href="%sarticles.html">Articles</a>' % префикс)
    строки.append('      <a href="%schanges.html">Changes</a>' % префикс)
    строки.append('      <a href="%sabout.html">About</a>' % префикс)
    return "    <nav>\n" + "\n".join(строки) + "\n    </nav>"


def подвал_приложения(префикс):
    строки = ['        <li><a href="%s%s">%s</a></li>' % (префикс, ф, и) for ф, и in ПРОДУКТЫ]
    return "\n".join(строки)


def все_страницы():
    для_обхода = []
    for корень, папки, файлы in os.walk(ПАПКА):
        if ".git" in корень:
            continue
        for имя in sorted(файлы):
            # служебные файлы подтверждения прав на сайт не страницы: в них нет <head>
            if имя.endswith(".html") and not имя.startswith("google"):
                для_обхода.append(os.path.join(корень, имя))
    return для_обхода


def починить(только_проверка=False):
    замечания = []
    исправлено = {"меню": 0, "подвал": 0, "счётчик": 0}

    for путь in все_страницы():
        s = io.open(путь, encoding="utf-8").read()
        до = s
        префикс = "/" if 'href="/clickable-svg.html"' in s or путь.count(os.sep) > ПАПКА.count(os.sep) + 1 else ""

        # меню
        новое_меню = меню(префикс)
        if "<nav>" in s and новое_меню not in s:
            s = re.sub(r"    <nav>.*?</nav>", новое_меню, s, count=1, flags=re.S)
            исправлено["меню"] += 1

        # подвал: список приложений
        м = re.search(r'(<h3>Apps</h3>\s*<ul>)(.*?)(</ul>)', s, re.S)
        if м and м.group(2).count("<li>") != len(ПРОДУКТЫ):
            s = s[:м.start(2)] + "\n" + подвал_приложения(префикс) + "\n      " + s[м.end(2):]
            исправлено["подвал"] += 1

        # тег Google Рекламы
        if ТЕГ_GOOGLE not in s:
            s = s.replace("</head>",
                          '<script async src="https://www.googletagmanager.com/gtag/js?id=AW-18433232021"></script>\n'
                          '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}\n'
                          "gtag('js', new Date());gtag('config','AW-18433232021');</script>\n</head>", 1)

        # счётчик посещений
        if СЧЁТЧИК not in s:
            s = s.replace("</head>",
                          '<script %s\n        async src="//gc.zgo.at/count.js"></script>\n</head>' % СЧЁТЧИК, 1)
            исправлено["счётчик"] += 1

        if s != до and not только_проверка:
            io.open(путь, "w", encoding="utf-8").write(s)

    # проверки по продуктам
    главная = io.open(os.path.join(ПАПКА, "index.html"), encoding="utf-8").read()
    for файл, имя in ПРОДУКТЫ:
        путь = os.path.join(ПАПКА, файл)
        if not os.path.exists(путь):
            замечания.append("НЕТ СТРАНИЦЫ: " + файл)
            continue
        s = io.open(путь, encoding="utf-8").read()
        if "application/ld+json" not in s:
            замечания.append("нет машинной разметки: " + файл)
        elif '"SoftwareApplication"' not in s:
            замечания.append("в разметке нет описания приложения с ценой: " + файл)
        if 'id="demo' not in s:
            замечания.append("нет живого демо: " + файл + " (это наш главный козырь)")
        if файл not in главная:
            замечания.append("нет блока на главной: " + файл)
        # документация: ищем ссылку на раздел docs со страницы продукта
        if not re.search(r'href="[^"]*docs/[^"]*"', s):
            замечания.append("со страницы не ведёт ссылка на документацию: " + файл)

    # карта сайта
    if not только_проверка:
        сегодня = datetime.date.today().isoformat()
        адреса = sorted({САЙТ + ("" if os.path.relpath(п, ПАПКА).replace("\\", "/") == "index.html"
                                else os.path.relpath(п, ПАПКА).replace("\\", "/").replace("docs/index.html", "docs/"))
                         for п in все_страницы()})
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        xml += "".join('  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n' % (а, сегодня) for а in адреса)
        io.open(os.path.join(ПАПКА, "sitemap.xml"), "w", encoding="utf-8").write(xml + "</urlset>\n")
        print("карта сайта: %d страниц" % len(адреса))

    print("меню поправлено на страницах: %d" % исправлено["меню"])
    print("подвалов поправлено: %d" % исправлено["подвал"])
    print("счётчик добавлен на страниц: %d" % исправлено["счётчик"])

    if замечания:
        print("\nЧего не хватает:")
        for з in замечания:
            print("  • " + з)
    else:
        print("\nВсё на месте: у каждого продукта страница, разметка, демо, блок на главной и документация.")


if __name__ == "__main__":
    починить("--tolko-proverka" in sys.argv)
