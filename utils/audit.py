# utils/audit.py
from models import db, AuditLog
from datetime import datetime

def log_audit(action, target_user_id=None, performed_by=None, meta=None):
    entry = AuditLog(
        target_user_id=target_user_id,
        action=action,
        performed_by=performed_by,
        meta=meta or {},
        timestamp=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()
    return entry
