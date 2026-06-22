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

## Example

```python
from business_agents.gateway.chained_receipt_store import ChainedReceiptStore
from business_agents.gateway.signing_key import load_signing_key

store = ChainedReceiptStore(
    "/var/lib/velvet/business/receipts.jsonl",
    signing_key=load_signing_key(required=True),
    require_signing=True,
)

assert store.verify_chain()
```

This first implementation assumes one local writer. File locking and multi-process coordination remain future hardening work.
