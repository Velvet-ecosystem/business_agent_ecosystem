# Route Contract Audit

The capability registry is checked against the actual gate and executor classes.

For every registered capability, tests import the declared modules and require each module to expose exactly one local class whose `route` matches the registry entry.

This prevents stale labels, copied route names, and silent registry drift. The audit does not instantiate executors or grant authority.