from __future__ import annotations

import logging
import struct
import zlib
from typing import Optional

from az_ai_healthcheck.models import HealthResult

logger = logging.getLogger(__name__)


def _crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", _crc32(chunk_type + data))
    return length + chunk_type + data + crc


def _generate_png_bytes(width: int, height: int) -> bytes:
    """Generate a simple RGBA PNG of the given size without external deps."""
    # PNG signature
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,  # bit depth
        6,  # color type RGBA
        0,  # compression
        0,  # filter
        0,  # interlace
    )
    ihdr_chunk = _png_chunk(b"IHDR", ihdr)

    # Raw image data: each row starts with filter byte 0, then width * 4 bytes RGBA
    row = b"\x00" + (b"\x00" * (width * 4))
    raw = row * height
    compressed = zlib.compress(raw)
    idat_chunk = _png_chunk(b"IDAT", compressed)
    iend_chunk = _png_chunk(b"IEND", b"")
    return sig + ihdr_chunk + idat_chunk + iend_chunk


def _get_image_analysis_client(endpoint: str, api_key: str):  # pragma: no cover - imported lazily
    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        from azure.ai.vision.imageanalysis.models import VisualFeatures
        from azure.core.credentials import AzureKeyCredential
    except Exception as e:  # ImportError or others
        raise ImportError(
            "Vision checks require the Azure Vision SDK. Install the vision extra: \n"
            "  pip install \"azure-ai-healthcheck[vision]\"\n"
            "(Alternatively install the SDK directly: pip install azure-ai-vision-imageanalysis)"
        ) from e

    client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
    return client, VisualFeatures


def check_azure_ai_vision(
    endpoint: str,
    api_key: str,
    timeout: float = 10.0,
    use_min_size_image: bool = True,
) -> HealthResult:
    """Health-check Azure AI Vision Image Analysis.

    Behavior:
    - Success -> ok=True
    - Else (401/403 and other non-2xx/errors, including 404) -> ok=False with details
    """
    if not endpoint or not api_key:
        raise ValueError("Missing required Azure Vision parameters. Verify endpoint and api_key.")

    width = 50 if use_min_size_image else 1
    height = 50 if use_min_size_image else 1
    image_bytes = _generate_png_bytes(width, height)
    provider = "azure_ai_vision"

    # Lazily import/create client; ImportError will bubble up with a helpful message from
    # _get_image_analysis_client() if the optional SDK is not installed.
    client, VisualFeatures = _get_image_analysis_client(endpoint, api_key)

    try:
        client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.CAPTION],
            # Not all versions support timeout or headers; rely on HTTP client defaults.
        )
        # If analyze returns without exception, consider success
        return HealthResult(
            provider=provider,
            endpoint=endpoint,
            ok=True,
            status_code=200,
            message="Azure Vision reachable. Credentials appear valid.",
        )
    except Exception as e:
        status: Optional[int] = getattr(e, "status_code", None)
        if status in (401, 403):
            message = (
                "Azure Vision authentication/permission failed (401/403). Verify API key and endpoint."
            )
            logger.warning(message)
            return HealthResult(
                provider=provider,
                endpoint=endpoint,
                ok=False,
                status_code=status,
                message=message,
            )

        # 404: Treat as failure but give a clear hint about likely causes.
        if status == 404:
            message = (
                "Azure Vision returned HTTP 404 (Not Found). This often indicates an incorrect endpoint/path, "
                "or in some cases the test image may be too small for analysis. Verify the endpoint format and "
                "consider using a slightly larger image."
            )
            logger.warning(message)
            return HealthResult(
                provider=provider,
                endpoint=endpoint,
                ok=False,
                status_code=404,
                message=message,
            )

        # Non-auth error (e.g., InvalidImageSize 400). Return ok=False with details.
        snippet = str(e)[:500]
        message = f"Azure AI Vision error. HTTP {status if status is not None else 'unknown'}. Details: {snippet}"
        logger.warning(message)
        return HealthResult(
            provider=provider,
            endpoint=endpoint,
            ok=False,
            status_code=status,
            message=message,
        )
