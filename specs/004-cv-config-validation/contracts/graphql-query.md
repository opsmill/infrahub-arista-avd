# Contract: Targeted GraphQL Query

## Operation

`cv_config_check` is a targeted check query.

```graphql
query CVConfigCheck($name: String!) {
  NetworkFabric(name__value: $name) {
    edges {
      node {
        id
        name {
          value
        }
        cloudvision_managed {
          value
        }
      }
    }
  }
  DcimDevice {
    edges {
      node {
        id
        name {
          value
        }
        serial {
          value
        }
        pod {
          node {
            id
            parent {
              node {
                __typename
                id
              }
            }
          }
        }
        avd_artifact {
          node {
            id
            structured_config_file {
              node {
                id
              }
            }
          }
        }
      }
    }
  }
}
```

## Variables

| Name | Type | Source |
| ---- | ---- | ------ |
| `name` | `String!` | Target fabric `name__value` from the `fabrics` group |

## Response Requirements

- `NetworkFabric.edges[0].node.id` identifies the target fabric.
- `NetworkFabric.edges[0].node.name.value` supplies the fabric display name.
- `NetworkFabric.edges[0].node.cloudvision_managed.value` determines whether CloudVision validation applies.
- `DcimDevice.edges[*].node.name.value` supplies device names.
- `DcimDevice.edges[*].node.serial.value` supplies CloudVision serial numbers.
- `DcimDevice.edges[*].node.pod.node.parent.node.id` supplies fabric membership.
- `DcimDevice.edges[*].node.avd_artifact.node.structured_config_file.node.id` supplies the structured-config file identity.

## Nullability Contract

The check must tolerate these values being absent or null:

- `pod`
- `pod.node`
- `pod.node.parent`
- `pod.node.parent.node`
- `avd_artifact`
- `avd_artifact.node`
- `avd_artifact.node.structured_config_file`
- `avd_artifact.node.structured_config_file.node`
- `serial.value`
- `cloudvision_managed.value`

Missing fabric `cloudvision_managed` is treated as `false` during rollout. Missing pod or parent relationship data means a device is not confirmed to belong to the target fabric and is ignored. Missing artifact or structured-config relationship data does not remove a confirmed managed-fabric device from serial-number or inventory eligibility; it only means that device has no generated config to deploy after eligibility succeeds.

## Acceptance Criteria

- The query declares and uses the `$name` variable.
- The generated query model reflects nullable relationship fields.
- The check never indexes a missing relationship without a guard.
- Device selection is computed from the target fabric ID, not from device name patterns.
- Managed-fabric serial-number and inventory eligibility is computed before structured-config deployment selection.
