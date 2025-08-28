"""az_ai_healthcheck

Lightweight health checks for Azure OpenAI and Azure AI Vision.
"""
from az_ai_healthcheck.models import HealthResult
from az_ai_healthcheck.azure_openai import check_azure_openai
from az_ai_healthcheck.azure_ai_vision import check_azure_ai_vision

# Backward compatibility: keep old name for users importing check_azure_vision
check_azure_vision = check_azure_ai_vision

__all__ = [
    "HealthResult",
    "check_azure_openai",
    "check_azure_ai_vision",
]
