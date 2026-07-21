# Contract: Infrahub Check Registration

## Repository Query Registration

`.infrahub.yml` must register the query under top-level `queries`:

```yaml
queries:
  - name: cv_config_check
    file_path: "./checks/cv_config_check.gql"
```

## Repository Check Definition

`.infrahub.yml` must register a targeted check definition:

```yaml
check_definitions:
  - name: cv-config-validation
    file_path: "./checks/cv_config_check.py"
    class_name: CVConfigValidationCheck
    targets: fabrics
    parameters:
      name: name__value
```

The repository check definition must not contain a `query` field. The Python check class binds the query by setting its query name to `cv_config_check`.

## Live Seed Objects

`repository_checks.yml` may seed live `CoreGraphQLQuery` and `CoreCheckDefinition` objects for environments that load repository objects explicitly. In that object data contract, the live `CoreCheckDefinition` can reference the query object because it is Infrahub object data, not `.infrahub.yml` repository config.

## Acceptance Criteria

- `cv_config_check` is present in top-level `queries`.
- `cv-config-validation` is present under `check_definitions`.
- `targets` is `fabrics`.
- `parameters.name` maps to `name__value`.
- `.infrahub.yml` check definition does not include `query`.
- The Python class query name matches the registered query name exactly.
