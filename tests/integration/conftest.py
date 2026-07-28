from pathlib import Path
from typing import Any

import pytest
from infrahub_sdk.yaml import SchemaFile

CURRENT_DIRECTORY = Path(__file__).parent.resolve()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--fabric`` selector for fabric-scoped integration validation.

    Example: ``pytest tests/integration -m e2e --fabric Fabric-L2LS`` scopes the
    fabric-deployment validation to ``Fabric-L2LS``. With no ``--fabric`` the
    selector is ``None`` and the fabric-scoped test skips, so the default suite
    behaviour is unchanged.
    """
    parser.addoption(
        "--fabric",
        action="store",
        default=None,
        help="Restrict fabric-scoped integration validation to this fabric (e.g. Fabric-L2LS).",
    )


@pytest.fixture
def target_fabric(request: pytest.FixtureRequest) -> str | None:
    """The fabric name passed via ``--fabric`` (or ``None`` when unset)."""
    return request.config.getoption("--fabric")


@pytest.fixture
def root_directory() -> Path:
    """
    Return the path of the root directory of the repository.
    """
    return CURRENT_DIRECTORY.parent.parent


@pytest.fixture
def schemas_directory(root_directory: Path) -> Path:
    return root_directory / "schemas"


@pytest.fixture
def schemas(schemas_directory: Path) -> list[dict[str, Any]]:
    schema_files = SchemaFile.load_from_disk(paths=[schemas_directory])
    return [item.content for item in schema_files if item.content]
