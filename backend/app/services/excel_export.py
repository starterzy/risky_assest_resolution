from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from sqlalchemy.orm import Session
from ..models import RiskItem, FillRecord


GREEN_FILL = PatternFill("solid", fgColor="92D050")
HEADER_FONT = Font(bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14)
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin")
)


def export_excel(db: Session, period: str, allowed_ids: set[int] | None = None) -> Workbook:
    wb = Workbook()
    query = db.query(RiskItem)
    if allowed_ids is not None:
        if not allowed_ids:
            return wb  # empty workbook
        query = query.filter(RiskItem.id.in_(allowed_ids))
    items = query.order_by(RiskItem.seq).all()
    prev_period = _prev_period(period)
    period_label = f"{period.split('-')[0]}年{int(period.split('-')[1])}月"

    _build_summary_sheet(wb, db, items, period, prev_period, period_label)
    _build_detail_sheet(wb, db, items, period, period_label)

    return wb


def _build_summary_sheet(wb, db, items, period, prev_period, period_label):
    ws = wb.active
    ws.title = "汇总表"
    ws.merge_cells("A1:I1")
    ws["A1"] = f"{period_label.split('年')[0]}年浙农控股风险资产压降进度一览表"
    ws["A1"].font = TITLE_FONT
    ws["I2"] = "单位：万元"

    headers = ["序号", "公司名称", "2025年12月底\n敞口金额",
               f"{_prev_period_label(period)}\n敞口金额",
               f"{period_label}\n敞口金额", f"{period_label}\n压降金额",
               f"{period_label.split('月')[0].split('年')[1]}月1-{int(period.split('-')[1])}月\n累计压降金额",
               "累计压降率", "备注"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    row = 4
    for item in items:
        current = db.query(FillRecord).filter(
            FillRecord.risk_item_id == item.id,
            FillRecord.period == period,
            FillRecord.status == "approved"
        ).first()
        prev = db.query(FillRecord).filter(
            FillRecord.risk_item_id == item.id,
            FillRecord.period == prev_period,
            FillRecord.status == "approved"
        ).first()

        amount_open = current.amount_open if current else (prev.amount_open if prev else item.amount_2025_end)
        prev_amount = prev.amount_open if prev else item.amount_2025_end
        monthly = (prev_amount - amount_open) if (prev_amount is not None and amount_open is not None) else 0
        cumulative = (item.amount_2025_end - amount_open) if (item.amount_2025_end is not None and amount_open is not None) else 0
        ratio = cumulative / item.amount_2025_end if (item.amount_2025_end and item.amount_2025_end != 0) else 0

        ws.cell(row=row, column=1, value=item.seq).border = THIN_BORDER
        ws.cell(row=row, column=2, value=item.company).border = THIN_BORDER
        ws.cell(row=row, column=3, value=item.amount_2025_end).border = THIN_BORDER
        ws.cell(row=row, column=4, value=prev_amount).border = THIN_BORDER
        ws.cell(row=row, column=5, value=amount_open).border = THIN_BORDER
        ws.cell(row=row, column=6, value=monthly).border = THIN_BORDER
        ws.cell(row=row, column=7, value=cumulative).border = THIN_BORDER
        ws.cell(row=row, column=8, value=ratio).border = THIN_BORDER
        ws.cell(row=row, column=8).number_format = "0.00%"
        row += 1


def _build_detail_sheet(wb, db, items, period, period_label):
    ws = wb.create_sheet("举措及责任分解")
    ws.merge_cells("A1:S1")
    ws["A1"] = "浙农控股风险化解举措及责任分解"
    ws["A1"].font = TITLE_FONT
    ws["S2"] = "单位：万元"

    headers = ["序号", "风险资产事项", "所属企业", "2025年12月底敞口金额",
               f"{period_label}敞口金额", f"{period_label}已计提减值", "预估未体现损失",
               "兴合集团\n目标及举措", "浙农控股\n目标及举措", "浙农控股\n2026年度目标及举措",
               "省社领导", "兴合集团领导", "浙农控股领导",
               "专班责任人/所属公司责任人/相关部门负责人", "浙农控股相关部门负责人",
               "时点", "2026年集团内部要求压降金额", "压降比例",
               f"截至{period_label}化解进展"]
    green_cols = [5, 6, 7, 19]

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        cell.border = THIN_BORDER
        if col in green_cols:
            cell.fill = GREEN_FILL

    row = 4
    for item in items:
        record = db.query(FillRecord).filter(
            FillRecord.risk_item_id == item.id,
            FillRecord.period == period,
            FillRecord.status == "approved"
        ).first()
        values = [
            item.seq, item.name, item.company, item.amount_2025_end,
            record.amount_open if record else None,
            record.amount_impairment if record else None,
            record.amount_est_loss if record else None,
            item.xinghe_target, item.zhenong_target, item.annual_target,
            item.leader_province, item.leader_xinghe, item.leader_zhenong,
            item.leader_team, item.leader_dept,
            item.deadline, item.target_amount, item.target_ratio,
            record.progress_text if record else None
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = THIN_BORDER
            if col in green_cols:
                cell.fill = GREEN_FILL
        row += 1


def _prev_period(period: str) -> str:
    parts = period.split("-")
    year, month = int(parts[0]), int(parts[1])
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year}-{month:02d}"


def _prev_period_label(period: str) -> str:
    prev = _prev_period(period)
    return f"{prev.split('-')[0]}年{int(prev.split('-')[1])}月底"
