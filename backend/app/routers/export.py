from urllib.parse import quote
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from ..database import get_db
from ..models import User, FillPermission, ApprovalChain
from ..auth import get_current_user
from ..services.excel_export import export_excel

router = APIRouter(prefix="/api/export", tags=["export"])


def _get_allowed_risk_item_ids(user: User, db: Session) -> set[int] | None:
    """Return a set of risk_item_ids the user can view. None means 'all' (admin)."""
    if user.role == "admin":
        return None
    ids = set()
    ids.update(p.risk_item_id for p in db.query(FillPermission).filter(FillPermission.user_id == user.id).all())
    ids.update(c.risk_item_id for c in db.query(ApprovalChain).filter(ApprovalChain.approver_id == user.id).all())
    return ids


@router.get("/excel")
def export_excel_endpoint(period: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed_ids = _get_allowed_risk_item_ids(user, db)
    wb = export_excel(db, period, allowed_ids)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f"风险资产压降进度情况表_{period}.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
