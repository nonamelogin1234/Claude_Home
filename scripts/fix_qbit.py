import re

path = '/home/sergei/qbittorrent/config/qBittorrent/qBittorrent.conf'

with open(path, 'r') as f:
    content = f.read()

# Убираем забаненные IP
content = re.sub(r'WebUI\\BanList=.*\n', 'WebUI\\BanList=\n', content)
# Сбрасываем счётчик неудачных попыток
content = re.sub(r'WebUI\\LoginFailedBanDuration=.*\n', '', content)

with open(path, 'w') as f:
    f.write(content)

print('Ban cleared')
print()
# Показать текущий WebUI блок
for line in content.split('\n'):
    if 'WebUI' in line:
        print(line)
