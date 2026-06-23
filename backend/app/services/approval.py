from datetime import datetime
from sqlalchemy.orm import Session
from ..models import FillRecord, ApprovalChain, ApprovalLog, FillRecordSnapshot, User


def get_next_level(db: Session, risk_item_id: int, current_level: int) -> int | None:
    """Get the next approval level, or None if current is the last."""
    chains = db.query(ApprovalChain).filter(ApprovalChain.risk_item_id == risk_item_id).order_by(ApprovalChain.level).all()
    if not chains:
        return None
    levels = [c.level for c in chains]
    if current_level in levels:
        idx = levels.index(current_level)
        if idx + 1 < len(levels):
            return levels[idx + 1]
    return None


def is_last_level(db: Session, risk_item_id: int, level: int) -> bool:
    chains = db.query(ApprovalChain).filter(ApprovalChain.risk_item_id == risk_item_id).order_by(ApprovalChain.level).all()
    return chains and chains[-1].level == level


def approve_record(db: Session, record: FillRecord, approver: User, current_level: int, modified_data: dict | None = None) -> FillRecord:
    """Approve a pending record. Optionally modify fill fields."""
    if modified_data:
        for key, val in modified_data.items():
            if val is not None:
                setattr(record, key, val)

    log = ApprovalLog(fill_record_id=record.id, approver_id=approver.id, level=current_level, action="approved", action_time=datetime.utcnow())
    db.add(log)

    last = is_last_level(db, record.risk_item_id, current_level)
    if last:
        record.status = "approved"
    else:
        next_lvl = get_next_level(db, record.risk_item_id, current_level)
        record.status = f"pending_level_{next_lvl}"
    db.commit()
    db.refresh(record)
    return record


def reject_record(db: Session, record: FillRecord, approver: User, current_level: int) -> FillRecord:
    """Reject a pending record."""
    log = ApprovalLog(fill_record_id=record.id, approver_id=approver.id, level=current_level, action="rejected", action_time=datetime.utcnow())
    db.add(log)
    record.status = "rejected"
    db.commit()
    db.refresh(record)
    return record


def group_modify_approved(db: Session, record: FillRecord, modifier: User, modified_data: dict) -> FillRecord:
    """Group approver modifies an approved record. Save snapshot first."""
    last_approver_log = db.query(ApprovalLog).filter(
        ApprovalLog.fill_record_id == record.id,
        ApprovalLog.action == "approved"
    ).order_by(ApprovalLog.action_time.desc()).first()

    snapshot = FillRecordSnapshot(
        fill_record_id=record.id,
        amount_open=record.amount_open,
        amount_impairment=record.amount_impairment,
        amount_est_loss=record.amount_est_loss,
        progress_text=record.progress_text,
        approved_by=last_approver_log.approver_id if last_approver_log else modifier.id,
        approved_at=last_approver_log.action_time if last_approver_log else datetime.utcnow(),
        modified_by=modifier.id,
        modified_at=datetime.utcnow(),
    )
    db.add(snapshot)

    for key, val in modified_data.items():
        if val is not None:
            setattr(record, key, val)
    db.commit()
    db.refresh(record)
    return record
