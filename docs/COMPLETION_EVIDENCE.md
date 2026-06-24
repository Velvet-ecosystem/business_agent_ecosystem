# Completion Evidence

Completion evidence is recorded before a job may be moved from `in-progress` to `completed`.

The first slice adds:

- `CompletionEvidence`
- `CompletionEvidenceStore`
- `CompletionEvidenceAgent`
- `CompletionEvidenceSafetyGate`
- `CompletionEvidenceExecutor`

Evidence records bind one job to:

- the verified principal who completed the work
- a completion summary
- one or more checklist confirmations
- optional artifact references
- optional customer acknowledgement

The agent derives `completed_by` from `_principal_id`. Caller-supplied actor text is ignored.

This pull request records evidence only. The next bounded change will require an exact evidence reference before the terminal `completed` job transition is authorized.
