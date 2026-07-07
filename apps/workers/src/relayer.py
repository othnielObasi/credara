import time
from datetime import datetime
from app.core.database import SessionLocal
from app.models.audit import BlockchainOutbox
from app.models.enums import OutboxStatus
from app.services.polygon import simulate_tx_hash


def process_once() -> int:
    db = SessionLocal()
    try:
        jobs = db.query(BlockchainOutbox).filter(BlockchainOutbox.status == OutboxStatus.PENDING.value).limit(10).all()
        for job in jobs:
            try:
                # Production path: sign and send contract transaction via web3.py.
                job.tx_hash = simulate_tx_hash(f"{job.id}:{job.action}:{job.payload_json}")
                job.status = OutboxStatus.SENT.value
                job.updated_at = datetime.utcnow()
            except Exception as exc:  # noqa: BLE001
                job.attempts += 1
                job.last_error = str(exc)
                job.status = OutboxStatus.FAILED.value if job.attempts >= 3 else OutboxStatus.PENDING.value
        db.commit()
        return len(jobs)
    finally:
        db.close()

if __name__ == '__main__':
    while True:
        count = process_once()
        time.sleep(5 if count == 0 else 1)
