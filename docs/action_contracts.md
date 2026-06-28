# Action Contracts

Each registry entry names one supported action.

Tests compare that action with the executor module's `allowed_actions` declaration. This catches stale or copied action names while leaving execution and approval behavior unchanged.