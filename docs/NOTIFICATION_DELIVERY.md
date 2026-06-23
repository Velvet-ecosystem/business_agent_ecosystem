# Notification Delivery Boundary

External notification delivery is a high-risk operation.

```text
stored notification draft
  -> Notification Delivery Agent
  -> strong-human safety gate
  -> Court authorization
  -> idempotent delivery adapter
  -> durable provider binding
  -> receipt
```

The executor re-reads the scheduled job and stored draft before delivery. Recipient, subject, and body come from the durable draft rather than caller input.

Every delivery uses an idempotency key. Retrying the same request returns the existing provider message instead of sending a duplicate.

If the provider adapter fails, no delivery record is written. A reused idempotency key cannot be rebound to another job or draft.

`InMemoryDeliveryAdapter` is for tests and local development. Production providers must implement the same adapter contract.
