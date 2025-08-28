from __future__ import annotations

import logging
import requests

from az_ai_healthcheck.models import HealthResult

logger = logging.getLogger(__name__)


def _build_chat_url(endpoint: str, api_version: str, deployment: str) -> str:
    base = (endpoint or "").rstrip("/")
    if base.endswith("/openai"):
        return f"{base}/deployments/{deployment}/chat/completions?api-version={api_version}"
    return f"{base}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"


def check_azure_openai(
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
    timeout: float = 10.0,
) -> HealthResult:
    """Health-check Azure OpenAI chat completions.

    Behavior:
    - 200 -> ok=True
    - else (401/403 and other non-2xx, or network errors) -> ok=False with details
    """
    if not endpoint or not api_key or not api_version or not deployment:
        raise ValueError(
            "Missing required Azure OpenAI parameters. Verify endpoint, api_key, api_version, deployment."
        )

    url = _build_chat_url(endpoint, api_version, deployment)
    provider = "azure_openai"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {"role": "system", "content": "health check"},
            {"role": "user", "content": "ping"},
        ],
        "max_tokens": 1,
        "temperature": 0,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except Exception as e:  # network issues, DNS, etc.
        msg = (
            "Failed to reach Azure OpenAI endpoint. Verify endpoint URL, networking, and DNS. "
            f"Details: {e}"
        )
        logger.warning(msg)
        return HealthResult(
            provider="azure_openai",
            endpoint=endpoint,
            ok=False,
            status_code=None,
            message="Network/connection error. Check endpoint and connectivity.",
        )

    status = resp.status_code
    text_snippet = (resp.text or "")[:500]

    if status == 200:
        return HealthResult(
            provider=provider,
            endpoint=endpoint,
            ok=True,
            status_code=200,
            message="Azure OpenAI reachable. Credentials and deployment appear valid.",
        )

    if status in (401, 403):
        message = (
            "Azure OpenAI authentication/permission failed (401/403). "
            "Verify API key, endpoint, api-version, and deployment name/permissions."
        )
        logger.warning(message)
        return HealthResult(
            provider=provider,
            endpoint=endpoint,
            ok=False,
            status_code=status,
            message=message,
        )

    if status == 404:
        message = (
            "Azure OpenAI returned HTTP 404 (Not Found). API key may be valid, but the endpoint/path, "
            "api-version, or deployment name is likely incorrect. Verify the endpoint format (no extra path), "
            "the api-version, and the deployment name. Response snippet: "
            f"{text_snippet}"
        )
        logger.warning(message)
        return HealthResult(
            provider=provider,
            endpoint=endpoint,
            ok=False,
            status_code=404,
            message=message,
        )

    message = (
        f"Azure OpenAI returned HTTP {status}. Verify endpoint, api-version, and deployment. "
        f"Response snippet: {text_snippet}"
    )
    logger.warning(message)
    return HealthResult(
        provider=provider,
        endpoint=endpoint,
        ok=False,
        status_code=status,
        message=f"Non-2xx response. {message}",
    )
