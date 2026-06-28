# Capability Registry Audit

The registry is a declarative inventory of bounded business capabilities.

Audit tests verify that:

- routes are unique,
- approval modes remain human-controlled,
- gate modules exist and import,
- executor modules exist and import,
- no registered capability claims external-action authority.

The registry describes capabilities. It does not dispatch intents, bypass safety gates, or grant execution authority.