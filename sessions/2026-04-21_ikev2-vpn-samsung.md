# IKEv2 VPN Samsung + Jellyfin fix — 21.04.2026

## Что обсуждали
- Настройка системного IKEv2 VPN на Samsung Android (для Samsung Routines/Bixby сценариев)
- Лечение зависаний Jellyfin на домашнем сервере

## Что решили
- Samsung Android 12+ поддерживает только IKEv2 варианты (XAuth/L2TP убраны)
- Рабочий стек: `philplckthun/strongswan` + IKEv2 EAP-MSCHAPv2 + сертификат сервера
- Корень проблемы с «нет интернета»: Ubuntu 24.04 использует nftables для iptables, а strongSwan пишет правила в iptables-legacy — два разных набора правил
- Jellyfin тормозил из-за qBittorrent (2.5GB RAM) — рестарт qBittorrent решил

## Что сделали

### Jellyfin fix
- Обнаружен qBittorrent с 2.5GB RAM → `docker restart qbittorrent` → освободилась память

### IKEv2 VPN
- Развёрнут `philplckthun/strongswan` в Docker (--network=host, --privileged)
- Заменён `/etc/ipsec.conf` на чистый с одним conn `ikev2-eap-mschapv2`
- Сгенерированы CA и сертификат сервера через `pki` внутри контейнера
- CA-сертификат установлен на телефон, прописан в профиле VPN
- Добавлены правила в **nftables** (не iptables-legacy!):
  ```
  nft insert rule ip filter FORWARD ip saddr 10.0.2.0/24 accept
  nft insert rule ip filter FORWARD ip daddr 10.0.2.0/24 accept
  ```
- VPN работает: подключение + интернет через туннель

## Следующий шаг
- Сделать nftables-правила persistent (прописать в /etc/nftables.conf или скрипт запуска)
- Настроить Samsung Routines сценарий с вкл/выкл VPN
- Решить проблему пересоздания сертификатов при ребуте контейнера (монтировать /etc/ipsec.d как volume)

## Грабли (добавлены в grabli.md)
- Samsung Android 12+ — только IKEv2 типы
- philplckthun/strongswan перезаписывает ipsec.secrets при старте → RSA ключ добавлять после
- nft add rule добавляет ПОСЛЕ встроенного drop → нужен nft insert rule
- Ubuntu 24.04: Docker/nftables vs strongSwan/iptables-legacy — разные наборы правил
- При пересоздании контейнера — сертификаты теряются, CA на телефоне надо обновлять
