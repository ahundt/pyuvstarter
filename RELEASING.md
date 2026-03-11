# Releasing pyuvstarter

## Version number locations (keep in sync)

| File | Location |
|------|----------|
| `pyproject.toml` | line 3: `version = "X.Y.Z"` |

The canonical version is read at runtime via `importlib.metadata.version("pyuvstarter")`.
There is no `__version__` in `pyuvstarter.py`; the source of truth is `pyproject.toml`.

## Version bump checklist

1. Update `pyproject.toml` `version = "X.Y.Z"`
2. Run full tests: `./tests/run_all_tests.sh`
3. Commit: `git commit -m "chore(version): bump to X.Y.Z"`
4. Reinstall: `uv tool install . --force`
5. Verify: `pyuvstarter --version`  # → "pyuvstarter X.Y.Z"
6. Tag: `git tag vX.Y.Z`
7. Push: `git push origin main --tags`

## PyPI Publishing (automated via GitHub Actions)

After pushing the tag (step above), GitHub Actions will:
1. Run the full CI test suite across all platforms (via reusable `ci.yml` workflow)
2. Verify the tag version matches `pyproject.toml` version
3. Build wheel + sdist with `uv build`
4. Publish to TestPyPI (requires `testpypi` environment — approve automatically)
5. Publish to PyPI (requires `pypi` environment — manual approval gate)

### First-time setup (one-time, before first tag push)

1. Create accounts on [pypi.org](https://pypi.org/account/register/) and [test.pypi.org](https://test.pypi.org/account/register/)
2. Enable 2FA on both accounts (required by PyPI since 2023)
3. Configure **Trusted Publishers** on **TestPyPI** first:
   - Project Name: `pyuvstarter`
   - Owner: `athundt`
   - Repository: `pyuvstarter`
   - Workflow filename: `publish.yml`
   - Environment: `testpypi`
4. Configure **Trusted Publishers** on **PyPI** (same fields, Environment: `pypi`)
5. Create GitHub Environments in repo Settings → Environments:
   - `testpypi` — no protection rules needed
   - `pypi` — add yourself as required reviewer (manual approval gate)

### First-time TestPyPI verification

```bash
uv pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    pyuvstarter
pyuvstarter --version
```

### Manual publishing (fallback if CI is unavailable)

```bash
uv build
uv publish  # prompts for credentials; use API token or OIDC if configured
```

### Troubleshooting

- **`startup_failure` in publish workflow**: The `test:` job that calls `ci.yml` must have a `permissions:` block. See `.github/workflows/publish.yml` — the `test:` job section.
- **Version mismatch error**: The git tag (e.g., `v0.4.0`) must exactly match `pyproject.toml` version (`0.4.0`).
- **Trusted Publisher 403**: Configure the publisher on the target registry BEFORE pushing the tag.
