# Receipt Atomicity

Executor-visible mutations are committed only after the corresponding receipt append succeeds.

```text
build candidate result
  -> append receipt
  -> expose task or note in executor state
```

If receipt storage raises an error, the executor propagates the failure and leaves no surviving task or note. The next successful operation begins with the expected first sequence identifier rather than inheriting a ghost mutation.

This establishes the local rule:

> No valid receipt, no surviving mutation.

The current guarantee covers executor-managed in-memory state. Future integrations with databases, files, vendor systems, or other durable stores must provide equivalent transactional or compensating behavior before they are treated as approved executors.
