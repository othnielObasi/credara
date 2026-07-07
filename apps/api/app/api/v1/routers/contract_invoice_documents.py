"""
Credara v6 Contract and Invoice Operating Records.

Adds rich contract/invoice detail APIs and downloadable HTML exports so contracts
and invoices behave as full operating records, not vague rows.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/contract-invoice", tags=["contract-invoice-documents"])


class AuditEvent(BaseModel):
    actor: str
    action: str
    timestamp: str
    reason: Optional[str] = None


class ContractLinkedRecords(BaseModel):
    invoice: str
    delivery_proof: str
    proof_bundle: str
    receivable: str
    smart_lc: str
    evidence_bundle: str


class RichTradeContract(BaseModel):
    contract_id: str
    buyer_business_id: str
    seller_business_id: str
    buyer_name: str
    seller_name: str
    created_by: str
    status: str
    trade_category: str
    description: str
    quantity: int
    unit_price: float
    total_value: float
    currency: str
    delivery_location: str
    delivery_deadline: str
    payment_terms: str
    dispute_window_days: int
    financing_allowed: bool
    receivable_tokenization_allowed: bool
    smart_lc_required: bool
    settlement_asset: str
    release_conditions: List[str]
    refund_conditions: List[str]
    expiry_date: str
    required_proof: List[str]
    proof_confidence_required: str
    max_advance_rate: float
    eligible_financier_scope: str
    contract_hash: str
    polygon_network: str
    polygon_tx_hash: str
    linked_records: ContractLinkedRecords
    audit_events: List[AuditEvent]


class InvoiceLineItem(BaseModel):
    sku: str
    description: str
    quantity: int
    unit_price: float
    tax: float = 0
    discount: float = 0
    total: float


class BuyerConfirmation(BaseModel):
    status: str
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[str] = None
    method: Optional[str] = None
    buyer_note: Optional[str] = None
    rejection_reason: Optional[str] = None


class DeliveryProofState(BaseModel):
    status: str
    confidence: str
    delivery_date: Optional[str] = None
    logistics_provider: Optional[str] = None
    tracking_reference: Optional[str] = None
    otp_matched: bool = False
    location_matched: bool = False
    timestamp_within_window: bool = False
    duplicate_check_passed: bool = False


class ReceivableEligibility(BaseModel):
    status: str
    reasons: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


class ReceivableSnapshot(BaseModel):
    receivable_id: Optional[str]
    status: str
    advance_rate: Optional[float] = None
    recommended_advance: Optional[float] = None


class FinanceOfferSnapshot(BaseModel):
    status: str
    financier: Optional[str] = None
    offer_amount: Optional[float] = None
    fee_rate: Optional[float] = None
    repayment_due: Optional[str] = None
    offer_expiry: Optional[str] = None


class SmartLCSnapshot(BaseModel):
    smart_lc_id: Optional[str]
    status: str
    escrow_amount: Optional[str] = None
    release_condition: Optional[str] = None
    settlement_rail: Optional[str] = None
    future_rail: Optional[str] = None


class PolygonInvoiceProof(BaseModel):
    proof_bundle_hash: Optional[str] = None
    proof_registry_tx_hash: Optional[str] = None
    receivable_registry_tx_hash: Optional[str] = None
    smart_lc_tx_hash: Optional[str] = None
    network: str = "Polygon Amoy"
    chain_id: str = "80002"


class RichInvoice(BaseModel):
    invoice_id: str
    contract_id: str
    buyer_business_id: str
    seller_business_id: str
    buyer_name: str
    seller_name: str
    status: str
    issue_date: str
    due_date: str
    currency: str
    subtotal: float
    tax: float
    discount: float
    total_amount: float
    payment_terms: str
    line_items: List[InvoiceLineItem]
    buyer_confirmation: BuyerConfirmation
    delivery_proof: DeliveryProofState
    receivable_eligibility: ReceivableEligibility
    receivable: ReceivableSnapshot
    finance_offer: FinanceOfferSnapshot
    smart_lc: SmartLCSnapshot
    polygon: PolygonInvoiceProof
    evidence_items: List[str]
    audit_events: List[AuditEvent]


def demo_contract(contract_id: str = "TC-2026-0012") -> RichTradeContract:
    return RichTradeContract(
        contract_id=contract_id,
        buyer_business_id="biz_buyer_global_retail",
        seller_business_id="biz_seller_acme_textiles",
        buyer_name="Global Retail Ltd",
        seller_name="Acme Textiles Ltd",
        created_by="Buyer",
        status="Active",
        trade_category="Textiles",
        description="Supply of 5,000 textile units for UAE retail distribution.",
        quantity=5000,
        unit_price=4.90,
        total_value=24500,
        currency="GBP",
        delivery_location="Jebel Ali Free Zone, Dubai",
        delivery_deadline="2026-08-15",
        payment_terms="Net 45 after buyer delivery confirmation",
        dispute_window_days=5,
        financing_allowed=True,
        receivable_tokenization_allowed=True,
        smart_lc_required=True,
        settlement_asset="Mock USDC / AED stablecoin-ready",
        release_conditions=["Invoice confirmed", "Delivery verified", "No open dispute"],
        refund_conditions=["Delivery deadline missed", "Dispute upheld"],
        expiry_date="2026-09-30",
        required_proof=["Delivery note", "Buyer OTP", "Timestamp", "Location match", "Logistics tracking"],
        proof_confidence_required="High",
        max_advance_rate=0.8,
        eligible_financier_scope="Open marketplace + invited financiers",
        contract_hash="0xcontract0012",
        polygon_network="Polygon Amoy",
        polygon_tx_hash="0xcontract...a912",
        linked_records=ContractLinkedRecords(
            invoice="INV-2025-045",
            delivery_proof="DP-2025-045",
            proof_bundle="PB-2025-045",
            receivable="REC-045",
            smart_lc="LC-015",
            evidence_bundle="EVB-2025-045",
        ),
        audit_events=[
            AuditEvent(actor="Daniel Reed", action="Contract created", timestamp="2026-06-04T14:31:00Z"),
            AuditEvent(actor="Amara Okafor", action="Seller accepted", timestamp="2026-06-04T16:08:00Z"),
        ],
    )


def demo_invoice(invoice_id: str = "INV-2025-045") -> RichInvoice:
    return RichInvoice(
        invoice_id=invoice_id,
        contract_id="TC-2026-0012",
        buyer_business_id="biz_buyer_global_retail",
        seller_business_id="biz_seller_acme_textiles",
        buyer_name="Global Retail Ltd",
        seller_name="Acme Textiles Ltd",
        status="Buyer Confirmed",
        issue_date="2026-06-04",
        due_date="2026-09-30",
        currency="GBP",
        subtotal=24500,
        tax=0,
        discount=0,
        total_amount=24500,
        payment_terms="Net 45",
        line_items=[InvoiceLineItem(sku="TXT-5000", description="Textile units", quantity=5000, unit_price=4.90, tax=0, discount=0, total=24500)],
        buyer_confirmation=BuyerConfirmation(status="Confirmed", confirmed_by="Daniel Reed", confirmed_at="2026-06-05T09:45:00Z", method="Buyer portal", buyer_note="Invoice matches agreed contract."),
        delivery_proof=DeliveryProofState(status="Verified", confidence="Very High", delivery_date="2026-08-12", logistics_provider="DP World Logistics", tracking_reference="DXB-JEA-8831", otp_matched=True, location_matched=True, timestamp_within_window=True, duplicate_check_passed=True),
        receivable_eligibility=ReceivableEligibility(status="Eligible", reasons=["Buyer confirmed", "Delivery proof verified", "KYB approved", "No open dispute", "Proof anchored on Polygon"], blockers=[]),
        receivable=ReceivableSnapshot(receivable_id="REC-045", status="Tokenized", advance_rate=0.8, recommended_advance=19600),
        finance_offer=FinanceOfferSnapshot(status="Offer Available", financier="Credara Capital", offer_amount=19600, fee_rate=0.005, repayment_due="45 days", offer_expiry="2026-06-10"),
        smart_lc=SmartLCSnapshot(smart_lc_id="LC-015", status="Funded", escrow_amount="24,500 Mock USDC", release_condition="delivery verified + no open dispute", settlement_rail="Polygon Amoy", future_rail="AED stablecoin-ready"),
        polygon=PolygonInvoiceProof(proof_bundle_hash="0xproof45", proof_registry_tx_hash="0x7f3a...ab24c", receivable_registry_tx_hash="0x4e2b...5b10f", smart_lc_tx_hash="0x9a20...19d2a"),
        evidence_items=["Invoice PDF", "Contract agreement", "Buyer confirmation", "Delivery proof", "Logistics proof", "KYB report", "Receivable record", "Smart LC record", "Polygon proof receipt", "Credit score snapshot"],
        audit_events=[
            AuditEvent(actor="Amara Okafor", action="Invoice issued", timestamp="2026-06-04T15:12:00Z"),
            AuditEvent(actor="Daniel Reed", action="Buyer confirmed", timestamp="2026-06-05T09:45:00Z"),
            AuditEvent(actor="System", action="Proof anchored", timestamp="2026-08-12T15:30:00Z"),
        ],
    )


def esc(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def row(label: str, value: Any) -> str:
    return f"<div class='row'><strong>{esc(label)}</strong><span>{esc(value)}</span></div>"


def contract_html(contract: RichTradeContract) -> str:
    body = "".join([
        row("Contract ID", contract.contract_id),
        row("Status", contract.status),
        row("Buyer", contract.buyer_name),
        row("Seller", contract.seller_name),
        row("Description", contract.description),
        row("Quantity", contract.quantity),
        row("Unit price", f"{contract.currency} {contract.unit_price:,.2f}"),
        row("Total value", f"{contract.currency} {contract.total_value:,.2f}"),
        row("Delivery location", contract.delivery_location),
        row("Delivery deadline", contract.delivery_deadline),
        row("Payment terms", contract.payment_terms),
        row("Required proof", ", ".join(contract.required_proof)),
        row("Financing allowed", "Yes" if contract.financing_allowed else "No"),
        row("Max advance rate", f"{contract.max_advance_rate:.0%}"),
        row("Smart LC required", "Yes" if contract.smart_lc_required else "No"),
        row("Settlement asset", contract.settlement_asset),
        row("Release conditions", ", ".join(contract.release_conditions)),
        row("Invoice", contract.linked_records.invoice),
        row("Receivable", contract.linked_records.receivable),
        row("Smart LC", contract.linked_records.smart_lc),
        row("Polygon tx", contract.polygon_tx_hash),
    ])
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{esc(contract.contract_id)}</title><style>body{{font-family:Arial,sans-serif;padding:32px;color:#111827;line-height:1.55}}h1{{color:#0b1536}}.badge{{background:#eef2ff;color:#4338ca;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:bold}}.row{{display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid #e5e7eb;padding:8px 0}}span{{text-align:right}}</style></head><body><h1>Trade Contract {esc(contract.contract_id)}</h1><p class='badge'>{esc(contract.status)}</p>{body}<p style='margin-top:32px;color:#6b7280;font-size:12px'>Generated by Credara.</p></body></html>"


def invoice_html(invoice: RichInvoice) -> str:
    line_rows = "".join(f"<tr><td>{esc(x.sku)}</td><td>{esc(x.description)}</td><td>{x.quantity}</td><td>{invoice.currency} {x.unit_price:,.2f}</td><td>{invoice.currency} {x.total:,.2f}</td></tr>" for x in invoice.line_items)
    body = "".join([
        row("Invoice ID", invoice.invoice_id),
        row("Contract ID", invoice.contract_id),
        row("Status", invoice.status),
        row("Buyer", invoice.buyer_name),
        row("Seller", invoice.seller_name),
        row("Issue date", invoice.issue_date),
        row("Due date", invoice.due_date),
        row("Payment terms", invoice.payment_terms),
        row("Buyer confirmation", invoice.buyer_confirmation.status),
        row("Delivery proof", f"{invoice.delivery_proof.status} · {invoice.delivery_proof.confidence}"),
        row("Receivable", f"{invoice.receivable.receivable_id} · {invoice.receivable.status}"),
        row("Finance offer", f"{invoice.currency} {invoice.finance_offer.offer_amount:,.2f} · {invoice.finance_offer.status}"),
        row("Smart LC", f"{invoice.smart_lc.smart_lc_id} · {invoice.smart_lc.status}"),
        row("ProofRegistry tx", invoice.polygon.proof_registry_tx_hash),
    ])
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{esc(invoice.invoice_id)}</title><style>body{{font-family:Arial,sans-serif;padding:32px;color:#111827;line-height:1.55}}h1{{color:#0b1536}}.badge{{background:#dcfce7;color:#166534;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:bold}}.row{{display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid #e5e7eb;padding:8px 0}}span{{text-align:right}}table{{width:100%;border-collapse:collapse;margin-top:16px}}td,th{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left}}</style></head><body><h1>Invoice {esc(invoice.invoice_id)}</h1><p class='badge'>{esc(invoice.status)}</p>{body}<h2>Line Items</h2><table><thead><tr><th>SKU</th><th>Description</th><th>Qty</th><th>Unit</th><th>Total</th></tr></thead><tbody>{line_rows}</tbody></table>{row('Total', f'{invoice.currency} {invoice.total_amount:,.2f}')}<p style='margin-top:32px;color:#6b7280;font-size:12px'>Generated by Credara.</p></body></html>"


@router.get("/contracts/{contract_id}", response_model=RichTradeContract)
def get_contract_detail(contract_id: str) -> RichTradeContract:
    return demo_contract(contract_id)


@router.get("/invoices/{invoice_id}", response_model=RichInvoice)
def get_invoice_detail(invoice_id: str) -> RichInvoice:
    return demo_invoice(invoice_id)


@router.get("/contracts/{contract_id}/download")
def download_contract(contract_id: str) -> Response:
    content = contract_html(demo_contract(contract_id))
    return Response(content=content, media_type="text/html", headers={"Content-Disposition": f'attachment; filename="{contract_id}-trade-contract.html"'})


@router.get("/invoices/{invoice_id}/download")
def download_invoice(invoice_id: str) -> Response:
    content = invoice_html(demo_invoice(invoice_id))
    return Response(content=content, media_type="text/html", headers={"Content-Disposition": f'attachment; filename="{invoice_id}-invoice.html"'})


@router.get("/contracts/{contract_id}/status-map")
def contract_status_map(contract_id: str) -> Dict[str, Any]:
    return {"contract_id": contract_id, "groups": ["Setup", "Agreement", "Execution", "Finance", "Settlement", "Closed / Exception"], "statuses": ["Draft", "Sent to Counterparty", "Awaiting Seller Acceptance", "Awaiting Buyer Acceptance", "Change Requested", "Accepted", "Active", "Invoice Issued", "Delivery In Progress", "Delivery Verified", "Receivable Created", "Financed", "Settlement Pending", "Settled", "Closed", "Disputed", "Cancelled", "Expired", "Rejected"]}


@router.get("/invoices/{invoice_id}/status-map")
def invoice_status_map(invoice_id: str) -> Dict[str, Any]:
    return {"invoice_id": invoice_id, "groups": ["Creation", "Buyer Confirmation", "Proof", "Receivable", "Finance", "Settlement", "Repayment", "Exception"], "statuses": ["Draft", "Sent to Buyer", "Correction Requested", "Buyer Confirmed", "Buyer Rejected", "Delivery Proof Required", "Proof Submitted", "Proof Verification Failed", "Delivery Verified", "Proof Anchored", "Receivable Eligible", "Receivable Tokenized", "Financing Submitted", "Offer Made", "Financed", "Smart LC Funded", "Settlement Released", "Paid", "Overdue", "Defaulted", "Disputed", "Cancelled", "Closed"]}
