@echo off
setlocal
rem SSH-туннель на VPS (172.18.0.4:5432 внутри docker-сети) + postgres MCP
rem Использует ключ id_ed25519 (уже добавлен на VPS, см. brain/workstations.md)

start /min ssh -i "%USERPROFILE%\.ssh\id_ed25519" -N -L 15432:172.18.0.4:5432 root@147.45.238.120

set DATABASE_URL=postgresql://jarvis:jarvis_pass@localhost:15432/jarvis_memory
npx -y @modelcontextprotocol/server-postgres "%DATABASE_URL%"
