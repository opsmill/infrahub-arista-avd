# Menu Contract: EVPN Gateway Domains

## Scope

This contract defines the EVPN Services navigation change for domain-first gateway intent.

## File Contract

Update:

```text
menus/menu.yml
```

The file must keep the existing menu header:

```yaml
# yaml-language-server:
#   $schema=https://schema.infrahub.app/infrahub/menu/latest.json
---
apiVersion: infrahub.app/v1
kind: Menu
spec:
  data:
```

## Item Contract

Add one item under the existing `EVPN Services` group, alongside Tenants, SVIs, and L2 VLANs:

```yaml
- namespace: Evpn
  name: Domains
  label: Domains
  kind: EvpnDomain
  icon: "mdi:domain"
```

The item must use `kind`, not `path`, so Infrahub resolves the object list view.

Do not add a direct `EvpnGatewayGroup` item under EVPN Services. Users should open an EVPN Domain and use its local or remote gateway group relationships to discover EVPN Gateway Groups.

## Schema Integration Contract

`EvpnDomain` must set:

```yaml
include_in_menu: false
```

This prevents duplicate auto-generated menu entries because the repository uses a custom menu.

`EvpnGatewayGroup` also sets `include_in_menu: false`; gateway group access is through EVPN Domain relationship views rather than a direct menu item in this phase.

## Validation Contract

Menu validation after implementation:

```bash
uv run infrahubctl menu load menus/ --branch <branch>
```

Expected outcome:

- The menu loads without YAML or schema errors.
- The EVPN Services section contains exactly one Domains item for `EvpnDomain`.
- The EVPN Services section contains no Gateway/Gateways item for `EvpnGatewayGroup`.
- A user can open an EVPN Domain and discover related gateway groups from the domain detail view.
- No duplicate auto-menu entry is created for `EvpnDomain` or `EvpnGatewayGroup`.
- No menu item points at the removed/out-of-scope `EvpnGateway` kind.
