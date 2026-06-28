"""Executor for approved stock reservation records."""

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JsonlJobStore
from business_agents.stock_reservations import StockReservation, StockReservationStore


class StockReservationExecutor(BaseExecutor):
    route = "stock-reservation"
    allowed_actions = frozenset({"record-stock-reservation"})

    def __init__(self, jobs: JsonlJobStore, reservations: StockReservationStore, receipts: JsonlReceiptStore) -> None:
        self.jobs = jobs
        self.reservations = reservations
        self.receipts = receipts

    def execute(self, intent: BusinessIntent, *, authorization_id: str, authorization_fingerprint: str, authorization_issued_at: float, authorization_expires_at: float) -> ExecutorResult:
        if not self.supports(intent):
            raise ValueError("unsupported intent")
        if not authorization_id.strip() or not authorization_fingerprint.strip():
            raise ValueError("authorization metadata is required")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")

        job = self.jobs.require(intent.subject_id)
        record = StockReservation(
            reservation_id=str(intent.parameters["reservation_id"]),
            job_id=job.job_id,
            item_reference=str(intent.parameters["item_reference"]),
            quantity_reference=str(intent.parameters["quantity_reference"]),
            location_reference=str(intent.parameters["location_reference"]),
            reserved_by=str(intent.parameters["reserved_by"]),
        )
        self.reservations.create(record)
        receipt = self.receipts.append(
            actor="Stock Reservation Executor",
            decision="completed",
            executor="Stock Reservation Executor",
            subject_id=job.job_id,
            details={
                "reservation_id": record.reservation_id,
                "job_id": record.job_id,
                "item_reference": record.item_reference,
                "quantity_reference": record.quantity_reference,
                "location_reference": record.location_reference,
                "reserved_by": record.reserved_by,
                "stock_changed": False,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        return ExecutorResult(
            executor_name="Stock Reservation Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"reservation_id": record.reservation_id, "job_id": record.job_id, "stock_changed": False},
        )
