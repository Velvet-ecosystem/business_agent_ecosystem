# Work-Start Authorization

A scheduled job may enter `in-progress` only through an explicit work-start ceremony.

```text
scheduled job + stored booking
  -> Work Start Agent
  -> work-start safety gate
  -> strong human approval
  -> Court authorization
  -> executor re-reads job and booking
  -> durable work-start record
  -> job becomes in-progress
  -> receipt
```

The request must name who is starting the work and why. The booking must exist and belong to the same job.

The executor rejects stale job state, missing bookings, bookings for another job, duplicate start records, and unexpected fields.

Work-start records are append-only. A job may have only one recorded start ceremony.
