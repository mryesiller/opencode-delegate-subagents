#!/usr/bin/env python3
'''Validate agent markdown frontmatter, opencode.json, and secret hygiene.'''
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / '.opencode' / 'agents'
EXPECTED = {
    'explorer',
    'tester',
    'refactorer',
    'researcher',
    'log-analyzer',
    'reviewer',
}
READONLY = {'explorer', 'researcher', 'log-analyzer', 'reviewer'}
WRITE = {'tester', 'refactorer'}
REQUIRED_FRONTMATTER = {'description', 'mode', 'model'}
LEGACY_FIELDS = {'temperature', 'tools', 'permission', 'prompt', 'disable', 'maxSteps'}
SECRET_VALUE = re.compile(
    r'(?ix)(?:sk-|gsk_|ghp_|gho_|github_pat_|xai-|nvapi-|AIza)[A-Za-z0-9_\-]{12,}'
    r'|(?<![A-Za-z0-9_])(?:eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,})'
)

errors: list[str] = []
warnings: list[str] = []


def parse_frontmatter(text: str, path: Path) -> dict:
    if not text.startswith('---'):
        errors.append(f'{path}: missing YAML frontmatter')
        return {}
    end = text.find('\n---', 3)
    if end == -1:
        errors.append(f'{path}: unclosed frontmatter')
        return {}
    raw = text[3:end].strip('\n')
    data: dict = {}
    key = None
    current_list = None
    current_map = None
    for line in raw.splitlines():
        if re.match(r'^\s*-\s+', line) and key:
            item = line.strip()[1:].strip()
            if ':' in item and current_list is not None:
                k, v = item.split(':', 1)
                current_map = {k.strip(): _scalar(v.strip())}
                current_list.append(current_map)
            elif current_list is not None:
                current_list.append(_scalar(item))
                current_map = None
            else:
                errors.append(f'{path}: list item without a key: {line!r}')
        elif re.match(r'^\s{2,}\S', line) and current_map is not None:
            k, v = line.strip().split(':', 1)
            current_map[k.strip()] = _scalar(v.strip())
        elif ':' in line and not line.startswith(' '):
            k, v = line.split(':', 1)
            key = k.strip()
            v = v.strip()
            if v == '':
                current_list = []
                data[key] = current_list
                current_map = None
            else:
                data[key] = _scalar(v)
                current_list = None
                current_map = None
        elif line.strip() == '':
            continue
        else:
            errors.append(f'{path}: cannot parse frontmatter line: {line!r}')
    return data


def _scalar(v: str):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    if v.lower() in ('true', 'false'):
        return v.lower() == 'true'
    if re.fullmatch(r'-?\d+', v):
        return int(v)
    return v


def check_agents() -> None:
    if not AGENTS_DIR.is_dir():
        errors.append(f'missing {AGENTS_DIR}')
        return
    found = set()
    for path in sorted(AGENTS_DIR.glob('*.md')):
        name = path.stem
        found.add(name)
        text = path.read_text(encoding='utf-8')
        data = parse_frontmatter(text, path)
        if not data:
            continue
        for field in REQUIRED_FRONTMATTER:
            if field not in data:
                errors.append(f'{path}: missing `{field}`')
        if data.get('mode') != 'subagent':
            errors.append(f'{path}: mode must be subagent, got {data.get("mode")!r}')
        model = data.get('model')
        if not (isinstance(model, str) and '/' in model):
            errors.append(f'{path}: model must look like provider/model')
        for legacy in LEGACY_FIELDS:
            if legacy in data:
                errors.append(f'{path}: legacy V1 field `{legacy}` must not be used')
        perms = data.get('permissions')
        if not isinstance(perms, list) or not perms:
            errors.append(f'{path}: permissions list is required')
            continue
        denied = set()
        for rule in perms:
            if not isinstance(rule, dict) or not {'action', 'resource', 'effect'} <= set(rule):
                errors.append(f'{path}: invalid permission rule {rule!r}')
                continue
            if rule.get('effect') == 'deny':
                denied.add(rule.get('action'))
        if name in READONLY and 'edit' not in denied:
            errors.append(f'{path}: read-only agent must deny action: edit')
        if name in WRITE and 'edit' in denied and any(
            isinstance(r, dict) and r.get('action') == 'edit' and r.get('resource') == '*'
            for r in perms
        ):
            errors.append(f'{path}: write agent should not deny all edits')
        body = text.split('\n---', 2)[-1]
        if 'STATUS:' not in body or 'SUMMARY:' not in body:
            errors.append(f'{path}: body must require the compact STATUS/SUMMARY report')
    missing = EXPECTED - found
    extra = found - EXPECTED
    if missing:
        errors.append(f'missing agents: {sorted(missing)}')
    if extra:
        warnings.append(f'unexpected agents: {sorted(extra)}')


def check_opencode_json() -> None:
    path = ROOT / 'opencode.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{path}: invalid JSON: {exc}')
        return
    if data.get('$schema') != 'https://opencode.ai/config.json':
        warnings.append(f'{path}: $schema should be https://opencode.ai/config.json')
    providers = data.get('providers') or data.get('provider') or {}
    if not isinstance(providers, dict) or not providers:
        errors.append(f'{path}: expected providers (or provider) map')
        return
    blob = json.dumps(data)
    if SECRET_VALUE.search(blob):
        errors.append(f'{path}: looks like a committed secret value (not printed)')
    if '{env:' not in blob:
        errors.append(f'{path}: API keys must be referenced via {{env:VAR}} only')
    if re.search(r'"apiKey"\s*:\s*"(?!\{env:)', blob):
        errors.append(f'{path}: apiKey must use {{env:VAR}} substitution')


def check_secret_hygiene() -> None:
    skip_dirs = {'.git', 'node_modules', 'dist'}
    for path in ROOT.rglob('*'):
        if any(part in skip_dirs for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.name.startswith('.env') and path.name != '.env.example':
            errors.append(f'{path.relative_to(ROOT)}: env file should be gitignored, not committed')
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        if SECRET_VALUE.search(text):
            errors.append(f'{path.relative_to(ROOT)}: possible secret value (not printed)')
        if path.name == '.env.example' and re.search(
            r'^(ZHIPU_API_KEY|ZAI_API_KEY|NVIDIA_API_KEY|OPENROUTER_API_KEY)=.+$', text, re.M
        ):
            errors.append('.env.example must leave key values empty')


def maybe_run_opencode() -> None:
    candidates = []
    env_bin = os.environ.get('OPENCODE_BIN')
    if env_bin:
        candidates.append(env_bin)
    pinned = Path('/tmp/opencode-v2/opencode')
    if pinned.is_file():
        candidates.append(str(pinned))
    which = shutil.which('opencode')
    if which:
        candidates.append(which)
    seen = set()
    bins = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            bins.append(c)
    if not bins:
        warnings.append('opencode not found; skipped live agent listing')
        return

    for bin_path in bins:
        try:
            ver = subprocess.run(
                [bin_path, '--version'],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            warnings.append(f'{bin_path}: could not run --version ({exc})')
            continue
        combined = (ver.stdout or '') + (ver.stderr or '')
        version = combined.strip().splitlines()[-1] if combined.strip() else 'unknown'
        listed = None
        for args in ([bin_path, 'debug', 'agents'], [bin_path, 'agent', 'list']):
            try:
                proc = subprocess.run(
                    args,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=45,
                    cwd=str(ROOT),
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                warnings.append(f'{bin_path} {" ".join(args[1:])}: {exc}')
                continue
            out = (proc.stdout or '') + (proc.stderr or '')
            if proc.returncode == 0 and out.strip():
                listed = out
                break
        if not listed:
            warnings.append(f'{bin_path} ({version}): could not list agents')
            continue
        missing = [name for name in sorted(EXPECTED) if name not in listed]
        if missing:
            msg = f'{bin_path} ({version}) did not list: {", ".join(missing)}'
            if re.search(r'\bv?1\.', version):
                warnings.append(msg + ' (OpenCode 1.x may not load V2 frontmatter)')
            else:
                errors.append(msg)
        else:
            print(f'ok    {bin_path} ({version}) listed all {len(EXPECTED)} subagents')


def main() -> int:
    check_agents()
    check_opencode_json()
    check_secret_hygiene()
    maybe_run_opencode()
    for w in warnings:
        print(f'warn  {w}')
    if errors:
        for e in errors:
            print(f'error {e}', file=sys.stderr)
        print(f'FAILED with {len(errors)} error(s), {len(warnings)} warning(s)')
        return 1
    print(f'OK ({len(warnings)} warning(s))')
    return 0


if __name__ == '__main__':
    sys.exit(main())
