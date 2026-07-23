# Hostvar Contract: EVPN Gateway Domains

## Scope

This contract defines how EVPN Gateway Group intent is exposed to pyAVD by the existing `generate-avd-device-hostvar` pipeline. The implementation extends the current generator query and Python class; it does not create a new Infrahub generator definition.

## GraphQL Contract

Update `generators/avd_device_hostvar.gql` so the target `DcimDevice(name__value: $name)` query can resolve the target device's optional gateway group, the group's parent `local_domain`, the group's selected `pod`, the Pod's `evpn_domain`, the selected `remote_domain`, and peer candidate groups that share the remote domain.

The target device traversal must include at least:

```graphql
evpn_gateway_group {
  node {
    id
    display_label
    name { value }
    resiliency_model { value }
    evpn_l2_enabled { value }
    evpn_l3_enabled { value }
    evpn_l3_inter_domain { value }
    d_path_enabled { value }
    all_active_multihoming_enabled { value }
    ethernet_segment_identifier { value }
    ethernet_segment_rt_import { value }
    local_domain {
      node {
        id
        display_label
        domain_id { value }
        fabric { node { id name { value } } }
      }
    }
    pod {
      node {
        id
        name { value }
        evpn_domain {
          node {
            id
            display_label
            domain_id { value }
            fabric { node { id name { value } } }
          }
        }
      }
    }
    members {
      edges {
        node {
          id
          name { value }
          role { value }
          pod { node { id name { value } } }
        }
      }
    }
    remote_domain {
      node {
        id
        display_label
        domain_id { value }
        fabric { node { id name { value } } }
        remote_gateway_groups {
          edges {
            node {
              id
              display_label
              name { value }
              local_domain {
                node {
                  id
                  domain_id { value }
                  fabric { node { id name { value } } }
                }
              }
              pod {
                node {
                  id
                  name { value }
                  evpn_domain {
                    node {
                      id
                      domain_id { value }
                      fabric { node { id name { value } } }
                    }
                  }
                }
              }
              members {
                edges {
                  node {
                    id
                    name { value }
                    role { value }
                    pod { node { id name { value } } }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

Regenerate the matching Pydantic query model after the `.gql` change. In this repository, `generators/avd_device_hostvar.gql` generates `generators/generate_avd_device_inputs_query.py`; do not hand-edit that file.

## Eligibility Contract

The generator emits EVPN Gateway hostvars only when all are true:

- The target device role is `border_leaf`.
- The target device is linked to exactly one `EvpnGatewayGroup`.
- The target device is a member of that group.
- The group has one parent `local_domain`.
- The group has one selected `pod`.
- The selected Pod has one `evpn_domain`.
- The selected Pod's `evpn_domain` is the same object as the group's `local_domain`.
- The group has one selected `remote_domain`.
- The selected `remote_domain` differs from the group's `local_domain`.
- The group has one or more member devices.
- Every member device has role `border_leaf`.
- Every member device belongs to the group's selected Pod.
- The group uses `resiliency_model == "all_active_multihoming"`.

For every other target role, including `leaf`, `l2leaf`, `spine`, and `super_spine`, the output must not contain an `evpn_gateway` key unless the device is incorrectly modeled as a gateway-group member, in which case generation must fail with an actionable error.

## Peer Derivation Contract

For an eligible target device, derive `remote_peers` from the target group's `remote_domain.remote_gateway_groups`:

- Include member devices from valid gateway groups sharing the same remote domain.
- Validate each candidate group's parent `local_domain`, selected Pod, Pod EVPN Domain, and member devices before using it.
- Exclude the target device.
- Include only candidates with role `border_leaf`.
- Sort peers by hostname.
- Do not store peer hostnames, local domain IDs, or remote domain IDs as independent schema fields.

If the remote domain is not shared by any other valid gateway group, the peer list is empty and the model remains valid unless pyAVD validation rejects the resulting hostvars.

The emitted remote peer entries are hostname-only in this phase:

```yaml
remote_peers:
  - hostname: <remote border leaf hostname>
```

This depends on the existing structured-config generator behavior: it fetches all generated hostvar files for the Fabric and passes the complete `hostname -> hostvars` mapping to `pyavd.get_avd_facts()` before building per-device structured configs. If a named remote peer is not present in that aggregated input, pyAVD cannot infer its BGP ASN and peering address; structured-config generation must report that as a validation failure. Do not add schema fields for peer IP address or BGP ASN in this feature.

## pyAVD Output Contract

For an eligible Border Leaf target, set the gateway payload on the target node under `l3leaf.nodes[0].evpn_gateway`:

```yaml
l3leaf:
  nodes:
    - name: <target device name>
      evpn_gateway:
        remote_peers:
          - hostname: <remote border leaf hostname>
        evpn_l2:
          enabled: <EvpnGatewayGroup.evpn_l2_enabled>
        evpn_l3:
          enabled: <EvpnGatewayGroup.evpn_l3_enabled>
          inter_domain: <EvpnGatewayGroup.evpn_l3_inter_domain>
        d_path:
          enabled: <EvpnGatewayGroup.d_path_enabled>
          local_domain_id: <EvpnGatewayGroup.local_domain.domain_id>
          remote_domain_id: <EvpnGatewayGroup.remote_domain.domain_id>
        all_active_multihoming:
          enabled: <EvpnGatewayGroup.all_active_multihoming_enabled>
          evpn_ethernet_segment:
            identifier: <EvpnGatewayGroup.ethernet_segment_identifier>
            rt_import: <EvpnGatewayGroup.ethernet_segment_rt_import>
```

Do not emit these deprecated pyAVD 6.3.0 keys:

- `all_active_multihoming.enable_d_path`
- `all_active_multihoming.evpn_domain_id_local`
- `all_active_multihoming.evpn_domain_id_remote`

## Ordering Contract

- Emit `remote_peers` in ascending hostname order.
- Do not alter existing deterministic ordering for uplinks, tenants, servers, or node groups.

## Validation Contract

- Call `pyavd.validate_inputs()` on the final hostvars before writing `AvdHostvarFile`.
- If gateway data is invalid or ambiguous, raise an actionable error that includes the group and device context.
- A failed validation must not write or update the target device's hostvar file.

## Tests Contract

Unit tests must cover:

- `border_leaf` maps to `l3leaf`.
- A gateway-group member Border Leaf emits `l3leaf.nodes[0].evpn_gateway`.
- Regular `leaf`, `l2leaf`, `spine`, `super_spine`, and ungrouped `border_leaf` devices do not emit `evpn_gateway`.
- `d_path.local_domain_id` is derived from `EvpnGatewayGroup.local_domain.domain_id`.
- Generator validation rejects a selected Pod whose `evpn_domain` does not match `EvpnGatewayGroup.local_domain`.
- Generator validation rejects a `remote_domain` that equals `EvpnGatewayGroup.local_domain`.
- Remote peer hostnames are derived from other gateway-group member Border Leafs sharing the remote domain.
- Peer hostname ordering is deterministic.
- Generated hostvars pass pyAVD 6.3.0 `validate_inputs()`.
- A fabric-level pyAVD smoke path with two gateway hostvar files can run `get_avd_facts()` and `get_device_structured_config()` with hostname-only remote peers.
- Invalid gateway-group linkage raises an actionable error.
