#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Post or update a Grok review comment on the current pull request."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

MARKER = "<!-- grok-pr-review -->"
MODEL = "grok-4.6"
API_URL = "https://api.x.ai/v1/chat/completions"
MAX_DIFF_CHARS = 80_000

SYSTEM = """You review pull requests for VIA Browser Connect, a Linux udev/WebHID helper for VIA, Vial, and Keychron Launcher.

Focus on real problems: udev mistakes, permission/security issues, broken USB vs 2.4G copy, Python 3 compatibility, and missing human-facing instructions. Do not nitpick style. Do not rewrite the whole diff.

Reply in GitHub markdown with short sections:
- Summary (1-3 sentences)
- Issues (bullet list; write "None." if the diff looks sound)
- Notes (optional)

The human still reviews and merges. You are an assistant, not the maintainer.
"""


def run(args: list[str], *, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        input=input_bytes.decode("utf-8") if input_bytes is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )


def die(message: str, code: int = 1) -> None:
    sys.stderr.write(message.rstrip() + "\n")
    raise SystemExit(code)


def grok_review(api_key: str, diff: str, title: str) -> str:
    payload = {
        "model": MODEL,
        "temperature": 0.2,
        "max_tokens": 2048,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": f"Pull request title: {title}\n\nDiff:\n```\n{diff}\n```",
            },
        ],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        die(f"xAI API error {exc.code}: {detail}")
    try:
        text = body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        die(f"Unexpected xAI response: {body!r}")
    if not text:
        die("Grok returned an empty review.")
    return text


def gh_json(args: list[str]):
    result = run(["gh", *args])
    if result.returncode != 0:
        die(result.stderr or result.stdout or "gh failed")
    return json.loads(result.stdout) if result.stdout.strip() else None


def publish_comment(repo: str, pr: str, body: str) -> None:
    comments = gh_json(["api", f"repos/{repo}/issues/{pr}/comments"]) or []
    existing = next((c for c in comments if MARKER in (c.get("body") or "")), None)
    payload = json.dumps({"body": body}).encode("utf-8")
    if existing:
        path = f"repos/{repo}/issues/comments/{existing['id']}"
        result = run(["gh", "api", "--method", "PATCH", path, "--input", "-"], input_bytes=payload)
    else:
        path = f"repos/{repo}/issues/{pr}/comments"
        result = run(["gh", "api", "--method", "POST", path, "--input", "-"], input_bytes=payload)
    if result.returncode != 0:
        die(result.stderr or result.stdout or "failed to publish review comment")


def main() -> int:
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    repo = os.environ.get("REPO", "").strip()
    pr = os.environ.get("PR_NUMBER", "").strip()
    if not api_key:
        print(
            "No XAI_API_KEY secret. Add one from https://console.x.ai to enable Grok PR review. Skipping."
        )
        return 0
    if not repo or not pr:
        print("Not a pull request event. Skipping.")
        return 0

    diff_run = run(["gh", "pr", "diff", pr, "--repo", repo])
    if diff_run.returncode != 0:
        die(diff_run.stderr or "could not read pull request diff")
    diff = diff_run.stdout or ""
    if not diff.strip():
        print("Empty diff. Skipping.")
        return 0
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[diff truncated]\n"

    pr_info = gh_json(["pr", "view", pr, "--repo", repo, "--json", "title"]) or {}
    title = str(pr_info.get("title") or f"#{pr}")
    review = grok_review(api_key, diff, title)
    body = (
        f"{MARKER}\n"
        f"**Grok review** (`{MODEL}`). Human review still required.\n\n"
        f"{review}\n"
    )
    publish_comment(repo, pr, body)
    print(f"Posted Grok review on {repo}#{pr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
