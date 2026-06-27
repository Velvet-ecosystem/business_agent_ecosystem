"""Executor for approved account-to-job links."""

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.customer_accounts import CustomerAccount, CustomerAccountStore, JobCustomerBinding, JobCustomerBindingStore
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JsonlJobStore


class AccountLinkExecutor(BaseExecutor):
    route = "customer-account-binding"
    allowed_actions = frozenset({"create-and-bind-customer"})

    def __init__(self, jobs: JsonlJobStore, accounts: CustomerAccountStore, links: JobCustomerBindingStore, receipts: JsonlReceiptStore) -> None:
        self.jobs = jobs
        self.accounts = accounts
        self.links = links
        self.receipts = receipts

    def execute(self, intent: BusinessIntent, *, authorization_id: str, authorization_fingerprint: str, authorization_issued_at: float, authorization_expires_at: float) -> ExecutorResult:
        if not self.supports(intent):
            raise ValueError("unsupported intent")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")
        job = self.jobs.require(intent.subject_id)
        if self.links.get_by_job(job.job_id) is not None:
            raise ValueError("job already linked")

        account = CustomerAccount(
            customer_id=str(intent.parameters["customer_id"]),
            display_name=str(intent.parameters["display_name"]),
            primary_contact_reference=str(intent.parameters["primary_contact_reference"]),
        )
        existing = self.accounts.get(account.customer_id)
        if existing is None:
            self.accounts.create(account)
        elif existing != account:
            raise ValueError("account record mismatch")

        link = JobCustomerBinding(
            binding_id=str(intent.parameters["binding_id"]),
            job_id=job.job_id,
            customer_id=account.customer_id,
            bound_by=str(intent.parameters["bound_by"]),
        )
        self.links.create(link)
        receipt = self.receipts.append(
            actor="Account Link Executor",
            decision="completed",
            executor="Account Link Executor",
            subject_id=job.job_id,
            details={
                "customer_id": account.customer_id,
                "binding_id": link.binding_id,
                "job_id": link.job_id,
                "snapshot_preserved": True,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        return ExecutorResult(
            executor_name="Account Link Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"customer_id": account.customer_id, "binding_id": link.binding_id, "job_id": link.job_id},
        )
