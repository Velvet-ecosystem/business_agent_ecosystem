# Business Stack Checkpoint

The first business capability sequence is complete:

- invoice delivery preparation and confirmation
- payment reconciliation records
- customer accounts and job bindings
- change-order amendment records
- job cost and material references
- stock reservation records
- communication history
- derived report snapshots

Each capability uses stable identifiers, explicit approval, append-only records, bounded execution, and receipts.

## Current integration gap

Capabilities currently declare their own route, action, risk, approval mode, gate, and executor. The next foundation should add a central capability registry and an audit test that confirms every registered route has:

1. one declared approval mode,
2. one safety gate,
3. one bounded executor,
4. receipt production,
5. an explicit external-action boundary.

The registry must describe capabilities only. It must not bypass gates, grant authority, or execute actions.

## Deferred areas

Payroll, automated banking, tax filing, autonomous purchasing, subscription billing, and broad accounting integrations remain out of scope.