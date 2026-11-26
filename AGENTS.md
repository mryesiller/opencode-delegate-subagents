# Delegation guide

This project offloads **high-volume, low-risk** work from an expensive primary model to cheaper OpenCode subagents. The primary agent keeps architecture, judgment, and security-sensitive work.

OpenCode 2.x launches these as child sessions (`mode: subagent`) via the `subagent` tool. Ask for the agent by name, for example:

> Use the explorer subagent to map how authentication is wired under `src/auth`.

Definitions live in `.opencode/agents/*.md` (preferred OpenCode 2.x path). Install them globally with `./install.sh --global` or into a project with `./install.sh --project /path/to/repo`.

This is **not** the same as the built-in `explore` / `general` subagents: those inherit the parent model unless you override them. These specialists are pinned to cheaper models.

## When the primary agent MUST keep the work

Do **not** delegate:

- Architecture, system design, or choosing abstractions and dependencies
- Security-sensitive code: auth, crypto, input validation, secrets, permissions
- Concurrency, performance-critical paths, or subtle correctness
- Ambiguous requirements that still need a judgment call or a clarifying question
- Public API / interface design and breaking changes
- Debugging a non-obvious failure whose root cause is unknown (you may delegate log analysis, then decide yourself)
- Anything where a wrong edit is costly or hard to detect

Heuristic: **high volume + low risk → delegate. Low volume + high risk → keep it. When unsure, keep it.**

## When to delegate, and to whom

Delegate only when the task is self-contained (briefable without the full chat history), has clear acceptance criteria, and the blast radius is small.

| Situation | Subagent | Writes? |
| --- | --- | --- |
| Recon: map a repo/area, find symbols and call sites | `explorer` | no |
| Write or run tests for well-specified behavior | `tester` | yes (tests; prod only if unavoidable) |
| Mechanical edits: renames, moves, prop/signature propagation, import updates, lint/type fixes | `refactorer` | yes |
| Look up docs, APIs, library options; compare approaches | `researcher` | no |
| Parse logs, traces, CI failure output for likely causes | `log-analyzer` | no |
| Review a diff or change for bugs, regressions, security, missing tests | `reviewer` | no |

Do not send write tasks to the read-only agents. Do not ask `refactorer` or `tester` to design a new architecture.

## How to brief a subagent

Give a complete, self-contained brief:

1. Goal and acceptance criteria (ideally verifiable)
2. Scope (paths, symbols, commands) and what is out of scope
3. Constraints (do not touch X, match existing style Y)
4. How to verify (test command, typecheck, expected files)

The child starts with a **fresh context**. It cannot see your earlier conversation unless you paste the needed facts into the brief.

## Required report format

Every subagent in this repo is instructed to return only this compact report, so the expensive parent does not ingest raw logs or file dumps:

```
STATUS: OK | PARTIAL | FAIL
SUMMARY:
- 3–6 bullets of the outcome
FILES: (omit if none)
- path — one-line description
EVIDENCE:
- commands + exit status, or the 2–3 most important findings with file:line
RISKS:
- only unresolved issues or follow-ups; omit if none
```

After a write delegation, verify the result yourself (tests, typecheck, or a `reviewer` pass) before accepting it.

## Models

Default routing (verified in the OpenCode 2.4.2 `opencode models` catalog on 2026-11-26). Swap the `model:` field in the agent markdown if you prefer another cheap model.

| Subagent | Default model | Why |
| --- | --- | --- |
| `explorer` | `opencode/mimo-v2.6-flash-free` | Free OpenCode model, good enough for code maps, no paid key required once the OpenCode provider is available |
| `tester` | `zai/glm-5.3` | Strong, cheaper coder for writing and running tests |
| `refactorer` | `zai/glm-5.3` | Same: mechanical edits need a solid coding model |
| `researcher` | `opencode/deepseek-v4.1-flash-free` | Free OpenCode model, solid at gathering and summarizing sources |
| `log-analyzer` | `nvidia/z-ai/glm-5.3-flash` | Free on NVIDIA NIM in the current catalog, long context for bulky logs |
| `reviewer` | `zai/glm-5.3` | Review needs better judgment than a flash/free model; still much cheaper than a frontier parent |

Notes:

- `zai/glm-5.3` is the real Z.AI catalog id (not a typo). If you subscribe to the Z.AI Coding Plan, `opencode auth login` and consider `zai-coding-plan/glm-5.3` instead.
- `opencode/glm-5.3-flash-free` and `nvidia/z-ai/glm-5.3` (non-flash) appear on some models.dev snapshots but were **not** in the OpenCode 2.4.2 catalog; this repo does not use them as defaults.
- After connecting OpenRouter, run `opencode models` and you can point any agent at an OpenRouter id. Keys are referenced only as `{env:ZAI_API_KEY}`, `{env:NVIDIA_API_KEY}`, `{env:OPENROUTER_API_KEY}` — never put a real key in git or in chat.
- Sampling (`temperature`) is **not** set in agent frontmatter. OpenCode 2.x treats `temperature` / `tools` as legacy V1 fields and ignores them in V2 files. Use `permissions` instead of `tools`.

## Claude Code (Mac) and MCP

Native subagents run **inside OpenCode**. Claude Code (and Codex) cannot launch these markdown agents directly. A minimal MCP server that shells out to `opencode run` lives under `mcp/` for that path. See `mcp/README.md`.

## omp role alignment (todo)

A later pass should align these defaults with `~/.omp/agent/config.yml` on the Mac mini (roles: DEFAULT, SMOL, COMMIT, TINY, TASK, SLOW, PLAN, VISION, ADVISOR, REVIEW, designer, TEST). A proposed mapping is in `docs/omp-role-mapping.md`. This repo does not read that file.
