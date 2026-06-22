# Internal Operations Note Slice

The second business-agent vertical slice records a short local-only operations note.

```text
operations context
  -> Operations Note Agent proposal
  -> route-aware safety registry
  -> Internal Note safety gate
  -> Court decision
  -> executor registry
  -> Note Executor
  -> receipt
```

The note route is intentionally narrow:

- local storage only
- no recipients
- no email or webhook fields
- no payments or purchase orders
- title limited to 120 characters
- body limited to 2,000 characters

The slice proves that one coordinator can safely route two distinct approved capabilities:

- `internal-task` to `TaskExecutor`
- `internal-note` to `NoteExecutor`

The route registry does not grant authority. Identity, safety, Court approval, executor capability checks, and receipts remain mandatory.
