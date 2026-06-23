# Calendar Booking Boundary

Real calendar booking is a high-risk operation.

The approved flow is:

```text
booking preparation
  -> Booking Agent
  -> Booking Safety Gate
  -> strong human approval
  -> Court authorization
  -> Booking Executor
  -> calendar adapter
  -> booking record
  -> job becomes scheduled
  -> receipt
```

The executor verifies the job state and preparation ownership before calling the adapter.

Every request carries an idempotency key. Repeating the same request returns the same event instead of creating another event.

The job changes to `scheduled` only after a calendar event exists. Adapter failure leaves the job in `ready-to-schedule`.

A job already marked `scheduled` may only replay the same stored booking. A different idempotency key is rejected.

`InMemoryCalendarAdapter` is for tests and local development. Production adapters must implement the same contract.
