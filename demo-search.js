/* Живое демо Smart Search.
   Человек выбирает условия из выпадающих списков, видит фразу обычным языком
   и список страниц, который пересобирается сразу же — как макет в Confluence. */

(function () {
  const корень = document.querySelector('#demo2');
  if (!корень) return;

  const выборПространства = корень.querySelector('#ss-space');
  const выборМетки        = корень.querySelector('#ss-label');
  const выборДавности     = корень.querySelector('#ss-age');
  const сортировка        = корень.querySelector('#ss-sort');
  const фраза   = корень.querySelector('#ss-sentence');
  const итог    = корень.querySelector('#ss-summary');
  const тело    = корень.querySelector('#ss-rows');
  const пусто   = корень.querySelector('#ss-empty');

  /* Страницы вымышленной вики. Дни — сколько назад страницу трогали. */
  const СТРАНИЦЫ = [
    ['Payments API runbook',            'Engineering', 'runbook',    2],
    ['Ledger service overview',         'Engineering', 'reference',  9],
    ['On-call handbook',                'Engineering', 'runbook',   24],
    ['Deploy checklist',                'Engineering', 'process',   41],
    ['Legacy SOAP gateway',             'Engineering', 'reference', 690],
    ['Windows XP kiosk setup',          'IT',          'howto',     902],
    ['VPN troubleshooting',             'IT',          'howto',      63],
    ['Laptop request process',          'IT',          'process',   118],
    ['Office printer, floor 3',         'IT',          'howto',     540],
    ['Onboarding: first week',          'People',      'onboarding', 12],
    ['Onboarding: engineering',         'People',      'onboarding', 35],
    ['Expense policy 2023',             'People',      'policy',    610],
    ['Remote work policy',              'People',      'policy',     88],
    ['Interview scorecards',            'People',      'process',   210],
    ['Quarterly close, step by step',   'Finance',     'process',    17],
    ['Vendor onboarding',               'Finance',     'process',   152],
    ['Old invoicing system notes',      'Finance',     'reference', 780],
    ['Travel reimbursement',            'Finance',     'policy',    240],
    ['Incident review: 12 March',       'Engineering', 'postmortem', 55],
    ['Incident review: October outage', 'Engineering', 'postmortem',430],
    ['Data retention rules',            'Legal',       'policy',     74],
    ['Contract templates',              'Legal',       'reference', 320],
    ['GDPR request handling',           'Legal',       'process',   134],
    ['Brand assets',                    'Marketing',   'reference', 265],
    ['Launch checklist',                'Marketing',   'process',    28],
  ];

  function kogda(дней) {
    if (дней < 14) return дней + ' days ago';
    if (дней < 60) return Math.round(дней / 7) + ' weeks ago';
    if (дней < 730) return Math.round(дней / 30) + ' months ago';
    return Math.round(дней / 365) + ' years ago';
  }

  function sobrat() {
    const пространство = выборПространства.value;
    const метка        = выборМетки.value;
    const давность     = parseInt(выборДавности.value, 10);

    let строки = СТРАНИЦЫ.filter(с =>
      (пространство === 'any' || с[1] === пространство) &&
      (метка === 'any'        || с[2] === метка) &&
      (давность === 0         || с[3] >= давность));

    строки.sort((а, б) => сортировка.value === 'oldest' ? б[3] - а[3] : а[3] - б[3]);

    /* Фраза обычным языком — то, чем приложение отличается от языка запросов */
    const части = ['Pages'];
    части.push(пространство === 'any' ? 'in any space' : 'in ' + пространство);
    if (метка !== 'any') части.push('labelled ' + метка);
    части.push(давность === 0 ? 'updated at any time' : 'not updated for ' + давность + ' days');
    фраза.textContent = части.join(', ') + '.';

    итог.textContent = строки.length === 1 ? '1 page' : строки.length + ' pages';

    тело.innerHTML = '';
    for (const [имя, простр, мет, дней] of строки) {
      const ряд = document.createElement('tr');
      ряд.innerHTML =
        '<td class="ss-name">' + имя + '</td>' +
        '<td>' + простр + '</td>' +
        '<td><span class="ss-tag">' + мет + '</span></td>' +
        '<td class="ss-when">' + kogda(дней) + '</td>';
      тело.appendChild(ряд);
    }
    пусто.hidden = строки.length > 0;
  }

  [выборПространства, выборМетки, выборДавности, сортировка]
    .forEach(э => э.addEventListener('change', sobrat));

  корень.querySelector('#ss-preset-stale').addEventListener('click', () => {
    выборПространства.value = 'any'; выборМетки.value = 'any';
    выборДавности.value = '365'; сортировка.value = 'oldest'; sobrat();
  });
  корень.querySelector('#ss-preset-onboarding').addEventListener('click', () => {
    выборПространства.value = 'any'; выборМетки.value = 'onboarding';
    выборДавности.value = '0'; сортировка.value = 'newest'; sobrat();
  });

  sobrat();
})();
