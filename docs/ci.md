# Continuous Integration

The test workflow runs on pushes to `main`, pull requests, and manual dispatch.

It installs the package with development dependencies and executes:

```bash
pytest -q
```

The workflow is intentionally small so a failed run points directly at packaging, dependency, or test problems rather than hiding them behind a larger build matrix.
