# Contract: DCI Link GraphQL Input and PyAVD Output

This contract defines the data shape the hostvars generator must consume and the
PyAVD `l3_edge` shape it must produce.

## Query Scope

Extend `generators/avd_device_hostvar.gql` so each target `DcimDevice` can
evaluate DCI links in the device's fabric. The query may fetch all
`NetworkDciLink` objects in the relevant fabric and filter in typed Python, or
use server-side relationship filters if the generated GraphQL schema supports
them.

The implementation must regenerate
`generators/generate_avd_device_inputs_query.py` after changing the query.

## Required DCI Fields

The final query must provide enough data to build and validate each DCI link:

```graphql
NetworkDciLink {
  edges {
    node {
      __typename
      id
      display_label
      name { value }
      include_in_underlay_protocol { value }
      endpoint_1_bgp_asn { value }
      endpoint_2_bgp_asn { value }
      connected_endpoints {
        edges {
          node {
            __typename
            id
            ... on InterfacePhysical {
              name { value }
              description { value }
              device {
                node {
                  __typename
                  id
                  name { value }
                  ... on DcimDevice {
                    role { value }
                    pod {
                      node {
                        parent {
                          node {
                            __typename
                            id
                            ... on NetworkFabric {
                              dci_pool {
                                node {
                                  id
                                  name { value }
                                  default_prefix_length { value }
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
            }
          }
        }
      }
    }
  }
}
```

If the generated GraphQL schema exposes inherited endpoint relationships under
different field names, adjust the query while preserving the contract: link
identity, underlay flag, two BGP ASN values, two physical interfaces, endpoint
device role/fabric, and the fabric DCI pool source.

## Allocation Contract

For each valid DCI link, allocate or reuse one `/31` prefix from
`NetworkFabric.dci_pool` using a stable identifier based on the DCI link
identity. Convert the two usable addresses from that prefix into the generated
PyAVD `ip` list in the same normalized endpoint order used for `nodes`,
`interfaces`, and `as`.

The allocation must be idempotent:

- Re-running generation for unchanged data reuses the same `/31`.
- The same DCI link is not allocated twice when both endpoint devices generate
  hostvars.
- Duplicate endpoint-interface pairs are detected before allocation.

## PyAVD Output Contract

For every valid DCI link, emit one deterministic `l3_edge.p2p_links[]` entry:

| PyAVD link field | Source |
|------------------|--------|
| `nodes` | connected endpoint device names |
| `interfaces` | connected physical interface names |
| `as` | DCI link BGP ASN values paired with endpoint order |
| `ip` | two addresses from the allocated `/31` |
| `speed` | existing typed interface speed if available; otherwise documented default `100g` |
| `include_in_underlay_protocol` | DCI link underlay flag, defaulting `true` |

Normalize the two endpoints into a stable order before producing lists, and sort
multiple DCI links by stable link identity plus endpoint identity. Only the
supported PyAVD fields listed above are emitted for this phase. DCI output must
not emit `l3_edge.p2p_links_profiles[]`, `profile`, or shared DCI profile
references.

## Invalid DCI Handling

The generator must report actionable context for:

- Fewer or more than two endpoints.
- Non-physical endpoint objects.
- Non-Border Leaf endpoint devices.
- Same-device or same-interface endpoint pairs.
- Duplicate endpoint-interface pairs.
- Missing BGP ASN values.
- Missing fabric DCI pool.
- Failed `/31` allocation.

Silent omission is not acceptable.
