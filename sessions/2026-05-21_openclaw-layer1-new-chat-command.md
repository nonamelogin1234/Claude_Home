# OpenClaw слой 1 и команда перехода — 2026-05-21

## Что обсуждали
- OpenClaw Personal Secretary должен стать личным секретарем, а не девопс-ботом.
- Пользователь хочет, чтобы Коготь имел роботную личность в духе роботов-напарников из Interstellar: честность, сухой юмор, спокойствие, тактичность.
- Пользователя раздражает длинный ритуал перед переходом в новый чат: нужно заменить его одной командой «Переходим в новый чат».
- Нужно фиксировать MCP и локальные инструменты по рабочему/домашнему ПК, потому что Codex живет локально и настройки не переносятся автоматически.
- Важно: пользователь поправил, что Codex и Коготь нельзя смешивать. Codex — отдельная личность и рабочий инженерный напарник здесь. Коготь — отдельный OpenClaw-агент в Telegram.

## Что сделали
- Развернули слой 1 OpenClaw на `homeserver`.
- Добавили MCP `openclaw-secretary` через официальный Python SDK `mcp`/`FastMCP`.
- MCP дает allowlist-инструменты: `save_note`, `save_task`, `save_decision`, `search_memory`, `open_tasks`, `search_context`, `project_status`, `sync_context`.
- Настроили `Claude_Home` checkout на `homeserver`: `/home/sergei/Claude_Home`.
- Подключили запись в PostgreSQL `jarvis_memory` через таблицы `assistant_*`.
- Применили `openclaw exec-policy preset deny-all`, чтобы не было произвольного shell из Telegram.
- Добавили личность Когтя: `SOUL.md`, `IDENTITY.md`, `SECRETARY.md`, `AGENTS.md`, `MEMORY.md`.
- Проверили live-агента: он отвечает как “личный тактический робот-секретарь и второй мозг”.
- Добавили команду `.claude/commands/new-chat.md`.
- Добавили `brain/workstations.md` — реестр MCP и инструментов по рабочему ПК, домашнему ПК, homeserver и VPS.

## Что решили
- Фраза **«Переходим в новый чат»** означает: обновить контекст, memory graph, саммари сессии, commit, push и выдать готовый prompt для следующего чата.
- Если на одном компьютере настроили MCP/инструмент, это фиксируется в `brain/workstations.md`, чтобы повторить настройку на другом компьютере без повторного объяснения.
- Не говорить, что Коготь — это Codex или “форма Codex”. Это разные сущности/роли.

## Проверено
- `openclaw-secretary__save_note` сохраняет заметку в `assistant_notes`.
- `openclaw-secretary__project_status` возвращает красные/желтые хвосты из `brain/projects.md`.
- `openclaw-secretary__search_memory` + `search_context` находят решение по OpenClaw.
- Gateway OpenClaw активен после перезапуска.

## Следующий шаг
- Улучшить UX слоя 1: более умная классификация “запомни” → note/task/decision.
- При необходимости убрать тестовые записи из `assistant_*`.
- После push последних коммитов перевести `/home/sergei/Claude_Home` на чистую git-синхронизацию без ручного `scp` актуального `infra/openclaw`.
- В следующем чате начать с `git pull`, прочитать `brain/`, `infra/openclaw/context.md`, `infra/openclaw/implementation-plan.md`, `brain/workstations.md` и продолжить слой 1.
