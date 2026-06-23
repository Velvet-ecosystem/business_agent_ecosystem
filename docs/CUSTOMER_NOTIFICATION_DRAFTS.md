# Customer Notification Drafts

A scheduled job may produce an internal booking-confirmation email draft.

```text
scheduled job + stored booking
  -> Notification Draft Agent
  -> notification-draft safety gate
  -> human approval
  -> Court authorization
  -> executor re-reads job and booking
  -> durable unsent draft
  -> receipt
```

The recipient is taken from the durable job record. The event reference and times are taken from the durable booking record. Callers cannot provide their own recipient, subject, body, or send instruction.

The first supported channel is email, using the fixed `booking-confirmation` template.

The resulting artifact is a draft only. It does not send an email, text message, push notification, or customer-facing event. Receipts record `sent: false`.

A later notification-delivery executor must use a separate approval and idempotent provider boundary.
