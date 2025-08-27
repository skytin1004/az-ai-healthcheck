"""azure_ai_healthcheck

Lightweight health checks for Azure OpenAI and Azure AI Vision.
"""
from azure_ai_healthcheck.models import HealthResult
from azure_ai_healthcheck.azure_openai import check_azure_openai
from azure_ai_healthcheck.vision import check_azure_vision

__all__ = [
    "HealthResult",
    "check_azure_openai",
    "check_azure_vision",
]
