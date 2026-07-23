"""Documentation contract tests for EVPN Gateway domain ownership."""

from pathlib import Path


def test_gateway_docs_describe_domain_owned_local_gateway_groups() -> None:
    schema_docs = Path("docs/docs/developer-guide/schemas.md").read_text(encoding="utf-8")
    hostvar_docs = Path("docs/docs/developer-guide/avd/hostvars.md").read_text(encoding="utf-8")
    generator_docs = Path("docs/docs/developer-guide/generators.md").read_text(encoding="utf-8")
    capabilities = Path("docs/docs/supported-capabilities.md").read_text(encoding="utf-8")

    combined = f"{schema_docs}\n{hostvar_docs}\n{generator_docs}\n{capabilities}"

    assert "local_domain` -> `EvpnDomain` (parent)" in schema_docs
    assert "selected Pod must have `evpn_domain` set to the same object as `local_domain`" in schema_docs
    assert "schema-valid HFID uses the selected Pod and group name" in schema_docs
    assert "EvpnDomain.local_gateway_groups" in schema_docs
    assert "derives the local D-PATH domain ID from `EvpnGatewayGroup.local_domain`" in hostvar_docs
    assert "Pod/local-domain mismatches" in generator_docs
    assert "domain-owned local `EvpnGatewayGroup` children" in capabilities
    assert "Pod-scoped `EvpnGatewayGroup`" not in combined
    assert "derived from `pod.evpn_domain`" not in combined
