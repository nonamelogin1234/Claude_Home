const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const state = {
  chart: null,
  lastMeta: null,
};

const endpoints = {
  hero: "/api/hero",
  quests: "/api/quests",
  bosses: "/api/bosses",
  stats: "/api/stats",
  events: "/api/events",
  weightChart: "/api/weight-chart",
};

document.addEventListener("DOMContentLoaded", () => {
  renderSkeletons();
  refreshDashboard();
  window.setInterval(refreshDashboard, REFRESH_INTERVAL_MS);
});

async function refreshDashboard() {
  setStatus("Призываем свежие данные из хроник...", null);

  try {
    const responses = await Promise.all(
      Object.entries(endpoints).map(async ([key, url]) => [key, await fetchJson(url)]),
    );
    const payloads = Object.fromEntries(responses);

    renderHero(payloads.hero.hero);
    renderQuests(payloads.quests.quests);
    renderBosses(payloads.bosses.bosses);
    renderStats(payloads.stats.stats);
    renderEvents(payloads.events.events);
    renderWeightChart(payloads.weightChart.points);

    const meta = latestMeta(payloads);
    state.lastMeta = meta;
    setStatus(meta.stale ? "Показаны последние сохранённые данные" : "Хроники обновлены", meta);
  } catch (error) {
    setStatus(`Связь с API потеряна: ${error.message}`, state.lastMeta, true);
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function renderSkeletons() {
  setHtml("hero-stats", Array.from({ length: 4 }).map(() => `<div class="attribute skeleton"></div>`).join(""));
  setHtml("active-quests", `<div class="quest-item skeleton"></div><div class="quest-item skeleton"></div>`);
  setHtml("archive-quests", `<div class="quest-item skeleton"></div>`);
  setHtml("bosses-list", Array.from({ length: 5 }).map(() => `<div class="boss-card skeleton"></div>`).join(""));
  setHtml("stats-grid", Array.from({ length: 8 }).map(() => `<div class="stat-card skeleton"></div>`).join(""));
  setHtml("events-list", `<div class="event-item skeleton"></div><div class="event-item skeleton"></div>`);
}

function renderHero(hero) {
  document.getElementById("hero-class").textContent = hero.class || hero.hero_class || "Воин — Путь Трансформации";
  document.getElementById("hero-level").textContent = `Уровень ${safeNumber(hero.level, 0)}`;
  document.getElementById("hero-rank").textContent = `Ранг: ${safeText(hero.rank_title)}`;
  document.getElementById("hero-last-workout").textContent = `Последний бой: ${formatDate(hero.last_workout_date)}`;
  document.getElementById("hero-progress-label").textContent = `${safeNumber(hero.progress_percent, 0).toFixed(1)}%`;
  document.getElementById("hero-progress-bar").style.width = `${clampPercent(hero.progress_percent)}%`;

  setHtml(
    "hero-stats",
    (hero.stats || [])
      .map(
        (stat) => `
          <article class="attribute">
            <span>${escapeHtml(stat.name)}</span>
            <strong>${escapeHtml(stat.display_value)}</strong>
            <p>${escapeHtml(stat.unit)}</p>
          </article>
        `,
      )
      .join(""),
  );
}

function renderQuests(quests) {
  const active = quests.filter((quest) => quest.category === "active");
  const archive = quests.filter((quest) => quest.category === "archive");

  setHtml("active-quests", active.map(renderQuestCard).join("") || emptyBlock("Нет активных квестов"));
  setHtml("archive-quests", archive.map(renderQuestCard).join("") || emptyBlock("Архив пока пуст"));
}

function renderQuestCard(quest) {
  return `
    <article class="quest-item">
      <header>
        <div>
          <div>${escapeHtml(quest.icon)} ${escapeHtml(quest.title)}</div>
          <p>${escapeHtml(quest.description)}</p>
        </div>
        <span class="pill ${escapeClassName(quest.status)}">${escapeHtml(questStatusText(quest.status))}</span>
      </header>
      <div class="mini-progress">
        <div class="quest-progress">
          <span>${escapeHtml(quest.progress_label)}</span>
          <span>${clampPercent(quest.progress_percent).toFixed(0)}%</span>
        </div>
        <div class="progress-bar"><span style="width:${clampPercent(quest.progress_percent)}%"></span></div>
      </div>
    </article>
  `;
}

function renderBosses(bosses) {
  setHtml(
    "bosses-list",
    bosses
      .map(
        (boss) => `
          <article class="boss-card">
            <header>
              <div>
                <div>${escapeHtml(boss.icon)} ${escapeHtml(boss.title)}</div>
                <p>Цель: ${safeNumber(boss.target_weight, 0).toFixed(1)} кг</p>
              </div>
              <span class="pill ${escapeClassName(boss.status)}">${escapeHtml(bossStatusText(boss.status))}</span>
            </header>
            <strong>${boss.current_weight != null ? `${safeNumber(boss.current_weight, 0).toFixed(1)} кг сейчас` : "Нет веса"}</strong>
            <p>${escapeHtml(boss.subtitle)}</p>
            <div class="progress-bar"><span style="width:${clampPercent(boss.progress_percent)}%"></span></div>
          </article>
        `,
      )
      .join(""),
  );
}

function renderStats(stats) {
  const cards = [
    ["Вес сегодня", stats.current_weight != null ? `${safeNumber(stats.current_weight, 0).toFixed(1)} кг` : "Нет данных", formatDate(stats.current_weight_date)],
    ["Всего тренировок", `${safeInt(stats.total_workouts, 0)}`, "Журнал Hevy"],
    ["Тренировок за 30 дней", `${safeInt(stats.workouts_last_30_days, 0)}`, "Последний месяц"],
    ["Серия недель", `${safeInt(stats.current_week_streak, 0)}`, "Недель подряд с тренировками"],
    ["Суммарный объём", `${Math.round(safeNumber(stats.total_volume_kg, 0))} кг`, "За всё время"],
    ["Рекордная тренировка", stats.record_workout_volume_kg != null ? `${Math.round(safeNumber(stats.record_workout_volume_kg, 0))} кг` : "Нет данных", formatDate(stats.record_workout_date)],
    ["Средний объём 5 тренировок", `${Math.round(safeNumber(stats.average_last_5_workouts_kg, 0))} кг`, "Скользящее среднее"],
    ["Текущий фокус", stats.current_weight && safeNumber(stats.current_weight, 0) > 110 ? "Страж Порога" : "Следующий рубеж", "Контроль веса"],
  ];

  setHtml(
    "stats-grid",
    cards
      .map(
        ([title, value, subtitle]) => `
          <article class="stat-card">
            <span>${escapeHtml(title)}</span>
            <strong>${escapeHtml(value)}</strong>
            <p>${escapeHtml(subtitle)}</p>
          </article>
        `,
      )
      .join(""),
  );
}

function renderEvents(events) {
  setHtml(
    "events-list",
    events
      .map(
        (event) => `
          <article class="event-item">
            <header>
              <span>${escapeHtml(event.icon)} ${escapeHtml(event.title)}</span>
              <span class="event-date">${escapeHtml(formatShortDate(event.date))}</span>
            </header>
            <p>${escapeHtml(event.description)}</p>
          </article>
        `,
      )
      .join("") || emptyBlock("События появятся, как только в БД будут записи."),
  );
}

function renderWeightChart(points) {
  const ctx = document.getElementById("weight-chart");
  if (!window.Chart || !ctx) {
    return;
  }

  const labels = points.map((point) => formatShortDate(point.date));
  const values = points.map((point) => safeNumber(point.weight, 0));
  const data = {
    labels,
    datasets: [
      {
        label: "Вес",
        data: values,
        borderColor: "#f0c060",
        backgroundColor: "rgba(240, 192, 96, 0.18)",
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 5,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: "#f6edd1" } },
    },
    scales: {
      x: { ticks: { color: "#c8b98d" }, grid: { color: "rgba(240,192,96,0.08)" } },
      y: { ticks: { color: "#c8b98d" }, grid: { color: "rgba(240,192,96,0.08)" } },
    },
  };

  if (state.chart) {
    state.chart.data = data;
    state.chart.update();
    return;
  }

  state.chart = new Chart(ctx, { type: "line", data, options });
}

function latestMeta(payloads) {
  return Object.values(payloads)
    .map((payload) => payload.meta)
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))[0];
}

function setStatus(message, meta, isError = false) {
  const statusText = document.getElementById("status-text");
  const statusUpdated = document.getElementById("status-updated");

  statusText.textContent = message;
  statusText.style.color = isError ? "#ffb08d" : "";
  statusUpdated.textContent = meta?.updated_at
    ? `Обновлено: ${new Date(meta.updated_at).toLocaleString("ru-RU")}`
    : "Ожидание первого ответа";
}

function emptyBlock(text) {
  return `<article class="quest-item"><p>${escapeHtml(text)}</p></article>`;
}

function setHtml(id, value) {
  document.getElementById(id).innerHTML = value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeClassName(value) {
  return String(value ?? "").replace(/[^a-z0-9_-]/gi, "");
}

function safeText(value) {
  return String(value ?? "");
}

function safeNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function safeInt(value, fallback) {
  return Math.trunc(safeNumber(value, fallback));
}

function clampPercent(value) {
  return Math.max(0, Math.min(100, safeNumber(value, 0)));
}

function formatDate(value) {
  if (!value) {
    return "нет данных";
  }
  return new Date(value).toLocaleDateString("ru-RU");
}

function formatShortDate(value) {
  if (!value) {
    return "--.--";
  }
  return new Date(value).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
}

function questStatusText(status) {
  return { active: "Активен", completed: "Выполнен", locked: "Закрыт" }[status] || status;
}

function bossStatusText(status) {
  return { active: "Активный", completed: "Побеждён", locked: "Закрыт" }[status] || status;
}
