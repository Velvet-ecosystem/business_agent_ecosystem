# Continuous Integration

The `tests` workflow runs on:

- every push to `main`
- every pull request
- manual dispatch

The supported CI tier is Python 3.11, matching the repository's declared minimum version.

The workflow performs these checks in order:

```bash
python -m pip install -e ".[dev]"
python -m pip check
python -m compileall -q business_agents tests
python -c "import business_agents"
python -m pytest -q -ra
```

The workflow uses read-only repository permissions and cancels an older in-progress run when a newer commit arrives for the same branch or pull request.

A green workflow means the package installs, dependencies are consistent, Python can compile and import the project, and the complete test suite passes.

Branch protection should require the `Python 3.11` job before merging changes into `main`. Repository settings control that requirement; the workflow file alone cannot enforce branch protection.
