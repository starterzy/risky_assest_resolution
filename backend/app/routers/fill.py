from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import User, RiskItem, FillRecord, FillPermission, ApprovalChain
from ..auth import get_current_user
from ..schemas import FillRecordCreate, FillRecordUpdate, FillRecordOut

router = APIRouter(prefix="/api/fill", tags=["fill"])


@router.get("/my-items")
def my_fill_items(period: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get risk items the current user can fill, with fill record status for given period."""
    if user.role == "admin":
        perm_item_ids = [i.id for i in db.query(RiskItem).all()]
    else:
        perm_item_ids = [p.risk_item_id for p in db.query(FillPermission).filter(FillPermission.user_id == user.id).all()]

    items = db.query(RiskItem).filter(RiskItem.id.in_(perm_item_ids)).order_by(RiskItem.seq).all()
    result = []
    for item in items:
        record = db.query(FillRecord).filter(FillRecord.risk_item_id == item.id, FillRecord.period == period).first()
        result.append({
            "id": item.id,
            "seq": item.seq,
            "name": item.name,
            "company": item.company,
            "amount_2025_end": item.amount_2025_end,
            "xinghe_target": item.xinghe_target,
            "zhenong_target": item.zhenong_target,
            "annual_target": item.annual_target,
            "record_id": record.id if record else None,
            "status": record.status if record else None,
            "amount_open": record.amount_open if record else None,
            "amount_impairment": record.amount_impairment if record else None,
            "amount_est_loss": record.amount_est_loss if record else None,
            "progress_text": record.progress_text if record else None,
        })
    return result


@router.post("/records", response_model=FillRecordOut)
def create_or_save_record(req: FillRecordCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check permission
    if user.role != "admin":
        if not db.query(FillPermission).filter(FillPermission.user_id == user.id, FillPermission.risk_item_id == req.risk_item_id).first():
            raise HTTPException(status_code=403, detail="无填报权限")
    # Check existing
    existing = db.query(FillRecord).filter(FillRecord.risk_item_id == req.risk_item_id, FillRecord.period == req.period).first()
    if existing:
        if existing.status not in ("draft", "rejected"):
            raise HTTPException(status_code=400, detail="当前状态不可修改")
        existing.amount_open = req.amount_open
        existing.amount_impairment = req.amount_impairment
        existing.amount_est_loss = req.amount_est_loss
        existing.progress_text = req.progress_text
        db.commit()
        db.refresh(existing)
        return existing
    record = FillRecord(
        risk_item_id=req.risk_item_id,
        period=req.period,
        amount_open=req.amount_open,
        amount_impairment=req.amount_impairment,
        amount_est_loss=req.amount_est_loss,
        progress_text=req.progress_text,
        filler_id=user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/records/{record_id}/submit")
def submit_record(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(FillRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if user.role != "admin" and record.filler_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if record.status not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="当前状态不可提交")
    chain = db.query(ApprovalChain).filter(ApprovalChain.risk_item_id == record.risk_item_id).order_by(ApprovalChain.level).first()
    if not chain:
        record.status = "approved"
    else:
        record.status = f"pending_level_{chain.level}"
    record.submit_time = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": record.status}
