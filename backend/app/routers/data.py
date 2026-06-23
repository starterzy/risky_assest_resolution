from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, RiskItem, FillRecord, FillPermission, ApprovalChain
from ..auth import get_current_user

router = APIRouter(prefix="/api/data", tags=["data"])


def _get_allowed_risk_item_ids(user: User, db: Session) -> set[int] | None:
    """Return a set of risk_item_ids the user can view. None means 'all' (admin)."""
    if user.role == "admin":
        return None
    ids = set()
    # filler: items assigned via FillPermission
    ids.update(p.risk_item_id for p in db.query(FillPermission).filter(FillPermission.user_id == user.id).all())
    # approver / group_approver: items in their approval chain
    ids.update(c.risk_item_id for c in db.query(ApprovalChain).filter(ApprovalChain.approver_id == user.id).all())
    return ids


@router.get("/detail")
def get_detail(period: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get full detail (举措及责任分解) for a given period. Non-admin users only see rows they have permission for."""
    allowed_ids = _get_allowed_risk_item_ids(user, db)
    query = db.query(RiskItem)
    if allowed_ids is not None:
        if not allowed_ids:
            return []
        query = query.filter(RiskItem.id.in_(allowed_ids))
    items = query.order_by(RiskItem.seq).all()
    result = []
    for item in items:
        record = db.query(FillRecord).filter(
            FillRecord.risk_item_id == item.id,
            FillRecord.period == period,
            FillRecord.status == "approved"
        ).first()
        result.append({
            "seq": item.seq,
            "name": item.name,
            "company": item.company,
            "amount_2025_end": item.amount_2025_end,
            "amount_open": record.amount_open if record else None,
            "amount_impairment": record.amount_impairment if record else None,
            "amount_est_loss": record.amount_est_loss if record else None,
            "progress_text": record.progress_text if record else None,
            "xinghe_target": item.xinghe_target,
            "zhenong_target": item.zhenong_target,
            "annual_target": item.annual_target,
            "leader_province": item.leader_province,
            "leader_xinghe": item.leader_xinghe,
            "leader_zhenong": item.leader_zhenong,
            "leader_team": item.leader_team,
            "leader_dept": item.leader_dept,
            "deadline": item.deadline,
            "target_amount": item.target_amount,
            "target_ratio": item.target_ratio,
        })
    return result
