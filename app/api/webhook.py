"""
GitHub Webhook API Endpoint
============================
Receives push and pull_request events from GitHub and dispatches them
to the BugLens review pipeline.

Security
--------
Every incoming request is verified against the HMAC-SHA256 signature
that GitHub attaches in the `X-Hub-Signature-256` header.
Requests that fail signature verification are rejected with 403.
"""

from __future__ import annotations

import hashlib
import hmac
import json

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from app.core.config import settings
from app.services.github_bot import handle_pull_request_event, handle_push_event

router = APIRouter()


# ── HMAC signature verification ───────────────────────────────────────────────

def _verify_signature(body: bytes, signature_header: str | None) -> None:
    """
    Verify the GitHub webhook HMAC-SHA256 signature.
    Raises HTTP 403 if the signature is missing or does not match.
    """
    if not settings.GITHUB_WEBHOOK_SECRET:
        # If no secret is configured we skip verification (dev-only convenience).
        return

    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or malformed X-Hub-Signature-256 header.",
        )

    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook signature verification failed.",
        )


# ── Background task wrappers (keep the HTTP response fast) ───────────────────

def _bg_pr(payload: dict) -> None:
    try:
        result = handle_pull_request_event(payload)
        print(f"[webhook] PR review done: {result}")
    except Exception as exc:
        print(f"[webhook] PR review error: {exc}")


def _bg_push(payload: dict) -> None:
    try:
        result = handle_push_event(payload)
        print(f"[webhook] push review done: {result}")
    except Exception as exc:
        print(f"[webhook] push review error: {exc}")


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    """
    Receive a GitHub App webhook event.

    - Verifies the HMAC-SHA256 signature.
    - Dispatches `pull_request` and `push` events to the review pipeline
      as background tasks so GitHub doesn't time out waiting for a response.
    - Returns 202 Accepted immediately; reviews are posted asynchronously.
    """
    body = await request.body()
    _verify_signature(body, x_hub_signature_256)

    event = x_github_event or ""
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body is not valid JSON.",
        )

    if event == "pull_request":
        background_tasks.add_task(_bg_pr, payload)
        return {"accepted": True, "event": "pull_request"}

    if event == "push":
        background_tasks.add_task(_bg_push, payload)
        return {"accepted": True, "event": "push"}

    # All other events (ping, installation, etc.) are acknowledged but ignored
    return {"accepted": True, "event": event, "action": "ignored"}
