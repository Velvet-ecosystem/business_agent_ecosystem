# Proposal-Only Scheduling

A job in `ready-to-schedule` may produce durable internal candidate windows through a bounded Scheduling Agent flow.

```text
ready-to-schedule job + candidate windows
  -> Scheduling Agent
  -> schedule-proposal safety gate
  -> human approval
  -> Court authorization
  -> executor re-reads durable job state
  -> append-only schedule proposal
  -> receipt
```

Candidate windows must:

- include timezone offsets
- use a valid named timezone
- be ordered
- not overlap
- contain between one and ten choices

The executor refuses to create a proposal if the durable job is no longer `ready-to-schedule`. Duplicate proposal identifiers are rejected.

A schedule proposal is not a booking. It does not create a calendar event, contact the customer, reserve staff, or move the job to `scheduled`.

`JsonlScheduleStore` currently preserves immutable internal proposals while the later booking contract is designed.
