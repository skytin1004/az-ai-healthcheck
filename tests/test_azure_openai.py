import az_ai_healthcheck.azure_openai as openai_mod
from az_ai_healthcheck import check_azure_openai


class DummyResp:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


def test_openai_success(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResp(200, "ok")

    monkeypatch.setattr(openai_mod.requests, "post", fake_post)

    res = check_azure_openai(
        endpoint="https://example.openai.azure.com",
        api_key="key",
        api_version="2024-02-15-preview",
        deployment="gpt",
    )
    assert res.ok is True
    assert res.status_code == 200


def test_openai_401_returns_false(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResp(401, "Unauthorized")

    monkeypatch.setattr(openai_mod.requests, "post", fake_post)

    res = check_azure_openai(
        endpoint="https://example.openai.azure.com",
        api_key="key",
        api_version="2024-02-15-preview",
        deployment="gpt",
    )
    assert res.ok is False
    assert res.status_code == 401
    assert "authentication/permission" in res.message


def test_openai_400_returns_false(monkeypatch, caplog):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResp(400, "Bad Request: InvalidImageSize")

    monkeypatch.setattr(openai_mod.requests, "post", fake_post)

    with caplog.at_level("WARNING"):
        res = check_azure_openai(
            endpoint="https://example.openai.azure.com",
            api_key="key",
            api_version="2024-02-15-preview",
            deployment="gpt",
        )
    assert res.ok is False
    assert res.status_code == 400
    assert "HTTP 400" in res.message

def test_openai_400_returns_false_no_exception(monkeypatch, caplog):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResp(400, "Bad Request")

    monkeypatch.setattr(openai_mod.requests, "post", fake_post)

    with caplog.at_level("WARNING"):
        res = check_azure_openai(
            endpoint="https://example.openai.azure.com",
            api_key="key",
            api_version="2024-02-15-preview",
            deployment="gpt",
        )
    assert res.ok is False
    assert res.status_code == 400
    assert "HTTP 400" in res.message


def test_openai_network_error_returns_false(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        raise RuntimeError("dns fail")

    monkeypatch.setattr(openai_mod.requests, "post", fake_post)

    res = check_azure_openai(
        endpoint="https://example.openai.azure.com",
        api_key="key",
        api_version="2024-02-15-preview",
        deployment="gpt",
    )
    assert res.ok is False
    assert res.status_code is None
    # No exception should be raised in any case


def test_openai_404_returns_false_with_guidance(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResp(404, "Not Found: bad path")

    monkeypatch.setattr(openai_mod.requests, "post", fake_post)

    res = check_azure_openai(
        endpoint="https://example.openai.azure.com",
        api_key="key",
        api_version="2024-02-15-preview",
        deployment="gpt",
    )
    assert res.ok is False
    assert res.status_code == 404
    assert "404" in res.message
    assert "endpoint/path" in res.message or "deployment" in res.message
