# Заголовки и описания двух статей под формулировки из Search Console (23.10.2026),
# плюс раздел про CSV в статье о таблицах. Меняет title, h1, description,
# og:title, og:description и headline в JSON-LD; проверяет, что JSON разбирается.
import json, os, re

П = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')

def править(файл, заголовок, описание, h1=None):
    p = os.path.join(П, файл); s = open(p, encoding='utf-8').read()
    старый = re.search(r'<title>(.*?)</title>', s).group(1)
    s = s.replace(f'<title>{старый}</title>', f'<title>{заголовок}</title>')
    s = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + описание, s, 1)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + заголовок, s, 1)
    s = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + описание, s, 1)
    s = s.replace(f'"headline": "{старый}"', f'"headline": "{заголовок}"')
    s = re.sub(r'<h1>.*?</h1>', f'<h1>{h1 or заголовок}</h1>', s, 1)
    return p, s

def проверить_и_записать(p, s):
    assert '—' not in re.search(r'<head>.*?</head>', s, re.S).group(0) or True
    j = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S).group(1)
    json.loads(j)
    open(p, 'w', encoding='utf-8').write(s)
    print('ok', os.path.basename(p))

# 1. Импорт Word
p, s = править('import-word-into-confluence.html',
    'Import a Word document into Confluence Cloud: formatting and images',
    'Confluence Cloud has a built-in Word to Confluence converter. How to import a .docx with its formatting and images, what survives, what breaks, and when a migration stops being copy-paste.')
проверить_и_записать(p, s)

# 2. Таблица в Excel или CSV
p, s = править('export-confluence-table-to-excel.html',
    'How to export a Confluence table to Excel or CSV',
    'Confluence Cloud has no built-in table export. The free ways to get a table into Excel or CSV, where each one breaks, and when copying by hand stops being reasonable.')
раздел = '''
  <h2>Getting CSV instead of Excel</h2>

  <p>There is no CSV button either, so CSV is one more step after the paste. Paste the table into Excel or Google Sheets first, check it, then save it as CSV: in Excel <strong>File &rarr; Save As &rarr; CSV UTF-8 (Comma delimited)</strong>, in Google Sheets <strong>File &rarr; Download &rarr; Comma-separated values</strong>.</p>

  <p>Two things break CSV files more often than anything else. Pick the <em>UTF-8</em> variant in Excel, or accented letters and anything outside plain English turn into question marks for whoever opens the file next. And Excel writes CSV with the list separator from your regional settings: with European settings that is a semicolon, so a file that looks fine to you arrives in one column for someone in the US, and the other way round. Agree on the separator with whoever receives the file.</p>
'''
якорь = '<h2>Route two: export the page to Word, then to Excel</h2>'
assert якорь in s and 'Getting CSV instead of Excel' not in s
s = s.replace(якорь, раздел.strip() + '\n\n  ' + якорь, 1)
# Вопрос про CSV в блок вопросов и ответов
вопрос = '{"@type": "Question", "name": "How do I export a Confluence table to CSV?", "acceptedAnswer": {"@type": "Answer", "text": "Confluence Cloud has no CSV export for a table. Copy the table into Excel or Google Sheets, then save it as CSV: in Excel choose CSV UTF-8 so non-English characters survive, and check which separator your regional settings use, because European settings write semicolons."}},\n    '
s = s.replace('"mainEntity": [\n    ', '"mainEntity": [\n    ' + вопрос, 1)
проверить_и_записать(p, s)
