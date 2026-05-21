# Cost Footer

## Цель
Добавлять к ответам OpenClaw короткий хвост стоимости:

```text
(≈1.4 ₽)
```

## Важно
Модель не должна выдумывать стоимость. Стоимость считает внешний слой после ответа.

В session JSONL OpenClaw уже сохраняет usage:

```json
"usage": {
  "input": 11076,
  "output": 434,
  "cacheRead": 192,
  "cost": {
    "input": 0.013845,
    "output": 0.001085,
    "cacheRead": 0.0000384,
    "total": 0.0149684
  }
}
```

## MVP
`scripts/openclaw-cost-footer.py` читает последний assistant message из session JSONL и печатает рублевый footer.

```bash
USD_RUB_RATE=90 python3 scripts/openclaw-cost-footer.py \
  /home/sergei/.openclaw/agents/main/sessions/SESSION.jsonl
```

## Как встроить в Telegram
Варианты:

1. Плагин/hook OpenClaw на событии после финализации ответа: лучший вариант, хвост добавляется в тот же ответ.
2. Отдельный post-processor по session logs: проще, но может отправлять стоимость вторым сообщением.
3. Писать стоимость только в dashboard/лог: самый безопасный режим без шума в Telegram.

## Политика
- Если usage найден: писать `(≈N ₽)`.
- Если usage не найден: не выдумывать, писать `(стоимость: нет данных)` или молчать.
- Курс USD/RUB обновлять не на каждый запрос, а раз в день и хранить локально.
- Для heartbeat и служебных сообщений footer можно отключить.

