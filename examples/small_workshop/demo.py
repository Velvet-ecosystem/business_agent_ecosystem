"""Run the first Velvet business-agent vertical slice."""

from pathlib import Path

from business_agents.agents.inventory_agent import InventoryAgent
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_gate import InternalTaskSafetyGate


def main() -> None:
    receipt_store = JsonlReceiptStore(Path("state/receipts.jsonl"))
    executor = TaskExecutor(receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=InternalTaskSafetyGate(),
        task_executor=executor,
    )

    print("Inventory Agent detected low stock")
    result = coordinator.run(
        InventoryAgent(),
        {
            "sku": "FILTER-001",
            "location": "small-workshop",
            "on_hand": 2,
            "reorder_point": 8,
            "suggested_quantity": 12,
        },
        identity_verified=True,
    )
    print("Court approved internal task creation")
    print(f"Task Executor created task: {result.output['title']}")
    print(f"Receipt written: {result.receipt_id}")


if __name__ == "__main__":
    main()
