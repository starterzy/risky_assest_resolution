# 浙农控股风险资产压降填报系统 - 设计文档

## 概述

为浙农控股开发风险资产压降进度填报系统，替代现有Excel手工填报方式。系统支持按行粒度分配填报权限、多级审批流程、自动生成汇总报表和台账、导出与现有Excel格式一致的文件。

## 技术选型

- 前端：Vue3 + Element Plus
- 后端：FastAPI + SQLAlchemy
- 数据库：SQLite（WAL模式）
- Excel处理：openpyxl
- 认证：JWT + bcrypt
- 部署：Docker Compose（前端 + 后端 + Nginx）

## 整体架构

```
┌─────────────────────────────────────────┐
│              Nginx (反向代理)             │
├──────────────────┬──────────────────────┤
│   Vue3 + Element │    FastAPI            │
│   Plus (前端)     │    (后端API)          │
│                  │                       │
│  - 登录/权限      │  - /api/auth  认证    │
│  - 填报表单      │  - /api/fill   填报   │
│  - 审批流程      │  - /api/approve 审批  │
│  - 数据查看      │  - /api/admin 管理    │
│  - Excel导出     │  - /api/export 导出   │
├──────────────────┴──────────────────────┤
│         SQLite (WAL模式)                 │
└─────────────────────────────────────────┘
```

## 目录结构

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── fill.py
│   │   ├── approve.py
│   │   ├── admin.py
│   │   └── export.py
│   └── services/
│       ├── excel_export.py
│       └── approval.py
├── data/
└── requirements.txt

frontend/
├── src/
│   ├── views/
│   │   ├── Login.vue
│   │   ├── FillForm.vue
│   │   ├── ApprovalList.vue
│   │   ├── DataView.vue
│   │   └── Admin.vue
│   ├── stores/
│   ├── api/
│   └── router/
└── package.json
```

## 数据模型

### 用户表

```sql
users (
    id            INTEGER PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT NOT NULL,
    role          TEXT NOT NULL,    -- admin / filler / approver / group_approver
    is_active     BOOLEAN DEFAULT 1
)
```

### 风险资产事项表（固定数据，从Excel导入初始化）

```sql
risk_items (
    id                INTEGER PRIMARY KEY,
    seq               INTEGER NOT NULL,
    name              TEXT NOT NULL,
    company           TEXT NOT NULL,
    amount_2025_end   REAL,
    xinghe_target     TEXT,
    zhenong_target    TEXT,
    annual_target     TEXT,
    leader_province   TEXT,
    leader_xinghe     TEXT,
    leader_zhenong    TEXT,
    leader_team       TEXT,
    leader_dept       TEXT,
    deadline          TEXT,
    target_amount     REAL,
    target_ratio      REAL
)
```

### 填报记录表（每月每行一条）

```sql
fill_records (
    id                INTEGER PRIMARY KEY,
    risk_item_id      INTEGER NOT NULL,
    period            TEXT NOT NULL,          -- "2026-05"
    amount_open       REAL,
    amount_impairment REAL,
    amount_est_loss   REAL,
    progress_text     TEXT,
    status            TEXT NOT NULL DEFAULT 'draft',
    filler_id         INTEGER NOT NULL,
    submit_time       DATETIME,
    UNIQUE(risk_item_id, period)
)
```

status取值：draft / pending_level_N / approved / rejected

### 行级填报权限

```sql
fill_permissions (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL,
    risk_item_id  INTEGER NOT NULL,
    UNIQUE(user_id, risk_item_id)
)
```

### 审批链配置（按事项逐条配置）

```sql
approval_chains (
    id            INTEGER PRIMARY KEY,
    risk_item_id  INTEGER NOT NULL,
    level         INTEGER NOT NULL,
    approver_id   INTEGER NOT NULL,
    UNIQUE(risk_item_id, level)
)
```

最后一级(level最大值)自动标记为集团审核人。

### 审批记录

```sql
approval_logs (
    id             INTEGER PRIMARY KEY,
    fill_record_id INTEGER NOT NULL,
    approver_id    INTEGER NOT NULL,
    level          INTEGER NOT NULL,
    action         TEXT NOT NULL,    -- approved / rejected
    comment        TEXT,
    action_time    DATETIME NOT NULL
)
```

### 填报记录快照（集团审核人修改已审批记录时保存）

```sql
fill_record_snapshots (
    id                INTEGER PRIMARY KEY,
    fill_record_id    INTEGER NOT NULL,
    amount_open       REAL,
    amount_impairment REAL,
    amount_est_loss   REAL,
    progress_text     TEXT,
    approved_by       INTEGER NOT NULL,
    approved_at       DATETIME NOT NULL,
    modified_by       INTEGER NOT NULL,
    modified_at       DATETIME NOT NULL
)
```

集团审核人驳回不保存快照，仅在approved状态下修改时保存。

## 审批流转

```
填报者提交 → 审批级1 → 审批级2 → ... → 集团审核人(最后一级) → approved
                │                        │
                └── 驳回 → rejected ←────┘
```

### 状态流转

| 当前状态 | 动作 | 目标状态 | 操作者 |
|---------|------|---------|--------|
| draft | 保存 | draft | 填报者 |
| draft | 提交 | pending_level_1 | 填报者 |
| pending_level_N | 通过 | pending_level_N+1 或 approved | 第N级审批人 |
| pending_level_N | 驳回 | rejected | 第N级审批人 |
| rejected | 修改后重新提交 | pending_level_1 | 填报者 |
| approved | 修改 | approved | 集团审核人 |

### 规则

- 填报者可反复保存草稿，提交后不可修改
- 任意审批人均可在审批时修改4个填报字段
- 通过/驳回无需填写意见
- 驳回后退回填报者修改，重新提交从头审批
- 集团审核人始终是最后一级，自动标记
- 集团审核人可修改已审批记录，修改时保存快照到fill_record_snapshots
- 集团审核人驳回不保存快照
- 已审批记录只有集团审核人可修改
- 每月每行状态独立

## 审批链配置

按事项逐条配置，管理页面展示事项列表，每条可点击进入配置详情：

- 下拉选择审批人，支持上下调整层级顺序
- 最后一级自动标记为集团审核人
- 集团审核人选择逻辑：如果group_approver角色只有1人，则默认填入；多于1人则需手动选择
- 保存校验：至少1级，不能重复选同一人
- 已有审批记录的事项修改审批链，仅影响后续提交，不影响已提交记录

## 核心页面

### 登录页

用户名 + 密码登录，JWT鉴权，token不过期。

### 填报页面（填报者视角）

- 左侧：该用户有权限的风险事项列表，按所属企业分组
- 右侧：选中事项的填报表单，4个填报字段
- 上方月份选择器，切换不同月份
- 状态标识：草稿/待审批/已驳回/已审批
- 已驳回记录显示驳回来源层级
- 保存草稿 / 提交审批

### 审批页面（审批者视角）

- 待审批列表：显示待自己审批的所有记录
- 点击进入详情：上方固定信息 + 下方4个填报字段
- 审批人可直接修改4个填报字段
- 通过 / 驳回
- 集团审核人额外有"已审批记录"标签页，可查看并修改已审批记录

### 数据查看页（所有人）

- 按月份查看汇总表和举措及责任分解完整数据
- 只读，按权限可见范围展示

### 管理页面（admin）

- 用户管理：增删改用户、分配角色
- 权限分配：按行为用户分配填报权限
- 审批链配置：为每个风险事项逐条配置多级审批人
- 基础数据管理：维护risk_items固定列数据

## Excel导出

选择月份导出，4个Sheet：

1. **汇总表**：按公司汇总fill_records，自动计算压降金额/比例
2. **举措及责任分解**：固定列 + 4个填报列，格式与现有模板对齐
3. **2025年底风险资产台账**：固定模板，初始化时导入
4. **当月底风险资产台账**：基于2025年底台账 + 当月填报数据更新

关键点：
- 表头中的月份信息动态生成（如"截至2026年5月末化解进展"）
- 只有approved状态的记录纳入导出
- 合并单元格、列宽、字体、颜色与现有模板对齐
- 填报列保留绿色填充标记

## 系统初始化

1. 管理员创建账号，设置角色
2. 导入现有Excel：
   - risk_items：从"举措及责任分解"提取32条事项的固定列
   - 台账模板：保存2025年底台账
   - 历史数据：将3月、4月fill_records导入，状态标记为approved
3. 为每个事项配置审批链
4. 为每个事项分配填报权限

## 安全

- JWT token，不过期
- 密码bcrypt加密
- 权限控制：admin/filler/approver/group_approver四级角色
- 按行粒度控制填报权限

## 部署

Docker Compose单机部署，SQLite文件挂载为volume，备份即复制文件。

## v1不支持

- 表结构变更（增减字段）
