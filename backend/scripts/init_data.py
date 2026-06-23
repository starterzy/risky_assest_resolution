"""Import existing Excel data into the database.

Usage: python scripts/init_data.py <excel_file_path>
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from openpyxl import load_workbook
from app.database import engine, SessionLocal, Base
from app.models import User, RiskItem, FillRecord
from app.auth import hash_password

Base.metadata.create_all(bind=engine)


def safe_float(val):
    """Convert cell value to float, treating '/' and non-numeric as 0."""
    if val is None or val == "/" or val == "":
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def import_data(excel_path: str):
    wb = load_workbook(excel_path, data_only=True)
    db = SessionLocal()

    # 1. Create admin user
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(username="admin", password_hash=hash_password("admin123"), name="管理员", role="admin")
        db.add(admin)

    # 2. Import risk_items from "举措及责任分解" sheet
    ws = wb["举措及责任分解"]
    existing_count = db.query(RiskItem).count()
    if existing_count == 0:
        for row in range(4, ws.max_row + 1):
            seq = ws.cell(row=row, column=1).value
            if seq is None:
                continue
            if seq == "合计":
                break
            item = RiskItem(
                seq=int(seq),
                name=ws.cell(row=row, column=2).value or "",
                company=ws.cell(row=row, column=3).value or "",
                amount_2025_end=safe_float(ws.cell(row=row, column=4).value),
                xinghe_target=ws.cell(row=row, column=8).value or "",
                zhenong_target=ws.cell(row=row, column=9).value or "",
                annual_target=ws.cell(row=row, column=10).value or "",
                leader_province=ws.cell(row=row, column=11).value or "",
                leader_xinghe=ws.cell(row=row, column=12).value or "",
                leader_zhenong=ws.cell(row=row, column=13).value or "",
                leader_team=ws.cell(row=row, column=14).value or "",
                leader_dept=ws.cell(row=row, column=15).value or "",
                deadline=str(ws.cell(row=row, column=16).value or ""),
                target_amount=safe_float(ws.cell(row=row, column=17).value),
                target_ratio=safe_float(ws.cell(row=row, column=18).value),
            )
            db.add(item)
        db.commit()

    # 3. Import April fill_records as approved
    if db.query(FillRecord).count() == 0:
        items = db.query(RiskItem).all()
        item_map = {item.seq: item.id for item in items}
        for row in range(4, ws.max_row + 1):
            seq = ws.cell(row=row, column=1).value
            if seq is None:
                continue
            if seq == "合计":
                break
            amount_open = safe_float(ws.cell(row=row, column=5).value)
            amount_impairment = safe_float(ws.cell(row=row, column=6).value)
            amount_est_loss = safe_float(ws.cell(row=row, column=7).value)
            progress_text = ws.cell(row=row, column=19).value
            risk_item_id = item_map.get(int(seq))
            if risk_item_id:
                record = FillRecord(
                    risk_item_id=risk_item_id,
                    period="2026-04",
                    amount_open=amount_open,
                    amount_impairment=amount_impairment,
                    amount_est_loss=amount_est_loss,
                    progress_text=progress_text or "",
                    status="approved",
                    filler_id=1,  # admin
                    submit_time=datetime(2026, 4, 30),
                )
                db.add(record)

    db.commit()
    db.close()
    print("Data import completed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/init_data.py <excel_file_path>")
        sys.exit(1)
    import_data(sys.argv[1])
