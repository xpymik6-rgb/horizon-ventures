/* Живое демо Table Export.
   Показывает то, из-за чего люди и покупают такие приложения: при копировании
   таблицы с объединёнными ячейками колонки уезжают, и файл выглядит правильным,
   пока кто-нибудь не посчитает сумму. Здесь это видно рядом, на одних данных. */

(function () {
  const корень = document.querySelector('#demo3');
  if (!корень) return;

  const переключатели = корень.querySelectorAll('[data-rezhim]');
  const превью   = корень.querySelector('#te-preview');
  const пояснение = корень.querySelector('#te-note');
  const скачать  = корень.querySelector('#te-download');
  const итог     = корень.querySelector('#te-summary');

  /* Таблица, как она выглядит на странице вики: столбец «Quarter» объединён
     по три строки, столбец «Owner» — по две. Это самый обычный бюджет. */
  const СТРОКИ = [
    { quarter: 'Q1', quarterRows: 3, item: 'Cloud hosting',   owner: 'Platform', ownerRows: 2, plan: 12000, fact: 11430 },
    { quarter: null,                 item: 'Monitoring',      owner: null,        plan: 3000,  fact: 3120  },
    { quarter: null,                 item: 'Support licences', owner: 'IT', ownerRows: 1, plan: 5400,  fact: 5400  },
    { quarter: 'Q2', quarterRows: 3, item: 'Cloud hosting',   owner: 'Platform', ownerRows: 2, plan: 12000, fact: 12980 },
    { quarter: null,                 item: 'Monitoring',      owner: null,        plan: 3000,  fact: 2860  },
    { quarter: null,                 item: 'Support licences', owner: 'IT', ownerRows: 1, plan: 5400,  fact: 6100  },
  ];

  /* ── таблица на «странице Confluence» ─────────────────────── */

  function narisovat_tablicu() {
    const тело = корень.querySelector('#te-rows');
    тело.innerHTML = '';
    for (const с of СТРОКИ) {
      const ряд = document.createElement('tr');
      if (с.quarter) ряд.innerHTML += '<td rowspan="' + с.quarterRows + '" class="te-merged">' + с.quarter + '</td>';
      ряд.innerHTML += '<td>' + с.item + '</td>';
      if (с.owner) ряд.innerHTML += '<td rowspan="' + (с.ownerRows || 1) + '" class="te-merged">' + с.owner + '</td>';
      ряд.innerHTML += '<td class="te-num">' + с.plan.toLocaleString('en-US') + '</td>' +
                       '<td class="te-num">' + с.fact.toLocaleString('en-US') + '</td>';
      тело.appendChild(ряд);
    }
  }

  /* ── два способа получить из неё файл ─────────────────────── */

  // Как получается при обычном копировании: объединённая ячейка существует
  // один раз, поэтому в следующих строках колонок меньше и всё съезжает влево.
  function kak_pri_kopirovanii() {
    const строки = [['Quarter', 'Item', 'Owner', 'Plan', 'Actual']];
    for (const с of СТРОКИ) {
      const ряд = [];
      if (с.quarter) ряд.push(с.quarter);
      ряд.push(с.item);
      if (с.owner) ряд.push(с.owner);
      ряд.push(String(с.plan), String(с.fact));
      строки.push(ряд);
    }
    return строки;
  }

  // Как делает приложение: значение объединённой ячейки повторяется в каждой
  // строке, которую она накрывала, и колонки остаются на местах.
  function kak_delaet_prilozhenie() {
    const строки = [['Quarter', 'Item', 'Owner', 'Plan', 'Actual']];
    let квартал = null, владелец = null;
    for (const с of СТРОКИ) {
      if (с.quarter) квартал = с.quarter;
      if (с.owner) владелец = с.owner;
      строки.push([квартал, с.item, владелец, String(с.plan), String(с.fact)]);
    }
    return строки;
  }

  function v_csv(строки) {
    return строки.map(р => р.map(з => /[",]/.test(з) ? '"' + з.replace(/"/g, '""') + '"' : з).join(',')).join('\n');
  }

  /* ── показ ────────────────────────────────────────────────── */

  let режим = 'app';

  function pokazat() {
    const строки = режим === 'copy' ? kak_pri_kopirovanii() : kak_delaet_prilozhenie();
    const текст = v_csv(строки);

    // раскрашиваем: в режиме копирования подсвечиваем короткие строки
    превью.innerHTML = '';
    строки.forEach((р, номер) => {
      const линия = document.createElement('div');
      линия.className = 'te-line' + (номер === 0 ? ' te-head' : '') +
                        (номер > 0 && р.length < 5 ? ' te-broken' : '');
      линия.textContent = р.join(',');
      превью.appendChild(линия);
    });

    if (режим === 'copy') {
      const битых = строки.slice(1).filter(р => р.length < 5).length;
      пояснение.className = 'te-note te-bad';
      пояснение.textContent = битых + ' of ' + (строки.length - 1) +
        ' rows have fewer columns than the header. In a spreadsheet the values after the gap shift left: ' +
        'the owner column fills with numbers and the totals quietly stop meaning anything.';
      итог.textContent = 'Sum of the Plan column in this file: ' + posschitat(строки, 3) +
        ' instead of 40,800.';
    } else {
      пояснение.className = 'te-note te-good';
      пояснение.textContent = 'Every row has all five columns: the merged value is repeated for each row it covered. ' +
        'The file opens as a normal table and the totals are correct.';
      итог.textContent = 'Sum of the Plan column in this file: ' + posschitat(строки, 3) + '.';
    }

    скачать.onclick = () => skachat(текст, режим === 'copy' ? 'budget-copied-by-hand.csv' : 'budget-table-export.csv');
  }

  // считаем колонку так, как её посчитает таблица: по номеру столбца, а не по смыслу
  function posschitat(строки, столбец) {
    let сумма = 0;
    for (const р of строки.slice(1)) {
      const з = parseFloat((р[столбец] || '').replace(/[^0-9.-]/g, ''));
      if (!isNaN(з)) сумма += з;
    }
    return сумма.toLocaleString('en-US');
  }

  function skachat(текст, имя) {
    const blob = new Blob([текст], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const ссылка = document.createElement('a');
    ссылка.href = url; ссылка.download = имя;
    document.body.appendChild(ссылка); ссылка.click();
    document.body.removeChild(ссылка);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  переключатели.forEach(к => к.addEventListener('click', () => {
    режим = к.getAttribute('data-rezhim');
    переключатели.forEach(д => д.classList.toggle('is-on', д === к));
    pokazat();
  }));

  narisovat_tablicu();
  pokazat();
})();
