# Reported Amount Reconciliation

This slice records a strongly approved reported amount against an existing invoice.

The executor requires a completed job, matching invoice, matching handoff confirmation, matching currency, and verified principal. It supports partial reconciliation and rejects totals above the invoice amount.

The system records evidence and computes remaining balance. It does not initiate a transaction or connect to an external financial service.
