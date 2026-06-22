# Executor Routing

Approved intents are resolved through `ExecutorRegistry` by route and action.

The coordinator does not know the concrete executor type. It asks the registry for one executor that explicitly supports the authorized intent.

```text
approved intent
  -> executor registry
  -> route lookup
  -> action support check
  -> bounded executor
  -> receipt
```

The registry rejects:

- unknown routes
- unsupported actions
- duplicate route registrations
- executors without a route

A missing executor produces a denied receipt with the route, action, and authorization identifier preserved for audit.

This registry changes routing only. It does not grant authority, bypass safety checks, or allow an executor to broaden its own capabilities.
