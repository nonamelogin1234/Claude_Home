import hashlib, os, re

path = '/home/sergei/qbittorrent/config/qBittorrent/qBittorrent.conf'

password = '4815'
salt = os.urandom(16).hex()
h = hashlib.pbkdf2_hmac('sha512', password.encode(), salt.encode(), 100000)
password_hash = '@ByteArray(' + h.hex() + ':' + salt + ')'

with open(path, 'r') as f:
    content = f.read()

# Remove old password lines if any
content = re.sub(r'WebUI\\Password_PBKDF2.*\n', '', content)
content = re.sub(r'WebUI\\Password_ha1.*\n', '', content)

# Insert after WebUI\Port line
content = content.replace(
    'WebUI\\Port=8090',
    'WebUI\\Password_PBKDF2="' + password_hash + '"\nWebUI\\Port=8090'
)

with open(path, 'w') as f:
    f.write(content)

print('Password set OK')
print('Hash:', password_hash[:40], '...')
