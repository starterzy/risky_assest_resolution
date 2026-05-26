from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin / filler / approver / group_approver
    is_active = Column(Boolean, default=True)


class RiskItem(Base):
    __tablename__ = "risk_items"
    id = Column(Integer, primary_key=True, index=True)
    seq = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    company = Column(String, nullable=False)
    amount_2025_end = Column(Float)
    xinghe_target = Column(Text)
    zhenong_target = Column(Text)
    annual_target = Column(Text)
    leader_province = Column(String)
    leader_xinghe = Column(String)
    leader_zhenong = Column(String)
    leader_team = Column(String)
    leader_dept = Column(String)
    deadline = Column(String)
    target_amount = Column(Float)
    target_ratio = Column(Float)
    fill_permissions = relationship("FillPermission", back_populates="risk_item")
    approval_chains = relationship("ApprovalChain", back_populates="risk_item", order_by="ApprovalChain.level")
    fill_records = relationship("FillRecord", back_populates="risk_item")


class FillRecord(Base):
    __tablename__ = "fill_records"
    id = Column(Integer, primary_key=True, index=True)
    risk_item_id = Column(Integer, ForeignKey("risk_items.id"), nullable=False)
    period = Column(String, nullable=False)  # "2026-05"
    amount_open = Column(Float)
    amount_impairment = Column(Float)
    amount_est_loss = Column(Float)
    progress_text = Column(Text)
    status = Column(String, nullable=False, default="draft")  # draft / pending_level_N / approved / rejected
    filler_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submit_time = Column(DateTime)
    __table_args__ = (UniqueConstraint("risk_item_id", "period"),)
    risk_item = relationship("RiskItem", back_populates="fill_records")
    approval_logs = relationship("ApprovalLog", back_populates="fill_record")
    snapshots = relationship("FillRecordSnapshot", back_populates="fill_record")


class FillPermission(Base):
    __tablename__ = "fill_permissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    risk_item_id = Column(Integer, ForeignKey("risk_items.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "risk_item_id"),)
    risk_item = relationship("RiskItem", back_populates="fill_permissions")


class ApprovalChain(Base):
    __tablename__ = "approval_chains"
    id = Column(Integer, primary_key=True, index=True)
    risk_item_id = Column(Integer, ForeignKey("risk_items.id"), nullable=False)
    level = Column(Integer, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    __table_args__ = (UniqueConstraint("risk_item_id", "level"),)
    risk_item = relationship("RiskItem", back_populates="approval_chains")


class ApprovalLog(Base):
    __tablename__ = "approval_logs"
    id = Column(Integer, primary_key=True, index=True)
    fill_record_id = Column(Integer, ForeignKey("fill_records.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    level = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # approved / rejected
    comment = Column(Text)
    action_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    fill_record = relationship("FillRecord", back_populates="approval_logs")


class FillRecordSnapshot(Base):
    __tablename__ = "fill_record_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    fill_record_id = Column(Integer, ForeignKey("fill_records.id"), nullable=False)
    amount_open = Column(Float)
    amount_impairment = Column(Float)
    amount_est_loss = Column(Float)
    progress_text = Column(Text)
    approved_by = Column(Integer, nullable=False)
    approved_at = Column(DateTime, nullable=False)
    modified_by = Column(Integer, nullable=False)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    fill_record = relationship("FillRecord", back_populates="snapshots")
