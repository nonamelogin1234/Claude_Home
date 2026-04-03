// Config
const REFRESH_INTERVAL = 5 * 60 * 1000;
let weightChart = null;
let lastUpdated = null;
let cachedData = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadAllData();
    setInterval(loadAllData, REFRESH_INTERVAL);
});

async function loadAllData() {
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

        // Show app, hide loading
        document.getElementById('loading-overlay').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');

    } catch (err) {
        console.error('Failed to load data:', err);
        // Show app with cached data or error state
        document.getElementById('loading-overlay').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');
        if (lastUpdated) {
            updateLastUpdatedText();
        }
    }
}

async function fetchData(endpoint) {
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${endpoint}`);
    return res.json();
}

function updateLastUpdatedText() {
    const el = document.getElementById('last-updated');
    if (!lastUpdated) return;
    const mins = Math.floor((Date.now() - lastUpdated) / 60000);
    el.textContent = mins === 0 ? 'обновлено только что' : `обновлено ${mins} мин назад`;
    setTimeout(updateLastUpdatedText, 30000);
}

function renderHero(data) {
    document.getElementById('hero-level').textContent = data.level;
    document.getElementById('hero-level-name').textContent = data.level_name;

    const range = data.next_level_threshold - data.prev_level_threshold;
    const progress = range > 0
        ? ((data.workouts_count - data.prev_level_threshold) / range * 100).toFixed(0)
        : 100;
    const bar = document.getElementById('level-progress-bar');
    bar.style.width = Math.min(100, Math.max(0, progress)) + '%';
    document.getElementById('level-progress-text').textContent =
        `${data.workouts_count} тренировок (следующий уровень: ${data.next_level_threshold})`;

    document.getElementById('stat-strength').textContent = data.strength.toFixed(0);
    document.getElementById('stat-endurance').textContent = data.endurance.toFixed(0);
    document.getElementById('stat-recovery').textContent = data.recovery.toFixed(0);
    document.getElementById('stat-volume').textContent = (data.volume / 1000).toFixed(1);
}

function renderQuests(quests) {
    const activeEl = document.getElementById('active-quests-list');
    const completedEl = document.getElementById('completed-quests-list');
    activeEl.innerHTML = '';
    completedEl.innerHTML = '';

    quests.forEach(q => {
        const el = createQuestElement(q);
        if (q.status === 'completed') {
            completedEl.appendChild(el);
        } else {
            activeEl.appendChild(el);
        }
    });
}

function createQuestElement(quest) {
    const div = document.createElement('div');
    div.className = `quest-item quest-${quest.status}`;
    const progressPct = (quest.progress * 100).toFixed(0);
    div.innerHTML = `
        <div class="quest-header">
            <span class="quest-icon">${quest.icon}</span>
            <div class="quest-info">
                <div class="quest-name">${quest.name}</div>
                <div class="quest-desc">${quest.description}</div>
            </div>
            <div class="quest-status-badge quest-badge-${quest.status}">${questStatusText(quest.status)}</div>
        </div>
        ${quest.status !== 'locked' ? `
        <div class="quest-progress-track">
            <div class="quest-progress-fill quest-fill-${quest.status}" style="width: ${progressPct}%"></div>
        </div>
        <div class="quest-progress-text">${quest.progress_text}</div>
        ` : ''}
    `;
    return div;
}

function questStatusText(status) {
    return { active: 'АКТИВЕН', completed: '✓ ВЫПОЛНЕН', locked: '🔒 ЗАБЛОК.' }[status] || status;
}

function renderBosses(bosses) {
    const el = document.getElementById('bosses-list');
    el.innerHTML = '';

    const currentWeight = bosses.find(b => b.status === 'active')?.current_weight
                       || bosses[0]?.current_weight || 0;
    document.getElementById('current-weight-display').textContent = currentWeight.toFixed(1);

    bosses.forEach(boss => {
        const div = document.createElement('div');
        div.className = `boss-item boss-${boss.status}`;
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
                <div class="boss-progress-fill boss-fill-${boss.status}" style="width: ${pct}%"></div>
            </div>
            <div class="boss-progress-text">${pct}% выполнено</div>
        `;
        el.appendChild(div);
    });
}

function bossStatusText(status) {
    return { defeated: '✅ ПОБЕЖДЁН', active: '🗡️ БИТВА', locked: '🔒 НЕДОСЯГ.' }[status] || status;
}

function renderStats(stats) {
    document.getElementById('sc-weight-val').textContent =
        stats.current_weight ? stats.current_weight.toFixed(1) : '—';
    document.getElementById('sc-workouts-val').textContent = stats.total_workouts || '0';
    document.getElementById('sc-workouts30-val').textContent = stats.workouts_30d || '0';
    document.getElementById('sc-streak-val').textContent = stats.current_streak_weeks || '0';
    document.getElementById('sc-total-vol-val').textContent =
        stats.total_volume ? (stats.total_volume / 1000).toFixed(1) : '0';
    document.getElementById('sc-avg5-val').textContent =
        stats.avg_volume_5 ? stats.avg_volume_5.toFixed(0) : '—';

    if (stats.best_workout) {
        document.getElementById('sc-best-val').textContent =
            stats.best_workout.total_volume_kg.toFixed(0) + ' кг';
        const d = new Date(stats.best_workout.workout_date);
        document.getElementById('sc-best-date').textContent =
            d.toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit', year: 'numeric'});
    }
}

function renderEvents(events) {
    const el = document.getElementById('event-list');
    el.innerHTML = '';
    events.forEach(ev => {
        const div = document.createElement('div');
        div.className = 'event-item';
        div.innerHTML = `<span class="ev-date">[${ev.date_str}]</span> <span class="ev-icon">${ev.icon}</span> <span class="ev-text">${ev.text}</span>`;
        el.appendChild(div);
    });
}

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
                borderColor: '#C0A030',
                backgroundColor: 'rgba(192, 160, 48, 0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#F0C060',
                pointBorderColor: '#C0A030',
                pointRadius: 4,
                tension: 0.4,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1A1208',
                    borderColor: '#C0A030',
                    borderWidth: 1,
                    titleColor: '#F0C060',
                    bodyColor: '#E8D8A0',
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(192,160,48,0.1)' },
                    ticks: { color: '#8A7848' }
                },
                y: {
                    grid: { color: 'rgba(192,160,48,0.1)' },
                    ticks: { color: '#8A7848' },
                    min: function(ctx) {
                        const vals = ctx.chart.data.datasets[0].data;
                        if (!vals || vals.length === 0) return 0;
                        const min = Math.min(...vals);
                        return Math.max(0, min - 3);
                    }
                }
            }
        }
    });
}
