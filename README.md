# opencode-delegate-subagents

Offload token-heavy grunt work (code scans, tests, mechanical refactors, research, log analysis, review) from an expensive primary model to **cheap OpenCode-native subagents**.

This is the successor approach to [`opencode-delegate-mcp`](https://github.com/mryesiller/opencode-delegate-mcp). The old repo is an MCP server so Claude Code or Codex can call `opencode run`. This repo uses OpenCode's own subagents (`.opencode/agents/*.md`, `mode: subagent`, per-agent `model`) so the primary OpenCode session delegates without an MCP hop.

Türkçe: [README.tr.md](README.tr.md)

## How it works

```
┌──────────────────────┐  subagent tool   ┌─────────────────────────────┐
│  Primary OpenCode    │ ───────────────► │  explorer / tester /        │
│  (expensive model)   │                  │  refactorer / researcher /  │
│                      │ ◄─────────────── │  log-analyzer / reviewer    │
└──────────────────────┘   short report   │  (cheap model, fresh ctx)   │
                                          └─────────────────────────────┘
```

- Subagents run in a **fresh child session** and return a compact report (see [AGENTS.md](AGENTS.md)) so the parent does not ingest raw logs.
- Read-only agents (`explorer`, `researcher`, `log-analyzer`, `reviewer`) have `edit` and `shell` denied.
- Write agents (`tester`, `refactorer`) may edit and run commands, but cannot `git commit` / `git push` or launch further subagents.

## Default models

IDs were checked against the **OpenCode 2.4.2** `opencode models` catalog (2026-11-26) and the public Z.AI / NVIDIA / OpenCode entries on [models.dev](https://models.dev).

| Subagent | Model | Writes? | Why this model |
| --- | --- | --- | --- |
| `explorer` | `opencode/mimo-v2.6-flash-free` | no | Free OpenCode model, enough for code maps |
| `tester` | `zai-coding-plan/glm-5.3` | yes | Z.AI Coding Plan flagship; solid coder on plan quota |
| `refactorer` | `zai-coding-plan/glm-5.3` | yes | Same, for mechanical multi-file edits |
| `researcher` | `opencode/deepseek-v4.1-flash-free` | no | Free OpenCode model, good at sourced summaries |
| `log-analyzer` | `nvidia/z-ai/glm-5.3-flash` | no | NVIDIA NIM, listed at $0, long context |
| `reviewer` | `zai-coding-plan/glm-5.3` | no | Stronger judgment than flash/free, still on Coding Plan quota |

Change any routing by editing the `model:` field in `.opencode/agents/<name>.md`.

`zai-coding-plan/glm-5.3` is the verified Z.AI **Coding Plan** id (models.dev and the OpenCode 2.4.2 catalog). Connect it with `opencode auth login` and choose **Z.AI Coding Plan**, or set `ZHIPU_API_KEY` (official env name; `ZAI_API_KEY` is also accepted as a fallback). The pay-per-token id `zai/glm-5.3` is a different provider. Some models.dev snapshots list `opencode/glm-5.3-flash-free` and `nvidia/z-ai/glm-5.3` (non-flash); those were **not** listed by `opencode models` on 2.4.2, so they are not the defaults. Coding Plan models appear in `opencode models` after that provider is connected.

OpenRouter is configured as an optional provider in `opencode.json`. After you connect it, run `opencode models` and point an agent at an OpenRouter id if you want.

## Requirements

- [OpenCode](https://opencode.ai) **2.x** recommended (validated against 2.4.2). OpenCode 1.19 also has subagents and still discovers `agent/` and `agents/`, but V2 frontmatter (`permissions` as a list, no `temperature` / `tools`) is what this repo ships. The official preferred path is `.opencode/agents/` (plural).
- Provider credentials via `opencode auth login` **or** environment variables: official Coding Plan name `ZHIPU_API_KEY` (fallback `ZAI_API_KEY`), plus `{env:NVIDIA_API_KEY}` and `{env:OPENROUTER_API_KEY}` in `opencode.json`. Never commit real keys.

## Install

```bash
git clone https://github.com/mryesiller/opencode-delegate-subagents.git
cd opencode-delegate-subagents
./install.sh --project /path/to/your/repo    # or: ./install.sh --global
```

- `--project [dir]` copies (default) or `--link`s the agent files into `<dir>/.opencode/agents/` and, if missing, `AGENTS.md`.
- `--global` does the same for `~/.config/opencode/agents/` (and `~/.config/opencode/AGENTS.md` only if that file does not already exist).
- The script is idempotent: identical files are skipped; agents are updated when the source changes. Existing `opencode.json` / `opencode.jsonc` and an existing `AGENTS.md` are never overwritten unless you pass `--force`.

Then, in the target repo or after a global install, connect providers and restart OpenCode:

```bash
cp .env.example .env   # fill locally, do not commit
# or:
opencode auth login    # choose Z.AI Coding Plan, plus NVIDIA / OpenCode / OpenRouter as needed
```

Ask the primary agent: *Use the explorer subagent to map src/.*

## Layout

```
.opencode/agents/     OpenCode 2.x subagent definitions
AGENTS.md             When to delegate, whom to call, report format
opencode.json         Example provider config (env vars only)
.env.example          Key names, no values
install.sh            Project or global install
mcp/                  Optional MCP bridge for Claude Code / Codex
docs/omp-role-mapping.md   Proposed alignment with omp roles (not applied)
```

## Claude Code setup (MCP bridge)

OpenCode-native subagents only run inside OpenCode. If the primary agent is **Claude Code** or **Codex** (for example on a Mac mini), use the maintained MCP bridge in [`mcp/`](mcp/README.md). It shells out to `opencode run` and defaults to `zai-coding-plan/glm-5.3`. It includes the OpenCode 2.x compatibility fix from [opencode-delegate-mcp#1](https://github.com/mryesiller/opencode-delegate-mcp/pull/1). This server does not store API keys — authenticate OpenCode on that machine first:

```bash
opencode auth login    # choose "Z.AI Coding Plan"
```

Build the server (Node 18+):

```bash
git clone https://github.com/mryesiller/opencode-delegate-subagents.git
cd opencode-delegate-subagents/mcp
npm install
npm run build
```

Register it with Claude Code (stdio, user scope). Replace the path with the absolute path to `mcp/dist/index.js` on that machine. Do **not** put API keys in this command:

```bash
claude mcp add --transport stdio --scope user opencode-delegate -- node /absolute/path/to/opencode-delegate-subagents/mcp/dist/index.js
```

The on-disk config (`~/.config/opencode-delegate/config.json`) uses camelCase. A missing file already defaults to the Coding Plan model; to set it explicitly:

```json
{
  "defaultModel": "zai-coding-plan/glm-5.3",
  "opencodeBin": "opencode"
}
```

Restart Claude Code (or `/mcp`) so it picks up the server.

Quick test from Claude Code, in a trusted directory:

> Use `list_models` with provider `zai-coding-plan`. Then use `delegate_task` to create a file `/tmp/opencode-delegate-smoke.txt` containing `hi`.

You should see `zai-coding-plan/glm-5.3` in the model list, and the smoke file created in `/tmp`. Then delete the smoke file. If `delegate_task` fails with an unknown `--dir` flag, the OpenCode 2.x binary is older than this port — rebuild from this repo.

## Configuration notes

- Do **not** put `temperature` or V1 `tools` / `permission` in these agent files. OpenCode 2.x documents those as legacy; a file that already uses V2 fields (`permissions`, `mode`, `model`) will ignore the old ones. Configure sampling on the provider/model if you need it.
- Keys belong in the environment or `opencode auth`, never in git. `.gitignore` ignores `.env` and `.env.*` but keeps `.env.example`.
- Model-to-role mapping should later be aligned with `~/.omp/agent/config.yml` (omp). See [docs/omp-role-mapping.md](docs/omp-role-mapping.md). This repository does not read that file.

## License

MIT. See [LICENSE](LICENSE).
