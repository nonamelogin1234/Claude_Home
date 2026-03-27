# Claude_Home

Личная рабочая среда Claude — память, проекты, контекст.

## Структура

```
Claude_Home/
├── CLAUDE.md              ← точка входа для Claude Code
├── .claude/
│   ├── settings.json      ← разрешения
│   └── commands/
│       ├── start.md       ← /project:start — git pull
│       └── finish.md      ← /project:finish [сообщение] — git push
├── brain/
│   ├── CHAT_INIT.md       ← инструкция для claude.ai (что читать при инициализации)
│   ├── infra.md           ← серверы, порты, VPS, домашний сервер
│   ├── projects.md        ← статусы всех проектов
│   ├── grabli.md          ← что не делать и почему
│   └── rules.md           ← правила ведения файлов + шаблоны
├── docai/
│   ├── CLAUDE.md          ← контекст для Claude Code (загружается автоматически)
│   ├── context.md         ← статус проекта
│   └── [код проекта]
├── kinoclaude/
│   ├── CLAUDE.md          ← контекст для Claude Code
│   ├── context.md         ← статус проекта
│   └── [код проекта]
└── sessions/              ← саммари важных сессий claude.ai
```

## Первый раз на новом компе

```powershell
git clone https://github.com/nonamelogin1234/Claude_Home "C:\Users\ИМЯ\Documents\Claude_Home"
```

Потом создать `CLAUDE.local.md` в корне (он в .gitignore) с машинно-специфичными настройками:
```markdown
# Этот комп
- Имя: [домашний / рабочий]
- Пользователь: [user / torganov-a]
- Путь к srv.ps1: C:\Users\ИМЯ\srv.ps1
```

## Запуск Claude Code

```powershell
cd "C:\Users\ИМЯ\Documents\Claude_Home"
claude
```

## Claude Chat (claude.ai)
При инициализации говорить: **«читай контекст»** — читает `brain/CHAT_INIT.md` и следует инструкциям оттуда.
