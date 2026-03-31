# VPN HIDE — АНТИ-DPI VPN

## ЦЕЛЬ
Скрыть факт использования VPN от российского оператора связи (DPI/ТСПУ).
Не обход белых списков — только маскировка трафика.

## СТАТУС
🟢 Поднято и работает (2026-03-31)

## ПРОТОКОЛЫ

### 1. Hysteria2 — ОСНОВНОЙ (UDP 443)
**Почему:** QUIC-based, маскируется под HTTP/3, Salamander obfuscation ломает
DPI-сигнатуру ещё на уровне первого пакета. Лучший выбор для Wi-Fi и там
где UDP 443 не режется.

**Конфиг на сервере:**
- Порт: `0.0.0.0:443/UDP` (nginx занимает только TCP 443 — конфликта нет)
- Auth password: `411a2ec8-ab60-4d42-8abf-5a4a07428a63`
- OBFS: salamander, password: `420d0879059e018cfdb02f38a7209b62`
- TLS cert: `/etc/letsencrypt/live/mcp.myserver-ai.ru/` (Let's Encrypt)
- SNI: `mcp.myserver-ai.ru`
- Masquerade: `https://www.bing.com`

**Строка подключения:**
```
hysteria2://411a2ec8-ab60-4d42-8abf-5a4a07428a63@147.45.238.120:443?obfs=salamander&obfs-password=420d0879059e018cfdb02f38a7209b62&sni=mcp.myserver-ai.ru&insecure=0#Hysteria2-mcp
```

---

### 2. VLESS + Reality — РЕЗЕРВ (TCP 2083)
**Почему:** Reality имитирует TLS-handshake реального сайта (www.microsoft.com).
DPI видит обычный HTTPS к Microsoft. Используй если UDP заблокирован.

**Конфиг на сервере:**
- Порт: `0.0.0.0:2083/TCP` (прямой, без nginx)
- UUID: `6406c688-4887-4bbd-aa77-5a79062f58bc`
- Flow: `xtls-rprx-vision`
- SNI (camouflage): `www.microsoft.com`
- Public key: `F16Dn4deH2JxnAqnsotNVOhoM0h7-NiHL1P-KIkaRQw`
- Private key: `wD9uDnqIGqKQboySBDPKanzFRJil6FWdZFKJaB4xIWM` (только на сервере!)
- Short ID: `534e476e60fa3c20`

**Строка подключения:**
```
vless://6406c688-4887-4bbd-aa77-5a79062f58bc@147.45.238.120:2083?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.microsoft.com&fp=chrome&pbk=F16Dn4deH2JxnAqnsotNVOhoM0h7-NiHL1P-KIkaRQw&sid=534e476e60fa3c20&type=tcp&headerType=none#VLESS-Reality
```

---

### 3. VLESS + WebSocket (старый, нетронутый)
- Доступен через `vpn.myserver-ai.ru/vpn/` (nginx TLS proxy)
- Порт sing-box: `127.0.0.1:10080`
- UUID: `eb9dff6e-149d-4569-b446-4cde3b041422`
- **Не маскирует факт VPN — только для совместимости**

---

## КЛИЕНТЫ

| Платформа | Приложение | Поддерживает |
|-----------|-----------|--------------|
| iOS | **Hiddify** | Hysteria2 + Reality |
| Android | **Hiddify** или v2rayNG | Hysteria2 + Reality |
| Windows | **Hiddify** или v2rayN | Hysteria2 + Reality |
| macOS | **Hiddify** | Hysteria2 + Reality |

**Добавление в Hiddify:** Вставить строку подключения (Add profile → вставить URL)

---

## КАК ПРОВЕРИТЬ МАСКИРОВКУ

1. **Wireshark / tcpdump на стороне оператора** — не у всех есть доступ
2. **Простой тест**: подключись и открой `https://2ip.ru` или `https://whoer.net`
   → должен показать IP нидерландского VPS
3. **OBFS Hysteria2 тест**: на сервере `tcpdump -i eth0 udp port 443` —
   увидишь случайные байты вместо QUIC-пакетов (значит Salamander работает)
4. **Reality тест**: DPI снаружи видит TLS ClientHello к `www.microsoft.com` —
   проверить через `tcpdump -i eth0 port 2083 -A | grep microsoft`

---

## АКТУАЛЬНОСТЬ (март 2026)

| Протокол | Статус в РФ |
|----------|-------------|
| WireGuard, OpenVPN, L2TP | ❌ Детектируется и блокируется |
| VLESS+WebSocket+TLS | ⚠️ Детектируется по паттернам WS |
| VLESS+Reality+TCP (vision) | ⚠️ 15-20KB TCP throttle для иностранных IP |
| **Hysteria2+Salamander** | ✅ Работает, лучший вариант для Wi-Fi |
| **VLESS+Reality** | ✅ Работает, резерв если UDP заблокирован |

## ГРАБЛИ
- `xhttp` транспорт НЕ скомпилирован в системном sing-box 1.13.4 → использован TCP+vision
- nginx занимает TCP 443, sing-box слушает UDP 443 — это разные протоколы, конфликта нет
- Hysteria2 SNI должен совпадать с Let's Encrypt сертом (`mcp.myserver-ai.ru`)

## ЧТО СДЕЛАНО
- [2026-03-31] Настроены Hysteria2+Salamander (UDP 443) + VLESS+Reality (TCP 2083) → sing-box 1.13.4 запущен, все существующие сервисы не тронуты

## СЛЕДУЮЩИЙ ШАГ
Протестировать подключение с телефона через мобильный интернет:
1. Hysteria2 строку в Hiddify
2. Если не работает — попробовать VLESS+Reality
3. Если Reality режется по 15-20KB — обновить sing-box и добавить xhttp транспорт

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Конфиг sing-box: `/etc/sing-box/config.json`
- Бэкап старого конфига: `/etc/sing-box/config.json.bak`
- Сертификат Hysteria2: `/etc/letsencrypt/live/mcp.myserver-ai.ru/`
