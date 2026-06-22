# Receipt Signing

Business-agent receipts may use HMAC-SHA256 so a verifier can confirm both content integrity and possession of the local signing key.

## Key Sources

Use one of these local sources:

- environment variable `VELVET_RECEIPT_SIGNING_KEY`
- a local key file supplied by deployment configuration

The key must not be committed to Git. File-based keys should be readable only by the service account running the local gateway.

## Example

```python
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.signing_key import load_signing_key

key = load_signing_key(required=True)
store = JsonlReceiptStore(
    "/var/lib/velvet/business/receipts.jsonl",
    signing_key=key,
    require_signing=True,
)
```

## Deployment Rule

Development may allow unsigned SHA-256 receipts for compatibility. Production-like deployments should require HMAC signing and fail closed when the key is absent.

Rotating a key creates a verification boundary. Preserve the old key securely or record a key identifier in a future receipt schema before rotation is introduced.
