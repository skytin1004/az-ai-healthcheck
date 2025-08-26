# azure-ai-healthcheck

[![Python package](https://img.shields.io/pypi/v/azure-ai-healthcheck?color=4BA3FF)](https://pypi.org/project/azure-ai-healthcheck/)
[![License: MIT](https://img.shields.io/github/license/skytin1004/azure-ai-healthcheck?color=4BA3FF)](https://github.com/skytin1004/azure-ai-healthcheck/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/azure-ai-healthcheck)](https://pepy.tech/project/azure-ai-healthcheck)
[![Downloads](https://static.pepy.tech/badge/azure-ai-healthcheck/month)](https://pepy.tech/project/azure-ai-healthcheck)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![GitHub contributors](https://img.shields.io/github/contributors/skytin1004/azure-ai-healthcheck.svg)](https://GitHub.com/skytin1004/azure-ai-healthcheck/graphs/contributors/)
[![GitHub issues](https://img.shields.io/github/issues/skytin1004/azure-ai-healthcheck.svg)](https://GitHub.com/skytin1004/azure-ai-healthcheck/issues/)
[![GitHub pull-requests](https://img.shields.io/github/issues-pr/skytin1004/azure-ai-healthcheck.svg)](https://GitHub.com/skytin1004/azure-ai-healthcheck/pulls/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
`

Lightweight, dependency-minimal health checks for Azure OpenAI and Azure AI Vision.

- Minimal dataplane calls with tiny payloads and short timeouts
- Clear, predictable behavior (always returns HealthResult)
- Minimal core install; add services via optional extras (e.g., [vision])
- Designed for application boot checks and CI/CD

## Installation

Core (OpenAI only):

```bash
pip install azure-ai-healthcheck
```

With Vision support:

```bash
pip install "azure-ai-healthcheck[vision]"
```

## Usage

### Azure OpenAI (Chat Completions) health check

```python
from azure_ai_healthcheck import check_azure_openai

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

### Azure Vision (Image Analysis) health check

```python
from azure_ai_healthcheck import check_azure_vision

res = check_azure_vision(
    endpoint="https://my-cv.cognitiveservices.azure.com",
    api_key="***",
    timeout=10.0,
)
print(res.ok, res.status_code, res.message)
```

- Uses `ImageAnalysisClient.analyze` with `VisualFeatures.CAPTION`.
- Sends an in-memory PNG. `use_min_size_image=True` (default) uses 50x50 to reduce 400s.
- `use_min_size_image=False` can trigger 400 (e.g., InvalidImageSize); the function will return ok=False with details.

## HealthResult

```python
from azure_ai_healthcheck import HealthResult
# dataclass fields: provider, endpoint, ok, status_code, message
```

Providers: `"azure_openai"`, `"azure_vision"`.

## Notes

- Azure OpenAI uses `requests` only; no SDK dependency.
- Azure Vision requires `azure-ai-vision-imageanalysis` (install via extra).
- No custom User-Agent header is set (keep requests minimal).
