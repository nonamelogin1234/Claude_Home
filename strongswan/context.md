# IKEv2 VPN (strongSwan) для Samsung

## ЦЕЛЬ
Системный VPN на Samsung Android для управления через Samsung Routines (Bixby). Тип: IKEv2/IPSec MSCHAPv2.

## СТАТУС
🟢 Работает — VPN подключается, интернет идёт через туннель

## ЧТО СДЕЛАНО
- [2026-04-21] Развёрнут philplckthun/strongswan в Docker → подключение работает
- [2026-04-21] Сгенерированы CA + серверный сертификат через pki внутри контейнера
- [2026-04-21] Добавлены nftables правила для FORWARD и MASQUERADE → интернет через VPN
- [2026-04-21] CA-сертификат установлен на телефон

## СЛЕДУЮЩИЙ ШАГ
1. Сделать nftables правила persistent (`/etc/nftables.conf`)
2. Монтировать `/etc/ipsec.d` как Docker volume чтобы сертификаты не терялись при пересоздании
3. Настроить Samsung Routines сценарий вкл/выкл VPN

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Docker контейнер
```
docker run -d --name strongswan --restart=unless-stopped \
  --privileged --network=host \
  -e VPN_PSK=MyServerVpnKey2026 \
  -e VPN_USER=sergei \
  -e VPN_PASSWORD=Vpn2026Spb! \
  philplckthun/strongswan
```

### После запуска (обязательно!)
```bash
# Заменить ipsec.conf
curl -s https://raw.githubusercontent.com/nonamelogin1234/Claude_Home/main/strongswan/ipsec-clean.conf \
  -o /tmp/ipsec-clean.conf && docker cp /tmp/ipsec-clean.conf strongswan:/etc/ipsec.conf

# Добавить RSA ключ в secrets
docker exec strongswan sh -c 'echo ": RSA srv-key.pem" >> /etc/ipsec.secrets'
docker exec strongswan ipsec rereadsecrets

# nftables правила (ОБЯЗАТЕЛЬНО, иначе нет интернета)
nft insert rule ip filter FORWARD ip saddr 10.0.2.0/24 accept
nft insert rule ip filter FORWARD ip daddr 10.0.2.0/24 accept
```

### Генерация сертификатов (если пересоздан контейнер)
```bash
docker exec strongswan sh -c '
  pki --gen --type rsa --size 2048 --outform pem > /etc/ipsec.d/private/server-cert-key.pem
  pki --self --ca --lifetime 3650 --in /etc/ipsec.d/private/server-cert-key.pem \
    --dn "CN=MyServer VPN CA" --outform pem > /etc/ipsec.d/cacerts/ca-cert.pem
  pki --gen --type rsa --size 2048 --outform pem > /etc/ipsec.d/private/srv-key.pem
  pki --pub --in /etc/ipsec.d/private/srv-key.pem | \
    pki --issue --lifetime 3650 \
      --cacert /etc/ipsec.d/cacerts/ca-cert.pem \
      --cakey /etc/ipsec.d/private/server-cert-key.pem \
      --dn "CN=147.45.238.120" --san 147.45.238.120 --flag serverAuth \
      --outform pem > /etc/ipsec.d/certs/server-cert.pem
'
# Выгрузить CA для телефона
docker cp strongswan:/etc/ipsec.d/cacerts/ca-cert.pem /var/www/html/vpn-ca.pem
chmod 644 /var/www/html/vpn-ca.pem
```

### Настройки VPN на телефоне
| Поле | Значение |
|------|----------|
| Тип | IKEv2/IPSec MSCHAPv2 |
| Адрес сервера | 147.45.238.120 |
| Идентификатор IPSec | 147.45.238.120 |
| Сертификат ЦС | cn=myserver vpn ca (из списка) |
| Логин | sergei |
| Пароль | Vpn2026Spb! |

### Диагностика
```bash
# Проверить что сессия установилась
docker exec strongswan ipsec statusall | grep -E 'ESTABLISHED|bytes'

# Проверить трафик
tcpdump -i eth0 -n 'dst 8.8.8.8 or src 8.8.8.8' 

# Проверить nftables правила
nft list chain ip filter FORWARD | tail -10
```

## ГРАБЛИ
- При пересоздании контейнера — сертификаты уничтожаются. CA на телефоне надо менять.
- strongSwan перезаписывает /etc/ipsec.secrets при каждом старте → RSA ключ добавлять ПОСЛЕ старта
- nft add rule добавляет ПОСЛЕ встроенного drop → нужен nft **insert** rule
- Ubuntu 24.04: nftables (Docker) vs iptables-legacy (strongSwan) — разные наборы правил, только nftables реально работает
- philplckthun/strongswan создаёт несколько conn-ов — без замены ipsec.conf выбирает неправильный
