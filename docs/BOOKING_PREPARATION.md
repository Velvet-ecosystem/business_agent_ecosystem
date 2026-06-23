# Exact-Window Booking Preparation

One candidate window from a stored schedule proposal may be selected for internal booking preparation.

```text
stored schedule proposal + selected index
  -> Booking Preparation Agent
  -> booking-preparation safety gate
  -> human approval
  -> Court authorization
  -> executor re-reads job and proposal
  -> exact stored window selected
  -> durable preparation record and receipt
```

The executor verifies that:

- the job is still `ready-to-schedule`
- the schedule proposal exists
- the proposal belongs to the same job
- the selected index exists in the stored proposal

The selected start and end times are copied from the durable proposal, not accepted from caller input.

A preparation record is not a booking. It does not create a calendar event, reserve staff, contact a customer, or move the job to `scheduled`. Receipts record `booking_created: false`.
