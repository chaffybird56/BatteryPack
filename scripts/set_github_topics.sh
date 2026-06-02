#!/usr/bin/env bash
# Apply GitHub repository description + topics from .github/repository-topics.json
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="${ROOT}/.github/repository-topics.json"
REPO="${1:-chaffybird56/BatteryPack}"

apply_via_gh() {
  command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1
}

apply_via_git_credential() {
  python3 << PY
import json
import subprocess
import sys
import urllib.request

config_path = "${CONFIG}"
repo = "${REPO}"

proc = subprocess.run(
    ["git", "credential", "fill"],
    input="protocol=https\\nhost=github.com\\n\\n",
    capture_output=True,
    text=True,
    cwd="${ROOT}",
)
creds = {}
for line in proc.stdout.splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        creds[k] = v
token = creds.get("password")
if not token:
    sys.exit(1)

data = json.load(open(config_path))

def api(method, path, body=None):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status

api("PATCH", f"/repos/{repo}", {"description": data["description"]})
api("PUT", f"/repos/{repo}/topics", {"names": data["topics"]})
print(f"Updated {repo}: description + {len(data['topics'])} topics (git credential)")
PY
}

if apply_via_gh; then
  DESC=$(python3 -c "import json; print(json.load(open('$CONFIG'))['description'])")
  mapfile -t TOPICS < <(python3 -c "import json; d=json.load(open('$CONFIG')); print('\n'.join(d['topics']))")
  ARGS=()
  for t in "${TOPICS[@]}"; do ARGS+=(--add-topic "$t"); done
  gh repo edit "$REPO" --description "$DESC" "${ARGS[@]}"
  echo "Updated $REPO via gh CLI."
elif apply_via_git_credential; then
  :
else
  echo "Could not authenticate. Options:"
  echo "  1) Ensure git can push to GitHub (credential helper), then re-run this script"
  echo "  2) mkdir -p ~/.local/gh && export GH_CONFIG_DIR=~/.local/gh && gh auth login"
  echo "  3) Repo → About → Topics → paste tags from README Topics section"
  exit 1
fi
