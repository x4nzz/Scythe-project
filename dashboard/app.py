import os
import re
import time
import sqlite3
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# ==========================================
# PATH RESOLVER
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))       # /home/container/dashboard
ROOT_DIR = os.path.dirname(CURRENT_DIR)                         # /home/container

load_dotenv(os.path.join(ROOT_DIR, ".env"))
load_dotenv()

DB_PATH = os.path.join(ROOT_DIR, "scyth_database.db")
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(CURRENT_DIR, "scyth_database.db")

TEMPLATES_DIR = os.path.join(CURRENT_DIR, "templates")
if not os.path.exists(TEMPLATES_DIR):
    TEMPLATES_DIR = os.path.join(ROOT_DIR, "dashboard", "templates")

STATIC_DIR = os.path.join(CURRENT_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1449164530486608006")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
SESSION_SECRET = os.getenv("SESSION_SECRET_KEY", "scyth-underground-session-key-32chars")
MAIN_GUILD_ID = int(os.getenv("MAIN_GUILD_ID", 1531895848177500200))
PORT = int(os.getenv("SERVER_PORT", os.getenv("PORT", 25606)))

DISCORD_API = "https://discord.com/api/v10"

def init_dashboard_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_dashboard_settings (
                guild_id INTEGER PRIMARY KEY,
                anti_nuke INTEGER DEFAULT 1,
                anti_invite INTEGER DEFAULT 1,
                anti_raid INTEGER DEFAULT 1,
                welcome_channel_id INTEGER DEFAULT NULL,
                welcome_message TEXT DEFAULT 'Welcome {user} to {server}!'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_playback (
                guild_id INTEGER PRIMARY KEY,
                title TEXT,
                artist TEXT,
                uri TEXT,
                artwork TEXT,
                duration INTEGER,
                started_at REAL,
                is_playing INTEGER
            )
        """)
        conn.commit()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_redirect_uri(request: Request) -> str:
    """Dynamically matches the live public URL so Discord OAuth never throws invalid redirect."""
    env_redirect = os.getenv("DISCORD_REDIRECT_URI")
    if env_redirect and not env_redirect.startswith("http://localhost"):
        return env_redirect
    return f"{str(request.base_url).rstrip('/')}/auth/callback"

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_dashboard_db()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=86400 * 7)

# Serve static files (logo, images)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

def get_current_user(request: Request) -> Optional[dict]:
    return request.session.get("user")

def is_guild_admin(permissions: int) -> bool:
    return (permissions & 0x8 == 0x8) or (permissions & 0x20 == 0x20)

# ==========================================
# API: LIVE PLAYBACK DATA (LAST PLAYED SUPPORT)
# ==========================================
@app.get("/api/now-playing")
async def api_now_playing():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Grab the latest track regardless of active status
        cursor.execute("SELECT * FROM active_playback WHERE guild_id = ?", (MAIN_GUILD_ID,))
        row = cursor.fetchone()

    if not row:
        return JSONResponse({"hasData": False, "isActive": False})

    is_active = bool(row["is_playing"])
    duration = row["duration"] or 1
    elapsed = max(0, int(time.time() - row["started_at"])) if is_active else duration

    return JSONResponse({
        "hasData": True,
        "isActive": is_active,
        "title": row["title"],
        "artist": row["artist"],
        "uri": row["uri"],
        "artwork": row["artwork"] or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80",
        "duration": duration,
        "elapsed": min(elapsed, duration) if is_active else duration,
        "statusLabel": "PLAYING" if is_active else "LAST PLAYED"
    })

# ==========================================
# PAGE ROUTES
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    invite_url = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": user, "invite_url": invite_url}
    )

@app.get("/login")
async def login(request: Request):
    redirect = get_redirect_uri(request)
    discord_auth_url = (
        f"{DISCORD_API}/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={redirect}&response_type=code"
        f"&scope=identify%20guilds"
    )
    return RedirectResponse(url=discord_auth_url)

@app.get("/auth/callback")
async def auth_callback(request: Request, code: Optional[str] = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing auth code")

    redirect = get_redirect_uri(request)
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch access token")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        user_resp = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user data")

        user_data = user_resp.json()

    request.session["user"] = {
        "id": user_data["id"],
        "username": user_data["username"],
        "avatar": user_data.get("avatar"),
    }
    request.session["access_token"] = access_token

    return RedirectResponse(url="/servers")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/servers", response_class=HTMLResponse)
async def list_servers(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    token = request.session.get("access_token")
    async with httpx.AsyncClient() as client:
        user_guilds_resp = await client.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"}
        )

    guilds = user_guilds_resp.json()
    return templates.TemplateResponse(
        request=request,
        name="servers.html",
        context={"user": user, "guilds": guilds}
    )

@app.get("/servers/{guild_id}", response_class=HTMLResponse)
async def server_settings(request: Request, guild_id: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    guild_id_int = int(guild_id)
    token = request.session.get("access_token")
    
    async with httpx.AsyncClient() as client:
        user_guilds_resp = await client.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    target_guild = next((g for g in user_guilds_resp.json() if int(g["id"]) == guild_id_int), None)
    if not target_guild:
        raise HTTPException(status_code=404, detail="Guild not found")
    
    if not is_guild_admin(int(target_guild.get("permissions", 0))):
        raise HTTPException(status_code=403, detail="Unauthorized")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT anti_nuke, anti_invite, anti_raid, welcome_channel_id, welcome_message
            FROM guild_dashboard_settings WHERE guild_id = ?
        """, (guild_id_int,))
        settings = cursor.fetchone()

    saved = request.query_params.get("saved") == "1"
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "user": user,
            "guild_id": guild_id_int,
            "settings": settings,
            "saved": saved
        }
    )

@app.post("/servers/{guild_id}/settings")
async def update_server_settings(
    request: Request,
    guild_id: str,
    anti_nuke: Optional[str] = Form(None),
    anti_invite: Optional[str] = Form(None),
    anti_raid: Optional[str] = Form(None),
    welcome_channel_id: Optional[str] = Form(None),
    welcome_message: Optional[str] = Form(None),
    conn: sqlite3.Connection = Depends(get_db)
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")

    token = request.session.get("access_token")
    async with httpx.AsyncClient() as client:
        user_guilds_resp = await client.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {token}"}
        )
    target_guild = next((g for g in user_guilds_resp.json() if int(g["id"]) == int(guild_id)), None)
    if not target_guild or not is_guild_admin(int(target_guild.get("permissions", 0))):
        raise HTTPException(status_code=403, detail="Unauthorized")

    nuke_val = 1 if anti_nuke == "on" else 0
    invite_val = 1 if anti_invite == "on" else 0
    raid_val = 1 if anti_raid == "on" else 0
    channel_id = int(welcome_channel_id.strip()) if welcome_channel_id and welcome_channel_id.strip().isdigit() else None

    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO guild_dashboard_settings
        (guild_id, anti_nuke, anti_invite, anti_raid, welcome_channel_id, welcome_message)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (int(guild_id), nuke_val, invite_val, raid_val, channel_id, welcome_message))
    conn.commit()

    return RedirectResponse(url=f"/servers/{guild_id}?saved=1", status_code=303)

@app.get("/commands", response_class=HTMLResponse)
async def command_list(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(
        request=request,
        name="commands.html",
        context={"user": user}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
