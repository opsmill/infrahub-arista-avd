# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-01

### Added

- Initial release of the Infrahub Workflow Routing preset
- `speckit.specify` command override with Infrahub artifact routing
- `speckit.plan` command override with mandatory Infrahub skill invocation
- `speckit.implement` command override with task-level artifact detection
- Multi-artifact dependency chain ordering (Schema first)
- Connectivity gating via `infrahubctl info`
- Artifact type detection for schema, transform, check, generator, and menu
