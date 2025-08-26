"""azure_ai_healthcheck

Lightweight health checks for Azure OpenAI and Azure AI Vision.
"""
from .models import HealthResult
from .azure_openai import check_azure_openai
from .vision import check_azure_vision

__all__ = [
    "HealthResult",
    "check_azure_openai",
    "check_azure_vision",
]

__version__ = "0.1.0"
