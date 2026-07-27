from __future__ import annotations

from pathlib import Path


def test_service_portal_generator_run_exposes_no_override_input() -> None:
    source = Path("service_catalog/utils/api.py").read_text(encoding="utf-8")
    run_generator_source = source[source.index("    def _run_generator(") : source.index("    def run_avd_pipeline(")]

    assert "override" not in run_generator_source.lower()
    assert "$targetNodeIds: [String!]" in run_generator_source
    assert "data: { id: $generatorId, nodes: $targetNodeIds }" in run_generator_source
    assert "data: { id: $generatorId, nodes: $targetNodeIds, override" not in run_generator_source
