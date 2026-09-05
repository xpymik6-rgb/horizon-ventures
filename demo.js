/* Живое демо Clickable SVG прямо на сайте.
   Повторяет поведение приложения: клик по фигуре открывает страницу,
   работает поиск с подсветкой, увеличение и перетаскивание.
   Никаких библиотек — всё на обычном JavaScript. */

(function () {
  const корень = document.querySelector('#demo');
  if (!корень) return;

  const холст   = корень.querySelector('.demo-canvas');
  const схема   = корень.querySelector('#demo-svg');
  const поле    = корень.querySelector('#demo-search');
  const счёт    = корень.querySelector('#demo-count');
  const дальше  = корень.querySelector('#demo-next');
  const панель  = корень.querySelector('#demo-page');
  const заголовокСтр = панель.querySelector('.demo-page-title');
  const меткиСтр     = панель.querySelector('.demo-page-meta');
  const текстСтр     = панель.querySelector('.demo-page-body');
  const закрыть = панель.querySelector('.demo-page-close');
  const подсказка = корень.querySelector('#demo-tip');

  /* Страницы, на которые ведут фигуры. В настоящем приложении это страницы
     вашей вики; здесь — их короткие двойники. */
  const СТРАНИЦЫ = {
    'web-frontend':  ['Web frontend', 'Space: Engineering · updated 3 days ago',
      'React application served from the edge. Deploys run from the main branch; rollback is a one-click revert in the pipeline. On-call owns the build, not the content.'],
    'mobile-app':    ['Mobile app', 'Space: Engineering · updated last week',
      'iOS and Android clients share the payments SDK. Release trains go out every second Tuesday. Crash reports land in the mobile channel.'],
    'partner-api':   ['Partner API', 'Space: Integrations · updated yesterday',
      'Public API for partner integrations. Keys are issued per partner and rotate every 90 days. Rate limits are documented on the page below.'],
    'payments-api':  ['Payments API runbook', 'Space: Engineering · updated today',
      'Entry point for every payment. Start here during an incident: health checks, common failure modes, and how to drain traffic without dropping in-flight transactions.'],
    'ledger':        ['Ledger service', 'Space: Finance systems · updated 2 days ago',
      'Double-entry ledger. Nothing is ever deleted; corrections are written as compensating entries. Month-end close depends on this service being consistent.'],
    'fraud-check':   ['Fraud check', 'Space: Risk · updated 5 days ago',
      'Scores each transaction before it is captured. Rules live in the risk repository and are reviewed monthly. False positives are triaged by the risk team.'],
    'notifications': ['Notifications', 'Space: Engineering · updated last month',
      'Sends receipts and failure alerts. Templates are edited in this space, so a copy change does not need a deploy.'],
    'identity':      ['Identity', 'Space: Platform · updated 3 weeks ago',
      'Tokens, sessions and service-to-service auth. Every other service on this map depends on it, which is why it has its own on-call rota.'],
    'postgres':      ['PostgreSQL cluster', 'Space: Platform · updated 4 days ago',
      'Primary with two replicas. Failover is automatic; the runbook covers the manual path for when it is not. Backups are verified weekly by restore.'],
    'kafka':         ['Kafka', 'Space: Platform · updated 2 weeks ago',
      'Event backbone. Topic naming, retention and consumer group ownership are listed here. Adding a topic requires a short review.'],
    's3-archive':    ['Archive storage', 'Space: Platform · updated last month',
      'Seven-year retention for settled transactions. Legal signs off on the retention policy; engineering owns the lifecycle rules.'],
  };

  /* ── страница, на которую ведёт фигура ─────────────────────── */

  let открытаФигура = null;

  function pokazat_strinicu(ид) {
    const данные = СТРАНИЦЫ[ид];
    if (!данные) return;
    заголовокСтр.textContent = данные[0];
    меткиСтр.textContent     = данные[1];
    текстСтр.textContent     = данные[2];
    панель.hidden = false;
    панель.parentElement.classList.add('is-open');

    схема.querySelectorAll('.demo-node').forEach(у => у.classList.remove('is-open'));
    const узел = схема.querySelector('[data-page="' + ид + '"]');
    if (узел) узел.classList.add('is-open');
    открытаФигура = ид;
  }

  function zakryt_stranicu() {
    панель.hidden = true;
    панель.parentElement.classList.remove('is-open');
    открытаФигура = null;
    схема.querySelectorAll('.demo-node').forEach(у => у.classList.remove('is-open'));
  }

  закрыть.addEventListener('click', zakryt_stranicu);
  document.addEventListener('keydown', е => { if (е.key === 'Escape' && !панель.hidden) zakryt_stranicu(); });

  схема.querySelectorAll('.demo-node').forEach(узел => {
    const ид = узел.getAttribute('data-page');
    узел.setAttribute('tabindex', '0');
    узел.setAttribute('role', 'button');
    const имя = СТРАНИЦЫ[ид] ? СТРАНИЦЫ[ид][0] : ид;
    узел.setAttribute('aria-label', 'Open ' + имя);

    узел.addEventListener('click', е => { е.preventDefault(); pokazat_strinicu(ид); });
    узел.addEventListener('keydown', е => {
      if (е.key === 'Enter' || е.key === ' ') { е.preventDefault(); pokazat_strinicu(ид); }
    });

    // Подсказка «куда ведёт» — как в приложении при наведении
    узел.addEventListener('mouseenter', () => {
      if (!имя) return;
      подсказка.textContent = 'Opens: ' + имя;
      подсказка.hidden = false;
    });
    узел.addEventListener('mouseleave', () => { подсказка.hidden = true; });
  });

  холст.addEventListener('mouseleave', () => { подсказка.hidden = true; });
  холст.addEventListener('mousemove', е => {
    if (подсказка.hidden) return;
    const к = холст.getBoundingClientRect();
    подсказка.style.left = (е.clientX - к.left + 14) + 'px';
    подсказка.style.top  = (е.clientY - к.top + 16) + 'px';
  });

  /* ── поиск по подписям ─────────────────────────────────────── */

  let совпадения = [];
  let текущее = -1;

  function iskat(слово) {
    схема.querySelectorAll('.demo-node').forEach(у => {
      у.classList.remove('is-dim', 'is-mark', 'is-current');
    });
    совпадения = [];
    текущее = -1;

    const искомое = (слово || '').trim().toLowerCase();
    if (!искомое) { счёт.textContent = ''; дальше.disabled = true; return; }

    схема.querySelectorAll('.demo-node').forEach(узел => {
      const подпись = (узел.textContent || '').toLowerCase();
      if (подпись.includes(искомое)) { совпадения.push(узел); узел.classList.add('is-mark'); }
      else узел.classList.add('is-dim');
    });

    счёт.textContent = совпадения.length
      ? совпадения.length + (совпадения.length === 1 ? ' match' : ' matches')
      : 'nothing found';
    дальше.disabled = совпадения.length < 2;
    if (совпадения.length) perejti(0);
  }

  function perejti(номер) {
    if (!совпадения.length) return;
    совпадения.forEach(у => у.classList.remove('is-current'));
    текущее = (номер + совпадения.length) % совпадения.length;
    совпадения[текущее].classList.add('is-current');
  }

  поле.addEventListener('input', () => { подсказка.hidden = true; iskat(поле.value); });
  дальше.addEventListener('click', () => perejti(текущее + 1));
  поле.addEventListener('keydown', е => {
    if (е.key === 'Enter') { е.preventDefault(); perejti(текущее + 1); }
  });

  /* ── увеличение и перетаскивание ───────────────────────────── */

  const ИСХОДНЫЙ = { x: 0, y: 0, w: 900, h: 560 };
  let вид = Object.assign({}, ИСХОДНЫЙ);

  function primenit() {
    схема.setAttribute('viewBox', вид.x + ' ' + вид.y + ' ' + вид.w + ' ' + вид.h);
  }

  function masshtab(во_сколько, центрX, центрY) {
    const новаяШ = вид.w / во_сколько;
    const новаяВ = вид.h / во_сколько;
    // не даём улететь слишком далеко в обе стороны
    if (новаяШ < 220 || новаяШ > 2200) return;
    вид.x += (вид.w - новаяШ) * (центрX === undefined ? 0.5 : центрX);
    вид.y += (вид.h - новаяВ) * (центрY === undefined ? 0.5 : центрY);
    вид.w = новаяШ;
    вид.h = новаяВ;
    primenit();
  }

  корень.querySelector('#demo-in').addEventListener('click',  () => masshtab(1.25));
  корень.querySelector('#demo-out').addEventListener('click', () => masshtab(1 / 1.25));
  корень.querySelector('#demo-reset').addEventListener('click', () => {
    вид = Object.assign({}, ИСХОДНЫЙ); primenit();
    поле.value = ''; iskat(''); zakryt_stranicu();
  });

  холст.addEventListener('wheel', е => {
    е.preventDefault();
    const к = схема.getBoundingClientRect();
    masshtab(е.deltaY < 0 ? 1.12 : 1 / 1.12,
      (е.clientX - к.left) / к.width, (е.clientY - к.top) / к.height);
  }, { passive: false });

  let тащим = null;
  холст.addEventListener('pointerdown', е => {
    if (е.target.closest('.demo-node')) return; // по фигуре — это клик, не перетаскивание
    тащим = { x: е.clientX, y: е.clientY, vx: вид.x, vy: вид.y };
    холст.setPointerCapture(е.pointerId);
    холст.classList.add('is-dragging');
  });
  холст.addEventListener('pointermove', е => {
    if (!тащим) return;
    const к = схема.getBoundingClientRect();
    вид.x = тащим.vx - (е.clientX - тащим.x) * (вид.w / к.width);
    вид.y = тащим.vy - (е.clientY - тащим.y) * (вид.h / к.height);
    primenit();
  });
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(с =>
    холст.addEventListener(с, () => { тащим = null; холст.classList.remove('is-dragging'); }));

  primenit();
})();
