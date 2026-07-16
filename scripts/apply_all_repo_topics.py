#!/usr/bin/env python3
"""Apply GitHub descriptions and topics for chaffybird56 repos from repo_topics_catalog.json."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "chaffybird56"
SKIP = {"chaffybird56", "portfolio", "BatteryPack"}
CATALOG = Path(__file__).resolve().parent / "repo_topics_catalog.json"
MAX_TOPICS = 20


def git_token() -> str:
    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
    )
    creds = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    token = creds.get("password")
    if not token:
        raise SystemExit("No GitHub token from git credential helper.")
    return token


def api(token: str, method: str, path: str, body: dict | None = None) -> tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def get_topics(token: str, repo: str) -> list[str]:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{repo}/topics",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.mercy-preview+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()).get("names", [])
    except urllib.error.HTTPError:
        return []


def merge_topics(existing: list[str], new: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for t in existing + new:
        t = t.strip().lower().replace(" ", "-")
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= MAX_TOPICS:
            break
    return out


def main() -> None:
    catalog = json.loads(CATALOG.read_text())
    token = git_token()
    updated = skipped = failed = 0

    for repo, meta in sorted(catalog.items()):
        if repo in SKIP:
            continue
        desc = meta["description"]
        desired = meta["topics"]
        try:
            existing = get_topics(token, repo)
        except Exception:
            existing = []
        topics = merge_topics(existing, desired)

        s1, _ = api(token, "PATCH", f"/repos/{OWNER}/{repo}", {"description": desc})
        s2, body2 = api(
            token,
            "PUT",
            f"/repos/{OWNER}/{repo}/topics",
            {"names": topics},
        )
        if s1 == 200 and s2 == 200:
            added = len(set(topics) - set(existing))
            print(f"OK  {repo}: {len(topics)} topics (+{added} new)")
            updated += 1
        else:
            print(f"FAIL {repo}: PATCH={s1} PUT={s2} {body2[:120]}")
            failed += 1
        time.sleep(0.35)

    print(f"\nDone: {updated} updated, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()
