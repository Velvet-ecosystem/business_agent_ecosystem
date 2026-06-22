# Receipt Chain

`ChainedReceiptStore` links each receipt to the integrity tag of the previous record.

This allows the full log to detect:

- missing records
- reordered records
- altered chain links
- altered receipt contents

The chain metadata is stored inside the signed receipt details:

- `_chain_sequence`
- `_previous_integrity_tag`

## Single-Writer Lock

Chained appends use an adjacent lock file created atomically. A second local writer waits for the lock and fails with `TimeoutError` if it cannot acquire it in time.

Stale lock files may be recovered after the configured age. The lock file is removed when the append completes or raises an exception.

This protects one receipt log on one local filesystem. Distributed writers still require a separate coordination service.

## Example

```python
from business_agents.gateway.chained_receipt_store import ChainedReceiptStore
from business_agents.gateway.signing_key import load_signing_key

store = ChainedReceiptStore(
    "/var/lib/velvet/business/receipts.jsonl",
    signing_key=load_signing_key(required=True),
    require_signing=True,
    lock_timeout=5.0,
    stale_lock_after=60.0,
)

assert store.verify_chain()
```
