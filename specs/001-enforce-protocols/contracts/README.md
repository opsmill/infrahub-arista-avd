# Contracts: Enforce Protocol-Typed Access

No new API contracts are introduced by this feature. This is an internal refactoring that changes how existing code references Infrahub node types (string kinds → protocol classes, raw dicts → Pydantic models).

The "contracts" enforced by this feature are:

1. **Protocol class contract**: All `client.create()`, `client.get()`, and `client.filters()` calls must use protocol class references, not string-based kind parameters.
2. **Pydantic query model contract**: All GraphQL query response access must use typed Pydantic models, not raw dict access.

These contracts are validated by:
- `grep 'kind="' generators/*.py` — must return zero matches
- `mypy` — must pass without new type suppressions
- Code review — dict-style access patterns (`data["key"]`) must not appear in transforms
