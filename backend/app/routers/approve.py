from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import User, FillRecord, ApprovalChain, ApprovalLog
from ..auth import get_current_user
from ..schemas import ApprovalAction, GroupApproverModify, FillRecordOut
from ..services.approval import approve_record, reject_record, group_modify_approved, is_last_level

router = APIRouter(prefix="/api/approve", tags=["approve"])


def _get_chain_info(db: Session, risk_item_id: int, fill_record_id: int, current_status: str):
    """Build approval chain status info for a record."""
    chains = db.query(ApprovalChain).filter(
        ApprovalChain.risk_item_id == risk_item_id
    ).order_by(ApprovalChain.level).all()

    logs = db.query(ApprovalLog).filter(
        ApprovalLog.fill_record_id == fill_record_id
    ).all()
    log_by_level = {}
    for log in logs:
        log_by_level[log.level] = log.action

    current_level = int(current_status.split("_")[-1]) if current_status.startswith("pending_level_") else None

    result = []
    for c in chains:
        approver = db.query(User).get(c.approver_id)
        action = log_by_level.get(c.level)
        if action == "approved":
            level_status = "approved"
        elif action == "rejected":
            level_status = "rejected"
        elif current_level is not None and c.level == current_level:
            level_status = "pending"
        else:
            level_status = "waiting"

        result.append({
            "level": c.level,
            "approver_name": approver.name if approver else "未知",
            "status": level_status,
        })
    return result


@router.get("/pending")
def list_pending(
    period: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List records pending approval by current user. Admin sees all pending records. Optionally filter by period."""
    if user.role == "admin":
        query = db.query(FillRecord).filter(FillRecord.status.like("pending_level_%"))
        if period:
            query = query.filter(FillRecord.period == period)
        records = query.all()
        results = []
        for r in records:
            item = r.risk_item
            current_level = int(r.status.split("_")[-1])
            results.append({
                "record_id": r.id,
                "risk_item_id": r.risk_item_id,
                "seq": item.seq,
                "name": item.name,
                "period": r.period,
                "amount_2025_end": item.amount_2025_end,
                "amount_open": r.amount_open,
                "amount_impairment": r.amount_impairment,
                "amount_est_loss": r.amount_est_loss,
                "progress_text": r.progress_text,
                "level": current_level,
                "is_last": is_last_level(db, item.id, current_level),
                "chain": _get_chain_info(db, item.id, r.id, r.status),
            })
        return results

    chains = db.query(ApprovalChain).filter(ApprovalChain.approver_id == user.id).all()
    results = []
    for chain in chains:
        status_val = f"pending_level_{chain.level}"
        query = db.query(FillRecord).filter(
            FillRecord.risk_item_id == chain.risk_item_id,
            FillRecord.status == status_val
        )
        if period:
            query = query.filter(FillRecord.period == period)
        records = query.all()
        for r in records:
            item = r.risk_item
            results.append({
                "record_id": r.id,
                "risk_item_id": r.risk_item_id,
                "seq": item.seq,
                "name": item.name,
                "period": r.period,
                "amount_2025_end": item.amount_2025_end,
                "amount_open": r.amount_open,
                "amount_impairment": r.amount_impairment,
                "amount_est_loss": r.amount_est_loss,
                "progress_text": r.progress_text,
                "level": chain.level,
                "is_last": is_last_level(db, chain.risk_item_id, chain.level),
                "chain": _get_chain_info(db, item.id, r.id, r.status),
            })
    return results


@router.post("/records/{record_id}/action", response_model=FillRecordOut)
def handle_action(record_id: int, req: ApprovalAction, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(FillRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if not record.status.startswith("pending_level_"):
        raise HTTPException(status_code=400, detail="记录不在审批状态")

    current_level = int(record.status.split("_")[-1])
    if user.role != "admin":
        chain = db.query(ApprovalChain).filter(
            ApprovalChain.risk_item_id == record.risk_item_id,
            ApprovalChain.level == current_level,
            ApprovalChain.approver_id == user.id
        ).first()
        if not chain:
            raise HTTPException(status_code=403, detail="您不是当前级审批人")

    modified_data = None
    if any(v is not None for v in [req.amount_open, req.amount_impairment, req.amount_est_loss, req.progress_text]):
        modified_data = {
            "amount_open": req.amount_open,
            "amount_impairment": req.amount_impairment,
            "amount_est_loss": req.amount_est_loss,
            "progress_text": req.progress_text,
        }

    if req.action == "approved":
        return approve_record(db, record, user, current_level, modified_data)
    elif req.action == "rejected":
        return reject_record(db, record, user, current_level)
    else:
        raise HTTPException(status_code=400, detail="无效操作")


@router.get("/approved")
def list_approved(
    period: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List approved records. Admin sees all; group_approver sees their chain."""
    if user.role == "admin":
        query = db.query(FillRecord).filter(FillRecord.status == "approved")
    elif user.role == "group_approver":
        chains = db.query(ApprovalChain).filter(ApprovalChain.approver_id == user.id).all()
        risk_item_ids = [c.risk_item_id for c in chains]
        query = db.query(FillRecord).filter(
            FillRecord.risk_item_id.in_(risk_item_ids),
            FillRecord.status == "approved"
        )
    else:
        raise HTTPException(status_code=403, detail="需要集团审核人或管理员权限")
    if period:
        query = query.filter(FillRecord.period == period)
    records = query.all()
    results = []
    for r in records:
        item = r.risk_item
        results.append({
            "record_id": r.id,
            "risk_item_id": r.risk_item_id,
            "seq": item.seq,
            "name": item.name,
            "period": r.period,
            "amount_2025_end": item.amount_2025_end,
            "amount_open": r.amount_open,
            "amount_impairment": r.amount_impairment,
            "amount_est_loss": r.amount_est_loss,
            "progress_text": r.progress_text,
            "chain": _get_chain_info(db, item.id, r.id, r.status),
        })
    return results


@router.put("/records/{record_id}/group-modify", response_model=FillRecordOut)
def modify_approved(record_id: int, req: GroupApproverModify, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ("admin", "group_approver"):
        raise HTTPException(status_code=403, detail="需要集团审核人或管理员权限")
    record = db.query(FillRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if record.status != "approved":
        raise HTTPException(status_code=400, detail="记录不在已审批状态")
    return group_modify_approved(db, record, user, req.model_dump(exclude_unset=True))
