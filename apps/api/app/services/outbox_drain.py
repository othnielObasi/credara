"""Drain pending BlockchainOutbox jobs (shared by worker process and Vercel Cron)."""

from datetime import datetime

from app.core.database import SessionLocal
from app.models.audit import BlockchainOutbox
from app.models.enums import OutboxStatus, ProofStatus
from app.models.trade import ProofBundle
from app.services.polygon import publish_tx


def process_once() -> int:
    db = SessionLocal()
    try:
        jobs = (
            db.query(BlockchainOutbox)
            .filter(BlockchainOutbox.status == OutboxStatus.PENDING.value)
            .limit(10)
            .all()
        )
        for job in jobs:
            try:
                proof_hash = None
                bundle_id = None
                if isinstance(job.payload_json, dict):
                    proof_hash = job.payload_json.get('proof_hash')
                    bundle_id = job.payload_json.get('bundle_id')
                seed = f'{job.id}:{job.action}:{job.payload_json}'
                tx_hash, on_chain = publish_tx(seed, proof_hash=proof_hash)
                job.tx_hash = tx_hash
                job.status = OutboxStatus.SENT.value
                job.updated_at = datetime.utcnow()
                if bundle_id:
                    bundle = db.get(ProofBundle, bundle_id)
                    if bundle:
                        bundle.polygon_tx_hash = tx_hash
                        bundle.status = ProofStatus.ANCHORED.value
                if not on_chain:
                    job.last_error = 'simulated_tx_fallback'
            except Exception as exc:  # noqa: BLE001
                job.attempts += 1
                job.last_error = str(exc)
                job.status = OutboxStatus.FAILED.value if job.attempts >= 3 else OutboxStatus.PENDING.value
        db.commit()
        return len(jobs)
    finally:
        db.close()
