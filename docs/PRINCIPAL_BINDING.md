# Principal-Bound Execution

`VerifiedBusinessCoordinator` is the strict execution wrapper for verified actors.

It rejects stale principals before agent proposal or Court evaluation, injects reserved principal context, delegates through the existing safety and Court path, and appends an actor-binding receipt linked to the executor receipt.

`VerifiedWorkStartAgent` derives `started_by` from `_principal_id`. Caller-supplied actor names are ignored.

The compatibility coordinator remains available for older tests and slices. New high-risk flows should use the verified coordinator and principal-derived agents.

The remaining migration item is to replace the legacy Court implementation with a principal-and-session-bound grant store once the authority module can be changed safely without breaking existing authorization tests.
