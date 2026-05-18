from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime, timedelta

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


def calculate_score(alerts):
    score = 0
    reasons = []

    alert_types = [a[2] for a in alerts]

    if "momentum" in alert_types:
        score += 3
        reasons.append("momentum")

    if "volume" in alert_types:
        score += 3
        reasons.append("volume")

    if "breakout" in alert_types:
        score += 4
        reasons.append("breakout")

    if len(alerts) >= 2:
        score += 1
        reasons.append("multiple alerts")

    if score >= 7:
        status = "CANDIDATE"
    elif score >= 4:
        status = "WATCH"
    else:
        status = "SKIP"

    return score, status, ", ".join(reasons)


@app.get("/")
def home():
    return {"status": "app is running"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
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

        return {"status": "ok", "saved": data}

    except Exception as e:
        print("ERROR:", str(e))
        return {"status": "error", "message": str(e)}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    since = (datetime.utcnow() - timedelta(minutes=60)).isoformat()

    cur.execute("""
        SELECT symbol, price, alert_type, interval, tradingview_time, created_at
        FROM alerts
        WHERE created_at >= ?
        ORDER BY created_at DESC
    """, (since,))

    alerts = cur.fetchall()
    conn.close()

    grouped = {}

    for alert in alerts:
        symbol = alert[0]
        grouped.setdefault(symbol, []).append(alert)

    rows = ""

    for symbol, symbol_alerts in grouped.items():
        latest = symbol_alerts[0]
        score, status, reasons = calculate_score(symbol_alerts)

        status_class = status.lower()

        rows += f"""
        <tr class="{status_class}">
            <td>{symbol}</td>
            <td>{latest[1]}</td>
            <td>{score}/10</td>
            <td><strong>{status}</strong></td>
            <td>{reasons}</td>
            <td>{len(symbol_alerts)}</td>
            <td>{latest[5]}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crypto Decision Dashboard</title>
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
            .candidate {{
                background: rgba(0, 255, 153, 0.15);
            }}
            .watch {{
                background: rgba(255, 193, 7, 0.12);
            }}
            .skip {{
                opacity: 0.65;
            }}
        </style>
    </head>
    <body>
        <h1>Crypto Decision Dashboard</h1>
        <p>Coins gegroepeerd op alerts van de laatste 60 minuten</p>

        <table>
            <tr>
                <th>Coin</th>
                <th>Laatste prijs</th>
                <th>Score</th>
                <th>Status</th>
                <th>Reden</th>
                <th>Aantal alerts</th>
                <th>Laatste alert</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)