#!/usr/bin/env bash
# Lint agent frontmatter, opencode.json, and (optionally) load agents with OpenCode.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/validate.py" "$@"
