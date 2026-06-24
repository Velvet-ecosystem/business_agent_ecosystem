# Final Store Migration Batch

Schedules, estimates, and receipts now use the locked, legacy-compatible JSONL transport.

New records use schema envelopes, process locks, flush, and `fsync`. Existing raw JSONL records remain readable.

Receipt integrity calculations are unchanged. The receipt payload is signed or hashed exactly as before; only the file transport now uses the locked versioned envelope.

The default application already constructs these store classes, so this migration is active immediately.

With this batch complete, all primary lifecycle stores in the composition root now use locked persistence or locked production replacements.
