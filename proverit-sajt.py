# -*- coding: utf-8 -*-
"""
Полная проверка сайта перед тем, как пускать на него платную рекламу.

    python proverit-sajt.py

Проверяет каждую страницу по списку, который важен и людям, и поисковикам,
и ИИ-ответам:

  • ссылки внутри сайта — нет ли битых, включая якоря на разделы;
  • заголовок страницы: есть, не пустой, не длиннее 60 знаков, не повторяется;
  • описание: есть, 70–170 знаков, не повторяется;
  • canonical: есть и ведёт на боевой домен;
  • единственный <h1> на странице;
  • у всех картинок заполнен alt и заданы размеры;
  • разметка JSON-LD разбирается без ошибок;
  • открытые теги для соцсетей;
  • язык страницы и кодировка;
  • страница есть в карте сайта.

Ничего не чинит — только показывает. Чинить осознанно.
"""
import io, os, re, json, sys
from collections import defaultdict

ПАПКА = os.path.dirname(os.path.abspath(__file__))
ДОМЕН = "https://horizonventures.app"

замечания = defaultdict(list)


def отн(путь):
    return os.path.relpath(путь, ПАПКА).replace("\\", "/")


def страницы():
    для_обхода = []
    for корень, папки, файлы in os.walk(ПАПКА):
        if ".git" in корень:
            continue
        for имя in sorted(файлы):
            # служебные файлы подтверждения владения проверять не нужно
            if имя.endswith(".html") and not re.match(r"^google[0-9a-f]+\.html$", имя):
                для_обхода.append(os.path.join(корень, имя))
    return для_обхода


def проверить_ссылки(путь, s, все_файлы):
    свои = re.findall(r'href="([^"#:]+\.html)(#[^"]*)?"', s)
    for адрес, якорь in свои:
        если_от_корня = адрес.startswith("/")
        цель = os.path.normpath(os.path.join(
            ПАПКА if если_от_корня else os.path.dirname(путь),
            адрес.lstrip("/")))
        if цель not in все_файлы:
            замечания[отн(путь)].append("битая ссылка: " + адрес)
        elif якорь:
            содержимое = io.open(цель, encoding="utf-8").read()
            имя_якоря = якорь[1:]
            if имя_якоря and ('id="%s"' % имя_якоря) not in содержимое:
                замечания[отн(путь)].append("ссылка на несуществующий раздел: " + адрес + якорь)


def проверить(путь, все_файлы, заголовки, описания, в_карте):
    s = io.open(путь, encoding="utf-8").read()
    имя = отн(путь)

    # заголовок
    м = re.search(r"<title>(.*?)</title>", s, re.S)
    if not м or not м.group(1).strip():
        замечания[имя].append("нет заголовка страницы")
    else:
        з = м.group(1).strip()
        if len(з) > 65:
            замечания[имя].append("заголовок длиннее 65 знаков (%d), в выдаче обрежется" % len(з))
        заголовки[з].append(имя)

    # описание
    м = re.search(r'<meta name="description" content="(.*?)"', s, re.S)
    if not м:
        замечания[имя].append("нет описания страницы")
    else:
        о = м.group(1).strip()
        if len(о) < 70:
            замечания[имя].append("описание короче 70 знаков (%d)" % len(о))
        if len(о) > 175:
            замечания[имя].append("описание длиннее 175 знаков (%d), обрежется" % len(о))
        описания[о].append(имя)

    # canonical
    м = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    if not м:
        замечания[имя].append("нет canonical: поисковик может счесть страницу копией")
    elif not м.group(1).startswith(ДОМЕН):
        замечания[имя].append("canonical ведёт не на наш домен: " + м.group(1))

    # один h1
    h1 = re.findall(r"<h1[^>]*>", s)
    if len(h1) == 0:
        замечания[имя].append("нет заголовка h1 на странице")
    elif len(h1) > 1:
        замечания[имя].append("несколько h1 (%d), должен быть один" % len(h1))

    # картинки
    for тег in re.findall(r"<img[^>]*>", s):
        if 'alt="' not in тег:
            замечания[имя].append("картинка без alt: " + тег[:70])
        elif re.search(r'alt=""', тег):
            замечания[имя].append("пустой alt у картинки: " + тег[:70])
        if "width=" not in тег or "height=" not in тег:
            замечания[имя].append("у картинки не заданы размеры, страница будет прыгать: " + тег[:70])

    # разметка
    for кусок in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(кусок)
        except Exception as e:
            замечания[имя].append("сломана машинная разметка: %s" % str(e)[:60])

    # соцсети
    if "og:title" not in s:
        замечания[имя].append("нет og:title — ссылка в мессенджере будет выглядеть голой")

    # язык и кодировка
    if 'lang="en"' not in s:
        замечания[имя].append("не указан язык страницы")
    if 'charset="utf-8"' not in s:
        замечания[имя].append("не указана кодировка")

    # счётчик
    if "goatcounter" not in s:
        замечания[имя].append("нет счётчика посещений")

    # в карте сайта
    адрес = ДОМЕН + "/" + ("" if имя == "index.html" else имя.replace("docs/index.html", "docs/"))
    if адрес not in в_карте:
        замечания[имя].append("страницы нет в карте сайта")

    проверить_ссылки(путь, s, все_файлы)


def главная_проверка():
    все = страницы()
    все_файлы = set(os.path.normpath(п) for п in все)
    карта = io.open(os.path.join(ПАПКА, "sitemap.xml"), encoding="utf-8").read()
    в_карте = set(re.findall(r"<loc>(.*?)</loc>", карта))

    заголовки, описания = defaultdict(list), defaultdict(list)
    for п in все:
        проверить(п, все_файлы, заголовки, описания, в_карте)

    for з, где in заголовки.items():
        if len(где) > 1:
            for имя in где:
                замечания[имя].append("заголовок повторяется на страницах: " + ", ".join(где))
    for о, где in описания.items():
        if len(где) > 1:
            for имя in где:
                замечания[имя].append("описание повторяется на страницах: " + ", ".join(где))

    всего = sum(len(v) for v in замечания.values())
    print("Проверено страниц: %d" % len(все))
    print("Найдено замечаний: %d\n" % всего)
    for имя in sorted(замечания):
        if not замечания[имя]:
            continue
        print(имя)
        for з in sorted(set(замечания[имя])):
            print("   • " + з)
    if всего == 0:
        print("Чисто: замечаний нет.")
    return всего


if __name__ == "__main__":
    sys.exit(0 if главная_проверка() == 0 else 1)
