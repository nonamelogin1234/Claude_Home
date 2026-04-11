// ════════════════════════════════════════════════════════════
//  RPG TRACKER — Premium JS
//  Waterfall physics · Ambient dust · 3D-tilt · Ripple · Magnetic
// ════════════════════════════════════════════════════════════

const REFRESH_INTERVAL = 5 * 60 * 1000;
let weightChart = null;
let lastUpdated = null;
let cachedData  = {};

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initWaterfall();
    initCardTilt();
    initMagneticAvatar();
    initRipple();
    loadAllData();
    setInterval(loadAllData, REFRESH_INTERVAL);
});

// ════════════════════════════════════════════════════════════
//  WATERFALL — Particle Physics System
// ════════════════════════════════════════════════════════════

class WaterfallSystem {
    constructor(canvas) {
        this.canvas  = canvas;
        this.ctx     = canvas.getContext('2d');
        this.main    = [];   // falling drops
        this.splash  = [];   // impact spray
        this.mist    = [];   // soft fog blobs
        this.streams = [];   // fixed x positions
        this.t       = 0;

        // Pre-render a reusable mist sprite to avoid per-frame gradients
        this._mistSprite = this._buildMistSprite();
        this._resize();
    }

    _resize() {
        const r = this.canvas.parentElement.getBoundingClientRect();
        this.W  = r.width  || 900;
        this.H  = r.height || 220;
        this.canvas.width  = this.W;
        this.canvas.height = this.H;
        this.fallY  = this.H * 0.82;   // where drops hit the pool
        // Distribute streams across width — avoid pure edges
        const count = Math.max(4, Math.min(8, Math.floor(this.W / 180)));
        this.streams = [];
        for (let i = 0; i < count; i++) {
            this.streams.push({
                x:     this.W * (0.08 + 0.84 * (i / (count - 1))),
                rate:  5 + Math.random() * 4,    // particles per frame
                phase: Math.random() * Math.PI * 2,
            });
        }
    }

    _buildMistSprite() {
        const sz = 80;
        const oc = document.createElement('canvas');
        oc.width = oc.height = sz;
        const ctx = oc.getContext('2d');
        const g = ctx.createRadialGradient(sz/2, sz/2, 0, sz/2, sz/2, sz/2);
        g.addColorStop(0,   'rgba(180,215,240,0.06)');
        g.addColorStop(0.5, 'rgba(160,200,230,0.03)');
        g.addColorStop(1,   'rgba(140,190,225,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, sz, sz);
        return oc;
    }

    _spawnDrop(sx) {
        const speed = 1.8 + Math.random() * 2.2;
        const spreadFactor = 1 + this.H * 0.004;   // wider near bottom
        return {
            x:    sx + (Math.random() - 0.5) * 6,
            y:    -4,
            vx:   (Math.random() - 0.5) * 0.6,
            vy:   speed,
            r:    0.9 + Math.random() * 1.4,
            a:    0.22 + Math.random() * 0.38,
            life: 1.0,
            dr:   0.006 + Math.random() * 0.005,
            layer: Math.floor(Math.random() * 3),
            spread: spreadFactor,
        };
    }

    _spawnSplash(x, y) {
        const n = 3 + Math.floor(Math.random() * 5);
        for (let i = 0; i < n; i++) {
            const angle = -Math.PI * 0.9 + Math.random() * Math.PI * 0.8;
            const sp = 1.2 + Math.random() * 3.0;
            this.splash.push({
                x, y,
                vx: Math.cos(angle) * sp,
                vy: Math.sin(angle) * sp - 1.8,
                r:  0.6 + Math.random() * 1.0,
                a:  0.55 + Math.random() * 0.35,
                dr: 0.03 + Math.random() * 0.025,
            });
        }
    }

    _spawnMist(x, y) {
        if (Math.random() > 0.18) return;
        this.mist.push({
            x: x + (Math.random() - 0.5) * 50,
            y: y + (Math.random() - 0.5) * 12,
            vx: (Math.random() - 0.5) * 0.5,
            vy: -0.25 - Math.random() * 0.45,
            sz: 28 + Math.random() * 36,
            a:  0.08 + Math.random() * 0.08,
            dr: 0.003 + Math.random() * 0.003,
        });
    }

    update() {
        const G = 0.11;

        // Spawn from streams
        this.streams.forEach(s => {
            const n = Math.round(s.rate * (0.7 + 0.3 * Math.sin(this.t * 0.04 + s.phase)));
            for (let i = 0; i < n && this.main.length < 400; i++) {
                this.main.push(this._spawnDrop(s.x));
            }
        });

        // Update main drops
        this.main = this.main.filter(p => {
            p.vy += G;
            p.vx *= 0.998;
            p.x  += p.vx;
            p.y  += p.vy;
            p.life -= p.dr;
            if (p.y >= this.fallY) {
                this._spawnSplash(p.x, this.fallY);
                this._spawnMist(p.x, this.fallY);
                return false;
            }
            return p.life > 0;
        });

        // Update splash
        this.splash = this.splash.filter(p => {
            p.vy += G * 0.65;
            p.x  += p.vx;
            p.y  += p.vy;
            p.vx *= 0.97;
            p.life -= p.dr;
            return p.life > 0 && p.y < this.fallY + 6;
        });

        // Update mist
        this.mist = this.mist.filter(p => {
            p.x += p.vx + Math.sin(this.t * 0.025 + p.y * 0.08) * 0.2;
            p.y += p.vy;
            p.a  = Math.max(0, p.a - 0.0002);
            p.life -= p.dr;
            return p.life > 0;
        });

        this.t++;
    }

    draw() {
        const ctx = this.ctx;
        const W   = this.W;
        const H   = this.H;
        ctx.clearRect(0, 0, W, H);

        // ── Mist (back layer) — stamp pre-rendered sprite ──────────────────
        this.mist.forEach(p => {
            const opacity = p.a * p.life;
            if (opacity < 0.005) return;
            ctx.save();
            ctx.globalAlpha = opacity;
            ctx.drawImage(this._mistSprite,
                p.x - p.sz / 2, p.y - p.sz / 2,
                p.sz, p.sz);
            ctx.restore();
        });

        // ── Main drops — elongated tear shapes, 3 depth layers ─────────────
        ctx.save();
        ctx.lineCap = 'round';
        [0, 1, 2].forEach(layer => {
            const opMult    = [0.38, 0.65, 1.0][layer];
            const scaleMult = [0.72, 0.87, 1.0][layer];
            const colorB    = [200, 215, 230][layer];

            this.main.filter(p => p.layer === layer).forEach(p => {
                const alpha = p.a * p.life * opMult;
                if (alpha < 0.01) return;

                const speed  = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
                const tail   = Math.min(speed * 2.0, 10);
                const nx     = speed > 0 ? p.vx / speed : 0;
                const ny     = speed > 0 ? p.vy / speed : 1;
                const r      = p.r * scaleMult;

                ctx.beginPath();
                ctx.moveTo(p.x - nx * tail, p.y - ny * tail);
                ctx.lineTo(p.x + nx * 0.5,  p.y + ny * 0.5);
                ctx.strokeStyle = `rgba(100,${colorB},238,${alpha})`;
                ctx.lineWidth   = r * 2.0;
                ctx.stroke();
            });
        });
        ctx.restore();

        // ── Splash dots ─────────────────────────────────────────────────────
        ctx.save();
        this.splash.forEach(p => {
            const alpha = p.a * p.life;
            if (alpha < 0.01) return;
            ctx.globalAlpha = alpha;
            ctx.fillStyle = `rgba(155,205,240,1)`;
            ctx.beginPath();
            ctx.arc(Math.round(p.x), Math.round(p.y), p.r, 0, Math.PI * 2);
            ctx.fill();
        });
        ctx.restore();

        // ── Pool surface — animated sine ────────────────────────────────────
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(0, H);
        for (let x = 0; x <= W; x += 3) {
            const wy = this.fallY
                + Math.sin(x * 0.038 + this.t * 0.055) * 2.8
                + Math.sin(x * 0.021 + this.t * 0.033) * 1.6;
            ctx.lineTo(x, wy);
        }
        ctx.lineTo(W, H);
        ctx.lineTo(0, H);
        ctx.closePath();
        const pg = ctx.createLinearGradient(0, this.fallY, 0, H);
        pg.addColorStop(0, 'rgba(80,155,215,0.22)');
        pg.addColorStop(1, 'rgba(46,95,163,0.06)');
        ctx.fillStyle = pg;
        ctx.fill();
        ctx.restore();
    }
}

// ════════════════════════════════════════════════════════════
//  AMBIENT DUST — Floating golden motes
// ════════════════════════════════════════════════════════════

class AmbientDustSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx    = canvas.getContext('2d');
        this.dust   = [];
        this.t      = 0;
        this._init();
    }

    _init() {
        const W = this.canvas.width  || 900;
        const H = this.canvas.height || 220;
        for (let i = 0; i < 55; i++) {
            this.dust.push(this._create(W, H, true));
        }
    }

    _create(W, H, randomY = false) {
        return {
            baseX:     Math.random() * W,
            x:         Math.random() * W,
            y:         randomY ? Math.random() * H : H + 5,
            speed:     0.12 + Math.random() * 0.28,
            driftF:    0.003 + Math.random() * 0.009,
            driftA:    18 + Math.random() * 40,
            driftPh:   Math.random() * Math.PI * 2,
            r:         0.7 + Math.random() * 2.0,
            baseAlpha: 0.04 + Math.random() * 0.13,
            pulseF:    0.018 + Math.random() * 0.038,
            pulsePh:   Math.random() * Math.PI * 2,
            layer:     Math.floor(Math.random() * 3),
        };
    }

    update() {
        const W = this.canvas.width  || 900;
        const H = this.canvas.height || 220;
        this.dust.forEach(p => {
            const layerSpeed = [0.5, 0.75, 1.0][p.layer];
            p.y    -= p.speed * layerSpeed;
            p.x     = p.baseX + Math.sin(this.t * p.driftF + p.driftPh) * p.driftA;
            if (p.y < -8) {
                Object.assign(p, this._create(W, H, false));
            }
        });
        this.t++;
    }

    draw() {
        const ctx = this.ctx;
        ctx.save();
        this.dust.forEach(p => {
            const pulsed = p.baseAlpha * (0.55 + 0.45 * Math.sin(this.t * p.pulseF + p.pulsePh));
            if (pulsed < 0.01) return;
            ctx.globalAlpha = pulsed;
            ctx.fillStyle   = p.layer === 2 ? '#C9A84C' : p.layer === 1 ? '#B8952E' : '#D4B060';
            ctx.beginPath();
            ctx.arc(Math.round(p.x), Math.round(p.y), p.r, 0, Math.PI * 2);
            ctx.fill();
        });
        ctx.restore();
    }
}

// ── Canvas init ───────────────────────────────────────────────────────────────
let _waterfall = null;
let _dust      = null;

function initWaterfall() {
    const canvas = document.getElementById('water-canvas');
    if (!canvas) return;

    _waterfall = new WaterfallSystem(canvas);
    _dust      = new AmbientDustSystem(canvas);

    window.addEventListener('resize', () => {
        if (_waterfall) _waterfall._resize();
        if (_dust) {
            _dust.dust = [];
            _dust._init();
        }
    });

    function loop() {
        _waterfall.update();
        _dust.update();
        _waterfall.draw();
        _dust.draw();
        requestAnimationFrame(loop);
    }
    loop();
}

// ════════════════════════════════════════════════════════════
//  3D CARD TILT — light sheen follows cursor
// ════════════════════════════════════════════════════════════

function initCardTilt() {
    document.querySelectorAll('.panel').forEach(card => {
        let raf = null;
        let tx = 0, ty = 0;
        let cx = 0, cy = 0;

        card.addEventListener('mouseenter', () => {
            card.style.transition = 'transform 0.15s ease, box-shadow 0.15s ease';
        });

        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top)  / rect.height;

            // Target rotation
            tx = (y - 0.5) * -7;
            ty = (x - 0.5) * 7;
            cx = x * 100;
            cy = y * 100;

            if (raf) cancelAnimationFrame(raf);
            raf = requestAnimationFrame(() => {
                card.style.transform = `
                    perspective(900px)
                    rotateX(${tx}deg)
                    rotateY(${ty}deg)
                    translateZ(4px)
                    translateY(-1px)
                `;
                // Moving light sheen
                card.style.backgroundImage = `
                    radial-gradient(
                        ellipse 80% 60% at ${cx}% ${cy}%,
                        rgba(255,255,255,0.055) 0%,
                        transparent 65%
                    )
                `;
            });
        });

        card.addEventListener('mouseleave', () => {
            if (raf) cancelAnimationFrame(raf);
            card.style.transition = 'transform 0.65s cubic-bezier(0.23,1,0.32,1), box-shadow 0.65s cubic-bezier(0.23,1,0.32,1), background-image 0.3s ease';
            card.style.transform = 'perspective(900px) rotateX(0) rotateY(0) translateZ(0) translateY(0)';
            card.style.backgroundImage = 'none';
            setTimeout(() => { card.style.transition = ''; }, 700);
        });
    });
}

// ════════════════════════════════════════════════════════════
//  MAGNETIC AVATAR
// ════════════════════════════════════════════════════════════

function initMagneticAvatar() {
    const avatar = document.querySelector('.hero-avatar');
    if (!avatar) return;

    avatar.style.cursor = 'pointer';
    avatar.style.transition = 'transform 0.1s ease';

    avatar.addEventListener('mousemove', e => {
        const rect = avatar.getBoundingClientRect();
        const cx = rect.left + rect.width  / 2;
        const cy = rect.top  + rect.height / 2;
        const dx = (e.clientX - cx) * 0.38;
        const dy = (e.clientY - cy) * 0.38;
        avatar.style.transform = `translate(${dx}px, ${dy}px) scale(1.06)`;
        avatar.style.transition = 'transform 0.08s ease';
    });

    avatar.addEventListener('mouseleave', () => {
        avatar.style.transition = 'transform 0.55s cubic-bezier(0.34,1.56,0.64,1)';
        avatar.style.transform = 'translate(0,0) scale(1)';
    });
}

// ════════════════════════════════════════════════════════════
//  RIPPLE on click
// ════════════════════════════════════════════════════════════

function initRipple() {
    document.querySelectorAll('.stat-card, .quest-item, .boss-item').forEach(el => {
        el.style.position = 'relative';
        el.style.overflow = 'hidden';
        el.addEventListener('click', e => {
            const rect = el.getBoundingClientRect();
            const sz   = Math.max(rect.width, rect.height) * 2.2;
            const rp   = document.createElement('span');
            rp.style.cssText = `
                position: absolute;
                pointer-events: none;
                border-radius: 50%;
                width:  ${sz}px;
                height: ${sz}px;
                left:   ${e.clientX - rect.left - sz / 2}px;
                top:    ${e.clientY - rect.top  - sz / 2}px;
                background: radial-gradient(circle,
                    rgba(201,168,76,0.22) 0%,
                    rgba(196,103,58,0.08) 40%,
                    transparent 70%);
                transform: scale(0);
                animation: rippleExpand 0.65s cubic-bezier(0.0,0.0,0.2,1) forwards;
            `;
            el.appendChild(rp);
            setTimeout(() => rp.remove(), 700);
        });
    });
}

// ════════════════════════════════════════════════════════════
//  DATA LOADING
// ════════════════════════════════════════════════════════════

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

        // Re-init effects after DOM is populated
        requestAnimationFrame(() => {
            initCardTilt();
            initRipple();
        });

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

// ── Refresh dot ────────────────────────────────────────────────────────────────
function setRefreshDot(active) {
    const dot = document.getElementById('refresh-dot');
    if (!dot) return;
    active ? dot.classList.add('active') : dot.classList.remove('active');
}

function updateLastUpdatedText() {
    const el = document.getElementById('last-updated');
    if (!lastUpdated || !el) return;
    const mins = Math.floor((Date.now() - lastUpdated) / 60000);
    const dot  = el.querySelector('.refresh-dot');
    el.innerHTML = '';
    if (dot) el.appendChild(dot);
    el.appendChild(document.createTextNode(
        ' ' + (mins === 0 ? 'обновлено только что' : `обновлено ${mins} мин назад`)
    ));
    setTimeout(updateLastUpdatedText, 30000);
}

// ════════════════════════════════════════════════════════════
//  RENDER HELPERS
// ════════════════════════════════════════════════════════════

// ── Number counter animation ────────────────────────────────────────────────
function animateCounter(el, target, duration = 1000, decimals = 0) {
    if (!el || isNaN(target) || target === null) return;
    const startTime = performance.now();
    function update(now) {
        const p = Math.min((now - startTime) / duration, 1);
        const e = 1 - Math.pow(1 - p, 3);  // ease-out cubic
        el.textContent = decimals > 0
            ? (target * e).toFixed(decimals)
            : Math.round(target * e).toString();
        if (p < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ── Progress bar deferred ────────────────────────────────────────────────────
function animateBar(el, pct, delay = 90) {
    if (!el) return;
    el.style.width = '0%';
    setTimeout(() => { el.style.width = Math.min(100, Math.max(0, pct)) + '%'; }, delay);
}

// ── Hero ──────────────────────────────────────────────────────────────────────
function renderHero(data) {
    document.getElementById('hero-level').textContent    = data.level;
    document.getElementById('hero-level-name').textContent = data.level_name;
    document.getElementById('hero-class').textContent   = data.class_name || 'Путь трансформации';

    const range    = data.next_level_threshold - data.prev_level_threshold;
    const progress = range > 0
        ? (data.workouts_count - data.prev_level_threshold) / range * 100
        : 100;

    animateBar(document.getElementById('level-progress-bar'), progress);
    document.getElementById('level-progress-text').textContent =
        `${data.workouts_count} тренировок · следующий этап: ${data.next_level_threshold}`;

    animateCounter(document.getElementById('stat-strength'), data.strength, 950, 0);
    animateCounter(document.getElementById('stat-endurance'), data.endurance, 950, 0);
    animateCounter(document.getElementById('stat-recovery'), data.recovery, 950, 0);
    animateCounter(document.getElementById('stat-volume'), data.volume / 1000, 1100, 1);
}

// ── Quests / Практики ─────────────────────────────────────────────────────────
function renderQuests(quests) {
    const activeEl    = document.getElementById('active-quests-list');
    const completedEl = document.getElementById('completed-quests-list');
    activeEl.innerHTML    = '';
    completedEl.innerHTML = '';

    quests.forEach((q, i) => {
        const el = createQuestElement(q, i);
        (q.status === 'completed' ? completedEl : activeEl).appendChild(el);
    });

    // Defer bar animations until DOM settles
    setTimeout(() => {
        document.querySelectorAll('.quest-progress-fill[data-pct]').forEach(fill => {
            fill.style.width = fill.dataset.pct + '%';
        });
    }, 180);
}

function createQuestElement(quest, idx) {
    const div = document.createElement('div');
    div.className = `quest-item quest-${quest.status}`;
    div.style.cssText = 'opacity:0; transform:translateY(10px);';

    const pct  = (quest.progress * 100).toFixed(0);
    const show = quest.status !== 'locked';

    div.innerHTML = `
        <div class="quest-header">
            <span class="quest-icon">${quest.icon}</span>
            <div class="quest-info">
                <div class="quest-name">${quest.name}</div>
                <div class="quest-desc">${quest.description}</div>
            </div>
            <div class="quest-status-badge quest-badge-${quest.status}">${questStatusText(quest.status)}</div>
        </div>
        ${show ? `
        <div class="quest-progress-track">
            <div class="quest-progress-fill quest-fill-${quest.status}" style="width:0%" data-pct="${pct}"></div>
        </div>
        <div class="quest-progress-text">${quest.progress_text}</div>
        ` : ''}
    `;

    setTimeout(() => {
        div.style.transition = 'opacity 0.45s cubic-bezier(0.0,0.0,0.2,1), transform 0.45s cubic-bezier(0.0,0.0,0.2,1)';
        div.style.opacity    = '1';
        div.style.transform  = 'translateY(0)';
    }, idx * 45 + 80);

    return div;
}

function questStatusText(s) {
    return { active: 'в процессе', completed: 'достигнуто', locked: 'впереди' }[s] || s;
}

// ── Bosses / Рубежи ───────────────────────────────────────────────────────────
function renderBosses(bosses) {
    const el = document.getElementById('bosses-list');
    el.innerHTML = '';

    const cw = bosses.find(b => b.status === 'active')?.current_weight
             || bosses[0]?.current_weight || 0;
    animateCounter(document.getElementById('current-weight-display'), cw, 950, 1);

    bosses.forEach((boss, i) => {
        const div = document.createElement('div');
        div.className = `boss-item boss-${boss.status}`;
        div.style.cssText = 'opacity:0;';

        const pct = (boss.progress * 100).toFixed(0);
        div.innerHTML = `
            <div class="boss-header">
                <span class="boss-icon">${boss.icon}</span>
                <div class="boss-info">
                    <div class="boss-name">${boss.name}</div>
                    <div class="boss-target">Цель: ${boss.target_weight} кг</div>
                </div>
                <div class="boss-status-badge boss-badge-${boss.status}">${bossStatusText(boss.status)}</div>
            </div>
            <div class="boss-progress-track">
                <div class="boss-progress-fill boss-fill-${boss.status}" style="width:0%" data-pct="${pct}"></div>
            </div>
            <div class="boss-progress-text">${pct}% пройдено</div>
        `;
        el.appendChild(div);

        setTimeout(() => {
            div.style.transition = 'opacity 0.4s cubic-bezier(0.0,0.0,0.2,1)';
            div.style.opacity    = '1';
        }, i * 70 + 100);
    });

    setTimeout(() => {
        document.querySelectorAll('.boss-progress-fill[data-pct]').forEach(f => {
            f.style.width = f.dataset.pct + '%';
        });
    }, 200);
}

function bossStatusText(s) {
    return { defeated: 'достигнуто', active: 'в процессе', locked: 'впереди' }[s] || s;
}

// ── Stats ─────────────────────────────────────────────────────────────────────
function renderStats(stats) {
    const wEl = document.getElementById('sc-weight-val');
    stats.current_weight
        ? animateCounter(wEl, stats.current_weight, 950, 1)
        : (wEl.textContent = '—');

    animateCounter(document.getElementById('sc-workouts-val'),   stats.total_workouts     || 0, 1000);
    animateCounter(document.getElementById('sc-workouts30-val'), stats.workouts_30d       || 0, 850);
    animateCounter(document.getElementById('sc-streak-val'),     stats.current_streak_weeks || 0, 850);

    const volEl = document.getElementById('sc-total-vol-val');
    stats.total_volume
        ? animateCounter(volEl, stats.total_volume / 1000, 1100, 1)
        : (volEl.textContent = '0');

    const avgEl = document.getElementById('sc-avg5-val');
    stats.avg_volume_5
        ? animateCounter(avgEl, stats.avg_volume_5, 950, 0)
        : (avgEl.textContent = '—');

    if (stats.best_workout) {
        const bEl = document.getElementById('sc-best-val');
        animateCounter(bEl, stats.best_workout.total_volume_kg, 1050, 0);
        setTimeout(() => {
            if (!bEl.textContent.includes('кг')) bEl.textContent += ' кг';
        }, 1100);
        const d = new Date(stats.best_workout.workout_date);
        document.getElementById('sc-best-date').textContent =
            d.toLocaleDateString('ru-RU', { day:'2-digit', month:'2-digit', year:'numeric' });
    }
}

// ── Events / Хроника ──────────────────────────────────────────────────────────
function renderEvents(events) {
    const el = document.getElementById('event-list');
    el.innerHTML = '';
    events.forEach((ev, i) => {
        const div = document.createElement('div');
        div.className = 'event-item';
        div.style.cssText = 'opacity:0; transform:translateX(-10px);';
        div.innerHTML = `<span class="ev-date">${ev.date_str}</span> <span class="ev-icon">${ev.icon}</span> <span class="ev-text">${ev.text}</span>`;
        el.appendChild(div);
        setTimeout(() => {
            div.style.transition = 'opacity 0.38s cubic-bezier(0.0,0.0,0.2,1), transform 0.38s cubic-bezier(0.0,0.0,0.2,1)';
            div.style.opacity    = '1';
            div.style.transform  = 'translateX(0)';
        }, i * 48 + 80);
    });
}

// ── Weight Chart ──────────────────────────────────────────────────────────────
function renderWeightChart(data) {
    const ctx = document.getElementById('weight-chart').getContext('2d');

    const labels  = data.map(d => {
        const dt = new Date(d.date);
        return dt.toLocaleDateString('ru-RU', { day:'2-digit', month:'2-digit' });
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
                label:              'Вес (кг)',
                data:               weights,
                borderColor:        '#C9A84C',
                backgroundColor:    'rgba(201,168,76,0.07)',
                borderWidth:        1.5,
                pointBackgroundColor: '#C4673A',
                pointBorderColor:   '#C9A84C',
                pointBorderWidth:   1,
                pointRadius:        3,
                pointHoverRadius:   6,
                pointHoverBackgroundColor: '#C9A84C',
                tension:            0.4,
                fill:               true,
            }]
        },
        options: {
            responsive:          true,
            maintainAspectRatio: false,
            animation: { duration: 1100, easing: 'easeOutQuart' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#FFFDF8',
                    borderColor:     'rgba(196,103,58,0.22)',
                    borderWidth:     1,
                    titleColor:      '#2C1F14',
                    bodyColor:       '#7A6650',
                    titleFont:       { family:"'Playfair Display', Georgia, serif", size: 13, style:'italic' },
                    bodyFont:        { family:"'Lato', sans-serif", size: 12 },
                    padding:         12,
                    cornerRadius:    3,
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.y.toFixed(1)} кг`,
                    }
                }
            },
            scales: {
                x: {
                    grid:   { color:'rgba(196,103,58,0.06)', drawBorder:false },
                    ticks:  { color:'#A89070', font:{ family:"'Lato',sans-serif", size:11 } },
                    border: { display:false },
                },
                y: {
                    grid:   { color:'rgba(196,103,58,0.06)', drawBorder:false },
                    ticks:  { color:'#A89070', font:{ family:"'Lato',sans-serif", size:11 } },
                    border: { display:false },
                    min: ctx => {
                        const vals = ctx.chart.data.datasets[0].data;
                        return (!vals || !vals.length) ? 0 : Math.max(0, Math.min(...vals) - 2);
                    }
                }
            }
        }
    });
}
