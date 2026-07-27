# Contributing

Thank you for helping improve Velvet business operations.

## Start with the boundary

This repository is a bounded business surface within Velvet Unified-Organ AI. Contributions must preserve these rules:

- Runtime coordinates production execution.
- Court authorizes bounded capabilities.
- Event Protocol carries observations, requests, proposals, results, and lifecycle events.
- Models and business organs may reason and propose, but never hold authority.
- Executors perform one validated operation.
- Receipts preserve evidence and never grant permission.
- External actions must be idempotent, reconciled, and fail closed.

Do not add direct connector, shell, file, finance, inventory-mutation, credential, or hardware paths that bypass Runtime, Court, safety gates, executor registration, or Receipts.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Pull requests

Keep pull requests focused. Explain:

1. the business problem;
2. the authority and safety boundary;
3. what can and cannot produce side effects;
4. tests for denial, stale state, replay, failure, and idempotency where applicable;
5. whether any material is public-safe.

Legacy `agent` package and class names remain for compatibility. New architecture documentation should use bounded business organ language unless discussing an exact implementation symbol.

## Public and private material

Never commit credentials, API keys, customer records, financial records, medical data, owner policy, private archives, real addresses, provider tokens, or hardware-specific secrets. Use synthetic examples and local secret storage.

## External connectors

Production connectors require a separate review. They must not select credentials or authority from model output, and provider attempts must remain durably reconcilable through idempotency keys, operation journals, and canonical Receipts.
