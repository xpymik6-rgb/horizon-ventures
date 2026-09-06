# -*- coding: utf-8 -*-
"""
Чинит то, что находит proverit-sajt.py в служебной части страниц:
canonical, теги для соцсетей, слишком длинные заголовки и описания,
отсутствующие описания у страниц вроде privacy и terms.

    python pochinit-meta.py

Сам текст статей не трогает: только то, что видят поисковики и мессенджеры.
"""
import io, os, re

ПАПКА = os.path.dirname(os.path.abspath(__file__))
ДОМЕН = "https://horizonventures.app"

# описания для служебных страниц, у которых их нет
ОПИСАНИЯ = {
    "docs/privacy.html": "Privacy statement for Clickable SVG for Confluence: what the app reads, what it stores, and why nothing leaves your Atlassian site.",
    "docs/terms.html": "Terms of use for Clickable SVG for Confluence: licence, support expectations, liability and how the app is billed through Atlassian.",
    "docs/smart-search/privacy.html": "Privacy statement for Smart Search for Confluence: the app reads pages inside your own site, stores nothing of its own and sends nothing to the vendor.",
    "docs/smart-search/terms.html": "Terms of use for Smart Search for Confluence: licence, support, liability and billing through the Atlassian Marketplace.",
    "docs/table-export/privacy.html": "Privacy statement for Table Export for Confluence: tables are read and converted inside your own Atlassian site, and no content is sent to the vendor.",
    "docs/table-export/terms.html": "Terms of use for Table Export for Confluence: licence, support, liability and billing through the Atlassian Marketplace.",
    "docs/word-import/privacy.html": "Privacy statement for Word Import for Confluence: documents are read in your browser, turned into pages through Confluence, and never uploaded to the vendor.",
    "docs/word-import/terms.html": "Terms of use for Word Import for Confluence: licence, support, liability and billing through the Atlassian Marketplace.",
}


def отн(путь):
    return os.path.relpath(путь, ПАПКА).replace("\\", "/")


def адрес_страницы(имя):
    return ДОМЕН + "/" + ("" if имя == "index.html" else имя.replace("docs/index.html", "docs/"))


def укоротить_заголовок(з):
    """Режем по смысловой границе, а не посреди слова."""
    for разделитель in [" — ", ", and where", ": ", " and what", ", and "]:
        if разделитель in з and len(з.split(разделитель)[0]) >= 25:
            коротко = з.split(разделитель)[0].strip()
            if len(коротко) <= 65:
                return коротко
    if len(з) <= 65:
        return з
    # последнее средство: обрезаем по слову
    слова, собрано = з.split(), ""
    for с in слова:
        if len(собрано) + len(с) + 1 > 62:
            break
        собрано += (" " if собрано else "") + с
    return собрано


def укоротить_описание(о):
    if len(о) <= 175:
        return о
    # пробуем закончить на границе предложения
    куски = re.split(r"(?<=[.!?]) ", о)
    собрано = ""
    for к in куски:
        if len(собрано) + len(к) + 1 > 172:
            break
        собрано += (" " if собрано else "") + к
    if len(собрано) >= 70:
        return собрано
    слова, собрано = о.split(), ""
    for с in слова:
        if len(собрано) + len(с) + 1 > 170:
            break
        собрано += (" " if собрано else "") + с
    return собрано.rstrip(",;:") + "."


def починить(путь):
    имя = отн(путь)
    s = io.open(путь, encoding="utf-8").read()
    до = s

    # заголовок
    м = re.search(r"<title>(.*?)</title>", s, re.S)
    заголовок = м.group(1).strip() if м else ""
    if заголовок and len(заголовок) > 65:
        новый = укоротить_заголовок(заголовок)
        s = s.replace("<title>%s</title>" % м.group(1), "<title>%s</title>" % новый, 1)
        заголовок = новый

    # описание
    м = re.search(r'<meta name="description" content="([^"]*)"', s)
    if м:
        описание = м.group(1).strip()
        if len(описание) > 175:
            новое = укоротить_описание(описание)
            s = s.replace(м.group(0), '<meta name="description" content="%s"' % новое, 1)
            описание = новое
    else:
        описание = ОПИСАНИЯ.get(имя, "")
        if описание:
            s = s.replace("</head>", '<meta name="description" content="%s">\n</head>' % описание, 1)

    # canonical
    if 'rel="canonical"' not in s:
        s = s.replace("</head>", '<link rel="canonical" href="%s">\n</head>' % адрес_страницы(имя), 1)

    # теги для соцсетей
    if "og:title" not in s and заголовок:
        блок = ('<meta property="og:title" content="%s">\n'
                '<meta property="og:description" content="%s">\n'
                '<meta property="og:type" content="website">\n'
                '<meta property="og:url" content="%s">\n') % (
            заголовок.replace('"', "&quot;"), описание.replace('"', "&quot;"), адрес_страницы(имя))
        s = s.replace("</head>", блок + "</head>", 1)

    if s != до:
        io.open(путь, "w", encoding="utf-8").write(s)
        return True
    return False


if __name__ == "__main__":
    починено = 0
    for корень, папки, файлы in os.walk(ПАПКА):
        if ".git" in корень:
            continue
        for имя in sorted(файлы):
            if имя.endswith(".html") and починить(os.path.join(корень, имя)):
                починено += 1
    print("страниц поправлено:", починено)
