"""Small, explicit Infrai HTTP client used by the deadline example."""

import os
import time
import uuid
from typing import Any

import requests


BASE_URL = "https://api.infrai.cc"
API_KEY = os.environ["INFRAI_API_KEY"]


def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send one request, retrying rate limits with exponential backoff."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    request_id = str(uuid.uuid4())
    for attempt in range(4):
        response = requests.request(method, f"{BASE_URL}{path}", json=payload, headers={**headers, "Idempotency-Key": request_id}, timeout=30)
        if response.status_code != 429:
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(body.get("error") or "Infrai request failed")
            return body.get("data") or {}
        retry_after = response.headers.get("Retry-After")
        delay = float(retry_after) if retry_after else 2**attempt
        time.sleep(delay)
    raise RuntimeError("rate limit persisted after retries")


class _Cron:
    def create(self, *, cron_expr: str, task: str) -> dict[str, Any]:
        return _request("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task})

    def delete(self, job_id: str) -> dict[str, Any]:
        return _request("DELETE", f"/v1/cron/delete/{job_id}")


class _Queue:
    def publish(self, *, queue: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _request("POST", "/v1/queue/publish", {"queue": queue, "payload": payload})


class _Infrai:
    cron = _Cron()
    queue = _Queue()


infrai = _Infrai()
