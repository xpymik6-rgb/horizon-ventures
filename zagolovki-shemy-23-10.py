# Заголовки трёх статей про схемы под формулировки из Search Console (23.10.2026):
# «diagram in confluence», «confluence free diagram plugin», «plantuml confluence»,
# «confluence mermaid». Слово «alternative» остаётся в описании: оно ловит тех,
# у кого приложение на уходящей платформе Connect.
import json, os, re

П = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')

ПРАВКИ = [
    ('diagrams-in-confluence-compared.html',
     'Diagrams in Confluence: free and paid diagram apps compared',
     'Diagrams in Confluence: free and paid options, honestly compared',
     'How to add diagrams to Confluence Cloud: draw.io, Mermaid, PlantUML and image-based options compared, which diagram plugins are free, who can edit them and what survives.'),
    ('plantuml-confluence-alternative.html',
     'PlantUML in Confluence Cloud: free and paid options',
     'PlantUML in Confluence Cloud: what to use now',
     'How to render PlantUML diagrams in Confluence Cloud: the free options first, the apps that do it, and an alternative if your PlantUML app runs on the retiring Connect platform.'),
    ('mermaid-confluence-alternative.html',
     'Mermaid in Confluence Cloud: free and paid options',
     'Mermaid in Confluence Cloud: what to use now',
     'How to render Mermaid diagrams in Confluence Cloud, which does not do it natively: the free options first, the apps, and an alternative if your Mermaid app runs on the retiring Connect platform.'),
]

for файл, заголовок, h1, описание in ПРАВКИ:
    p = os.path.join(П, файл); s = open(p, encoding='utf-8').read()
    старый = re.search(r'<title>(.*?)</title>', s).group(1)
    s = s.replace(f'<title>{старый}</title>', f'<title>{заголовок}</title>')
    s = s.replace(f'"headline": "{старый}"', f'"headline": "{заголовок}"')
    s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + заголовок, s, count=1)
    s = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + описание, s, count=1)
    s = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + описание, s, count=1)
    s = re.sub(r'<h1>.*?</h1>', f'<h1>{h1}</h1>', s, count=1)
    for б in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        json.loads(б)
    assert '—' not in s and '–' not in s
    open(p, 'w', encoding='utf-8').write(s)
    print('ok', файл, '|', старый, '→', заголовок)
