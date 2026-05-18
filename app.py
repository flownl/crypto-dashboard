@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DB = "alerts.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            alert_type TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    symbol = data.get("symbol")
    price = float(data.get("price", 0))
    alert_type = data.get("alert", "unknown")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (symbol, price, alert_type, created_at) VALUES (?, ?, ?, ?)",
        (symbol, price, alert_type, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, price, alert_type, created_at
        FROM alerts
        ORDER BY id DESC
        LIMIT 100
    """)
    alerts = cur.fetchall()
    conn.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "alerts": alerts}
    )