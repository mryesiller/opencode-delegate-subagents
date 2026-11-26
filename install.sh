#!/usr/bin/env bash
# Install OpenCode-native delegate subagents into a project or the user config.
# Idempotent: identical files are skipped; agent definitions are refreshed when
# the source changes. Existing AGENTS.md / opencode.json(c) are not overwritten
# unless --force is passed.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: install.sh [options]

  --project [DIR]   Install into DIR (default: current directory)
  --global          Install into ~/.config/opencode
  --link            Symlink agent files instead of copying
  --force           Overwrite existing AGENTS.md and example opencode.json
  -h, --help        Show this help

Examples:
  ./install.sh --project ~/src/my-app
  ./install.sh --global --link
USAGE
}

MODE=""
TARGET=""
LINK=0
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      MODE="project"
      if [[ "${2:-}" != "" && "${2:-}" != --* ]]; then
        TARGET="$2"
        shift 2
      else
        TARGET="$PWD"
        shift
      fi
      ;;
    --global)
      MODE="global"
      shift
      ;;
    --link)
      LINK=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$MODE" ]]; then
  MODE="project"
  TARGET="${TARGET:-$PWD}"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_AGENTS="$SCRIPT_DIR/.opencode/agents"
SRC_AGENTS_MD="$SCRIPT_DIR/AGENTS.md"
SRC_CONFIG="$SCRIPT_DIR/opencode.json"

if [[ ! -d "$SRC_AGENTS" ]]; then
  echo "error: agent definitions not found at $SRC_AGENTS" >&2
  exit 1
fi

if [[ "$MODE" == "global" ]]; then
  CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
  DEST_ROOT="$CONFIG_HOME/opencode"
  DEST_AGENTS="$DEST_ROOT/agents"
  DEST_AGENTS_MD="$DEST_ROOT/AGENTS.md"
  DEST_CONFIG_EXAMPLE="$DEST_ROOT/opencode.delegate-subagents.example.json"
else
  if [[ -z "$TARGET" ]]; then
    TARGET="$PWD"
  fi
  # Resolve to an absolute path without requiring the dir to exist yet.
  mkdir -p "$TARGET"
  TARGET="$(cd "$TARGET" && pwd)"
  DEST_ROOT="$TARGET"
  DEST_AGENTS="$TARGET/.opencode/agents"
  DEST_AGENTS_MD="$TARGET/AGENTS.md"
  DEST_CONFIG_EXAMPLE="$TARGET/opencode.delegate-subagents.example.json"
fi

mkdir -p "$DEST_AGENTS"

relpath() {
  # portable-enough relative path for symlink targets
  python3 - "$1" "$2" <<'PY'
import os, sys
print(os.path.relpath(sys.argv[1], sys.argv[2]))
PY
}

install_file() {
  local src="$1"
  local dest="$2"
  local kind="${3:-file}" # file | agents-md | config

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ "$LINK" -eq 1 && -L "$dest" ]]; then
      local current
      current="$(readlink "$dest")"
      local want
      if [[ "$current" = /* ]]; then
        want="$src"
      else
        want="$(relpath "$src" "$(dirname "$dest")")"
      fi
      if [[ "$current" == "$want" || "$(readlink -f "$dest" 2>/dev/null || true)" == "$(readlink -f "$src")" ]]; then
        echo "skip  $dest (already linked)"
        return 0
      fi
    elif [[ "$LINK" -eq 0 && -f "$dest" && ! -L "$dest" ]] && cmp -s "$src" "$dest"; then
      echo "skip  $dest (identical)"
      return 0
    fi

    if [[ "$kind" != "file" && "$FORCE" -ne 1 ]]; then
      echo "keep  $dest (exists, use --force to replace)"
      return 0
    fi

    rm -f "$dest"
  fi

  if [[ "$LINK" -eq 1 ]]; then
    local link_target
    link_target="$(relpath "$src" "$(dirname "$dest")")"
    ln -s "$link_target" "$dest"
    echo "link  $dest -> $link_target"
  else
    cp "$src" "$dest"
    echo "copy  $dest"
  fi
}

echo "Installing delegate subagents"
echo "  source: $SRC_AGENTS"
echo "  dest:   $DEST_AGENTS"
echo

shopt -s nullglob
for src in "$SRC_AGENTS"/*.md; do
  base="$(basename "$src")"
  install_file "$src" "$DEST_AGENTS/$base" "file"
done

# AGENTS.md: install when missing; only replace with --force
install_file "$SRC_AGENTS_MD" "$DEST_AGENTS_MD" "agents-md"

# Never touch an existing opencode.json / opencode.jsonc. Always refresh a
# clearly named example file (unless identical).
if [[ "$MODE" == "project" ]]; then
  if [[ -f "$DEST_ROOT/opencode.json" || -f "$DEST_ROOT/opencode.jsonc" || -f "$DEST_ROOT/.opencode/opencode.json" || -f "$DEST_ROOT/.opencode/opencode.jsonc" ]]; then
    install_file "$SRC_CONFIG" "$DEST_CONFIG_EXAMPLE" "file"
    echo "note  existing OpenCode config left unchanged; see $DEST_CONFIG_EXAMPLE"
  else
    if [[ "$FORCE" -eq 1 ]]; then
      install_file "$SRC_CONFIG" "$DEST_ROOT/opencode.json" "config"
    else
      install_file "$SRC_CONFIG" "$DEST_ROOT/opencode.json" "config"
    fi
  fi
else
  # Global: never overwrite ~/.config/opencode/opencode.json. Drop an example.
  install_file "$SRC_CONFIG" "$DEST_CONFIG_EXAMPLE" "file"
  if [[ -f "$DEST_ROOT/opencode.json" || -f "$DEST_ROOT/opencode.jsonc" ]]; then
    echo "note  existing $DEST_ROOT/opencode.json(c) left unchanged; merge providers from $DEST_CONFIG_EXAMPLE if needed"
  else
    echo "note  no global opencode.json found; copy $DEST_CONFIG_EXAMPLE to $DEST_ROOT/opencode.json and add keys via env / auth"
  fi
fi

echo
echo "Done. Restart OpenCode (or start a new session) so it picks up the agents."
echo "Connect providers with:  opencode auth login"
echo "Or set ZHIPU_API_KEY (Coding Plan; ZAI_API_KEY also accepted), NVIDIA_API_KEY, OPENROUTER_API_KEY (see .env.example)."
