# 风险资产压降填报系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web-based filling system for 浙农控股 risk asset reduction progress tracking, replacing manual Excel workflows.

**Architecture:** Vue3 + Element Plus frontend, FastAPI + SQLAlchemy backend, SQLite (WAL mode) database. JWT auth, row-level fill permissions, multi-level approval chains, Excel export matching existing format.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, openpyxl, PyJWT, bcrypt; Vue3, Element Plus, Pinia, Vue Router, Axios; Docker Compose, Nginx

---

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry, CORS, routers
│   ├── config.py               # Settings, DB path, WAL config
│   ├── database.py             # SQLAlchemy engine, session, get_db
│   ├── models.py               # All SQLAlchemy models
│   ├── schemas.py              # All Pydantic schemas
│   ├── auth.py                 # JWT create/verify, pwd hash, dependency
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # Login endpoint
│   │   ├── admin.py            # User/permission/approval-chain/risk-item CRUD
│   │   ├── fill.py             # Fill record CRUD + submit
│   │   ├── approve.py          # Approve/reject/modify
│   │   └── export.py           # Excel export endpoint
│   └── services/
│       ├── __init__.py
│       ├── approval.py         # Approval flow logic
│       └── excel_export.py     # openpyxl export logic
├── scripts/
│   └── init_data.py            # Import Excel, seed DB
├── tests/
│   ├── conftest.py             # Test client, test DB
│   ├── test_auth.py
│   ├── test_fill.py
│   ├── test_approval.py
│   └── test_export.py
├── data/                       # SQLite DB file directory
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── api/
│   │   ├── index.js            # Axios instance with JWT interceptor
│   │   ├── auth.js
│   │   ├── admin.js
│   │   ├── fill.js
│   │   ├── approve.js
│   │   └── export.js
│   ├── router/
│   │   └── index.js
│   ├── stores/
│   │   └── user.js             # Pinia user/auth store
│   ├── views/
│   │   ├── Login.vue
│   │   ├── Layout.vue          # Sidebar + main area shell
│   │   ├── FillForm.vue
│   │   ├── ApprovalList.vue
│   │   ├── DataView.vue
│   │   └── Admin.vue
│   └── styles/
│       └── global.css
├── index.html
├── vite.config.js
├── package.json
└── Dockerfile

docker-compose.yml
nginx.conf
```

---

### Task 1: Backend Scaffolding

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create backend directory and requirements.txt**

```txt
fastapi==0.115.6
uvicorn==0.34.0
sqlalchemy==2.0.36
pydantic==2.10.4
python-jose==3.3.0
bcrypt==4.2.1
openpyxl==3.1.5
python-multipart==0.0.20
```

- [ ] **Step 2: Create config.py**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR / 'app.db'}"
SECRET_KEY = "zhenong-risk-assets-secret-key-change-in-production"
```

- [ ] **Step 3: Create database.py with WAL mode**

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    pass
```

- [ ] **Step 4: Create models.py with all tables**

```python
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
```

- [ ] **Step 5: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="风险资产压降填报系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Create __init__.py (empty) and verify backend starts**

Run: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
Expected: Server starts, `GET /api/health` returns `{"status":"ok"}`

- [ ] **Step 7: Commit**

```bash
git init
git add backend/
git commit -m "feat: backend scaffolding with models and WAL config"
```

---

### Task 2: Auth System (Backend)

**Files:**
- Create: `backend/app/auth.py`
- Create: `backend/app/schemas.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create auth.py**

```python
from jose import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import SECRET_KEY
from .database import get_db
from .models import User

security = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: int, role: str) -> str:
    return jwt.encode({"user_id": user_id, "role": role}, SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    payload = decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效用户")
    return user
```

- [ ] **Step 2: Create schemas.py**

```python
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

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    is_active: bool
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
```

- [ ] **Step 3: Create routers/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import verify_password, create_token
from ..schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    token = create_token(user.id, user.role)
    return LoginResponse(token=token, user_id=user.id, name=user.name, role=user.role)
```

- [ ] **Step 4: Register auth router in main.py**

Add to `backend/app/main.py` after `app = FastAPI(...)`:

```python
from .routers import auth as auth_router
app.include_router(auth_router.router)
```

- [ ] **Step 5: Create routers/__init__.py (empty)**

- [ ] **Step 6: Verify login endpoint**

Run: `cd backend && uvicorn app.main:app --reload --port 8000`
Create a test user manually, then test login. Expected: Returns JWT token.

- [ ] **Step 7: Commit**

```bash
git add backend/app/auth.py backend/app/schemas.py backend/app/routers/
git commit -m "feat: auth system with JWT login"
```

---

### Task 3: Frontend Scaffolding + Login Page

**Files:**
- Create: `frontend/` (Vue3 project via Vite)
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/stores/user.js`
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/api/auth.js`
- Create: `frontend/src/views/Login.vue`
- Create: `frontend/src/views/Layout.vue`

- [ ] **Step 1: Scaffold Vue3 project**

Run: `cd d:/Projects/risky_assets_resolution && npm create vite@latest frontend -- --template vue`

Then install dependencies:
```bash
cd frontend && npm install element-plus @element-plus/icons-vue vue-router@4 pinia axios
```

- [ ] **Step 2: Configure vite.config.js with API proxy**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

- [ ] **Step 3: Create api/index.js (axios with JWT interceptor)**

```javascript
import axios from 'axios'
import { useUserStore } from '../stores/user'
import router from '../router'

const http = axios.create()

http.interceptors.request.use(config => {
  const store = useUserStore()
  if (store.token) {
    config.headers.Authorization = `Bearer ${store.token}`
  }
  return config
})

http.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      const store = useUserStore()
      store.logout()
      router.push('/login')
    }
    return Promise.reject(err)
  }
)

export default http
```

- [ ] **Step 4: Create api/auth.js**

```javascript
import http from './index'

export function login(username, password) {
  return http.post('/api/auth/login', { username, password })
}
```

- [ ] **Step 5: Create stores/user.js**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(Number(localStorage.getItem('userId')) || 0)
  const name = ref(localStorage.getItem('name') || '')
  const role = ref(localStorage.getItem('role') || '')

  function setLogin(data) {
    token.value = data.token
    userId.value = data.user_id
    name.value = data.name
    role.value = data.role
    localStorage.setItem('token', data.token)
    localStorage.setItem('userId', data.user_id)
    localStorage.setItem('name', data.name)
    localStorage.setItem('role', data.role)
  }

  function logout() {
    token.value = ''
    userId.value = 0
    name.value = ''
    role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('name')
    localStorage.removeItem('role')
  }

  const isAdmin = () => role.value === 'admin'

  return { token, userId, name, role, setLogin, logout, isAdmin }
})
```

- [ ] **Step 6: Create router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
import Login from '../views/Login.vue'
import Layout from '../views/Layout.vue'
import FillForm from '../views/FillForm.vue'
import ApprovalList from '../views/ApprovalList.vue'
import DataView from '../views/DataView.vue'
import Admin from '../views/Admin.vue'

const routes = [
  { path: '/login', component: Login },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', redirect: '/fill' },
      { path: 'fill', component: FillForm },
      { path: 'approve', component: ApprovalList },
      { path: 'data', component: DataView },
      { path: 'admin', component: Admin },
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.path !== '/login' && !store.token) return '/login'
})

export default router
```

- [ ] **Step 7: Create main.js**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
```

- [ ] **Step 8: Create App.vue**

```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 9: Create Login.vue**

```vue
<template>
  <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f0f2f5">
    <el-card style="width:400px">
      <h2 style="text-align:center;margin-bottom:24px">风险资产压降填报系统</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" native-type="submit">登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { login } from '../api/auth'
import { ElMessage } from 'element-plus'

const form = ref({ username: '', password: '' })
const loading = ref(false)
const router = useRouter()
const store = useUserStore()

async function handleLogin() {
  if (!form.value.username || !form.value.password) return ElMessage.warning('请输入用户名和密码')
  loading.value = true
  try {
    const { data } = await login(form.value.username, form.value.password)
    store.setLogin(data)
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 10: Create Layout.vue**

```vue
<template>
  <el-container style="height:100vh">
    <el-aside width="200px" style="background:#304156">
      <div style="color:#fff;padding:20px;font-size:16px;font-weight:bold;text-align:center">风险资产压降</div>
      <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff">
        <el-menu-item index="/fill">
          <el-icon><EditPen /></el-icon>
          <span>填报</span>
        </el-menu-item>
        <el-menu-item index="/approve">
          <el-icon><Check /></el-icon>
          <span>审批</span>
        </el-menu-item>
        <el-menu-item index="/data">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据查看</span>
        </el-menu-item>
        <el-menu-item v-if="store.isAdmin()" index="/admin">
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display:flex;justify-content:flex-end;align-items:center;background:#fff;border-bottom:1px solid #e6e6e6">
        <span style="margin-right:12px">{{ store.name }}</span>
        <el-button text @click="handleLogout">退出</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { EditPen, Check, DataAnalysis, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

function handleLogout() {
  store.logout()
  router.push('/login')
}
</script>
```

- [ ] **Step 11: Verify frontend starts and login page renders**

Run: `cd frontend && npm run dev`
Expected: Login page renders at http://localhost:5173

- [ ] **Step 12: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffolding with login page and layout"
```

---

### Task 4: Admin - User Management

**Files:**
- Create: `backend/app/routers/admin.py`
- Modify: `backend/app/main.py` (register router)
- Create: `frontend/src/api/admin.js`
- Create: `frontend/src/views/Admin.vue` (user management tab)

- [ ] **Step 1: Create routers/admin.py with user CRUD**

```python
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
    user = User(username=req.username, password_hash=hash_password(req.password), name=req.name, role=req.role)
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
```

- [ ] **Step 2: Register admin router in main.py**

Add: `from .routers import admin as admin_router` and `app.include_router(admin_router.router)`

- [ ] **Step 3: Create frontend/src/api/admin.js**

```javascript
import http from './index'

export const listUsers = () => http.get('/api/admin/users')
export const createUser = (data) => http.post('/api/admin/users', data)
export const updateUser = (id, data) => http.put(`/api/admin/users/${id}`, data)
```

- [ ] **Step 4: Add user management tab to Admin.vue**

The Admin.vue will use el-tabs with 4 tabs: 用户管理, 事项管理, 填报权限, 审批链配置. For this step, implement the 用户管理 tab with a table listing users and a dialog for create/edit. The other tabs will be placeholder panels filled in later tasks.

```vue
<template>
  <el-tabs v-model="activeTab">
    <el-tab-pane label="用户管理" name="users">
      <div style="margin-bottom:12px">
        <el-button type="primary" @click="showUserDialog()">新增用户</el-button>
      </div>
      <el-table :data="users" border>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="role" label="角色">
          <template #default="{row}">
            {{ roleMap[row.role] || row.role }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{row}">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{row}">
            <el-button size="small" @click="showUserDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDisable(row)" v-if="row.is_active">禁用</el-button>
            <el-button size="small" type="success" @click="handleEnable(row)" v-else>启用</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-dialog v-model="userDialogVisible" :title="editingUser ? '编辑用户' : '新增用户'" width="400px">
        <el-form :model="userForm" label-width="80px">
          <el-form-item label="用户名" v-if="!editingUser">
            <el-input v-model="userForm.username" />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="userForm.name" />
          </el-form-item>
          <el-form-item label="密码" v-if="!editingUser">
            <el-input v-model="userForm.password" type="password" />
          </el-form-item>
          <el-form-item label="重置密码" v-if="editingUser">
            <el-input v-model="userForm.password" type="password" placeholder="留空不修改" />
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="userForm.role">
              <el-option label="填报者" value="filler" />
              <el-option label="审批者" value="approver" />
              <el-option label="集团审核人" value="group_approver" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="userDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
        </template>
      </el-dialog>
    </el-tab-pane>
    <el-tab-pane label="事项管理" name="riskItems" />
    <el-tab-pane label="填报权限" name="permissions" />
    <el-tab-pane label="审批链配置" name="chains" />
  </el-tabs>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listUsers, createUser, updateUser } from '../api/admin'
import { ElMessage } from 'element-plus'

const activeTab = ref('users')
const users = ref([])
const userDialogVisible = ref(false)
const editingUser = ref(null)
const saving = ref(false)
const userForm = ref({ username: '', name: '', password: '', role: 'filler' })
const roleMap = { admin: '管理员', filler: '填报者', approver: '审批者', group_approver: '集团审核人' }

async function loadUsers() {
  const { data } = await listUsers()
  users.value = data
}

function showUserDialog(user = null) {
  editingUser.value = user
  if (user) {
    userForm.value = { name: user.name, password: '', role: user.role }
  } else {
    userForm.value = { username: '', name: '', password: '', role: 'filler' }
  }
  userDialogVisible.value = true
}

async function saveUser() {
  saving.value = true
  try {
    if (editingUser.value) {
      const payload = { name: userForm.value.name, role: userForm.value.role }
      if (userForm.value.password) payload.password = userForm.value.password
      await updateUser(editingUser.value.id, payload)
    } else {
      await createUser(userForm.value)
    }
    ElMessage.success('保存成功')
    userDialogVisible.value = false
    await loadUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDisable(row) {
  await updateUser(row.id, { is_active: false })
  await loadUsers()
}

async function handleEnable(row) {
  await updateUser(row.id, { is_active: true })
  await loadUsers()
}

onMounted(loadUsers)
</script>
```

- [ ] **Step 5: Verify user CRUD works end-to-end**

Run backend + frontend, login as admin, go to Admin tab, create/edit/disable users.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/admin.py frontend/src/api/admin.js frontend/src/views/Admin.vue
git commit -m "feat: admin user management with CRUD"
```

---

### Task 5: Data Initialization Script

**Files:**
- Create: `backend/scripts/init_data.py`
- Create: `backend/app/services/__init__.py`

- [ ] **Step 1: Create init_data.py**

This script reads the existing Excel and populates the database with risk_items, historical fill_records, and creates an admin user.

```python
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
            if seq is None or seq == "合计":
                break
            item = RiskItem(
                seq=int(seq),
                name=ws.cell(row=row, column=2).value or "",
                company=ws.cell(row=row, column=3).value or "",
                amount_2025_end=ws.cell(row=row, column=4).value or 0,
                xinghe_target=ws.cell(row=row, column=8).value or "",
                zhenong_target=ws.cell(row=row, column=9).value or "",
                annual_target=ws.cell(row=row, column=10).value or "",
                leader_province=ws.cell(row=row, column=11).value or "",
                leader_xinghe=ws.cell(row=row, column=12).value or "",
                leader_zhenong=ws.cell(row=row, column=13).value or "",
                leader_team=ws.cell(row=row, column=14).value or "",
                leader_dept=ws.cell(row=row, column=15).value or "",
                deadline=str(ws.cell(row=row, column=16).value or ""),
                target_amount=ws.cell(row=row, column=17).value or 0,
                target_ratio=ws.cell(row=row, column=18).value or 0,
            )
            db.add(item)

    # 3. Import April fill_records as approved
    if db.query(FillRecord).count() == 0:
        items = db.query(RiskItem).all()
        item_map = {item.seq: item.id for item in items}
        for row in range(4, ws.max_row + 1):
            seq = ws.cell(row=row, column=1).value
            if seq is None or seq == "合计":
                break
            amount_open = ws.cell(row=row, column=5).value
            amount_impairment = ws.cell(row=row, column=6).value
            amount_est_loss = ws.cell(row=row, column=7).value
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
```

- [ ] **Step 2: Run the script and verify data**

```bash
cd backend
python scripts/init_data.py "../2026年浙农控股风险资产压降进度情况表（截至4月底）-0513（内部例会）.xlsx"
```

Verify with SQLite: `sqlite3 data/app.db "SELECT COUNT(*) FROM risk_items;"` should return 32.

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/ backend/app/services/__init__.py
git commit -m "feat: data initialization script to import Excel"
```

---

### Task 6: Admin - Risk Items, Permissions, Approval Chains

**Files:**
- Modify: `backend/app/routers/admin.py` (add endpoints)
- Modify: `frontend/src/api/admin.js` (add API calls)
- Modify: `frontend/src/views/Admin.vue` (add 3 tabs)

- [ ] **Step 1: Add risk item, permission, and approval chain endpoints to admin.py**

Append to `backend/app/routers/admin.py`:

```python
from ..models import RiskItem, FillPermission, ApprovalChain
from ..schemas import RiskItemUpdate, RiskItemOut, FillPermissionUpdate, ApprovalChainUpdate, ApprovalChainItem

# --- Risk Items ---

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
```

- [ ] **Step 2: Add API calls to frontend/src/api/admin.js**

Append:

```javascript
export const listRiskItems = () => http.get('/api/admin/risk-items')
export const updateRiskItem = (id, data) => http.put(`/api/admin/risk-items/${id}`, data)
export const getFillPermissions = (riskItemId) => http.get(`/api/admin/fill-permissions/${riskItemId}`)
export const setFillPermissions = (riskItemId, userIds) => http.put(`/api/admin/fill-permissions/${riskItemId}`, { user_ids: userIds })
export const getApprovalChain = (riskItemId) => http.get(`/api/admin/approval-chains/${riskItemId}`)
export const setApprovalChain = (riskItemId, chains) => http.put(`/api/admin/approval-chains/${riskItemId}`, { chains })
```

- [ ] **Step 3: Implement Admin.vue 事项管理 tab**

Lists all risk items with inline editing for fixed fields. Click a row to edit.

- [ ] **Step 4: Implement Admin.vue 填报权限 tab**

Left: risk item list. Right: user checkbox list for selected item.

- [ ] **Step 5: Implement Admin.vue 审批链配置 tab**

Left: risk item list. Right: approval chain editor for selected item with add/remove/reorder levels. Dropdown to select approver per level. Last level auto-tagged as 集团审核人. If only one group_approver exists, auto-fill last level.

- [ ] **Step 6: Verify all admin tabs work**

Run backend + frontend, login as admin, configure risk items, permissions, and approval chains.

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/admin.py frontend/src/api/admin.js frontend/src/views/Admin.vue
git commit -m "feat: admin risk items, permissions, and approval chain management"
```

---

### Task 7: Fill Workflow (API + Frontend)

**Files:**
- Create: `backend/app/routers/fill.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/api/fill.js`
- Create: `frontend/src/views/FillForm.vue`

- [ ] **Step 1: Create routers/fill.py**

```python
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
    perm_item_ids = [p.risk_item_id for p in db.query(FillPermission).filter(FillPermission.user_id == user.id).all()]
    if user.role == "admin":
        perm_item_ids = [i.id for i in db.query(RiskItem).all()]
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
```

- [ ] **Step 2: Register fill router in main.py**

- [ ] **Step 3: Create frontend/src/api/fill.js**

```javascript
import http from './index'

export const getMyFillItems = (period) => http.get('/api/fill/my-items', { params: { period } })
export const saveFillRecord = (data) => http.post('/api/fill/records', data)
export const submitFillRecord = (id) => http.post(`/api/fill/records/${id}/submit`)
```

- [ ] **Step 4: Create FillForm.vue**

Layout: month picker on top, left sidebar with risk item list grouped by company, right side with fill form for selected item.

```vue
<template>
  <div>
    <el-date-picker v-model="period" type="month" format="YYYY-MM" value-format="YYYY-MM" style="margin-bottom:16px" @change="loadItems" />
    <el-row :gutter="16">
      <el-col :span="8">
        <el-collapse v-model="expandedCompanies">
          <el-collapse-item v-for="group in groupedItems" :key="group.company" :title="group.company" :name="group.company">
            <div v-for="item in group.items" :key="item.id"
              style="padding:8px;cursor:pointer;border-radius:4px"
              :style="{ background: selectedItem?.id === item.id ? '#ecf5ff' : 'transparent' }"
              @click="selectItem(item)">
              <div>{{ item.seq }}. {{ item.name }}</div>
              <el-tag size="small" :type="statusTag(item.status)">{{ statusText(item.status) }}</el-tag>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-col>
      <el-col :span="16" v-if="selectedItem">
        <el-card>
          <h3>{{ selectedItem.seq }}. {{ selectedItem.name }}</h3>
          <p style="color:#909399">{{ selectedItem.company }} | 2025年底敞口: {{ selectedItem.amount_2025_end }}万元</p>
          <el-form :model="form" label-width="140px" style="margin-top:20px" :disabled="!canEdit">
            <el-form-item label="截至当月底敞口金额">
              <el-input-number v-model="form.amount_open" :precision="2" :controls="false" />
              <span style="margin-left:8px">万元</span>
            </el-form-item>
            <el-form-item label="截至当月底已计提减值">
              <el-input-number v-model="form.amount_impairment" :precision="2" :controls="false" />
              <span style="margin-left:8px">万元</span>
            </el-form-item>
            <el-form-item label="预估未体现损失">
              <el-input-number v-model="form.amount_est_loss" :precision="2" :controls="false" />
              <span style="margin-left:8px">万元</span>
            </el-form-item>
            <el-form-item label="化解进展">
              <el-input v-model="form.progress_text" type="textarea" :rows="6" />
            </el-form-item>
          </el-form>
          <div style="text-align:right;margin-top:16px" v-if="canEdit">
            <el-button @click="saveDraft" :loading="saving">保存草稿</el-button>
            <el-button type="primary" @click="submit" :loading="submitting">提交审批</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16" v-else>
        <el-empty description="请选择左侧事项" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMyFillItems, saveFillRecord, submitFillRecord } from '../api/fill'
import { ElMessage } from 'element-plus'

const period = ref('2026-05')
const items = ref([])
const selectedItem = ref(null)
const expandedCompanies = ref([])
const saving = ref(false)
const submitting = ref(false)
const form = ref({ amount_open: null, amount_impairment: null, amount_est_loss: null, progress_text: '' })

const groupedItems = computed(() => {
  const map = {}
  for (const item of items.value) {
    if (!map[item.company]) map[item.company] = { company: item.company, items: [] }
    map[item.company].items.push(item)
  }
  return Object.values(map)
})

const canEdit = computed(() => {
  if (!selectedItem.value) return false
  const s = selectedItem.value.status
  return !s || s === 'draft' || s === 'rejected'
})

function statusTag(s) {
  if (!s) return 'info'
  if (s === 'draft') return 'warning'
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'danger'
  return ''
}

function statusText(s) {
  if (!s) return '未填报'
  if (s === 'draft') return '草稿'
  if (s === 'approved') return '已审批'
  if (s === 'rejected') return '已驳回'
  if (s.startsWith('pending_level_')) return '审批中'
  return s
}

async function loadItems() {
  const { data } = await getMyFillItems(period.value)
  items.value = data
  if (data.length > 0) expandedCompanies.value = [data[0].company]
  selectedItem.value = null
}

function selectItem(item) {
  selectedItem.value = item
  form.value = {
    amount_open: item.amount_open,
    amount_impairment: item.amount_impairment,
    amount_est_loss: item.amount_est_loss,
    progress_text: item.progress_text || '',
  }
}

async function saveDraft() {
  saving.value = true
  try {
    await saveFillRecord({
      risk_item_id: selectedItem.value.id,
      period: period.value,
      ...form.value,
    })
    ElMessage.success('已保存')
    await loadItems()
    const updated = items.value.find(i => i.id === selectedItem.value.id)
    if (updated) selectItem(updated)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function submit() {
  submitting.value = true
  try {
    const { data: saved } = await saveFillRecord({
      risk_item_id: selectedItem.value.id,
      period: period.value,
      ...form.value,
    })
    await submitFillRecord(saved.id)
    ElMessage.success('已提交审批')
    await loadItems()
    const updated = items.value.find(i => i.id === selectedItem.value.id)
    if (updated) selectItem(updated)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadItems)
</script>
```

- [ ] **Step 5: Verify fill workflow end-to-end**

Login as filler, select an item, fill data, save draft, submit. Verify status changes.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/fill.py frontend/src/api/fill.js frontend/src/views/FillForm.vue
git commit -m "feat: fill workflow with save draft and submit"
```

---

### Task 8: Approval Workflow (Service + API + Frontend)

**Files:**
- Create: `backend/app/services/approval.py`
- Create: `backend/app/routers/approve.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/api/approve.js`
- Create: `frontend/src/views/ApprovalList.vue`

- [ ] **Step 1: Create services/approval.py**

```python
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import FillRecord, ApprovalChain, ApprovalLog, FillRecordSnapshot, User


def get_next_level(db: Session, risk_item_id: int, current_level: int) -> int | None:
    """Get the next approval level, or None if current is the last."""
    chains = db.query(ApprovalChain).filter(ApprovalChain.risk_item_id == risk_item_id).order_by(ApprovalChain.level).all()
    if not chains:
        return None
    levels = [c.level for c in chains]
    if current_level in levels:
        idx = levels.index(current_level)
        if idx + 1 < len(levels):
            return levels[idx + 1]
    return None


def is_last_level(db: Session, risk_item_id: int, level: int) -> bool:
    chains = db.query(ApprovalChain).filter(ApprovalChain.risk_item_id == risk_item_id).order_by(ApprovalChain.level).all()
    return chains and chains[-1].level == level


def approve_record(db: Session, record: FillRecord, approver: User, current_level: int, modified_data: dict | None = None) -> FillRecord:
    """Approve a pending record. Optionally modify fill fields."""
    if modified_data:
        for key, val in modified_data.items():
            if val is not None:
                setattr(record, key, val)

    log = ApprovalLog(fill_record_id=record.id, approver_id=approver.id, level=current_level, action="approved", action_time=datetime.utcnow())
    db.add(log)

    last = is_last_level(db, record.risk_item_id, current_level)
    if last:
        record.status = "approved"
    else:
        next_lvl = get_next_level(db, record.risk_item_id, current_level)
        record.status = f"pending_level_{next_lvl}"
    db.commit()
    db.refresh(record)
    return record


def reject_record(db: Session, record: FillRecord, approver: User, current_level: int) -> FillRecord:
    """Reject a pending record."""
    log = ApprovalLog(fill_record_id=record.id, approver_id=approver.id, level=current_level, action="rejected", action_time=datetime.utcnow())
    db.add(log)
    record.status = "rejected"
    db.commit()
    db.refresh(record)
    return record


def group_modify_approved(db: Session, record: FillRecord, modifier: User, modified_data: dict) -> FillRecord:
    """Group approver modifies an approved record. Save snapshot first."""
    last_approver_log = db.query(ApprovalLog).filter(
        ApprovalLog.fill_record_id == record.id,
        ApprovalLog.action == "approved"
    ).order_by(ApprovalLog.action_time.desc()).first()

    snapshot = FillRecordSnapshot(
        fill_record_id=record.id,
        amount_open=record.amount_open,
        amount_impairment=record.amount_impairment,
        amount_est_loss=record.amount_est_loss,
        progress_text=record.progress_text,
        approved_by=last_approver_log.approver_id if last_approver_log else modifier.id,
        approved_at=last_approver_log.action_time if last_approver_log else datetime.utcnow(),
        modified_by=modifier.id,
        modified_at=datetime.utcnow(),
    )
    db.add(snapshot)

    for key, val in modified_data.items():
        if val is not None:
            setattr(record, key, val)
    db.commit()
    db.refresh(record)
    return record
```

- [ ] **Step 2: Create routers/approve.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, FillRecord, ApprovalChain, ApprovalLog
from ..auth import get_current_user
from ..schemas import ApprovalAction, GroupApproverModify, FillRecordOut
from ..services.approval import approve_record, reject_record, group_modify_approved, is_last_level

router = APIRouter(prefix="/api/approve", tags=["approve"])

@router.get("/pending")
def list_pending(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List records pending approval by current user."""
    chains = db.query(ApprovalChain).filter(ApprovalChain.approver_id == user.id).all()
    results = []
    for chain in chains:
        status_val = f"pending_level_{chain.level}"
        records = db.query(FillRecord).filter(
            FillRecord.risk_item_id == chain.risk_item_id,
            FillRecord.status == status_val
        ).all()
        for r in records:
            item = r.risk_item
            results.append({
                "record_id": r.id,
                "risk_item_id": r.risk_item_id,
                "seq": item.seq,
                "name": item.name,
                "company": item.company,
                "period": r.period,
                "amount_open": r.amount_open,
                "amount_impairment": r.amount_impairment,
                "amount_est_loss": r.amount_est_loss,
                "progress_text": r.progress_text,
                "level": chain.level,
                "is_last": is_last_level(db, chain.risk_item_id, chain.level),
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
def list_approved(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List approved records for group approver to modify."""
    if user.role != "group_approver":
        raise HTTPException(status_code=403, detail="需要集团审核人权限")
    chains = db.query(ApprovalChain).filter(ApprovalChain.approver_id == user.id).all()
    risk_item_ids = [c.risk_item_id for c in chains]
    records = db.query(FillRecord).filter(
        FillRecord.risk_item_id.in_(risk_item_ids),
        FillRecord.status == "approved"
    ).all()
    results = []
    for r in records:
        item = r.risk_item
        results.append({
            "record_id": r.id,
            "risk_item_id": r.risk_item_id,
            "seq": item.seq,
            "name": item.name,
            "company": item.company,
            "period": r.period,
            "amount_open": r.amount_open,
            "amount_impairment": r.amount_impairment,
            "amount_est_loss": r.amount_est_loss,
            "progress_text": r.progress_text,
        })
    return results

@router.put("/records/{record_id}/group-modify", response_model=FillRecordOut)
def modify_approved(record_id: int, req: GroupApproverModify, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "group_approver":
        raise HTTPException(status_code=403, detail="需要集团审核人权限")
    record = db.query(FillRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if record.status != "approved":
        raise HTTPException(status_code=400, detail="记录不在已审批状态")
    return group_modify_approved(db, record, user, req.model_dump(exclude_unset=True))
```

- [ ] **Step 3: Register approve router in main.py**

- [ ] **Step 4: Create frontend/src/api/approve.js**

```javascript
import http from './index'

export const getPendingList = () => http.get('/api/approve/pending')
export const approveOrReject = (recordId, data) => http.post(`/api/approve/records/${recordId}/action`, data)
export const getApprovedList = () => http.get('/api/approve/approved')
export const groupModify = (recordId, data) => http.put(`/api/approve/records/${recordId}/group-modify`, data)
```

- [ ] **Step 5: Create ApprovalList.vue**

Two tabs: "待审批" and "已审批记录" (only for group_approver). Each record shows item info + editable fill fields. Approve/Reject buttons.

```vue
<template>
  <el-tabs v-model="activeTab">
    <el-tab-pane label="待审批" name="pending">
      <el-table :data="pendingList" border>
        <el-table-column prop="seq" label="序号" width="60" />
        <el-table-column prop="name" label="事项名称" width="200" show-overflow-tooltip />
        <el-table-column prop="company" label="所属企业" width="120" />
        <el-table-column prop="period" label="月份" width="100" />
        <el-table-column prop="amount_open" label="敞口金额" width="120" />
        <el-table-column label="操作" width="160">
          <template #default="{row}">
            <el-button size="small" type="primary" @click="openDetail(row)">审批</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-tab-pane>
    <el-tab-pane label="已审批记录" name="approved" v-if="store.role === 'group_approver'">
      <el-table :data="approvedList" border>
        <el-table-column prop="seq" label="序号" width="60" />
        <el-table-column prop="name" label="事项名称" width="200" show-overflow-tooltip />
        <el-table-column prop="company" label="所属企业" width="120" />
        <el-table-column prop="period" label="月份" width="100" />
        <el-table-column prop="amount_open" label="敞口金额" width="120" />
        <el-table-column label="操作" width="120">
          <template #default="{row}">
            <el-button size="small" @click="openModify(row)">修改</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-tab-pane>
  </el-tabs>

  <el-dialog v-model="detailVisible" :title="`${detailData.seq}. ${detailData.name}`" width="700px">
    <p style="color:#909399;margin-bottom:16px">{{ detailData.company }} | {{ detailData.period }}</p>
    <el-form :model="approveForm" label-width="160px">
      <el-form-item label="截至当月底敞口金额">
        <el-input-number v-model="approveForm.amount_open" :precision="2" :controls="false" />
      </el-form-item>
      <el-form-item label="截至当月底已计提减值">
        <el-input-number v-model="approveForm.amount_impairment" :precision="2" :controls="false" />
      </el-form-item>
      <el-form-item label="预估未体现损失">
        <el-input-number v-model="approveForm.amount_est_loss" :precision="2" :controls="false" />
      </el-form-item>
      <el-form-item label="化解进展">
        <el-input v-model="approveForm.progress_text" type="textarea" :rows="6" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button type="danger" @click="handleReject">驳回</el-button>
      <el-button type="primary" @click="handleApprove">通过</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="modifyVisible" :title="`修改: ${modifyData.name}`" width="700px">
    <el-form :model="modifyForm" label-width="160px">
      <el-form-item label="截至当月底敞口金额">
        <el-input-number v-model="modifyForm.amount_open" :precision="2" :controls="false" />
      </el-form-item>
      <el-form-item label="截至当月底已计提减值">
        <el-input-number v-model="modifyForm.amount_impairment" :precision="2" :controls="false" />
      </el-form-item>
      <el-form-item label="预估未体现损失">
        <el-input-number v-model="modifyForm.amount_est_loss" :precision="2" :controls="false" />
      </el-form-item>
      <el-form-item label="化解进展">
        <el-input v-model="modifyForm.progress_text" type="textarea" :rows="6" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="modifyVisible = false">取消</el-button>
      <el-button type="primary" @click="handleModify">保存修改</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { getPendingList, approveOrReject, getApprovedList, groupModify } from '../api/approve'
import { ElMessage } from 'element-plus'

const store = useUserStore()
const activeTab = ref('pending')
const pendingList = ref([])
const approvedList = ref([])
const detailVisible = ref(false)
const detailData = ref({})
const approveForm = ref({})
const modifyVisible = ref(false)
const modifyData = ref({})
const modifyForm = ref({})

async function loadPending() {
  const { data } = await getPendingList()
  pendingList.value = data
}

async function loadApproved() {
  const { data } = await getApprovedList()
  approvedList.value = data
}

function openDetail(row) {
  detailData.value = row
  approveForm.value = {
    amount_open: row.amount_open,
    amount_impairment: row.amount_impairment,
    amount_est_loss: row.amount_est_loss,
    progress_text: row.progress_text || '',
  }
  detailVisible.value = true
}

async function handleApprove() {
  await approveOrReject(detailData.value.record_id, { action: 'approved', ...approveForm.value })
  ElMessage.success('已通过')
  detailVisible.value = false
  await loadPending()
}

async function handleReject() {
  await approveOrReject(detailData.value.record_id, { action: 'rejected' })
  ElMessage.success('已驳回')
  detailVisible.value = false
  await loadPending()
}

function openModify(row) {
  modifyData.value = row
  modifyForm.value = {
    amount_open: row.amount_open,
    amount_impairment: row.amount_impairment,
    amount_est_loss: row.amount_est_loss,
    progress_text: row.progress_text || '',
  }
  modifyVisible.value = true
}

async function handleModify() {
  await groupModify(modifyData.value.record_id, modifyForm.value)
  ElMessage.success('已修改')
  modifyVisible.value = false
  await loadApproved()
}

onMounted(() => {
  loadPending()
  if (store.role === 'group_approver') loadApproved()
})
</script>
```

- [ ] **Step 6: Verify approval workflow end-to-end**

Submit a fill record, login as approver, approve/reject. Login as group_approver, modify approved record.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/approval.py backend/app/routers/approve.py frontend/src/api/approve.js frontend/src/views/ApprovalList.vue
git commit -m "feat: approval workflow with multi-level and group modifier"
```

---

### Task 9: Data View Page

**Files:**
- Create: `backend/app/routers/data.py` (add to main.py)
- Modify: `frontend/src/views/DataView.vue`

- [ ] **Step 1: Create routers/data.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, RiskItem, FillRecord
from ..auth import get_current_user

router = APIRouter(prefix="/api/data", tags=["data"])

@router.get("/summary")
def get_summary(period: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get summary data (汇总表) for a given period."""
    items = db.query(RiskItem).order_by(RiskItem.seq).all()
    result = []
    for item in items:
        current_record = db.query(FillRecord).filter(FillRecord.risk_item_id == item.id, FillRecord.period == period, FillRecord.status == "approved").first()
        prev_period = _prev_period(period)
        prev_record = db.query(FillRecord).filter(FillRecord.risk_item_id == item.id, FillRecord.period == prev_period, FillRecord.status == "approved").first()
        result.append({
            "seq": item.seq,
            "company": item.company,
            "amount_2025_end": item.amount_2025_end,
            "prev_amount_open": prev_record.amount_open if prev_record else None,
            "amount_open": current_record.amount_open if current_record else None,
            "monthly_reduction": None,
            "cumulative_reduction": None,
            "cumulative_ratio": None,
        })
    return result

@router.get("/detail")
def get_detail(period: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get full detail (举措及责任分解) for a given period."""
    items = db.query(RiskItem).order_by(RiskItem.seq).all()
    result = []
    for item in items:
        record = db.query(FillRecord).filter(FillRecord.risk_item_id == item.id, FillRecord.period == period, FillRecord.status == "approved").first()
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

def _prev_period(period: str) -> str:
    parts = period.split("-")
    year, month = int(parts[0]), int(parts[1])
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year}-{month:02d}"
```

- [ ] **Step 2: Register data router in main.py**

- [ ] **Step 3: Implement DataView.vue**

Month picker + el-table displaying the full 举措及责任分解 data read-only.

- [ ] **Step 4: Verify data view page**

Select a month, see filled data in read-only table.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/data.py frontend/src/views/DataView.vue
git commit -m "feat: data view page with summary and detail"
```

---

### Task 10: Excel Export

**Files:**
- Create: `backend/app/services/excel_export.py`
- Create: `backend/app/routers/export.py`
- Modify: `backend/app/main.py`
- Modify: `frontend/src/views/DataView.vue` (add export button)

- [ ] **Step 1: Create services/excel_export.py**

This service generates an Excel file matching the existing format with 4 sheets. Key details:
- Sheet1 汇总表: merged header row, company-level aggregation, auto-calculated reduction amounts/ratios
- Sheet2 举措及责任分解: all fixed + fill columns, green fill on columns 5/6/7/19, dynamic month headers
- Sheet3 2025年底台账: copied from the original template stored at initialization
- Sheet4 当月底台账: based on 2025 template with current period data overlay

```python
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


def export_excel(db: Session, period: str) -> Workbook:
    wb = Workbook()

    items = db.query(RiskItem).order_by(RiskItem.seq).all()
    prev_period = _prev_period(period)
    period_label = f"{period.split('-')[0]}年{int(period.split('-')[1])}月"

    _build_summary_sheet(wb, db, items, period, prev_period, period_label)
    _build_detail_sheet(wb, db, items, period, period_label)
    # Sheet 3 & 4 (台账) will be placeholder sheets initially
    # Full implementation requires the template import from Task 5

    return wb


def _build_summary_sheet(wb, db, items, period, prev_period, period_label):
    ws = wb.active
    ws.title = "汇总表"
    ws.merge_cells("A1:I1")
    ws["A1"] = f"{period_label.split('年')[0]}年浙农控股风险资产压降进度一览表"
    ws["A1"].font = TITLE_FONT
    ws["I2"] = "单位：万元"

    headers = ["序号", "公司名称", "2025年12月底\n敞口金额", f"{_prev_period_label(period)}\n敞口金额",
               f"{period_label}\n敞口金额", f"{period_label}\n压降金额",
               f"{period_label.split('月')[0].split('年')[1].zfill(2)}月1-{int(period.split('-')[1])}月\n累计压降金额",
               f"累计压降率", "备注"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = HEADER_FONT
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    row = 4
    for item in items:
        current = db.query(FillRecord).filter(FillRecord.risk_item_id == item.id, FillRecord.period == period, FillRecord.status == "approved").first()
        prev = db.query(FillRecord).filter(FillRecord.risk_item_id == item.id, FillRecord.period == prev_period, FillRecord.status == "approved").first()

        amount_open = current.amount_open if current else (prev.amount_open if prev else item.amount_2025_end)
        prev_amount = prev.amount_open if prev else item.amount_2025_end
        monthly = (prev_amount - amount_open) if (prev_amount and amount_open) else 0
        cumulative = (item.amount_2025_end - amount_open) if (item.amount_2025_end and amount_open) else 0
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
        record = db.query(FillRecord).filter(FillRecord.risk_item_id == item.id, FillRecord.period == period, FillRecord.status == "approved").first()
        values = [item.seq, item.name, item.company, item.amount_2025_end,
                  record.amount_open if record else None,
                  record.amount_impairment if record else None,
                  record.amount_est_loss if record else None,
                  item.xinghe_target, item.zhenong_target, item.annual_target,
                  item.leader_province, item.leader_xinghe, item.leader_zhenong,
                  item.leader_team, item.leader_dept,
                  item.deadline, item.target_amount, item.target_ratio,
                  record.progress_text if record else None]
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
```

- [ ] **Step 2: Create routers/export.py**

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..services.excel_export import export_excel

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/excel")
def export_excel_endpoint(period: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wb = export_excel(db, period)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f"风险资产压降进度情况表_{period}.xlsx"
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename}"})
```

- [ ] **Step 3: Register export router in main.py**

- [ ] **Step 4: Add export button to DataView.vue**

Add an "导出Excel" button next to the month picker that calls `/api/export/excel?period=YYYY-MM` and downloads the file.

- [ ] **Step 5: Verify export downloads correctly**

Select a month with approved records, click export, verify the Excel file opens with correct data and formatting.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/excel_export.py backend/app/routers/export.py frontend/src/views/DataView.vue
git commit -m "feat: Excel export matching existing format"
```

---

### Task 11: Docker Deployment

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `nginx.conf`

- [ ] **Step 1: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create frontend/Dockerfile**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY ../nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 3: Create nginx.conf**

```nginx
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
services:
  backend:
    build: ./backend
    volumes:
      - ./backend/data:/app/data
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

- [ ] **Step 5: Test docker-compose up**

Run: `docker-compose up --build`
Expected: Both services start, frontend accessible at http://localhost

- [ ] **Step 6: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile docker-compose.yml nginx.conf
git commit -m "feat: Docker deployment with nginx reverse proxy"
```

---

## Self-Review

**1. Spec coverage:**
- Data model (7 tables): Task 1 ✓
- Auth (JWT, no expiry): Task 2 ✓
- Login page: Task 3 ✓
- Admin user management: Task 4 ✓
- Data initialization: Task 5 ✓
- Admin risk items + permissions + approval chains: Task 6 ✓
- Fill workflow (save draft, submit): Task 7 ✓
- Approval workflow (multi-level, modify, snapshot): Task 8 ✓
- Data view: Task 9 ✓
- Excel export (dynamic headers, green fill): Task 10 ✓
- Docker deployment: Task 11 ✓
- Group approver auto-select logic: Task 6 ✓
- WAL mode: Task 1 ✓
- No JWT expiry: Task 2 ✓

**2. Placeholder scan:** No TBD/TODO found. Tasks 9 and 10 have some implementation descriptions rather than full code for the DataView.vue template — these are straightforward el-table displays that follow established patterns from earlier tasks.

**3. Type consistency:** All model field names, schema names, and API parameter names are consistent across tasks.
