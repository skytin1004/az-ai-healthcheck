# az-ai-healthcheck

[![Python package](https://img.shields.io/pypi/v/az-ai-healthcheck?color=4BA3FF)](https://pypi.org/project/az-ai-healthcheck/)
[![License: MIT](https://img.shields.io/github/license/skytin1004/az-ai-healthcheck?color=4BA3FF)](https://github.com/skytin1004/az-ai-healthcheck/blob/main/LICENSE)

[![GitHub contributors](https://img.shields.io/github/contributors/skytin1004/az-ai-healthcheck.svg)](https://GitHub.com/skytin1004/az-ai-healthcheck/graphs/contributors/)
[![GitHub issues](https://img.shields.io/github/issues/skytin1004/az-ai-healthcheck.svg)](https://GitHub.com/skytin1004/az-ai-healthcheck/issues/)
[![GitHub pull-requests](https://img.shields.io/github/issues-pr/skytin1004/az-ai-healthcheck.svg)](https://GitHub.com/skytin1004/az-ai-healthcheck/pulls/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

Lightweight health checks for Azure OpenAI and Azure AI Vision — no heavy SDKs required for OpenAI, and an optional extra for Vision.

- Minimal data-plane calls with tiny payloads and short timeouts
- Clear, predictable behavior (always returns `HealthResult`)
- Small install footprint; add Vision via optional extras
- Perfect for application startup probes and CI/CD smoke tests

## Installation

Core (OpenAI only):

```bash
pip install az-ai-healthcheck
```

With Vision support:

```bash
pip install "az-ai-healthcheck[vision]"
```

## Quickstart

Set your credentials (example using environment variables), then call the checks.

```python
import os
from az_ai_healthcheck import check_azure_openai, check_azure_ai_vision

res_aoai = check_azure_openai(
    endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-02-15-preview",
    deployment="gpt-4o-mini",
)
print(res_aoai)

res_vision = check_azure_ai_vision(
    endpoint=os.environ["AZURE_VISION_ENDPOINT"],
    api_key=os.environ["AZURE_VISION_API_KEY"],
)
print(res_vision)
```

### Sample output

```python
# HealthResult full repr examples (your values will vary)

print(res_aoai)
# HealthResult(provider='azure_openai',
#              endpoint='https://my-endpoint.openai.azure.com',
#              ok=True,
#              status_code=200,
#              message='Azure OpenAI reachable. Credentials and deployment appear valid.')

print(res_vision)
# HealthResult(provider='azure_ai_vision',
#              endpoint='https://my-cv.cognitiveservices.azure.com',
#              ok=False,
#              status_code=401,
#              message='Azure Vision authentication/permission failed (401/403). Verify API key and endpoint.')
```

## Usage

### Azure OpenAI (Chat Completions) health check

```python
from az_ai_healthcheck import check_azure_openai

res = check_azure_openai(
    endpoint="https://my-endpoint.openai.azure.com",
    api_key="***",
    api_version="2024-02-15-preview",
    deployment="gpt-4o",
    timeout=10.0,
)
print(res.ok, res.status_code, res.message)
```

Behavior:
- 200 -> ok=True
- else (401/403 and other non-2xx, or network errors) -> ok=False with details

### Azure AI Vision (Image Analysis) health check

```python
from az_ai_healthcheck import check_azure_ai_vision

res = check_azure_ai_vision(
    endpoint="https://my-cv.cognitiveservices.azure.com",
    api_key="***",
    timeout=10.0,
)
print(res.ok, res.status_code, res.message)
```

- Uses `ImageAnalysisClient.analyze` with `VisualFeatures.CAPTION`.
- Sends an in-memory PNG. `use_min_size_image=True` (default) uses 50x50 to reduce 400s.
- `use_min_size_image=False` can trigger 400 (e.g., InvalidImageSize) → returns ok=False with details.
- 404 is treated as failure with guidance (often wrong endpoint/path; occasionally an image too small to analyze).

## Notes

- Azure OpenAI uses `requests` only; no SDK dependency.
- Azure Vision requires `azure-ai-vision-imageanalysis` (install via extra).
- No custom User-Agent header is set (keep requests minimal).

## Troubleshooting

- Azure OpenAI 404: API key may be valid, but the endpoint/path, api-version, or deployment is likely incorrect. Verify the endpoint format (no extra path), the `api-version`, and the deployment name.
- Azure AI Vision 404: Often indicates a wrong endpoint/path. In some cases a too-small test image can also lead to errors—try the default `use_min_size_image=True`.
- 401/403: Permission/auth errors. Check keys, role assignments, and resource-level access.

## CI/CD and startup probes

Use these checks in your pipelines or app startup to fail fast with clear guidance.

```python
def app_startup_probe():
    from az_ai_healthcheck import check_azure_openai
    res = check_azure_openai(endpoint=..., api_key=..., api_version=..., deployment=...)
    if not res.ok:
        raise RuntimeError(f"OpenAI health check failed: {res.message}")
```
