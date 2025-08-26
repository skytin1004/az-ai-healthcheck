import types
import pytest

import azure_ai_healthcheck.vision as vision_mod
from azure_ai_healthcheck import check_azure_vision


class DummyClient:
    def __init__(self, behavior: str, status: int | None = None, message: str = ""):
        self.behavior = behavior
        self.status = status
        self.message = message

    def analyze(self, *args, **kwargs):
        if self.behavior == "ok":
            return object()
        err = RuntimeError(self.message)
        if self.status is not None:
            setattr(err, "status_code", self.status)
        raise err


class DummyVisualFeatures:
    CAPTION = object()


def patch_client(monkeypatch, behavior: str, status: int | None = None, message: str = ""):
    def fake_get_client(endpoint, api_key):
        return DummyClient(behavior, status, message), DummyVisualFeatures

    monkeypatch.setattr(vision_mod, "_get_image_analysis_client", fake_get_client)


def test_vision_success(monkeypatch):
    patch_client(monkeypatch, behavior="ok")

    res = check_azure_vision(endpoint="https://cv.azure.com", api_key="key")
    assert res.ok is True
    assert res.status_code == 200


def test_vision_401_raises(monkeypatch):
    patch_client(monkeypatch, behavior="err", status=401, message="Unauthorized")

    res = check_azure_vision(endpoint="https://cv.azure.com", api_key="key")
    assert res.ok is False
    assert res.status_code == 401
    assert "401/403" in res.message


def test_vision_400_non_strict(monkeypatch, caplog):
    patch_client(monkeypatch, behavior="err", status=400, message="InvalidImageSize")

    with caplog.at_level("WARNING"):
        res = check_azure_vision(
            endpoint="https://cv.azure.com", api_key="key", use_min_size_image=False
        )
    assert res.ok is False
    assert res.status_code == 400
    assert "HTTP 400" in res.message


def test_vision_400_returns_false_no_exception(monkeypatch, caplog):
    patch_client(monkeypatch, behavior="err", status=400, message="Bad Request")

    with caplog.at_level("WARNING"):
        res = check_azure_vision(endpoint="https://cv.azure.com", api_key="key")
    assert res.ok is False
    assert res.status_code == 400
    assert "HTTP 400" in res.message
