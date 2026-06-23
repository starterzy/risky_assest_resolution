import os
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import httpx
from ..database import get_db
from ..models import User
from ..auth import create_token

router = APIRouter(prefix="/api/auth/wework", tags=["企业微信SSO"])

WEWORK_CORP_ID = os.getenv("WEWORK_CORP_ID", "wwbf3d667dc5365208")
WEWORK_AGENT_SECRET = os.getenv("WEWORK_AGENT_SECRET", "AaExshvmH1AzprG7Y0yiz1JToKfYW8Jfk_6YVq0mBcY")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8002")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def get_oauth_url() -> str:
    from urllib.parse import quote
    redirect_uri = quote(f"{BACKEND_URL}/api/auth/wework/callback", safe='')
    return (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={WEWORK_CORP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=snsapi_base"
        f"&state=1#wechat_redirect"
    )


@router.get("/auto-login")
async def wework_auto_login():
    return RedirectResponse(url=get_oauth_url())


@router.get("/redirect")
async def wework_redirect():
    return {"redirect_url": get_oauth_url()}


@router.get("/callback", response_class=HTMLResponse)
async def wework_callback(code: str = None, db: Session = Depends(get_db)):
    if not code:
        return _error_html("授权码无效，请重试")

    try:
        wework_userid = await _get_wework_userid(code)
        if not wework_userid:
            return _error_html("无法获取企业微信用户身份")

        user = db.query(User).filter(User.wework_userid == wework_userid).first()
        if not user:
            return _error_html("该用户未注册，请联系管理员在系统中绑定企业微信ID")

        if not user.is_active:
            return _error_html("用户已被禁用")

        token = create_token(user.id, user.role)

        return _success_html(token, {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
        })

    except Exception as e:
        return _error_html(str(e))


async def _get_wework_userid(code: str) -> str | None:
    access_token = await _get_wework_access_token()
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"
    params = {"access_token": access_token, "code": code}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        if data.get("errcode") != 0:
            return None
        return data.get("UserId")


async def _get_wework_access_token() -> str:
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    params = {"corpid": WEWORK_CORP_ID, "corpsecret": WEWORK_AGENT_SECRET}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        if data.get("errcode") != 0:
            raise HTTPException(status_code=500, detail="获取企业微信access_token失败")
        return data.get("access_token")


def _success_html(token: str, user: dict) -> HTMLResponse:
    content = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>登录成功</title></head><body>
<script>
localStorage.setItem('token', '{token}');
localStorage.setItem('userId', '{user["id"]}');
localStorage.setItem('name', '{user["name"]}');
localStorage.setItem('role', '{user["role"]}');
window.location.href = '{FRONTEND_URL}/';
</script></body></html>"""
    return HTMLResponse(content=content)


def _error_html(message: str) -> HTMLResponse:
    content = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>登录失败</title></head><body>
<script>
alert('{message}');
window.location.href = '{FRONTEND_URL}/login';
</script></body></html>"""
    return HTMLResponse(content=content)
