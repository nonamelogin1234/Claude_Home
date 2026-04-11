// ── Config ──────────────────────────────────────────────────────────────────
const REFRESH_INTERVAL = 5 * 60 * 1000;
let weightChart = null;
let lastUpdated = null;
let cachedData = {};

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initWaterCanvas();
    loadAllData();
    setInterval(loadAllData, REFRESH_INTERVAL);
});

// ── Water Canvas Animation ────────────────────────────────────────────────────
function initWaterCanvas() {
    const canvas = document.getElementById('water-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let t = 0;
    let animId = null;

    function resize() {
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width || 800;
        canvas.height = rect.height || 200;
    }

    resize();
    window.addEventListener('resize', () => { resize(); });

    function drawWave(W, H, offset, freq, amp, color, yBase) {
        ctx.beginPath();
        ctx.moveTo(0, H);
        for (let x = 0; x <= W + 4; x += 3) {
            const y = yBase + Math.sin(x * freq + offset) * amp
                            + Math.sin(x * freq * 1.7 + offset * 0.6) * (amp * 0.4);
            ctx.lineTo(x, y);
        }
        ctx.lineTo(W, H);
        ctx.lineTo(0, H);
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();
    }

    function draw() {
        const W = canvas.width;
        const H = canvas.height;
        ctx.clearRect(0, 0, W, H);

        const y1 = H * 0.52;
        const y2 = H * 0.62;
        const y3 = H * 0.70;

        drawWave(W, H, t * 0.45,  0.007, 14, 'rgba(46,95,163,0.055)', y1);
        drawWave(W, H, t * 0.65 + 1.2, 0.011, 10, 'rgba(46,95,163,0.040)', y2);
        drawWave(W, H, t * 0.90 + 2.5, 0.016,  7, 'rgba(201,168,76,0.025)', y3);

        t += 0.018;
        animId = requestAnimationFrame(draw);
    }

    draw();
}

// ── Data Loading ──────────────────────────────────────────────────────────────
async function loadAllData() {
    setRefreshDot(true);
    try {
        const [hero, quests, bosses, stats, events, weightData] = await Promise.all([
            fetchData('api/hero'),
            fetchData('api/quests'),
            fetchData('api/bosses'),
            fetchData('api/stats'),
            fetchData('api/events'),
            fetchData('api/weight-chart'),
        ]);

        cachedData = { hero, quests, bosses, stats, events, weightData };

        renderHero(hero);
        renderQuests(quests);
        renderBosses(bosses);
        renderStats(stats);
        renderEvents(events);
        renderWeightChart(weightData);

        lastUpdated = new Date();
        updateLastUpdatedText();

        document.getElementById('loading-overlay').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');

    } catch (err) {
        console.error('Failed to load data:', err);
        document.getElementById('loading-overlay').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');
        if (lastUpdated) updateLastUpdatedText();
    } finally {
        setRefreshDot(false);
    }
}

async function fetchData(endpoint) {
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${endpoint}`);
    return res.json();
}

// ── Refresh dot ───────────────────────────────────────────────────────────────
function setRefreshDot(active) {
    const dot = document.getElementById('refresh-dot');
    if (!dot) return;
    if (active) dot.classList.add('active');
    else dot.classList.remove('active');
}

function updateLastUpdatedText() {
    const el = document.getElementById('last-updated');
    if (!lastUpdated || !el) return;
    const mins = Math.floor((Date.now() - lastUpdated) / 60000);
    // preserve the dot span
    const dot = el.querySelector('.refresh-dot');
    const text = mins === 0 ? 'обновлено только что' : `обновлено ${mins} мин назад`;
    // clear text nodes, keep dot
    el.childNodes.forEach(n => { if (n.nodeType === 3) el.removeChild(n); });
    el.appendChild(document.createTextNode(' ' + text));
    setTimeout(updateLastUpdatedText, 30000);
}

// ── Number counter animation ──────────────────────────────────────────────────
function animateCounter(el, target, duration = 1000, decimals = 0) {
    if (!el || isNaN(target)) return;
    const startTime = performance.now();
    function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        el.textContent = decimals > 0 ? value.toFixed(decimals) : Math.round(value).toString();
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ── Progress bar deferred animation ──────────────────────────────────────────
function animateBar(el, pct, delay = 80) {
    if (!el) return;
    el.style.width = '0%';
    setTimeout(() => { el.style.width = Math.min(100, Math.max(0, pct)) + '%'; }, delay);
}

// ── Hero ──────────────────────────────────────────────────────────────────────
function renderHero(data) {
    document.getElementById('hero-level').textContent = data.level;
    document.getElementById('hero-level-name').textContent = data.level_name;
    document.getElementById('hero-class').textContent = data.class_name || 'Путь трансформации';

    const range = data.next_level_threshold - data.prev_level_threshold;
    const progress = range > 0
        ? ((data.workouts_count - data.prev_level_threshold) / range * 100)
        : 100;

    animateBar(document.getElementById('level-progress-bar'), progress);
    document.getElementById('level-progress-text').textContent =
        `${data.workouts_count} тренировок · следующий этап: ${data.next_level_threshold}`;

    animateCounter(document.getElementById('stat-strength'), data.strength, 900, 0);
    animateCounter(document.getElementById('stat-endurance'), data.endurance, 900, 0);
    animateCounter(document.getElementById('stat-recovery'), data.recovery, 900, 0);
    animateCounter(document.getElementById('stat-volume'), data.volume / 1000, 1100, 1);
}

// ── Quests / Практики ─────────────────────────────────────────────────────────
function renderQuests(quests) {
    const activeEl = document.getElementById('active-quests-list');
    const completedEl = document.getElementById('completed-quests-list');
    activeEl.innerHTML = '';
    completedEl.innerHTML = '';

    quests.forEach((q, i) => {
        const el = createQuestElement(q, i);
        if (q.status === 'completed') {
            completedEl.appendChild(el);
        } else {
            activeEl.appendChild(el);
        }
    });

    // Animate progress fills after stagger
    setTimeout(() => {
        document.querySelectorAll('.quest-progress-fill[data-pct]').forEach(fill => {
            fill.style.width = fill.dataset.pct + '%';
        });
    }, 150);
}

function createQuestElement(quest, idx) {
    const div = document.createElement('div');
    div.className = `quest-item quest-${quest.status}`;
    div.style.opacity = '0';
    div.style.transform = 'translateY(8px)';

    const progressPct = (quest.progress * 100).toFixed(0);
    const showProgress = quest.status !== 'locked';

    div.innerHTML = `
        <div class="quest-header">
            <span class="quest-icon">${quest.icon}</span>
            <div class="quest-info">
                <div class="quest-name">${quest.name}</div>
                <div class="quest-desc">${quest.description}</div>
            </div>
            <div class="quest-status-badge quest-badge-${quest.status}">${questStatusText(quest.status)}</div>
        </div>
        ${showProgress ? `
        <div class="quest-progress-track">
            <div class="quest-progress-fill quest-fill-${quest.status}" style="width:0%" data-pct="${progressPct}"></div>
        </div>
        <div class="quest-progress-text">${quest.progress_text}</div>
        ` : ''}
    `;

    // Stagger fade-in
    setTimeout(() => {
        div.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        div.style.opacity = '1';
        div.style.transform = 'translateY(0)';
    }, idx * 60 + 100);

    return div;
}

function questStatusText(status) {
    return {
        active:    'в процессе',
        completed: 'достигнуто',
        locked:    'впереди',
    }[status] || status;
}

// ── Bosses / Рубежи ───────────────────────────────────────────────────────────
function renderBosses(bosses) {
    const el = document.getElementById('bosses-list');
    el.innerHTML = '';

    const currentWeight = bosses.find(b => b.status === 'active')?.current_weight
                       || bosses[0]?.current_weight || 0;
    const cwEl = document.getElementById('current-weight-display');
    animateCounter(cwEl, currentWeight, 900, 1);

    bosses.forEach((boss, i) => {
        const div = document.createElement('div');
        div.className = `boss-item boss-${boss.status}`;
        div.style.opacity = '0';

        const pct = (boss.progress * 100).toFixed(0);
        div.innerHTML = `
            <div class="boss-header">
                <span class="boss-icon">${boss.icon}</span>
                <div class="boss-info">
                    <div class="boss-name">${boss.name}</div>
                    <div class="boss-target">Цель: ${boss.target_weight} кг</div>
                </div>
                <div class="boss-status-badge boss-badge-${boss.status}">
                    ${bossStatusText(boss.status)}
                </div>
            </div>
            <div class="boss-progress-track">
                <div class="boss-progress-fill boss-fill-${boss.status}" style="width:0%" data-pct="${pct}"></div>
            </div>
            <div class="boss-progress-text">${pct}% пройдено</div>
        `;

        el.appendChild(div);

        setTimeout(() => {
            div.style.transition = 'opacity 0.35s ease';
            div.style.opacity = '1';
        }, i * 80 + 100);
    });

    // Animate boss bars
    setTimeout(() => {
        document.querySelectorAll('.boss-progress-fill[data-pct]').forEach(fill => {
            fill.style.width = fill.dataset.pct + '%';
        });
    }, 200);
}

function bossStatusText(status) {
    return {
        defeated: 'достигнуто',
        active:   'в процессе',
        locked:   'впереди',
    }[status] || status;
}

// ── Stats ─────────────────────────────────────────────────────────────────────
function renderStats(stats) {
    const wEl = document.getElementById('sc-weight-val');
    if (stats.current_weight) animateCounter(wEl, stats.current_weight, 900, 1);
    else wEl.textContent = '—';

    animateCounter(document.getElementById('sc-workouts-val'), stats.total_workouts || 0, 1000, 0);
    animateCounter(document.getElementById('sc-workouts30-val'), stats.workouts_30d || 0, 800, 0);
    animateCounter(document.getElementById('sc-streak-val'), stats.current_streak_weeks || 0, 800, 0);

    const volEl = document.getElementById('sc-total-vol-val');
    if (stats.total_volume) animateCounter(volEl, stats.total_volume / 1000, 1100, 1);
    else volEl.textContent = '0';

    const avgEl = document.getElementById('sc-avg5-val');
    if (stats.avg_volume_5) animateCounter(avgEl, stats.avg_volume_5, 900, 0);
    else avgEl.textContent = '—';

    if (stats.best_workout) {
        const bestEl = document.getElementById('sc-best-val');
        animateCounter(bestEl, stats.best_workout.total_volume_kg, 1000, 0);
        document.getElementById('sc-best-val').dataset.suffix = ' кг';
        const d = new Date(stats.best_workout.workout_date);
        document.getElementById('sc-best-date').textContent =
            d.toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit', year: 'numeric'});
        // append suffix after animation
        setTimeout(() => {
            const el = document.getElementById('sc-best-val');
            if (!el.textContent.includes('кг')) el.textContent += ' кг';
        }, 1100);
    }
}

// ── Events / Хроника ──────────────────────────────────────────────────────────
function renderEvents(events) {
    const el = document.getElementById('event-list');
    el.innerHTML = '';
    events.forEach((ev, i) => {
        const div = document.createElement('div');
        div.className = 'event-item';
        div.style.opacity = '0';
        div.style.transform = 'translateX(-8px)';
        div.innerHTML = `<span class="ev-date">${ev.date_str}</span> <span class="ev-icon">${ev.icon}</span> <span class="ev-text">${ev.text}</span>`;
        el.appendChild(div);

        setTimeout(() => {
            div.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
            div.style.opacity = '1';
            div.style.transform = 'translateX(0)';
        }, i * 50 + 80);
    });
}

// ── Weight Chart ──────────────────────────────────────────────────────────────
function renderWeightChart(data) {
    const ctx = document.getElementById('weight-chart').getContext('2d');

    const labels = data.map(d => {
        const dt = new Date(d.date);
        return dt.toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit'});
    });
    const weights = data.map(d => d.weight);

    if (weightChart) {
        weightChart.data.labels = labels;
        weightChart.data.datasets[0].data = weights;
        weightChart.update('active');
        return;
    }

    weightChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Вес (кг)',
                data: weights,
                borderColor: '#C9A84C',
                backgroundColor: 'rgba(201,168,76,0.07)',
                borderWidth: 1.5,
                pointBackgroundColor: '#C4673A',
                pointBorderColor: '#C9A84C',
                pointRadius: 3,
                pointHoverRadius: 5,
                tension: 0.4,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000, easing: 'easeOutQuart' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#FFFDF8',
                    borderColor: 'rgba(196,103,58,0.25)',
                    borderWidth: 1,
                    titleColor: '#2C1F14',
                    bodyColor: '#7A6650',
                    titleFont: { family: "'Playfair Display', Georgia, serif", size: 13 },
                    bodyFont: { family: "'Lato', sans-serif", size: 12 },
                    padding: 10,
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(196,103,58,0.06)', drawBorder: false },
                    ticks: { color: '#A89070', font: { family: "'Lato', sans-serif", size: 11 } },
                    border: { display: false },
                },
                y: {
                    grid: { color: 'rgba(196,103,58,0.06)', drawBorder: false },
                    ticks: { color: '#A89070', font: { family: "'Lato', sans-serif", size: 11 } },
                    border: { display: false },
                    min: function(ctx) {
                        const vals = ctx.chart.data.datasets[0].data;
                        if (!vals || vals.length === 0) return 0;
                        return Math.max(0, Math.min(...vals) - 2);
                    }
                }
            }
        }
    });
}
