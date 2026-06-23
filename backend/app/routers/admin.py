from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user, hash_password
from ..schemas import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/users", response_model=UserOut)
def create_user(req: UserCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(username=req.username, password_hash=hash_password(req.password), name=req.name, role=req.role, wework_userid=req.wework_userid)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, req: UserUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.name is not None: user.name = req.name
    if req.role is not None: user.role = req.role
    if req.is_active is not None: user.is_active = req.is_active
    if req.wework_userid is not None: user.wework_userid = req.wework_userid
    if req.password: user.password_hash = hash_password(req.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    db.commit()
    return {"ok": True}


# --- Risk Items ---

from ..models import RiskItem, FillPermission, ApprovalChain
from ..schemas import RiskItemUpdate, RiskItemOut, FillPermissionUpdate, ApprovalChainUpdate


@router.get("/risk-items", response_model=list[RiskItemOut])
def list_risk_items(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(RiskItem).order_by(RiskItem.seq).all()


@router.put("/risk-items/{item_id}", response_model=RiskItemOut)
def update_risk_item(item_id: int, req: RiskItemUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.query(RiskItem).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="事项不存在")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return item


# --- Fill Permissions ---

@router.get("/fill-permissions/{risk_item_id}")
def get_fill_permissions(risk_item_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    perms = db.query(FillPermission).filter(FillPermission.risk_item_id == risk_item_id).all()
    return [p.user_id for p in perms]


@router.put("/fill-permissions/{risk_item_id}")
def set_fill_permissions(risk_item_id: int, req: FillPermissionUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    db.query(FillPermission).filter(FillPermission.risk_item_id == risk_item_id).delete()
    for uid in req.user_ids:
        db.add(FillPermission(user_id=uid, risk_item_id=risk_item_id))
    db.commit()
    return {"ok": True}


# --- Approval Chains ---

@router.get("/approval-chains/{risk_item_id}")
def get_approval_chain(risk_item_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    chains = db.query(ApprovalChain).filter(ApprovalChain.risk_item_id == risk_item_id).order_by(ApprovalChain.level).all()
    return [{"level": c.level, "approver_id": c.approver_id} for c in chains]


@router.put("/approval-chains/{risk_item_id}")
def set_approval_chain(risk_item_id: int, req: ApprovalChainUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    db.query(ApprovalChain).filter(ApprovalChain.risk_item_id == risk_item_id).delete()
    for item in req.chains:
        db.add(ApprovalChain(risk_item_id=risk_item_id, level=item.level, approver_id=item.approver_id))
    db.commit()
    return {"ok": True}
