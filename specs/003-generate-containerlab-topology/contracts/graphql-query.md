# Contract: GraphQL Query `containerlab_topology`

**File**: `transforms/containerlab_topology.gql`
**Registered**: `.infrahub.yml` → `queries[].name: containerlab_topology`
**Consumed by**: `ContainerLabTopology.query = "containerlab_topology"`

## Input

| Variable | Type | Source (artifact param) |
|----------|------|-------------------------|
| `$name` | `String!` | `name__value` of the target `NetworkFabric` |

## Required output fields

The query MUST return, scoped to the single named fabric:

```graphql
query ContainerLabTopology($name: String!) {
  NetworkFabric(name__value: $name) {
    edges {
      node {
        name { value }
        children {
          edges {
            node {
              ... on NetworkPod {
                devices {
                  edges { node { ...deviceFields } }
                }
                racks {
                  edges {
                    node {
                      devices { edges { node { ...deviceFields } } }
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

Where `deviceFields` (on `DcimDevice`) MUST include:

```graphql
name { value }
role { value }
device_type { node { name { value } } }
mgmt_ip { node { ... on IpamIPAddress { address { value } } } }
interfaces {
  edges {
    node {
      __typename
      name { value }
      ... on DcimEndpoint { connector { node { id } } }
    }
  }
}
```

## Endpoint resolution

Link endpoint details (device name + interface name on both ends of each `NetworkLink`) are
obtained either inline (if `connected_endpoints` with device+name is queryable in one shot) or via a
secondary batched `NetworkLink(ids: [...])` query following the `CablingPlan` pattern. Either
satisfies the contract; the response MUST expose, per link: two endpoints each with device name and
interface name.

## Guarantees the transform relies on

- Fabric name is present.
- Each device exposes `role`, `device_type.node.name`, and its interfaces.
- `mgmt_ip` MAY be null (handled — node emitted without `mgmt-ipv4`).
- Each participating interface exposes a `connector` link id.

## Typing

A Pydantic model in `transforms/containerlab_topology_query.py` MUST mirror this response shape
(no untyped dict access in transform logic — Constitution III).
