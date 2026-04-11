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

// ── Density profile: gaussian peaks for natural waterfall look ──────────────
function _waterfallDensity(xNorm, peaks) {
    // xNorm = 0..1; peaks = [{cx, sigma, amp}]
    return peaks.reduce((acc, p) => {
        const d = (xNorm - p.cx) / p.sigma;
        return acc + p.amp * Math.exp(-0.5 * d * d);
    }, 0.04);  // base ambient
}

class WaterfallCurtain {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx    = canvas.getContext('2d');
        this.foam   = [];
        this.mist   = [];
        this.t      = 0;
        // 2–3 dense columns that create "natural" waterfall structure
        this.peaks  = [
            { cx: 0.28, sigma: 0.14, amp: 0.28 },
            { cx: 0.62, sigma: 0.16, amp: 0.32 },
            { cx: 0.82, sigma: 0.09, amp: 0.18 },
        ];
        this._resize();
    }

    _resize() {
        const r   = this.canvas.parentElement.getBoundingClientRect();
        this.W    = r.width  || 900;
        this.H    = r.height || 280;
        this.canvas.width  = this.W;
        this.canvas.height = this.H;
        this.poolY = this.H * 0.80;
        this._buildThreads();
    }

    _buildThreads() {
        const spacing = 5.5;
        const count   = Math.ceil(this.W / spacing);
        this.threads  = Array.from({ length: count }, (_, i) => {
            const x     = i * spacing + (Math.random() - 0.5) * 2;
            const xNorm = x / this.W;
            const dens  = _waterfallDensity(xNorm, this.peaks);
            return {
                x,
                speed:   2.0 + Math.random() * 5.5,
                offset:  Math.random() * this.poolY * 2,
                w:       0.5 + Math.random() * 1.5,
                op:      Math.min(0.38, dens + Math.random() * 0.05),
                dashLen: 10 + Math.random() * 28,
                gapLen:  3  + Math.random() * 20,
                driftF:  0.002 + Math.random() * 0.006,
                driftPh: Math.random() * Math.PI * 2,
            };
        });
    }

    _spawnFoam(x) {
        if (Math.random() > 0.22) return;
        const xNorm = x / this.W;
        const dens  = _waterfallDensity(xNorm, this.peaks);
        if (Math.random() > dens * 3.5 + 0.15) return;
        const angle = -Math.PI * 0.88 + Math.random() * Math.PI * 0.76;
        const sp    = 0.6 + Math.random() * 3.2;
        this.foam.push({
            x, y: this.poolY + (Math.random() - 0.5) * 6,
            vx: Math.cos(angle) * sp,
            vy: Math.sin(angle) * sp - 1.0,
            r:  1.5 + Math.random() * 6,
            a:  0.55 + Math.random() * 0.4,
            dr: 0.018 + Math.random() * 0.022,
        });
    }

    _spawnMist() {
        if (Math.random() > 0.06) return;
        const cx = this.peaks[Math.floor(Math.random() * this.peaks.length)].cx * this.W;
        this.mist.push({
            x: cx + (Math.random() - 0.5) * this.W * 0.55,
            y: this.poolY + (Math.random() - 0.5) * 18,
            vx: (Math.random() - 0.5) * 0.9,
            vy: -0.35 - Math.random() * 0.85,
            r:  30 + Math.random() * 70,
            a:  0.04 + Math.random() * 0.05,
            dr: 0.0015 + Math.random() * 0.002,
        });
    }

    update() {
        // Scroll threads
        this.threads.forEach(th => {
            th.offset = (th.offset + th.speed) % (this.poolY * 2);
            th.x += Math.sin(this.t * th.driftF + th.driftPh) * 0.06;
        });
        // Spawn particles
        if (this.t % 2 === 0) {
            this.threads.forEach(th => this._spawnFoam(th.x));
        }
        this._spawnMist();
        // Update foam
        this.foam = this.foam.filter(p => {
            p.x += p.vx; p.y += p.vy; p.vy += 0.055; p.vx *= 0.96;
            p.life = (p.life || 1) - p.dr;
            return p.life > 0 && p.y < this.poolY + 14;
        });
        // Update mist
        this.mist = this.mist.filter(p => {
            p.x += p.vx + Math.sin(this.t * 0.012) * 0.35;
            p.y += p.vy; p.r += 0.45;
            p.life = (p.life || 1) - p.dr;
            return p.life > 0;
        });
        this.t++;
    }

    draw() {
        const ctx   = this.ctx;
        const W     = this.W;
        const H     = this.H;
        ctx.clearRect(0, 0, W, H);

        // ── 1. Water curtain (scrolling dashed threads) ────────────────────
        ctx.save();
        ctx.lineCap = 'butt';
        this.threads.forEach(th => {
            const g = ctx.createLinearGradient(0, 0, 0, this.poolY);
            g.addColorStop(0,    `rgba(100,175,238,0)`);
            g.addColorStop(0.07, `rgba(95,170,235,${th.op * 0.3})`);
            g.addColorStop(0.32, `rgba(85,162,232,${th.op})`);
            g.addColorStop(0.70, `rgba(75,152,228,${th.op * 1.4})`);
            g.addColorStop(0.91, `rgba(155,218,255,${th.op * 1.0})`);
            g.addColorStop(1,    `rgba(200,240,255,0)`);
            ctx.strokeStyle    = g;
            ctx.lineWidth      = th.w;
            ctx.setLineDash([th.dashLen, th.gapLen]);
            ctx.lineDashOffset = -th.offset;
            ctx.beginPath();
            ctx.moveTo(th.x, 0);
            ctx.lineTo(th.x, this.poolY);
            ctx.stroke();
        });
        ctx.setLineDash([]);
        ctx.restore();

        // ── 2. Light sparkles (shimmer through water) ──────────────────────
        ctx.save();
        if (this.t % 2 === 0) {
            const n = 14 + Math.floor(Math.random() * 18);
            for (let i = 0; i < n; i++) {
                // Bias sparkles toward dense zones
                const pk    = this.peaks[Math.floor(Math.random() * this.peaks.length)];
                const sx    = pk.cx * W + (Math.random() - 0.5) * W * 0.3;
                const sy    = 8 + Math.random() * this.poolY * 0.9;
                const sg    = ctx.createRadialGradient(sx, sy, 0, sx, sy, 3.5);
                sg.addColorStop(0, 'rgba(255,255,255,0.7)');
                sg.addColorStop(1, 'rgba(200,240,255,0)');
                ctx.fillStyle = sg;
                ctx.beginPath();
                ctx.arc(sx, sy, 3.5, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        ctx.restore();

        // ── 3. Mist blobs ─────────────────────────────────────────────────
        ctx.save();
        this.mist.forEach(p => {
            const a = (p.a || 0.04) * (p.life || 1);
            if (a < 0.005) return;
            const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
            g.addColorStop(0,   `rgba(215,238,255,${a})`);
            g.addColorStop(0.5, `rgba(190,225,250,${a * 0.38})`);
            g.addColorStop(1,   `rgba(170,215,248,0)`);
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.ellipse(p.x, p.y, p.r, p.r * 0.42, 0, 0, Math.PI * 2);
            ctx.fill();
        });
        ctx.restore();

        // ── 4. Foam / white spray ─────────────────────────────────────────
        ctx.save();
        this.foam.forEach(p => {
            const a = (p.a || 0.5) * (p.life || 1);
            if (a < 0.015) return;
            const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
            g.addColorStop(0,   `rgba(255,255,255,${a})`);
            g.addColorStop(0.45,`rgba(218,245,255,${a * 0.5})`);
            g.addColorStop(1,   `rgba(185,228,255,0)`);
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
        });
        ctx.restore();

        // ── 5. Pool surface ───────────────────────────────────────────────
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(0, H);
        for (let x = 0; x <= W; x += 2) {
            const xNorm = x / W;
            const dens  = _waterfallDensity(xNorm, this.peaks);
            const amp   = 1.5 + dens * 6;
            const wy = this.poolY
                + Math.sin(x * 0.042 + this.t * 0.062) * amp
                + Math.sin(x * 0.019 + this.t * 0.038) * (amp * 0.6)
                + Math.sin(x * 0.095 + this.t * 0.11)  * (amp * 0.3);
            ctx.lineTo(x, wy);
        }
        ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
        const pg = ctx.createLinearGradient(0, this.poolY, 0, H);
        pg.addColorStop(0,   'rgba(78,158,225,0.32)');
        pg.addColorStop(0.4, 'rgba(58,132,205,0.18)');
        pg.addColorStop(1,   'rgba(46,95,163,0.05)');
        ctx.fillStyle = pg;
        ctx.fill();
        ctx.restore();

        // ── 6. Top-edge fade (water "materializes" from above) ───────────
        ctx.save();
        const tf = ctx.createLinearGradient(0, 0, 0, 44);
        // Use the actual page background color
        tf.addColorStop(0, 'rgba(250,246,239,1)');
        tf.addColorStop(1, 'rgba(250,246,239,0)');
        ctx.fillStyle = tf;
        ctx.fillRect(0, 0, W, 44);
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

    _waterfall = new WaterfallCurtain(canvas);
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
