# Proposed omp role ↔ subagent mapping

Göksel's `oh my pi` (omp) agent routes work by role from `~/.omp/agent/config.yml` (on the Mac mini). That file was **not** read for this repo. The table below is a proposal to reconcile later, once the real role-to-model mapping is confirmed.

| omp role | Suggested use in this repo | Candidate model family |
| --- | --- | --- |
| DEFAULT | Primary / expensive parent. Do not put this on a grunt subagent. | Keep as-is in omp (frontier or Göksel's chosen default) |
| SMOL | `explorer`, short lookups | `opencode/mimo-v2.6-flash-free` or `zai-coding-plan/glm-5.3-flash` |
| TINY | Very small text tasks; closest here is a fast flash model, not a dedicated agent yet | `opencode/mimo-v2.6-flash-free` |
| COMMIT | Commit messages — no dedicated subagent yet; add later if wanted | flash / SMOL-class |
| TASK | `tester`, `refactorer` (general mechanical coding) | `zai-coding-plan/glm-5.3` |
| TEST | `tester` | `zai-coding-plan/glm-5.3` |
| REVIEW | `reviewer` | `zai-coding-plan/glm-5.3` |
| ADVISOR | `researcher` | `opencode/deepseek-v4.1-flash-free` |
| SLOW | Deeper review or hard analysis still on a cheap coder, or keep on parent if quality matters | `zai-coding-plan/glm-5.3` or parent |
| PLAN | Planning should usually stay on the parent (or OpenCode built-in `plan`). Do not silently downgrade. | parent / PLAN model in omp |
| VISION | No specialist in this repo yet. A later agent could use a VL model such as `opencode/nemotron-3.5-super-vl-free` or `zai/glm-5v-turbo`. | VL model in omp |
| designer | No specialist in this repo yet. | omp designer model |

Until this is aligned, changing an agent's `model:` in `.opencode/agents/<name>.md` is the one-line way to follow omp.
