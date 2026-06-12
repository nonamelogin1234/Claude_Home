import { existsSync, readdirSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

process.chdir(process.env.USERPROFILE || process.cwd());
process.env.TELEGRAM_AGENT_HOME = process.env.TELEGRAM_AGENT_HOME || ".telegram-agent";

function findMcpTelegramEntry() {
  if (process.env.MCP_TELEGRAM_ENTRY) {
    return process.env.MCP_TELEGRAM_ENTRY;
  }

  const localAppData = process.env.LOCALAPPDATA;
  if (!localAppData) {
    throw new Error("LOCALAPPDATA is not set; cannot find npm cache for mcp-telegram");
  }

  const npxCache = path.join(localAppData, "npm-cache", "_npx");
  for (const entry of readdirSync(npxCache, { withFileTypes: true })) {
    if (!entry.isDirectory()) {
      continue;
    }

    const candidate = path.join(
      npxCache,
      entry.name,
      "node_modules",
      "mcp-telegram",
      "dist",
      "index.js",
    );

    if (existsSync(candidate)) {
      return candidate;
    }
  }

  throw new Error(`mcp-telegram is not installed in ${npxCache}`);
}

await import(pathToFileURL(findMcpTelegramEntry()).href);
