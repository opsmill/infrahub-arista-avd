# Quickstart: CloudVision Config Validation

Run the custom webhook unit validation:

```bash
uv run pytest tests/unit/test_cv_integration.py
```

Run the standard lint gate:

```bash
uv run invoke lint
```

Submit or retry a CloudVision workspace for a proposed change:

```bash
uv run invoke submit-cv-workspace --proposed-change-id <proposed-change-id> --branch main
```

Use the required integration validation path before merge:

```text
$infrahub-run-integration-tests
```

Expected repository state:

- Exactly one intended CloudVision workspace submission `CoreCustomWebhook` is present.
