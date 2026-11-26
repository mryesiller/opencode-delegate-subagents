# MCP bridge (Claude Code / Codex)

OpenCode-native subagents in this repo only run **inside OpenCode**. If the primary agent is Claude Code or Codex (for example on a Mac mini), it cannot launch `.opencode/agents/*.md` directly. This directory is a maintained port of [`opencode-delegate-mcp`](https://github.com/mryesiller/opencode-delegate-mcp) that still shells out to `opencode run`.

Default model: `zai-coding-plan/glm-5.3` (Z.AI Coding Plan). This port includes the OpenCode 2.x compatibility fix from [PR #1](https://github.com/mryesiller/opencode-delegate-mcp/pull/1):

- Probe `opencode --version`. On 2.x, omit `--dir` / `--variant` and pass `provider/model#variant`.
- Set the child process `PWD` to the requested directory (2.x resolves the project from `$PWD`).
- If `tokens.total` is missing, sum input + output + reasoning.

The MCP server does **not** store API keys. Provider auth stays in OpenCode (`opencode auth login` → **Z.AI Coding Plan**, or the `ZHIPU_API_KEY` env var).

## Tools

| Tool | Purpose |
| --- | --- |
| `delegate_task` | Hand a self-contained coding task to a cheap model via OpenCode |
| `delegate_tests` | Write (and optionally run) tests for a given scope |
| `list_models` | List `provider/model` ids OpenCode can use |
| `get_delegate_config` / `set_delegate_config` | Read or change the default model and settings at runtime |

Prefer OpenCode-native subagents when you are already in OpenCode. Use this MCP when the parent is Claude Code or Codex.

## Claude Code setup

1. On the machine that will run Claude Code (and OpenCode), authenticate the Coding Plan. Do not put the key in git or in the `claude mcp add` command:

```bash
opencode auth login    # choose "Z.AI Coding Plan"
```

2. Build the server (Node 18+):

```bash
cd /absolute/path/to/opencode-delegate-subagents/mcp
npm install
npm run build
```

3. Register it with Claude Code. Replace the path with the absolute path to `dist/index.js` on that machine:

```bash
claude mcp add --transport stdio --scope user opencode-delegate -- node /absolute/path/to/opencode-delegate-subagents/mcp/dist/index.js
```

4. Optional on-disk config (camelCase) at `~/.config/opencode-delegate/config.json`. See `config.example.json`. If the file is missing, the server already defaults to `zai-coding-plan/glm-5.3`:

```json
{
  "defaultModel": "zai-coding-plan/glm-5.3",
  "opencodeBin": "opencode"
}
```

5. Restart Claude Code, or run `/mcp`, so it picks up the server.

### Quick test

In a trusted directory, ask Claude Code:

> Use `list_models` with provider `zai-coding-plan`. Then use `delegate_task` to create a file `/tmp/opencode-delegate-smoke.txt` containing `hi`.

Expect `zai-coding-plan/glm-5.3` in the list and a smoke file in `/tmp`. Delete the smoke file afterwards. If `delegate_task` fails with `Unrecognized flag: --dir`, rebuild this `mcp/` tree — an older 0.2.x server is not OpenCode 2.x compatible.

## Version

`0.3.1` — Coding Plan default model (`zai-coding-plan/glm-5.3`), ported from `opencode-delegate-mcp` `0.2.3` plus the 2.x backend fix.
