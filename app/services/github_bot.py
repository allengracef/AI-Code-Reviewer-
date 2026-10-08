"""
GitHub Bot Service
==================
Handles all GitHub API communication for the BugLens bot:
  - Generating a GitHub App JWT
  - Exchanging it for an installation access token
  - Fetching changed files from a push or PR
  - Posting inline PR review comments + a summary comment
  - Setting a commit status check (✅/❌)
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import jwt

from app.core.config import settings
from app.services.review import review_code

_GH_API = "https://api.github.com"
_ACCEPT = "application/vnd.github+json"

# File extensions we know how to review
_REVIEWABLE = {".py", ".js", ".java"}


# ── GitHub App auth ───────────────────────────────────────────────────────────

def _make_app_jwt() -> str:
    """
    Create a short-lived JWT signed with the GitHub App's private key.
    Valid for 10 minutes (GitHub maximum is 10 minutes).
    """
    now = int(time.time())
    payload = {
        "iat": now - 60,       # issued-at: a little in the past to allow clock skew
        "exp": now + (9 * 60), # expiry: 9 minutes
        "iss": settings.GITHUB_APP_ID,
    }
    return jwt.encode(payload, settings.GITHUB_PRIVATE_KEY, algorithm="RS256")


def _get_installation_token(installation_id: int) -> str:
    """Exchange the App JWT for a short-lived installation access token."""
    app_jwt = _make_app_jwt()
    url = f"{_GH_API}/app/installations/{installation_id}/access_tokens"
    resp = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": _ACCEPT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def _gh_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": _ACCEPT,
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ── File fetching ─────────────────────────────────────────────────────────────

def _fetch_file_content(token: str, owner: str, repo: str, path: str, ref: str) -> str | None:
    """Download raw file content at the given git ref. Returns None on failure."""
    url = f"{_GH_API}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    resp = httpx.get(url, headers=_gh_headers(token), timeout=20)
    if resp.status_code != 200:
        return None
    import base64
    data = resp.json()
    if data.get("encoding") == "base64":
        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except Exception:
            return None
    return None


def _get_pr_changed_files(token: str, owner: str, repo: str, pr_number: int) -> list[dict]:
    """Return the list of changed file objects for a pull request."""
    files: list[dict] = []
    page = 1
    while True:
        url = f"{_GH_API}/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100&page={page}"
        resp = httpx.get(url, headers=_gh_headers(token), timeout=20)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        files.extend(batch)
        page += 1
    return files


def _get_push_changed_files(token: str, owner: str, repo: str, commits: list[dict]) -> list[str]:
    """
    Return the unique set of file paths touched across all commits in a push.
    Only added or modified files are included.
    """
    seen: set[str] = set()
    paths: list[str] = []
    for commit in commits:
        for path in commit.get("added", []) + commit.get("modified", []):
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


# ── Posting results ───────────────────────────────────────────────────────────

def _post_commit_status(
    token: str, owner: str, repo: str, sha: str, risk_score: int, description: str
) -> None:
    """Post a ✅/❌ commit status check based on Code Risk Score (<= 45 is passing)."""
    state = "success" if risk_score <= 45 else "failure"
    httpx.post(
        f"{_GH_API}/repos/{owner}/{repo}/statuses/{sha}",
        headers=_gh_headers(token),
        json={
            "state": state,
            "context": "BugLens / Code Risk & Confidence",
            "description": description,
            "target_url": "",
        },
        timeout=15,
    )


def _post_pr_review(
    token: str,
    owner: str,
    repo: str,
    pr_number: int,
    commit_sha: str,
    file_reviews: list[dict],   # [{path, language, result}]
) -> None:
    """
    Post a GitHub PR review with:
      - Inline comments on each issue that has a line number
      - A top-level summary body with risk, confidence, coverage, and issue metrics
    """
    inline_comments: list[dict] = []
    all_results = []

    for fr in file_reviews:
        path = fr["path"]
        result = fr["result"]
        all_results.append((path, result))

        for issue in result.get("issues", []):
            raw_line = issue.get("line")
            line_no: int | None = None
            if isinstance(raw_line, int):
                line_no = raw_line
            elif isinstance(raw_line, str):
                parts = raw_line.replace(" ", "").split(",")
                if parts[0].isdigit():
                    line_no = int(parts[0])

            if line_no and line_no > 0:
                severity = issue.get("severity", "LOW")
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(severity, "⚪")
                body = (
                    f"{emoji} **[{severity}]** `{issue.get('category', '')}` — {issue.get('message', '')}\n\n"
                    f"{issue.get('explanation') or ''}\n\n"
                    f"💡 **Suggestion:** {issue.get('suggestion') or '_No suggestion available._'}"
                ).strip()

                inline_comments.append({
                    "path": path,
                    "line": line_no,
                    "side": "RIGHT",
                    "body": body,
                })

    # Build summary body
    summary_lines = ["## 🤖 BugLens Evidence-Weighted Code Review\n"]
    for path, result in all_results:
        risk_score = result.get("risk_score", "—")
        risk_lvl = result.get("risk_level", "—")
        conf_score = result.get("analysis_confidence", "—")
        cov_pct = result.get("analysis_coverage", "—")
        fw = result.get("detected_framework")
        issue_count = len(result.get("issues", []))
        summary_lines.append(
            f"### 📄 `{path}`\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| **Code Risk Score** | **{risk_score}/100** ({risk_lvl} Risk) |\n"
            f"| **Analysis Confidence** | **{conf_score}/100** (Evidence-Weighted) |\n"
            f"| **Analysis Coverage** | **{cov_pct}%** |\n"
            f"| **Detected Framework** | {fw or 'None detected'} |\n"
            f"| Issues Found | {issue_count} |\n\n"
            f"> {result.get('summary', '')}\n"
        )
        tc = result.get("time_complexity")
        sc = result.get("space_complexity")
        if tc or sc:
            summary_lines.append(
                f"**Complexity:** Time `{tc or '—'}` · Space `{sc or '—'}`\n"
            )
        summary_lines.append("\n---\n")

    summary_body = "\n".join(summary_lines)

    # Trim to GitHub's 65535-char limit per comment
    if len(summary_body) > 65000:
        summary_body = summary_body[:65000] + "\n\n_(truncated — too many files)_"

    # Cap inline comments at 30 (GitHub API limit per review)
    inline_comments = inline_comments[:30]

    payload: dict[str, Any] = {
        "commit_id": commit_sha,
        "body": summary_body,
        "event": "COMMENT",
        "comments": inline_comments,
    }

    resp = httpx.post(
        f"{_GH_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        headers=_gh_headers(token),
        json=payload,
        timeout=30,
    )
    # Non-fatal if posting fails — log and move on
    if resp.status_code not in (200, 201):
        print(f"[github_bot] PR review post failed {resp.status_code}: {resp.text[:300]}")


def _post_push_comment(
    token: str,
    owner: str,
    repo: str,
    commit_sha: str,
    file_reviews: list[dict],
) -> None:
    """
    For direct pushes (not PRs), post a commit comment with the review summary.
    """
    lines = ["## 🤖 BugLens Evidence-Weighted Code Review (push)\n"]
    for fr in file_reviews:
        result = fr["result"]
        risk_score = result.get("risk_score", "—")
        risk_lvl = result.get("risk_level", "—")
        conf_score = result.get("analysis_confidence", "—")
        cov_pct = result.get("analysis_coverage", "—")
        lines.append(
            f"### `{fr['path']}`\n"
            f"**Code Risk Score:** {risk_score}/100 ({risk_lvl} Risk)\n"
            f"**Analysis Confidence:** {conf_score}/100 · **Coverage:** {cov_pct}%\n"
            f"**Issues:** {len(result.get('issues', []))}\n\n"
            f"> {result.get('summary', '')}\n\n---\n"
        )

    body = "\n".join(lines)
    if len(body) > 65000:
        body = body[:65000] + "\n\n_(truncated)_"

    resp = httpx.post(
        f"{_GH_API}/repos/{owner}/{repo}/commits/{commit_sha}/comments",
        headers=_gh_headers(token),
        json={"body": body},
        timeout=20,
    )
    if resp.status_code not in (200, 201):
        print(f"[github_bot] Commit comment post failed {resp.status_code}: {resp.text[:300]}")


# ── Main entry points ─────────────────────────────────────────────────────────

def handle_pull_request_event(payload: dict) -> dict:
    """
    Handle a GitHub pull_request webhook event.
    Reviews all changed reviewable files and posts inline comments + a summary.
    """
    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"skipped": True, "reason": f"action '{action}' not reviewable"}

    installation_id = payload["installation"]["id"]
    repo_info = payload["repository"]
    owner = repo_info["owner"]["login"]
    repo = repo_info["name"]
    pr = payload["pull_request"]
    pr_number = pr["number"]
    head_sha = pr["head"]["sha"]
    head_ref = pr["head"]["ref"]

    token = _get_installation_token(installation_id)
    changed_files = _get_pr_changed_files(token, owner, repo, pr_number)

    file_reviews: list[dict] = []
    for f in changed_files:
        path: str = f.get("filename", "")
        status = f.get("status", "")
        if status == "removed":
            continue
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext not in _REVIEWABLE:
            continue

        content = _fetch_file_content(token, owner, repo, path, head_ref)
        if not content or not content.strip():
            continue

        language = {"py": "python", "js": "javascript", "java": "java"}.get(ext.lstrip("."), "python")
        result = review_code(content, language)
        file_reviews.append({"path": path, "language": language, "result": result})

    if not file_reviews:
        return {"skipped": True, "reason": "no reviewable files changed"}

    _post_pr_review(token, owner, repo, pr_number, head_sha, file_reviews)

    # Also set a commit status reflecting the worst (highest) risk_score
    worst_risk = max(
        (fr["result"].get("risk_score", 0) for fr in file_reviews),
        default=0,
    )
    matching_review = next(
        (fr["result"] for fr in file_reviews if fr["result"].get("risk_score") == worst_risk),
        file_reviews[0]["result"],
    )
    worst_level = matching_review.get("risk_level", "Low")
    worst_conf = matching_review.get("analysis_confidence", 100)

    _post_commit_status(
        token, owner, repo, head_sha,
        worst_risk,
        f"BugLens: {worst_level} Risk ({worst_risk}/100) · Conf {worst_conf}%",
    )

    return {
        "reviewed_files": [fr["path"] for fr in file_reviews],
        "worst_risk_score": worst_risk,
        "worst_risk_level": worst_level,
    }


def handle_push_event(payload: dict) -> dict:
    """
    Handle a GitHub push webhook event.
    Reviews all changed reviewable files and posts a commit comment.
    """
    # Skip branch deletions
    if payload.get("deleted"):
        return {"skipped": True, "reason": "branch deletion"}

    installation_id = payload.get("installation", {}).get("id")
    if not installation_id:
        return {"skipped": True, "reason": "no installation id"}

    repo_info = payload["repository"]
    owner = repo_info["owner"]["login"]
    repo = repo_info["name"]
    head_sha = payload.get("after", "")
    commits = payload.get("commits", [])
    ref = payload.get("ref", "refs/heads/main")
    branch = ref.replace("refs/heads/", "")

    token = _get_installation_token(installation_id)
    changed_paths = _get_push_changed_files(token, owner, repo, commits)

    file_reviews: list[dict] = []
    for path in changed_paths:
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext not in _REVIEWABLE:
            continue

        content = _fetch_file_content(token, owner, repo, path, branch)
        if not content or not content.strip():
            continue

        language = {"py": "python", "js": "javascript", "java": "java"}.get(ext.lstrip("."), "python")
        result = review_code(content, language)
        file_reviews.append({"path": path, "language": language, "result": result})

    if not file_reviews:
        return {"skipped": True, "reason": "no reviewable files changed"}

    _post_push_comment(token, owner, repo, head_sha, file_reviews)

    worst_risk = max(
        (fr["result"].get("risk_score", 0) for fr in file_reviews),
        default=0,
    )
    matching_review = next(
        (fr["result"] for fr in file_reviews if fr["result"].get("risk_score") == worst_risk),
        file_reviews[0]["result"],
    )
    worst_level = matching_review.get("risk_level", "Low")
    worst_conf = matching_review.get("analysis_confidence", 100)

    _post_commit_status(
        token, owner, repo, head_sha,
        worst_risk,
        f"BugLens: {worst_level} Risk ({worst_risk}/100) · Conf {worst_conf}%",
    )

    return {
        "reviewed_files": [fr["path"] for fr in file_reviews],
        "worst_risk_score": worst_risk,
        "worst_risk_level": worst_level,
    }
