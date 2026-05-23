# Codex Home startup protocol

Default workspace:

```text
C:\Users\no-na\Desktop\2027\Codex_Home
```

At the start of a new chat, Codex should:

1. Work from this folder by default.
2. Run `.\codex-start.ps1` if a repository is already cloned here.
3. Pull the latest changes from the current Git branch.
4. Read the main context files that exist in the repository:
   - `README.md`
   - `CLAUDE.md`
   - `AGENTS.md`
   - `CONTRIBUTING.md`
   - `docs\*.md`
   - `.github\pull_request_template.md`
   - `.github\copilot-instructions.md`
5. Make local edits in this workspace.
6. Commit, push, or open PRs only after the user explicitly asks.

Repository URL:

```text
https://github.com/nonamelogin1234/Claude_Home
```
