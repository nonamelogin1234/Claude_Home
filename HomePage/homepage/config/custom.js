/* ═══════════════════════════════════════════
   HOMEPAGE PREMIUM — custom.js
═══════════════════════════════════════════ */

var API = '/grok-news';
var NEWS_CACHE_KEY = 'hp_news';
var NEWS_TTL = 30 * 60 * 1000;

/* ── helpers ─────────────────────────────── */
function waitFor(sel, cb, tries) {
  tries = tries === undefined ? 40 : tries;
  var node = document.querySelector(sel);
  if (node) return cb(node);
  if (tries > 0) setTimeout(function() { waitFor(sel, cb, tries - 1); }, 150);
}

function makeEl(tag, attrs, children) {
  var node = document.createElement(tag);
  if (attrs) {
    Object.keys(attrs).forEach(function(k) {
      var v = attrs[k];
      if (k === 'class') node.className = v;
      else if (k === 'html') node.innerHTML = v;
      else node.setAttribute(k, v);
    });
  }
  if (children) {
    children.forEach(function(c) {
      if (!c) return;
      if (typeof c === 'string') node.appendChild(document.createTextNode(c));
      else node.appendChild(c);
    });
  }
  return node;
}

/* ── waterfall canvas ────────────────────── */
function initWaterfall() {
  var canvas = makeEl('canvas', { id: 'hp-waterfall' });
  document.body.appendChild(canvas);

  var ctx = canvas.getContext('2d');
  var W = 200;
  var H = window.innerHeight;
  canvas.width = W;
  canvas.height = H;

  var COLORS = [
    'rgba(99,102,241,', 'rgba(129,140,248,', 'rgba(79,70,229,',
    'rgba(139,92,246,', 'rgba(167,139,250,'
  ];

  var streams = [];
  for (var i = 0; i < 18; i++) {
    streams.push({
      x: Math.random() * W,
      y: Math.random() * H - H,
      speed: 0.4 + Math.random() * 0.9,
      len: 60 + Math.random() * 120,
      color: COLORS[i % COLORS.length],
      opacity: 0.4 + Math.random() * 0.6,
      width: 1 + Math.random() * 1.2,
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    streams.forEach(function(s) {
      var grad = ctx.createLinearGradient(s.x, s.y - s.len, s.x, s.y);
      grad.addColorStop(0, s.color + '0)');
      grad.addColorStop(0.5, s.color + s.opacity + ')');
      grad.addColorStop(1, s.color + '0)');
      ctx.beginPath();
      ctx.strokeStyle = grad;
      ctx.lineWidth = s.width;
      ctx.moveTo(s.x, s.y - s.len);
      ctx.lineTo(s.x, s.y);
      ctx.stroke();

      s.y += s.speed;
      if (s.y - s.len > H) {
        s.y = -s.len;
        s.x = Math.random() * W;
      }
    });
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', function() {
    H = window.innerHeight;
    canvas.height = H;
  });

  draw();
}

/* ── cursor glow ─────────────────────────── */
function initCursorGlow() {
  var glow = makeEl('div', { id: 'hp-glow' });
  document.body.appendChild(glow);
  document.addEventListener('mousemove', function(e) {
    glow.style.left = e.clientX + 'px';
    glow.style.top = e.clientY + 'px';
  });
}

/* ── parallax background ─────────────────── */
function initParallax() {
  document.addEventListener('mousemove', function(e) {
    var px = ((e.clientX / window.innerWidth) - 0.5) * 12;
    var py = ((e.clientY / window.innerHeight) - 0.5) * 8;
    document.documentElement.style.setProperty('--px', px + '%');
    document.documentElement.style.setProperty('--py', py + '%');
  });
}

/* ── header ──────────────────────────────── */
function greeting() {
  var h = new Date().getHours();
  if (h < 6)  return '\u0414\u043e\u0431\u0440\u043e\u0439 \u043d\u043e\u0447\u0438';
  if (h < 12) return '\u0414\u043e\u0431\u0440\u043e\u0435 \u0443\u0442\u0440\u043e';
  if (h < 18) return '\u0414\u043e\u0431\u0440\u044b\u0439 \u0434\u0435\u043d\u044c';
  return '\u0414\u043e\u0431\u0440\u044b\u0439 \u0432\u0435\u0447\u0435\u0440';
}

function buildHeader(main) {
  var header = makeEl('div', { id: 'hp-header' });

  var left = makeEl('div');
  var greetDiv = makeEl('div', { id: 'hp-greeting' }, [greeting()]);
  var timeDiv = makeEl('div', { id: 'hp-time' });
  left.appendChild(greetDiv);
  left.appendChild(timeDiv);

  function tick() {
    var now = new Date();
    timeDiv.textContent = now.toLocaleString('ru-RU', {
      weekday: 'long', day: 'numeric', month: 'long',
      hour: '2-digit', minute: '2-digit'
    });
  }
  tick();
  setInterval(tick, 30000);

  var right = makeEl('div', { id: 'hp-header-right' });

  var btnRefresh = makeEl('button', { class: 'hp-btn', html: '\u21bb \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0432\u0441\u0451' });
  btnRefresh.onclick = function() {
    loadWeather();
    loadHealth();
  };

  var btnNews = makeEl('button', { class: 'hp-btn accent', html: '\ud83d\udcf0 \u0421\u0432\u043e\u0434\u043a\u0430' });
  btnNews.onclick = function() { loadNews(true); };

  right.appendChild(btnRefresh);
  right.appendChild(btnNews);
  header.appendChild(left);
  header.appendChild(right);
  main.insertBefore(header, main.firstChild);
}

/* ── weather card ────────────────────────── */
function buildWeather() {
  var card = makeEl('div', { id: 'hp-weather', class: 'hp-glass' });
  card.innerHTML =
    '<div class="hp-card-label">\u041f\u043e\u0433\u043e\u0434\u0430 \u00b7 \u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433</div>' +
    '<div id="hp-weather-main">' +
      '<div id="hp-weather-temp">\u2014</div>' +
      '<div id="hp-weather-unit">\u00b0C</div>' +
    '</div>' +
    '<div id="hp-weather-cond">\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430\u2026</div>' +
    '<div id="hp-weather-stats">' +
      '<span class="hp-wstat">\u041e\u0449\u0443\u0449\u0430\u0435\u0442\u0441\u044f <b id="hw-feels">\u2014</b>\u00b0</span>' +
      '<span class="hp-wstat">\u0412\u043b\u0430\u0436\u043d\u043e\u0441\u0442\u044c <b id="hw-hum">\u2014</b>%</span>' +
      '<span class="hp-wstat">\u0412\u0435\u0442\u0435\u0440 <b id="hw-wind">\u2014</b> \u043a\u043c/\u0447</span>' +
    '</div>' +
    '<div id="hp-weather-forecast"></div>';
  return card;
}

function wmoIcon(code) {
  if (code === 0) return '\u2600\ufe0f';
  if (code <= 2) return '\u26c5';
  if (code <= 3) return '\u2601\ufe0f';
  if (code <= 48) return '\ud83c\udf2b\ufe0f';
  if (code <= 55) return '\ud83c\udf26\ufe0f';
  if (code <= 65) return '\ud83c\udf27\ufe0f';
  if (code <= 77) return '\u2744\ufe0f';
  if (code <= 82) return '\ud83c\udf29\ufe0f';
  if (code <= 86) return '\ud83c\udf28\ufe0f';
  return '\u26c8\ufe0f';
}

function renderWeather(d) {
  var t = document.getElementById('hp-weather-temp');
  var c = document.getElementById('hp-weather-cond');
  var f = document.getElementById('hw-feels');
  var hm = document.getElementById('hw-hum');
  var w = document.getElementById('hw-wind');
  var fc = document.getElementById('hp-weather-forecast');

  if (t) t.textContent = d.temp;
  if (c) c.textContent = d.condition;
  if (f) f.textContent = d.feels_like;
  if (hm) hm.textContent = d.humidity;
  if (w) w.textContent = d.wind;

  if (fc && d.forecast) {
    fc.innerHTML = '';
    d.forecast.forEach(function(day) {
      var dayEl = makeEl('div', { class: 'hp-fday' });
      dayEl.innerHTML =
        '<div class="hp-fday-name">' + day.day + '</div>' +
        '<div class="hp-fday-icon">' + wmoIcon(day.weathercode || 0) + '</div>' +
        '<div class="hp-fday-temps">' + day.max + '\u00b0 <span class="lo">' + day.min + '\u00b0</span></div>';
      fc.appendChild(dayEl);
    });
  }
}

function loadWeather() {
  fetch(API + '/weather')
    .then(function(r) { return r.json(); })
    .then(function(d) { if (!d.error) renderWeather(d); })
    .catch(function() {});
}

/* ── health card ─────────────────────────── */
function buildHealth() {
  var card = makeEl('div', { id: 'hp-health', class: 'hp-glass' });
  card.innerHTML =
    '<div class="hp-card-label">\u0417\u0434\u043e\u0440\u043e\u0432\u044c\u0435</div>' +
    '<div id="hp-wt-row">' +
      '<div id="hp-wt-cur">\u2014</div>' +
      '<div id="hp-wt-arrow">\u2192</div>' +
      '<div id="hp-wt-goal">85 \u043a\u0433</div>' +
    '</div>' +
    '<div id="hp-wt-diff"></div>' +
    '<div id="hp-bar"><div id="hp-bar-fill"></div></div>' +
    '<div id="hp-smoke">' +
      '<div id="hp-smoke-n">\u2014</div>' +
      '<div id="hp-smoke-lbl">\u0434\u043d\u0435\u0439<br>\u0431\u0435\u0437 \u0441\u0438\u0433\u0430\u0440\u0435\u0442</div>' +
    '</div>';
  return card;
}

function renderHealth(d) {
  var wc = document.getElementById('hp-wt-cur');
  var wd = document.getElementById('hp-wt-diff');
  var bf = document.getElementById('hp-bar-fill');
  var sn = document.getElementById('hp-smoke-n');

  if (wc && d.weight !== null && d.weight !== undefined) {
    wc.textContent = d.weight;
  }
  if (wd && d.diff !== undefined) {
    var sign = d.diff > 0 ? '\u2193 ' : '\u2713 ';
    wd.textContent = sign + Math.abs(d.diff) + ' \u043a\u0433 \u0434\u043e \u0446\u0435\u043b\u0438';
    wd.style.color = d.diff > 0 ? 'var(--c-muted)' : 'var(--c-success)';
  }
  if (bf && d.progress_pct !== undefined) {
    setTimeout(function() {
      bf.style.width = d.progress_pct + '%';
    }, 300);
  }
  if (sn) sn.textContent = d.smoke_days || 0;
}

function loadHealth() {
  fetch(API + '/health-stats')
    .then(function(r) { return r.json(); })
    .then(function(d) { renderHealth(d); })
    .catch(function() {});
}

/* ── news card ───────────────────────────── */
function buildNews() {
  var card = makeEl('div', { id: 'hp-news', class: 'hp-glass' });
  card.innerHTML =
    '<div id="hp-news-top">' +
      '<div class="hp-card-label">\u041d\u043e\u0432\u043e\u0441\u0442\u0438 \u00b7 Grok</div>' +
      '<button class="hp-btn" id="hp-news-btn">\u21bb \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c</button>' +
    '</div>' +
    '<div id="hp-news-meta"></div>' +
    '<div id="hp-news-body">\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u00ab\u0421\u0432\u043e\u0434\u043a\u0430\u00bb \u0434\u043b\u044f \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438\u2026</div>';

  setTimeout(function() {
    var btn = document.getElementById('hp-news-btn');
    if (btn) btn.onclick = function() { loadNews(true); };
  }, 100);

  return card;
}

function loadNews(force) {
  var body = document.getElementById('hp-news-body');
  var meta = document.getElementById('hp-news-meta');
  var btn = document.getElementById('hp-news-btn');
  if (!body) return;

  if (!force) {
    try {
      var cached = JSON.parse(localStorage.getItem(NEWS_CACHE_KEY) || 'null');
      if (cached && Date.now() - cached.ts < NEWS_TTL) {
        body.textContent = cached.text;
        body.className = 'loaded';
        if (meta) meta.textContent = '\u041a\u044d\u0448 \u043e\u0442 ' + new Date(cached.ts).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        return;
      }
    } catch(e) {}
    return;
  }

  body.className = '';
  body.textContent = '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430\u2026';
  if (btn) btn.disabled = true;

  fetch(API + '/summary', { method: 'POST' })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.error) throw new Error(d.error);
      body.textContent = d.summary;
      body.className = 'loaded';
      var ts = Date.now();
      if (meta) meta.textContent = '\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e \u0432 ' + new Date(ts).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
      localStorage.setItem(NEWS_CACHE_KEY, JSON.stringify({ text: d.summary, ts: ts }));
    })
    .catch(function(e) {
      body.textContent = '\u041e\u0448\u0438\u0431\u043a\u0430: ' + e.message;
      body.className = 'error';
    })
    .then(function() {
      if (btn) btn.disabled = false;
    });
}

/* ── widget row ──────────────────────────── */
function buildWidgets(main) {
  var row = makeEl('div', { id: 'hp-widgets' });
  row.appendChild(buildWeather());
  row.appendChild(buildHealth());

  var services = document.getElementById('services-list');
  if (services) {
    main.insertBefore(row, services);
    main.insertBefore(buildNews(), services);
  } else {
    main.appendChild(row);
    main.appendChild(buildNews());
  }
}

/* ── boot ────────────────────────────────── */
function init(main) {
  ['information-widgets', 'widgets-list'].forEach(function(id) {
    var node = document.getElementById(id);
    if (node) node.style.display = 'none';
  });

  buildHeader(main);
  buildWidgets(main);

  initWaterfall();
  initCursorGlow();
  initParallax();

  loadWeather();
  loadHealth();
  loadNews(false);
}

// Boot after window.load — by then React is guaranteed to have hydrated.
// waitFor('main') fires before hydration and gets wiped; waitFor('#services-list')
// times out because that ID doesn't exist in Homepage v1.12.3.
window.addEventListener('load', function() {
  setTimeout(function() {
    var main = document.querySelector('main') || document.body;
    init(main);
  }, 300);
});
