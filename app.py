from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime

app = FastAPI()
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
            interval TEXT,
            tradingview_time TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.get("/")
def home():
    return {"status": "app is running"}


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    symbol = data.get("symbol", "UNKNOWN")
    price = float(data.get("price", 0))
    alert_type = data.get("alert", "unknown")
    interval = data.get("interval", "")
    tradingview_time = data.get("time", "")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alerts
        (symbol, price, alert_type, interval, tradingview_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        price,
        alert_type,
        interval,
        tradingview_time,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

    print("Webhook opgeslagen:", data)

    return {"status": "ok", "saved": data}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, price, alert_type, interval, tradingview_time, created_at
        FROM alerts
        ORDER BY id DESC
        LIMIT 100
    """)
    alerts = cur.fetchall()
    conn.close()

    rows = ""
    for alert in alerts:
        rows += f"""
        <tr>
            <td>{alert[0]}</td>
            <td>{alert[1]}</td>
            <td>{alert[2]}</td>
            <td>{alert[3]}</td>
            <td>{alert[4]}</td>
            <td>{alert[5]}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crypto Alerts Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f1117;
                color: white;
                padding: 30px;
            }}
            h1 {{
                color: #00ff99;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #171a23;
            }}
            th, td {{
                padding: 12px;
                border-bottom: 1px solid #333;
                text-align: left;
            }}
            th {{
                background: #222633;
            }}
            tr:hover {{
                background: #222;
            }}
        </style>
    </head>
    <body>
        <h1>Crypto Alerts Dashboard</h1>
        <p>Laatste 100 TradingView alerts</p>

        <table>
            <tr>
                <th>Coin</th>
                <th>Prijs</th>
                <th>Alert</th>
                <th>Interval</th>
                <th>TradingView tijd</th>
                <th>Ontvangen</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)