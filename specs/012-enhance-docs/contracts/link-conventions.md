# Contract: Link Conventions

How docs link to each other and to source code. These rules give every link in the doc set a predictable shape and let `npm run build` catch as many breakages as possible.

## 1. Same-track links → Markdown-relative

Use the `./` or `../` form pointing at the `.md` file. Docusaurus rewrites the URL and validates the target at build time (`onBrokenMarkdownLinks: 'throw'`).

```md
For the full pipeline overview, see [AVD Integration Overview](./overview.md).
For the role table, see [Role Mapping](./role-mapping.md).
```

## 2. Cross-track links → site-absolute path with audience-signalling text

Cross-track links MUST start with `/user-guide/` or `/developer-guide/` and the surrounding sentence MUST include an audience word so a reader knows they are switching track.

**Audience words** (use one):
- For links into the user guide: "operator workflow", "user guide", "how-to"
- For links into the developer guide: "developer reference", "developer guide", "internals"

```md
For the operator workflow that creates these objects, see the
[Add a Network Segment how-to](/user-guide/how-to/add-network-segment).

The hostvars structure passed to pyAVD is documented in the
[developer reference for hostvars](/developer-guide/avd/hostvars).
```

A cross-track link without an audience word is a review-blocker (FR-004).

## 3. Source-code links → repo-absolute GitHub URL on `main`

For files outside `docs/`, link to the canonical GitHub URL on `main`. This matches the `editUrl` pattern already used in `docusaurus.config.ts` for the docs themselves.

```md
The role map lives in
[`src/solution_arista_avd/avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/avd.py).
```

When linking to a specific symbol, append the line range or a stable anchor only if the symbol is at a fixed location:

```md
See the [`InfrahubToAvdRole` mapping](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/avd.py#L42-L60).
```

Avoid line numbers if the file is volatile; prefer the symbol name and let the reader search.

## 4. Test references → name only, link via repo path

Where the docs cite a test that pins behaviour (FR-022), name the test file path and link it the same way as a source file:

```md
The role mapping is exercised by
[`tests/unit/test_avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/tests/unit/test_avd.py).
```

If the test is a single function, name it in prose: "see `test_role_map_super_spine`".

## 5. External docs → plain absolute URL

Third-party documentation (pyAVD, Infrahub, Arista) uses plain absolute URLs. Pin the version in the URL when the upstream offers versioned docs:

```md
[pyAVD documentation](https://avd.arista.com/5.5/docs/pyavd/pyavd.html)
```

## 6. Forbidden patterns

- Linking to `.md` files **across** tracks via `../`. Always use the site-absolute `/user-guide/...` or `/developer-guide/...` form for cross-track jumps so the path survives a directory move.
- Bare URLs (`See https://...`) — always use `[link text](url)`.
- Hard-coded localhost URLs in prose; use `${INFRAHUB_UI_URL}` or "the Infrahub UI" instead.
- Linking to a GitHub commit SHA except when documenting historical behaviour (R6).

## 7. Verification

- `npm run build` from `docs/` MUST pass with no warnings. The `onBrokenLinks: 'throw'` and `onBrokenMarkdownLinks: 'throw'` settings already on the project enforce rules 1 and 2 (path validity).
- Audience-word presence in cross-track link text (rule 2) is a manual review check.
- Source-link target validity (rules 3 and 4) is a manual review check; a follow-up CI step could `curl -I` each `github.com/opsmill/infrahub-arista-avd/blob/main/...` link, but that is out of scope.
