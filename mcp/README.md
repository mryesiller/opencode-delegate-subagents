# MCP bridge (Claude Code / Codex)

OpenCode-native subagents in this repo only run **inside OpenCode**. If the primary agent is Claude Code or Codex (for example on a Mac mini), it cannot launch `.opencode/agents/*.md` directly. This directory is a minimal port of [`opencode-delegate-mcp`](https://github.com/mryesiller/opencode-delegate-mcp) that still shells out to `opencode run`.

This port includes the OpenCode 2.x compatibility fix from [PR #1](https://github.com/mryesiller/opencode-delegate-mcp/pull/1) (still open on the old repo as of 2026-11-26):

- Probe `opencode --version`. On 2.x, omit `--dir` / `--variant` and pass `provider/model#variant`.
- Set the child process `PWD` to the requested directory (2.x resolves the project from `$PWD`).
- If `tokens.total` is missing, sum input + output + reasoning.

The MCP server does **not** store API keys. Provider auth stays in OpenCode (`opencode auth login` or env vars).

## Tools

| Tool | Purpose |
| --- | --- |
| `delegate_task` | Hand a self-contained coding task to a cheap model via OpenCode |
| `delegate_tests` | Write (and optionally run) tests for a given scope |
| `list_models` | List `provider/model` ids OpenCode can use |
| `get_delegate_config` / `set_delegate_config` | Read or change the default model and settings at runtime |

Prefer OpenCode-native subagents when you are already in OpenCode. Use this MCP only when the parent is a different host (Claude Code, Codex).

## Build and register (Claude Code)

```bash
cd mcp
npm install
npm run build
```

Add a stdio MCP server that runs `node /absolute/path/to/opencode-delegate-subagents/mcp/dist/index.js`.

Config lives in `~/.config/opencode-delegate/config.json` (same as the old repo). Example:

```json
{
  "default_model": "zai/glm-5.3",
  "opencode_bin": "opencode"
}
```

Do not put API keys in that file. After changing MCP registration, restart Claude Code (or reload its MCP servers).

The original web installer and GitHub Pages site stay with the old repo; this tree only keeps the server.

## Version

`0.3.0` — port of `opencode-delegate-mcp` `0.2.3` plus the 2.x backend fix.
