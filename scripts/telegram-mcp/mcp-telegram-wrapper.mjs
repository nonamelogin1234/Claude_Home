import { execFileSync, spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// chdir to USERPROFILE so .telegram-agent resolves correctly on Windows
process.chdir(os.homedir());

const indexPath = path.join(__dirname, 'node_modules', '@overpod', 'mcp-telegram', 'dist', 'index.js');

// Pass through env (TELEGRAM_AGENT_HOME etc.) and inherit stdio for MCP
const child = spawn(process.execPath, [indexPath], {
  stdio: 'inherit',
  env: process.env,
});

child.on('exit', (code) => process.exit(code ?? 0));
