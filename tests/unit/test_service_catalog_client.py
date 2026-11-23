"""Authentication modes of the Service Catalog's Infrahub client.

The module is loaded from its file because the `utils` package also imports
Streamlit, which is not part of the development dependencies.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from types import ModuleType

API_PATH = Path(__file__).resolve().parents[2] / "service_catalog" / "utils" / "api.py"
FAKE_TOKEN = "test-token"  # noqa: S105
FAKE_PASSWORD = "test-password"  # noqa: S105


@pytest.fixture(scope="module")
def api() -> ModuleType:
    spec = importlib.util.spec_from_file_location("service_catalog_api", API_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _no_infrahub_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("INFRAHUB_API_TOKEN", "INFRAHUB_USERNAME", "INFRAHUB_PASSWORD"):
        monkeypatch.delenv(name, raising=False)


def test_token_client_uses_the_token(api: ModuleType) -> None:
    client = api.InfrahubClient("http://infrahub:8000", api_token=FAKE_TOKEN)

    assert client._client.config.api_token == FAKE_TOKEN
    assert not client._client.config.password_authentication


def test_visitor_client_uses_the_visitor_account(api: ModuleType) -> None:
    client = api.InfrahubClient("http://infrahub:8000", username="guest", password=FAKE_PASSWORD)

    assert client.username == "guest"
    assert client._client.config.api_token is None
    assert client._client.config.password_authentication


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://infrahub:8000/api/auth/login")
    response = httpx.Response(status, request=request, text="denied")
    return httpx.HTTPStatusError("login failed", request=request, response=response)


def test_sign_in_reports_rejected_credentials(api: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    client = api.InfrahubClient("http://infrahub:8000", username="guest", password=FAKE_PASSWORD)

    def reject(refresh: bool = False) -> None:
        raise _status_error(401)

    monkeypatch.setattr(client._client, "login", reject)

    with pytest.raises(api.InfrahubHTTPError, match="Incorrect username or password"):
        client.sign_in()


def test_sign_in_reports_unreachable_infrahub(api: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    client = api.InfrahubClient("http://infrahub:8000", username="guest", password=FAKE_PASSWORD)

    def unreachable(refresh: bool = False) -> None:
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(client._client, "login", unreachable)

    with pytest.raises(api.InfrahubConnectionError, match="Could not reach Infrahub"):
        client.sign_in()
