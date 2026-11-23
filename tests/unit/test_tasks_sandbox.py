from types import SimpleNamespace
from typing import Any

import pytest
from invoke import Context, MockContext
from invoke.exceptions import Exit

import tasks


class _FakeRepositoryClient:
    """Return queued sync statuses for CoreRepository lookups and record created nodes."""

    def __init__(self, statuses: list[str | None] | None = None) -> None:
        self.statuses = list(statuses or [])
        self.created: list[dict[str, Any]] = []
        self.saved_with_upsert: list[bool] = []

    def get(self, kind: str, name__value: str, raise_when_missing: bool) -> Any:
        status = self.statuses.pop(0)
        if status is None:
            return None
        return SimpleNamespace(sync_status=SimpleNamespace(value=status))

    def create(self, kind: str, data: dict[str, Any]) -> Any:
        self.created.append({"kind": kind, **data})
        return _FakeNode(self.saved_with_upsert)


class _FakeNode:
    def __init__(self, saves: list[bool]) -> None:
        self.saves = saves

    def save(self, allow_upsert: bool) -> None:
        self.saves.append(allow_upsert)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks, "sleep", lambda _seconds: None)


def test_wait_for_repository_sync_returns_when_in_sync() -> None:
    client = _FakeRepositoryClient([None, "syncing", "in-sync"])

    tasks.wait_for_repository_sync("test-repository", client=client)  # type: ignore[arg-type]

    assert client.statuses == []


def test_wait_for_repository_sync_stops_on_import_error() -> None:
    client = _FakeRepositoryClient(["syncing", "error-import"])

    with pytest.raises(RuntimeError, match="failed to import"):
        tasks.wait_for_repository_sync("test-repository", client=client)  # type: ignore[arg-type]


def test_wait_for_repository_sync_times_out() -> None:
    client = _FakeRepositoryClient(["syncing", "syncing"])

    with pytest.raises(TimeoutError):
        tasks.wait_for_repository_sync("test-repository", timeout=10, interval=5, client=client)  # type: ignore[arg-type]


def test_register_repository_without_url_loads_local_definition(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INFRAHUB_REPO_URL", raising=False)
    ctx = MockContext(run={"infrahubctl object load repository.yml": True})

    tasks.register_repository(ctx)

    ctx.run.assert_called_once_with("infrahubctl object load repository.yml")  # type: ignore[attr-defined]


def test_register_repository_uses_supplied_url_and_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _FakeRepositoryClient()
    monkeypatch.setattr(tasks, "_infrahub_client", lambda: client)
    monkeypatch.setenv("INFRAHUB_REPO_URL", "https://github.com/opsmill/infrahub-arista-avd.git")
    monkeypatch.setenv("INFRAHUB_REPO_REF", "main")
    ctx = MockContext()

    tasks.register_repository(ctx)

    assert client.created == [
        {
            "kind": "CoreRepository",
            "name": tasks.REPOSITORY_NAME,
            "location": "https://github.com/opsmill/infrahub-arista-avd.git",
            "default_branch": "main",
        }
    ]
    assert client.saved_with_upsert == [True]


@pytest.mark.parametrize(
    ("address_supplied", "token", "expected"),
    [
        (False, "token", "INFRAHUB_ADDRESS"),
        (True, None, "INFRAHUB_API_TOKEN"),
    ],
)
def test_sandbox_setup_requires_supplied_infrahub(
    monkeypatch: pytest.MonkeyPatch, address_supplied: bool, token: str | None, expected: str
) -> None:
    monkeypatch.setattr(tasks, "INFRAHUB_ADDRESS_SUPPLIED", address_supplied)
    if token is None:
        monkeypatch.delenv("INFRAHUB_API_TOKEN", raising=False)
    else:
        monkeypatch.setenv("INFRAHUB_API_TOKEN", token)

    with pytest.raises(Exit, match=expected):
        tasks.sandbox_setup(Context())


def test_sandbox_setup_does_not_touch_semaphore(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks, "INFRAHUB_ADDRESS_SUPPLIED", True)
    monkeypatch.setenv("INFRAHUB_API_TOKEN", "token")
    monkeypatch.setattr(tasks, "init_semaphore", lambda *_a, **_k: pytest.fail("init_semaphore called"))
    calls: list[str] = []
    monkeypatch.setattr(tasks, "_load_infrahub_content", lambda _ctx, _selection: calls.append("content"))

    tasks.sandbox_setup(Context())

    assert calls == ["content"]
