# Contract: Validation Evidence

## Purpose

Define the evidence required before the direct submission revision is considered
ready for review.

## Local Unit Evidence

Required command:

```bash
uv run pytest tests/unit/test_cv_integration.py
```

Required coverage:

- Direct handler submits exactly one linked submit-ready workspace.
- Already-submitted workspace path issues no duplicate submit request.
- Missing linked workspace path skips CloudVision calls.
- Ambiguous linked workspace path blocks submission.
- CloudVision failure path records unresolved failure outcomes.
- Fallback logging path preserves operational context.
- Repository objects do not contain the removed placeholder webhook
  registration.
- Documentation does not require a separate placeholder receiver service.

## Static Evidence

Required command:

```bash
uv run invoke lint
```

If a narrower local check is used while developing, final review still requires
the full lint task or an explicit exception.

## Schema Evidence

If schema files are changed:

```bash
uv run infrahubctl schema check schemas/
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

If no schema files are changed, record that schema validation was not applicable
for this revision.

## Integration Evidence

Required validation:

```text
$infrahub-run-integration-tests
```

The evidence must include:

- tested branch,
- tested commit,
- pass/fail result,
- confirmation that repository loading does not install the placeholder
  CloudVision workspace submission webhook,
- or an explicit maintainer-approved exception.

## Documentation Evidence

Review `docs/docs/cloudvision.md` and feature quickstart output for these
required statements:

- direct post-merge/API execution path owns submission,
- manual retry uses `uv run invoke submit-cv-workspace`,
- no separate placeholder webhook receiver service is required,
- failures after Infrahub merge are recorded as unresolved CloudVision
  submission outcomes or fallback logs.
