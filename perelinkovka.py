# Перекрёстные ссылки со старых статей на новые по смыслу: Google по ним
# понимает тему страницы, а читатель находит продолжение. Ссылка добавляется
# в строку «Related» внизу статьи; если её нет, строка создаётся.
# Уже стоящую ссылку второй раз не ставит.
#   python perelinkovka.py
import os, re

ПАПКА = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
СВЯЗИ = [
    ('import-word-into-confluence', 'confluence-word-import-missing-content', 'why the built-in Word import drops text and images'),
    ('split-word-document-confluence-pages', 'confluence-word-import-missing-content', 'why the built-in Word import drops text and images'),
    ('import-word-existing-confluence-page', 'confluence-word-import-missing-content', 'why the built-in Word import drops text and images'),
    ('export-confluence-table-to-excel', 'confluence-table-paste-excel-merged-cells', 'why a pasted table breaks in Excel, tested step by step'),
    ('sum-column-confluence-table', 'confluence-table-paste-excel-merged-cells', 'why a Confluence table breaks when pasted into Excel'),
    ('table-exporter-alternative', 'confluence-table-paste-excel-merged-cells', 'why a Confluence table breaks when pasted into Excel'),
    ('confluence-svg-flat-image', 'drawio-svg-text-is-not-svg', 'why draw.io labels break in an exported SVG'),
    ('confluence-clickable-image', 'drawio-svg-text-is-not-svg', 'why draw.io labels break in an exported SVG'),
    ('diagrams-in-confluence-compared', 'drawio-svg-text-is-not-svg', 'why draw.io labels break in an exported SVG'),
    ('clickable-diagram-confluence', 'drawio-svg-text-is-not-svg', 'why draw.io labels break in an exported SVG'),
    ('list-confluence-pages-without-cql', 'confluence-cql-cheat-sheet', 'a CQL cheat sheet with tested queries'),
    ('find-stale-pages-confluence', 'confluence-cql-cheat-sheet', 'the CQL queries for stale pages, tested'),
    ('cql-search-alternative', 'confluence-cql-cheat-sheet', 'a CQL cheat sheet with tested queries'),
    ('confluence-live-search-macro', 'confluence-cql-cheat-sheet', 'a CQL cheat sheet with tested queries'),
]

for откуда, куда, текст in СВЯЗИ:
    п = os.path.join(ПАПКА, откуда + '.html')
    s = open(п, encoding='utf-8').read()
    if f'/docs/{куда}.html' in s:
        print('уже есть:', откуда, '→', куда); continue
    ссылка = f'<a href="/docs/{куда}.html">{текст}</a>'
    м = re.search(r'<p class="more">(.*?)</p>', s, re.S)
    if м:
        старое = м.group(0)
        новое = старое[:-4].rstrip() + f' Also: {ссылка}.</p>'
        s = s.replace(старое, новое, 1)
    else:
        конец = s.rfind('</div>\n</main>')
        if конец < 0:
            print('НЕ НАШЁЛ МЕСТО:', откуда); continue
        s = s[:конец] + f'  <p class="more">Related: {ссылка}.</p>\n\n' + s[конец:]
    open(п, 'w', encoding='utf-8').write(s)
    print('добавлено:', откуда, '→', куда)
