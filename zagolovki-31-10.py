# Заголовки четырёх статей под формулировки из Search Console (31.10.2026):
# «confluence link to image», «image map», «page restrictions confluence»,
# «confluence page list», «visio to confluence». Меняются title, h1, headline, og:title.
import json, os, re

П = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')

ПРАВКИ = {
    'confluence-clickable-image.html': 'Confluence Cloud: link to an image, clickable image and image map',
    'why-cannot-see-confluence-page.html': "Confluence page restrictions: why someone can't see a page",
    'list-confluence-pages-without-cql.html': 'Confluence page list: show a list of pages without writing CQL',
    'insert-visio-diagram-confluence.html': 'Visio to Confluence Cloud: how to insert a Visio diagram',
}

for файл, заголовок in ПРАВКИ.items():
    assert len(заголовок) <= 70, (файл, len(заголовок))
    p = os.path.join(П, файл)
    s = open(p, encoding='utf-8').read()
    старый = re.search(r'<title>(.*?)</title>', s).group(1)
    s = s.replace('<title>%s</title>' % старый, '<title>%s</title>' % заголовок, 1)
    # в JSON-LD апостроф и кавычки уже экранированы так же, как в старом заголовке
    s = s.replace('"headline": "%s"' % старый, '"headline": "%s"' % заголовок, 1)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + заголовок, s, count=1)
    s = re.sub(r'<h1>.*?</h1>', '<h1>%s</h1>' % заголовок, s, count=1)
    for б in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        json.loads(б)
    assert '—' not in s and '–' not in s
    open(p, 'w', encoding='utf-8').write(s)
    print('ok', файл, '|', старый, '->', заголовок)
