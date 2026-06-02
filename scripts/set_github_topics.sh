#!/usr/bin/env bash
# Apply GitHub repository topics locally (optional).
# Topics are normally applied by .github/workflows/set-topics.yml on push — no local auth required.
set -euo pipefail

REPO="${1:-chaffybird56/BatteryPack}"
CONFIG="${2:-$(dirname "$0")/../.github/repository-topics.json}"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  DESC=$(python3 -c "import json; print(json.load(open('$CONFIG'))['description'])")
  mapfile -t TOPICS < <(python3 -c "import json; d=json.load(open('$CONFIG')); print('\n'.join(d['topics']))")
  ARGS=()
  for t in "${TOPICS[@]}"; do ARGS+=(--add-topic "$t"); done
  gh repo edit "$REPO" --description "$DESC" "${ARGS[@]}"
  echo "Updated $REPO via gh CLI."
else
  echo "Local gh not available. Topics are set by GitHub Actions on push to main."
  echo "To trigger now: GitHub → Actions → 'Apply repository topics' → Run workflow"
  echo "Or fix gh config: mkdir -p ~/.local/gh && export GH_CONFIG_DIR=~/.local/gh"
fi
