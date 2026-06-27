"""Canonical customer accounts and explicit job bindings."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class CustomerAccount:
    customer_id: str
    display_name: str
    primary_contact_reference: str
    status: str = "active"

    def __post_init__(self) -> None:
        for name in ("customer_id", "display_name", "primary_contact_reference", "status"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.status not in {"active", "inactive"}:
            raise ValueError("unsupported customer status")


@dataclass(frozen=True)
class JobCustomerBinding:
    binding_id: str
    job_id: str
    customer_id: str
    bound_by: str

    def __post_init__(self) -> None:
        for name in ("binding_id", "job_id", "customer_id", "bound_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class CustomerAccountStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="customer-account")

    def create(self, record: CustomerAccount) -> CustomerAccount:
        self._storage.append_unique(asdict(record), field="customer_id")
        return record

    def get(self, customer_id: str) -> CustomerAccount | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("customer_id") == customer_id:
                return CustomerAccount(**payload)
        return None


class JobCustomerBindingStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="job-customer-binding")

    def create(self, record: JobCustomerBinding) -> JobCustomerBinding:
        existing = self.get_by_job(record.job_id)
        if existing is not None:
            raise ValueError(f"job already bound: {record.job_id}")
        self._storage.append_unique(asdict(record), field="binding_id")
        return record

    def get_by_job(self, job_id: str) -> JobCustomerBinding | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("job_id") == job_id:
                return JobCustomerBinding(**payload)
        return None
