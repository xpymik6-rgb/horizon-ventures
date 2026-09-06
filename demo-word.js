/* Живое демо Word Import.
   Человек бросает свой .docx, и прямо в браузере видно, какое дерево страниц
   из него получится. Файл никуда не уходит: распаковка и разбор идут здесь же,
   ровно так, как это делает само приложение. */

(function () {
  const корень = document.querySelector('#demo4');
  if (!корень) return;

  const зона    = корень.querySelector('#wi-drop');
  const выбор   = корень.querySelector('#wi-file');
  const уровень = корень.querySelector('#wi-level');
  const дерево  = корень.querySelector('#wi-tree');
  const итог    = корень.querySelector('#wi-summary');
  const имяФайла = корень.querySelector('#wi-filename');
  const пример  = корень.querySelector('#wi-example');

  /* Пример на случай, если документа под рукой нет: обычный регламент. */
  const ПРИМЕР = {
    имя: 'Information security policy.docx',
    заголовки: [
      [1, 'Information security policy'],
      [2, 'Purpose and scope'],
      [3, 'Who this applies to'],
      [3, 'What is out of scope'],
      [2, 'Access control'],
      [3, 'Granting access'],
      [3, 'Reviewing access quarterly'],
      [3, 'Revoking access when somebody leaves'],
      [2, 'Passwords and second factor'],
      [3, 'Requirements'],
      [3, 'Password manager'],
      [2, 'Incidents'],
      [3, 'How to report'],
      [3, 'What happens next'],
      [2, 'Annexes'],
      [3, 'Annex A. Approved software'],
      [3, 'Annex B. Contact list'],
    ],
  };

  /* ── распаковка .docx ─────────────────────────────────────── */
  // .docx — это zip-архив. Нам нужен из него один файл: word/document.xml.

  async function prochitat_docx(файл) {
    const данные = new Uint8Array(await файл.arrayBuffer());
    const вид = new DataView(данные.buffer);

    // хвост архива: оглавление лежит в самом конце
    let конец = -1;
    for (let i = данные.length - 22; i >= 0 && i > данные.length - 66000; i--) {
      if (вид.getUint32(i, true) === 0x06054b50) { конец = i; break; }
    }
    if (конец < 0) throw new Error('это не архив .docx');

    let место = вид.getUint32(конец + 16, true);       // где начинается оглавление
    const записей = вид.getUint16(конец + 10, true);

    let нужный = null;
    for (let n = 0; n < записей; n++) {
      if (вид.getUint32(место, true) !== 0x02014b50) break;
      const способ  = вид.getUint16(место + 10, true);
      const сжатый  = вид.getUint32(место + 20, true);
      const длинаИмени = вид.getUint16(место + 28, true);
      const длинаДопа  = вид.getUint16(место + 30, true);
      const длинаКоммента = вид.getUint16(место + 32, true);
      const смещение = вид.getUint32(место + 42, true);
      const имя = new TextDecoder().decode(данные.subarray(место + 46, место + 46 + длинаИмени));
      if (имя === 'word/document.xml') { нужный = { способ, сжатый, смещение }; break; }
      место += 46 + длинаИмени + длинаДопа + длинаКоммента;
    }
    if (!нужный) throw new Error('внутри нет word/document.xml');

    // от локального заголовка отсчитываем начало самих данных
    const л = нужный.смещение;
    const длинаИмени2 = вид.getUint16(л + 26, true);
    const длинаДопа2  = вид.getUint16(л + 28, true);
    const начало = л + 30 + длинаИмени2 + длинаДопа2;
    const кусок = данные.subarray(начало, начало + нужный.сжатый);

    if (нужный.способ === 0) return new TextDecoder().decode(кусок);   // без сжатия
    const поток = new Blob([кусок]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return await new Response(поток).text();
  }

  /* ── заголовки из документа ───────────────────────────────── */

  function zagolovki_iz_xml(xml) {
    const документ = new DOMParser().parseFromString(xml, 'application/xml');
    const абзацы = документ.getElementsByTagName('w:p');
    const найденные = [];
    for (const абзац of абзацы) {
      const стиль = абзац.getElementsByTagName('w:pStyle')[0];
      if (!стиль) continue;
      const имя = стиль.getAttribute('w:val') || '';
      const м = имя.match(/^Heading(\d)$|^Заголовок(\d)$|^(\d)$/i);
      if (!м) continue;
      const ур = parseInt(м[1] || м[2] || м[3], 10);
      if (!(ур >= 1 && ур <= 4)) continue;
      let текст = '';
      for (const т of абзац.getElementsByTagName('w:t')) текст += т.textContent;
      текст = текст.trim();
      if (текст) найденные.push([ур, текст]);
    }
    return найденные;
  }

  /* ── показ дерева ─────────────────────────────────────────── */

  let текущие = ПРИМЕР.заголовки;
  let текущееИмя = ПРИМЕР.имя;

  function narisovat() {
    const порог = parseInt(уровень.value, 10);
    дерево.innerHTML = '';
    let страниц = 0, разделов = 0;

    if (!текущие.length) {
      дерево.innerHTML = '<p class="wi-empty">В документе нет заголовков, размеченных стилями. ' +
        'Тогда он станет одной страницей — и это ровно тот случай, о котором мы пишем в статье.</p>';
      итог.textContent = '';
      return;
    }

    for (const [ур, текст] of текущие) {
      if (ур > порог) { разделов++; continue; }
      страниц++;
      const строка = document.createElement('div');
      строка.className = 'wi-node wi-l' + ур;
      строка.innerHTML = '<span class="wi-icon">▤</span><span class="wi-title"></span>';
      строка.querySelector('.wi-title').textContent = текст;
      дерево.appendChild(строка);
    }

    итог.textContent = страниц + (страниц === 1 ? ' page' : ' pages') +
      ' from one document' + (разделов ? ', with ' + разделов + ' deeper headings kept inside the pages.' : '.');
  }

  /* ── приём файла ──────────────────────────────────────────── */

  async function prinyat(файл) {
    if (!файл) return;
    имяФайла.textContent = файл.name;
    дерево.innerHTML = '<p class="wi-empty">Читаю документ…</p>';
    try {
      if (!/\.docx$/i.test(файл.name)) throw new Error('нужен файл .docx, старый .doc не подойдёт');
      const xml = await prochitat_docx(файл);
      текущие = zagolovki_iz_xml(xml);
      текущееИмя = файл.name;
      narisovat();
    } catch (е) {
      дерево.innerHTML = '';
      const с = document.createElement('p');
      с.className = 'wi-empty';
      с.textContent = 'Не вышло разобрать файл: ' + е.message + '. Показываю пример.';
      дерево.appendChild(с);
      текущие = ПРИМЕР.заголовки; текущееИмя = ПРИМЕР.имя;
      имяФайла.textContent = ПРИМЕР.имя;
      setTimeout(narisovat, 1500);
    }
  }

  зона.addEventListener('dragover', е => { е.preventDefault(); зона.classList.add('is-over'); });
  зона.addEventListener('dragleave', () => зона.classList.remove('is-over'));
  зона.addEventListener('drop', е => {
    е.preventDefault(); зона.classList.remove('is-over');
    prinyat(е.dataTransfer.files[0]);
  });
  зона.addEventListener('click', () => выбор.click());
  выбор.addEventListener('change', () => prinyat(выбор.files[0]));
  уровень.addEventListener('change', narisovat);
  пример.addEventListener('click', () => {
    текущие = ПРИМЕР.заголовки; текущееИмя = ПРИМЕР.имя;
    имяФайла.textContent = ПРИМЕР.имя;
    narisovat();
  });

  имяФайла.textContent = ПРИМЕР.имя;
  narisovat();
})();
