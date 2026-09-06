# -*- coding: utf-8 -*-
"""
Публикация статьи на сайте одной командой.

    python opublikovat.py docs/имя-статьи.html "Заголовок ссылки" "Описание для главной"

Что делает по шагам:
  1. проверяет, что машинная разметка в статье не сломана;
  2. ставит ссылку на статью в раздел статей на главной;
  3. пересобирает карту сайта;
  4. дописывает статью в llms.txt — файл для ИИ;
  5. делает коммит и отправляет на сайт;
  6. сообщает поисковикам через IndexNow.

Всё, что раньше делалось руками восемью действиями.
"""
import io, os, re, sys, json, datetime, subprocess, urllib.request

ПАПКА = os.path.dirname(os.path.abspath(__file__))
САЙТ = "https://horizonventures.app/"


def шаг(текст):
    print("  " + текст)


def проверить_razmetku(путь):
    s = io.open(путь, encoding="utf-8").read()
    куски = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if not куски:
        raise SystemExit("СТОП: в статье нет машинной разметки, поисковики её не поймут")
    типы = []
    for к in куски:
        д = json.loads(к)  # упадёт, если JSON сломан
        типы += [э.get("@type") for э in д.get("@graph", [д])]
    шаг("разметка в порядке: " + ", ".join(t for t in типы if t))
    заголовок = re.search(r"<title>(.*?)</title>", s, re.S)
    return заголовок.group(1).strip() if заголовок else ""


def ссылка_на_главной(отн, подпись, описание):
    p = os.path.join(ПАПКА, "index.html")
    g = io.open(p, encoding="utf-8").read()
    if отн in g:
        шаг("ссылка на главной уже есть")
        return
    пункт = ('      <li>\n'
             '        <h3><a href="%s">%s</a></h3>\n'
             '        <p>%s</p>\n'
             '      </li>\n' % (отн, подпись, описание))
    якорь = '    <ul class="facts">'
    место = g.find('<section id="replacing">')
    if место == -1:
        шаг("ВНИМАНИЕ: раздел статей на главной не найден, ссылку не поставил")
        return
    вставка = g.find(якорь, место)
    g = g[:вставка + len(якорь)] + "\n" + пункт + g[вставка + len(якорь):]
    io.open(p, "w", encoding="utf-8").write(g)
    шаг("ссылка на главной поставлена")


def собрать_адреса():
    адреса = []
    for корень, папки, файлы in os.walk(ПАПКА):
        if ".git" in корень:
            continue
        for имя in sorted(файлы):
            if имя.endswith(".html"):
                отн = os.path.relpath(os.path.join(корень, имя), ПАПКА).replace("\\", "/")
                адреса.append(САЙТ + ("" if отн == "index.html" else отн.replace("docs/index.html", "docs/")))
    return sorted(set(адреса))


def карта_сайта(адреса):
    сегодня = datetime.date.today().isoformat()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join('  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n' % (а, сегодня) for а in адреса)
    xml += "</urlset>\n"
    io.open(os.path.join(ПАПКА, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    шаг("карта сайта пересобрана: %d страниц" % len(адреса))


def дописать_llms(отн, подпись, описание):
    p = os.path.join(ПАПКА, "llms.txt")
    l = io.open(p, encoding="utf-8").read()
    if отн in l:
        шаг("в файле для ИИ уже есть")
        return
    строка = "- [%s](%s%s): %s\n" % (подпись, САЙТ, отн, описание)
    io.open(p, "w", encoding="utf-8").write(l.replace("## Company", строка + "\n## Company", 1))
    шаг("файл для ИИ дополнен")


def выложить(подпись):
    имя = ["-c", "user.name=Mikhail Klimenko", "-c", "user.email=support@horizonventures.app"]
    subprocess.run(["git", "add", "-A"], cwd=ПАПКА, check=True)
    сообщение = "Статья: %s\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>" % подпись
    subprocess.run(["git"] + имя + ["commit", "-q", "-m", сообщение], cwd=ПАПКА)
    subprocess.run(["git"] + имя + ["pull", "--rebase", "-q", "origin", "main"], cwd=ПАПКА)
    subprocess.run(["git", "push", "-q", "origin", "main"], cwd=ПАПКА, check=True)
    шаг("выложено на сайт")


def сообщить_poiskovikam(адреса):
    ключ = io.open(os.path.join(ПАПКА, "indexnow-key.txt"), encoding="utf-8").read().strip()
    данные = {"host": "horizonventures.app", "key": ключ,
              "keyLocation": САЙТ + ключ + ".txt", "urlList": адреса}
    з = urllib.request.Request("https://api.indexnow.org/indexnow",
                               data=json.dumps(данные).encode(), method="POST",
                               headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(з, timeout=40) as о:
            шаг("поисковики уведомлены (ответ %s)" % о.status)
    except Exception as e:
        шаг("поисковикам сообщить не вышло: %s" % str(e)[:80])


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    отн = sys.argv[1].replace("\\", "/")
    подпись, описание = sys.argv[2], sys.argv[3]
    путь = os.path.join(ПАПКА, отн)
    if not os.path.exists(путь):
        raise SystemExit("СТОП: нет файла " + путь)

    print("Публикую: " + отн)
    проверить_razmetku(путь)
    ссылка_на_главной(отн, подпись, описание)
    адреса = собрать_адреса()
    карта_сайта(адреса)
    дописать_llms(отн, подпись, описание)
    выложить(подпись)
    сообщить_poiskovikam(адреса)
    print("Готово: " + САЙТ + отн)
