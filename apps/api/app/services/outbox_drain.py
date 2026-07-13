"""Drain pending BlockchainOutbox jobs (shared by worker process and Vercel Cron)."""

from datetime import datetime

from app.core.database import SessionLocal
from app.models.audit import BlockchainOutbox
from app.models.enums import OutboxStatus, ProofStatus
from app.models.trade import ProofBundle
from app.services.polygon import ChainUnavailableError, publish_tx


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
                if not on_chain or not tx_hash:
                    job.attempts += 1
                    job.last_error = 'on_chain_unavailable'
                    job.status = OutboxStatus.FAILED.value if job.attempts >= 3 else OutboxStatus.PENDING.value
                    job.updated_at = datetime.utcnow()
                    continue
                job.tx_hash = tx_hash
                job.status = OutboxStatus.SENT.value
                job.last_error = None
                job.updated_at = datetime.utcnow()
                if bundle_id:
                    bundle = db.get(ProofBundle, bundle_id)
                    if bundle:
                        bundle.polygon_tx_hash = tx_hash
                        bundle.status = ProofStatus.ANCHORED.value
            except ChainUnavailableError as exc:
                job.attempts += 1
                job.last_error = str(exc)
                job.status = OutboxStatus.FAILED.value if job.attempts >= 3 else OutboxStatus.PENDING.value
                job.updated_at = datetime.utcnow()
            except Exception as exc:  # noqa: BLE001
                job.attempts += 1
                job.last_error = str(exc)
                job.status = OutboxStatus.FAILED.value if job.attempts >= 3 else OutboxStatus.PENDING.value
                job.updated_at = datetime.utcnow()
        db.commit()
        return len(jobs)
    finally:
        db.close()
