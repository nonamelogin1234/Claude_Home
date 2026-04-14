path = '/home/sergei/qbittorrent/config/qBittorrent/qBittorrent.conf'
with open(path, 'r') as f:
    content = f.read()
if 'HostHeaderValidation' not in content:
    content = content.replace('WebUI\\Port=8090', 'WebUI\\Port=8090\nWebUI\\HostHeaderValidation=false\nWebUI\\CSRFProtection=false')
with open(path, 'w') as f:
    f.write(content)
print('done')
