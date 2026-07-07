"""
Credara v8 Feature Structure and Noise Separation.

Exposes the production feature map used by the frontend to separate:
- real core product features
- useful supporting features
- demo-only controls
"""
from __future__ import annotations

from typing import Dict, List, Literal
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/feature-structure", tags=["feature-structure"])


class FeatureItem(BaseModel):
    key: str
    name: str
    category: Literal["core", "supporting", "demo"]
    pillar: str
    description: str
    route: str


class NavigationGroup(BaseModel):
    group: str
    routes: List[str]


CORE_FEATURES = [
    FeatureItem(key="network", name="Business Directory and Counterparty Network", category="core", pillar="Network", description="Find, invite and verify counterparties.", route="/directory"),
    FeatureItem(key="contracts", name="Trade Contracts", category="core", pillar="Trade", description="Create, accept and operate trade agreements.", route="/contracts"),
    FeatureItem(key="invoices", name="Invoices", category="core", pillar="Trade", description="Create buyer-confirmed payment claims linked to contracts.", route="/invoices"),
    FeatureItem(key="delivery_proof", name="Delivery Proof", category="core", pillar="Trust", description="Verify delivery through buyer, logistics, timestamp and location evidence.", route="/delivery-proof"),
    FeatureItem(key="proof_ledger", name="Proof Ledger", category="core", pillar="Trust", description="Record proof bundles and Polygon receipts.", route="/proof-ledger"),
    FeatureItem(key="receivables", name="Receivables", category="core", pillar="Finance", description="Turn eligible invoices into financeable receivables.", route="/receivables"),
    FeatureItem(key="deal_room", name="Financier Deal Room", category="core", pillar="Finance", description="Underwrite and fund verified receivables.", route="/deal-room"),
    FeatureItem(key="wallets", name="Wallets and Payment Intents", category="core", pillar="Settlement", description="Manage wallet-backed stablecoin payments.", route="/wallets"),
    FeatureItem(key="smart_lc", name="Smart LC Escrow", category="core", pillar="Settlement", description="Escrow funds and release/refund by rule.", route="/smart-lc"),
    FeatureItem(key="settlement_ledger", name="Settlement Ledger and Reconciliation", category="core", pillar="Settlement", description="Confirm payments, reconcile ledger, and report by role.", route="/settlement-ledger"),
    FeatureItem(key="kyb", name="KYB and Compliance", category="core", pillar="Trust", description="Verify businesses and manage risk checks.", route="/kyb"),
    FeatureItem(key="risk_rules", name="Risk Rules", category="core", pillar="Trust", description="Prevent unsafe financing and settlement actions.", route="/risk-rules"),
    FeatureItem(key="evidence_bundle", name="Evidence Bundle", category="core", pillar="Trust", description="Export audit and underwriting packages.", route="/evidence"),
]

SUPPORTING_FEATURES = [
    FeatureItem(key="api_explorer", name="API Explorer", category="supporting", pillar="Platform", description="Endpoint catalogue, examples and webhooks.", route="/api-explorer"),
    FeatureItem(key="permissions", name="Permissions", category="supporting", pillar="Platform", description="Role-based access matrix.", route="/permissions"),
    FeatureItem(key="launch_readiness", name="Launch Readiness", category="supporting", pillar="Platform", description="Polygon, UAE/DIFC and go-to-market checklist.", route="/launch"),
    FeatureItem(key="admin", name="Admin and Risk Console", category="supporting", pillar="Platform", description="Operations, audit and exception handling.", route="/admin"),
]

DEMO_FEATURES = [
    FeatureItem(key="run_next_step", name="Run Next Step", category="demo", pillar="Demo Controls", description="Simulates workflow progression.", route="#demo-run-next-step"),
    FeatureItem(key="simulate_chain_confirmation", name="Simulate Chain Confirmation", category="demo", pillar="Demo Controls", description="Simulates Polygon confirmation updates.", route="#demo-simulate-chain"),
    FeatureItem(key="reset_demo", name="Reset Demo", category="demo", pillar="Demo Controls", description="Restores mock state.", route="#demo-reset"),
]


@router.get("/pillars")
def pillars() -> Dict[str, List[str]]:
    return {
        "Network": ["Business directory", "Counterparty invites", "Trade opportunities", "Financier marketplace"],
        "Trade": ["Contracts", "Invoices", "Buyer confirmation", "Delivery obligations"],
        "Trust": ["KYB", "Delivery proof", "Proof ledger", "Evidence bundle", "Risk rules"],
        "Finance": ["Receivables", "Tokenization", "Underwriting", "Funding offers"],
        "Settlement": ["Wallets", "Payment intents", "Smart LC escrow", "Settlement ledger", "Reconciliation"],
    }


@router.get("/features", response_model=List[FeatureItem])
def features() -> List[FeatureItem]:
    return CORE_FEATURES + SUPPORTING_FEATURES + DEMO_FEATURES


@router.get("/features/core", response_model=List[FeatureItem])
def core_features() -> List[FeatureItem]:
    return CORE_FEATURES


@router.get("/features/supporting", response_model=List[FeatureItem])
def supporting_features() -> List[FeatureItem]:
    return SUPPORTING_FEATURES


@router.get("/features/demo", response_model=List[FeatureItem])
def demo_features() -> List[FeatureItem]:
    return DEMO_FEATURES


@router.get("/navigation", response_model=List[NavigationGroup])
def navigation() -> List[NavigationGroup]:
    return [
        NavigationGroup(group="Operate", routes=["dashboard", "contractDetail", "invoiceDetail", "delivery", "receivables"]),
        NavigationGroup(group="Network", routes=["directory", "opportunities", "proposals", "marketplace"]),
        NavigationGroup(group="Settlement", routes=["wallets", "settlement", "settlementLedger", "reconciliation", "repayments"]),
        NavigationGroup(group="Trust", routes=["proof", "evidence", "credit", "kyb", "riskRules"]),
        NavigationGroup(group="Platform", routes=["apiExplorer", "permissions", "admin", "launch"]),
    ]
