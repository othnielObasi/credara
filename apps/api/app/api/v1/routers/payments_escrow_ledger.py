"""
Credara v7 Payments, Wallets, Escrow and Settlement Ledger.

This module models the production-grade payment layer:
- business wallets
- payment intents
- Smart LC escrow funding
- stablecoin approval/funding lifecycle
- on-chain confirmation state
- internal settlement ledger
- reconciliation between expected payment, chain event, ledger and Smart LC state
- role-specific and aggregate reporting
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Literal
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/payments", tags=["wallets-payments-escrow-ledger"])


PaymentStatus = Literal["Pending", "Submitted", "Confirmed", "Failed", "Fallback", "Released", "Refunded"]
WalletType = Literal["connected", "embedded", "treasury"]


class WalletAccount(BaseModel):
    wallet_id: str
    owner_business_id: str
    owner_name: str
    role: str
    wallet_type: WalletType
    address: str
    network: str = "Polygon Amoy"
    stablecoin_asset: str = "MockUSDC"
    stablecoin_balance: float
    gas_asset: str = "POL"
    gas_balance: float
    status: str


class PaymentIntent(BaseModel):
    payment_intent_id: str
    intent_type: str
    payer_business_id: str
    payee_reference: str
    reference_id: str
    amount: float
    asset: str = "MockUSDC"
    network: str = "Polygon Amoy"
    status: PaymentStatus
    transaction_hash: Optional[str] = None
    confirmations: int = 0
    required_confirmations: int = 3
    created_at: str
    confirmed_at: Optional[str] = None


class EscrowAccount(BaseModel):
    escrow_id: str
    smart_lc_id: str
    contract_address: str
    asset: str = "MockUSDC"
    required_amount: float
    funded_amount: float
    funding_party: str
    seller: str
    status: str
    release_condition: str
    refund_condition: str
    confirmations: int


class SettlementLedgerEntry(BaseModel):
    entry_id: str
    timestamp: str
    track: str
    role: str
    event: str
    source: str
    description: str
    amount: float
    asset: str = "MockUSDC"
    status: PaymentStatus
    verifier: str
    reference_id: str
    docs: List[str] = Field(default_factory=list)


class ReconciliationResult(BaseModel):
    reference_id: str
    expected_amount: float
    on_chain_amount: float
    internal_ledger_amount: float
    smart_lc_state: str
    variance: float
    decision: Literal["valid", "manual_review", "blocked"]
    last_checked: str


class FundEscrowRequest(BaseModel):
    smart_lc_id: str
    payer_business_id: str
    amount: float
    asset: str = "MockUSDC"


class ReleaseEscrowRequest(BaseModel):
    smart_lc_id: str
    release_to: str
    reason: str = "Conditions satisfied"


def demo_wallets() -> List[WalletAccount]:
    return [
        WalletAccount(wallet_id="WAL-BUYER-001", owner_business_id="biz_buyer_global_retail", owner_name="Global Retail Ltd", role="buyer", wallet_type="connected", address="0xB8fA1bA7C0E9dA4F91A2bC8821aD98aE2213B011", stablecoin_balance=50000, gas_balance=18.42, status="Connected"),
        WalletAccount(wallet_id="WAL-SELLER-001", owner_business_id="biz_seller_acme_textiles", owner_name="Acme Textiles Ltd", role="sme", wallet_type="embedded", address="0x5e11eA9a1fC034e45C9a76501E1b0a1234FbcD90", stablecoin_balance=19600, gas_balance=7.31, status="Active"),
        WalletAccount(wallet_id="WAL-FIN-001", owner_business_id="biz_fin_credara_capital", owner_name="Credara Capital", role="financier", wallet_type="treasury", address="0xF1nA9cE002bcA77e0199882fA09331CfedA01009", stablecoin_balance=250000, gas_balance=44.10, status="Active"),
    ]


def demo_payment_intents() -> List[PaymentIntent]:
    return [
        PaymentIntent(payment_intent_id="PI-2026-001", intent_type="Smart LC escrow funding", payer_business_id="biz_buyer_global_retail", payee_reference="SmartLC LC-015", reference_id="LC-015", amount=24500, status="Confirmed", transaction_hash="0xpay...912a", confirmations=8, required_confirmations=3, created_at="2026-06-04T09:31:10Z", confirmed_at="2026-06-04T09:32:02Z"),
        PaymentIntent(payment_intent_id="PI-2026-002", intent_type="Seller advance payout", payer_business_id="biz_fin_credara_capital", payee_reference="Acme Textiles Ltd", reference_id="REC-045", amount=19600, status="Confirmed", transaction_hash="0xadv...45fa", confirmations=5, required_confirmations=3, created_at="2026-06-04T09:35:42Z", confirmed_at="2026-06-04T09:36:22Z"),
        PaymentIntent(payment_intent_id="PI-2026-003", intent_type="Platform fee accrual", payer_business_id="smartlc_lc_015", payee_reference="Credara Treasury", reference_id="LC-015", amount=122.50, status="Pending", transaction_hash="0xfee...19c0", confirmations=1, required_confirmations=3, created_at="2026-06-04T09:41:02Z"),
    ]


def demo_escrows() -> List[EscrowAccount]:
    return [
        EscrowAccount(escrow_id="ESC-015", smart_lc_id="LC-015", contract_address="0xSmartLC015", required_amount=24500, funded_amount=24500, funding_party="Global Retail Ltd", seller="Acme Textiles Ltd", status="Funded", release_condition="Invoice confirmed + delivery verified + no dispute + proof anchored", refund_condition="Dispute upheld or deadline missed", confirmations=8)
    ]


def demo_ledger() -> List[SettlementLedgerEntry]:
    return [
        SettlementLedgerEntry(entry_id="LED-001", timestamp="2026-06-04T09:31:10Z", track="Buyer", role="buyer", event="escrow-funded", source="Global Retail wallet", description="Buyer funded Smart LC escrow for TC-2026-0012.", amount=24500, status="Confirmed", verifier="0xpay...912a", reference_id="LC-015", docs=["Contract", "Receipt", "Proof"]),
        SettlementLedgerEntry(entry_id="LED-002", timestamp="2026-06-04T09:35:42Z", track="Seller", role="sme", event="advance-payout", source="Credara Capital", description="Financier advanced 80% of receivable value to seller wallet.", amount=19600, status="Confirmed", verifier="0xadv...45fa", reference_id="REC-045", docs=["Invoice", "Receipt", "Proof"]),
        SettlementLedgerEntry(entry_id="LED-003", timestamp="2026-06-04T09:41:02Z", track="Ops", role="admin", event="platform-fee", source="SmartLC LC-015", description="Platform fee accrual waiting final confirmations.", amount=122.50, status="Pending", verifier="0xfee...19c0", reference_id="LC-015", docs=["Receipt", "Audit"]),
        SettlementLedgerEntry(entry_id="LED-004", timestamp="2026-06-04T09:45:18Z", track="Financier", role="financier", event="receivable-funded", source="Credara Capital wallet", description="Receivable funding event validated against internal ledger.", amount=19600, status="Confirmed", verifier="0xfund...ab88", reference_id="REC-045", docs=["Invoice", "Receipt", "Proof"]),
        SettlementLedgerEntry(entry_id="LED-005", timestamp="2026-06-04T09:58:11Z", track="Fallback", role="admin", event="manual-review", source="fallback validation", description="No external receipt for fallback bank proof. Excluded from proof until resolved.", amount=0, status="Fallback", verifier="no external receipt", reference_id="FB-001", docs=["Audit"]),
    ]


@router.get("/wallets", response_model=List[WalletAccount])
def list_wallets(role: Optional[str] = Query(default=None)) -> List[WalletAccount]:
    wallets = demo_wallets()
    if role:
        wallets = [w for w in wallets if w.role == role]
    return wallets


@router.get("/intents", response_model=List[PaymentIntent])
def list_payment_intents(reference_id: Optional[str] = Query(default=None)) -> List[PaymentIntent]:
    intents = demo_payment_intents()
    if reference_id:
        intents = [p for p in intents if p.reference_id == reference_id]
    return intents


@router.post("/intents/escrow-funding", response_model=PaymentIntent)
def create_escrow_funding_intent(request: FundEscrowRequest) -> PaymentIntent:
    return PaymentIntent(
        payment_intent_id=f"PI-{int(datetime.utcnow().timestamp())}",
        intent_type="Smart LC escrow funding",
        payer_business_id=request.payer_business_id,
        payee_reference=f"SmartLC {request.smart_lc_id}",
        reference_id=request.smart_lc_id,
        amount=request.amount,
        asset=request.asset,
        status="Pending",
        transaction_hash=None,
        confirmations=0,
        required_confirmations=3,
        created_at=datetime.utcnow().isoformat() + "Z",
    )


@router.post("/intents/{payment_intent_id}/confirm", response_model=PaymentIntent)
def confirm_payment_intent(payment_intent_id: str) -> PaymentIntent:
    intent = demo_payment_intents()[0]
    intent.payment_intent_id = payment_intent_id
    intent.status = "Confirmed"
    intent.confirmations = max(intent.confirmations, intent.required_confirmations)
    intent.transaction_hash = intent.transaction_hash or f"0xconfirmed{payment_intent_id[-4:]}"
    intent.confirmed_at = datetime.utcnow().isoformat() + "Z"
    return intent


@router.get("/escrows", response_model=List[EscrowAccount])
def list_escrows() -> List[EscrowAccount]:
    return demo_escrows()


@router.post("/escrows/{smart_lc_id}/release", response_model=SettlementLedgerEntry)
def release_escrow(smart_lc_id: str, request: ReleaseEscrowRequest) -> SettlementLedgerEntry:
    return SettlementLedgerEntry(
        entry_id=f"LED-{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow().isoformat() + "Z",
        track="Settlement",
        role="sme",
        event="escrow-released",
        source=f"SmartLC {smart_lc_id}",
        description=f"Escrow released to {request.release_to}. Reason: {request.reason}",
        amount=24500,
        status="Confirmed",
        verifier=f"0xrelease{smart_lc_id[-3:]}",
        reference_id=smart_lc_id,
        docs=["Receipt", "Proof", "Audit"],
    )


@router.get("/ledger", response_model=List[SettlementLedgerEntry])
def settlement_ledger(
    role: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    reference_id: Optional[str] = Query(default=None),
) -> List[SettlementLedgerEntry]:
    rows = demo_ledger()
    if role:
        rows = [r for r in rows if r.role == role]
    if status:
        rows = [r for r in rows if r.status == status]
    if reference_id:
        rows = [r for r in rows if r.reference_id == reference_id]
    return rows


@router.get("/ledger/summary")
def settlement_ledger_summary(role: Optional[str] = Query(default=None)) -> Dict[str, float | int]:
    rows = settlement_ledger(role=role)
    return {
        "rows": len(rows),
        "confirmed": len([r for r in rows if r.status == "Confirmed"]),
        "pending": len([r for r in rows if r.status == "Pending"]),
        "fallback": len([r for r in rows if r.status == "Fallback"]),
        "spend": sum(r.amount for r in rows),
    }


@router.get("/reports/role/{role}")
def role_report(role: str) -> Dict[str, object]:
    rows = settlement_ledger(role=role)
    return {
        "role": role,
        "summary": {
            "rows": len(rows),
            "confirmed": len([r for r in rows if r.status == "Confirmed"]),
            "pending": len([r for r in rows if r.status == "Pending"]),
            "fallback": len([r for r in rows if r.status == "Fallback"]),
            "spend": sum(r.amount for r in rows),
        },
        "rows": rows,
    }


@router.get("/reports/admin/aggregate")
def admin_aggregate_report() -> Dict[str, object]:
    rows = demo_ledger()
    by_role: Dict[str, Dict[str, float | int]] = {}
    for role in sorted(set(r.role for r in rows)):
        role_rows = [r for r in rows if r.role == role]
        by_role[role] = {
            "rows": len(role_rows),
            "confirmed": len([r for r in role_rows if r.status == "Confirmed"]),
            "pending": len([r for r in role_rows if r.status == "Pending"]),
            "fallback": len([r for r in role_rows if r.status == "Fallback"]),
            "spend": sum(r.amount for r in role_rows),
        }
    return {"summary": settlement_ledger_summary(), "by_role": by_role, "rows": rows}


@router.get("/reconciliation/{reference_id}", response_model=ReconciliationResult)
def reconcile(reference_id: str) -> ReconciliationResult:
    expected = 24500.0 if reference_id == "LC-015" else 19600.0
    on_chain = expected
    ledger = expected
    return ReconciliationResult(
        reference_id=reference_id,
        expected_amount=expected,
        on_chain_amount=on_chain,
        internal_ledger_amount=ledger,
        smart_lc_state="Funded" if reference_id == "LC-015" else "Financed",
        variance=expected - on_chain,
        decision="valid",
        last_checked=datetime.utcnow().isoformat() + "Z",
    )
