from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int
    name: str
    role: str

class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str
    wework_userid: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    wework_userid: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    is_active: bool
    wework_userid: Optional[str] = None
    class Config:
        from_attributes = True

class FillRecordCreate(BaseModel):
    risk_item_id: int
    period: str
    amount_open: Optional[float] = None
    amount_impairment: Optional[float] = None
    amount_est_loss: Optional[float] = None
    progress_text: Optional[str] = None

class FillRecordUpdate(BaseModel):
    amount_open: Optional[float] = None
    amount_impairment: Optional[float] = None
    amount_est_loss: Optional[float] = None
    progress_text: Optional[str] = None

class FillRecordOut(BaseModel):
    id: int
    risk_item_id: int
    period: str
    amount_open: Optional[float]
    amount_impairment: Optional[float]
    amount_est_loss: Optional[float]
    progress_text: Optional[str]
    status: str
    filler_id: int
    submit_time: Optional[datetime]
    class Config:
        from_attributes = True

class ApprovalAction(BaseModel):
    action: str  # approved / rejected
    amount_open: Optional[float] = None
    amount_impairment: Optional[float] = None
    amount_est_loss: Optional[float] = None
    progress_text: Optional[str] = None

class GroupApproverModify(BaseModel):
    amount_open: Optional[float] = None
    amount_impairment: Optional[float] = None
    amount_est_loss: Optional[float] = None
    progress_text: Optional[str] = None

class ApprovalChainItem(BaseModel):
    level: int
    approver_id: int

class ApprovalChainUpdate(BaseModel):
    chains: list[ApprovalChainItem]

class FillPermissionUpdate(BaseModel):
    user_ids: list[int]

class RiskItemUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    amount_2025_end: Optional[float] = None
    xinghe_target: Optional[str] = None
    zhenong_target: Optional[str] = None
    annual_target: Optional[str] = None
    leader_province: Optional[str] = None
    leader_xinghe: Optional[str] = None
    leader_zhenong: Optional[str] = None
    leader_team: Optional[str] = None
    leader_dept: Optional[str] = None
    deadline: Optional[str] = None
    target_amount: Optional[float] = None
    target_ratio: Optional[float] = None

class RiskItemOut(BaseModel):
    id: int
    seq: int
    name: str
    company: str
    amount_2025_end: Optional[float]
    xinghe_target: Optional[str]
    zhenong_target: Optional[str]
    annual_target: Optional[str]
    leader_province: Optional[str]
    leader_xinghe: Optional[str]
    leader_zhenong: Optional[str]
    leader_team: Optional[str]
    leader_dept: Optional[str]
    deadline: Optional[str]
    target_amount: Optional[float]
    target_ratio: Optional[float]
    class Config:
        from_attributes = True
