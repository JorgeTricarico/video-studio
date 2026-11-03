#!/usr/bin/env python3
"""
Firule Analytics & Telemetry Tracker Service (Raspberry Pi 5)
- Tracks external vs internal visitors for the kindergarten story web
- Detailed device, OS, browser, geolocation, and video engagement analytics
- Auto-expires and gracefully shuts down after 2 months (Dec 27, 2026)
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import urllib.request
import re
import html
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import threading

PORT = 8765
DB_PATH = os.path.expanduser("~/firule-tracker/analytics.db")
EXPIRATION_DATE = datetime.datetime(2026, 12, 27, 23, 59, 59)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# Initialize Database
def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            client_ip TEXT,
            is_external INTEGER,
            country TEXT,
            region TEXT,
            city TEXT,
            isp TEXT,
            user_agent TEXT,
            device_brand TEXT,
            device_model TEXT,
            os_name TEXT,
            browser_name TEXT,
            screen_res TEXT,
            referrer TEXT,
            created_at TIMESTAMP,
            last_seen TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            event_type TEXT,
            event_data TEXT,
            timestamp TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# GeoIP Cache
geo_cache = {}

def get_geoip(ip):
    if not ip or ip in ("127.0.0.1", "localhost") or ip.startswith("192.168.") or ip.startswith("100.") or ip.startswith("10."):
        return {"country": "Red Local / Tailscale", "region": "-", "city": "Local", "isp": "Intranet"}
    if ip in geo_cache:
        return geo_cache[ip]
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp"
        req = urllib.request.Request(url, headers={"User-Agent": "FiruleTracker/1.0"})
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode())
            if data.get("status") == "success":
                geo = {
                    "country": data.get("country", "Desconocido"),
                    "region": data.get("regionName", "-"),
                    "city": data.get("city", "Desconocido"),
                    "isp": data.get("isp", "Desconocido")
                }
                geo_cache[ip] = geo
                return geo
    except Exception:
        pass
    return {"country": "Externo", "region": "-", "city": "Detectando", "isp": "Desconocido"}

def parse_user_agent(ua_str):
    ua = ua_str.lower()
    
    # OS
    os_name = "Desconocido"
    if "iphone" in ua or "ipad" in ua or "ipod" in ua:
        m = re.search(r"os ([\d_]+)", ua)
        ver = m.group(1).replace("_", ".") if m else ""
        os_name = f"iOS {ver}".strip()
    elif "android" in ua:
        m = re.search(r"android ([\d.]+)", ua)
        ver = m.group(1) if m else ""
        os_name = f"Android {ver}".strip()
    elif "windows nt 10.0" in ua:
        os_name = "Windows 10/11"
    elif "macintosh" in ua or "mac os x" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"

    # Device Brand & Model
    brand = "Desconocido"
    model = "Desktop/PC"
    if "iphone" in ua:
        brand = "Apple"
        model = "iPhone"
    elif "ipad" in ua:
        brand = "Apple"
        model = "iPad"
    elif "samsung" in ua or "sm-" in ua:
        brand = "Samsung"
        m = re.search(r"(sm-[a-z0-9]+)", ua)
        model = m.group(1).upper() if m else "Samsung Galaxy"
    elif "moto" in ua or "motorola" in ua:
        brand = "Motorola"
        m = re.search(r"(moto [a-z0-9\s]+?)(?:;|\)|build)", ua)
        model = m.group(1).title() if m else "Motorola"
    elif "redmi" in ua or "xiaomi" in ua or "poco" in ua:
        brand = "Xiaomi"
        model = "Xiaomi/Redmi"
    elif "pixel" in ua:
        brand = "Google"
        m = re.search(r"(pixel [\da-z]+)", ua)
        model = m.group(1).title() if m else "Pixel"
    elif "android" in ua:
        brand = "Android Device"
        model = "Smartphone"

    # Browser & In-App Webviews
    browser = "Navegador Web"
    if "fban" in ua or "fbav" in ua:
        browser = "Facebook App"
    elif "instagram" in ua:
        browser = "Instagram App"
    elif "whatsapp" in ua:
        browser = "WhatsApp Webview"
    elif "edg" in ua:
        browser = "Microsoft Edge"
    elif "chrome" in ua and "crios" not in ua:
        browser = "Google Chrome"
    elif "crios" in ua:
        browser = "Chrome iOS"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Apple Safari"
    elif "firefox" in ua:
        browser = "Mozilla Firefox"

    return brand, model, os_name, browser

def is_external_ip(ip):
    if not ip or ip in ("127.0.0.1", "localhost"):
        return 0
    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16.") or ip.startswith("100."):
        return 0
    return 1

class TrackerHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, User-Agent, X-Session-Id")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def get_client_ip(self):
        xff = self.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        ts_ip = self.headers.get("Tailscale-User-Login")
        if ts_ip:
            return ts_ip
        return self.client_address[0]

    def do_POST(self):
        # Auto-expiration check
        if datetime.datetime.now() > EXPIRATION_DATE:
            self.send_response(410)
            self.end_headers()
            return

        if self.path == "/api/track":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            client_ip = self.get_client_ip()
            user_agent = self.headers.get("User-Agent", data.get("user_agent", ""))
            session_id = data.get("session_id", f"anon_{int(time.time()*1000)}")
            event_type = data.get("event", "page_view")
            event_data = json.dumps(data.get("data", {}))
            screen_res = data.get("screen", "")
            referrer = data.get("referrer", "")

            external = is_external_ip(client_ip)
            brand, model, os_name, browser = parse_user_agent(user_agent)
            geo = get_geoip(client_ip)

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sessions (
                    session_id, client_ip, is_external, country, region, city, isp,
                    user_agent, device_brand, device_model, os_name, browser_name,
                    screen_res, referrer, created_at, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    client_ip = excluded.client_ip
            """, (
                session_id, client_ip, external, geo["country"], geo["region"], geo["city"], geo["isp"],
                user_agent, brand, model, os_name, browser, screen_res, referrer, now_str, now_str
            ))

            cur.execute("""
                INSERT INTO events (session_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, event_type, event_data, now_str))

            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            try:
                self.wfile.write(b'{"status":"ok"}')
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        # Auto-expiration check
        if datetime.datetime.now() > EXPIRATION_DATE:
            self.send_response(410)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Service expired on 2026-12-27.")
            return

        if self.path in ("/", "/stats", "/dashboard"):
            self.render_dashboard()
        elif self.path == "/api/stats/json":
            self.render_json_stats()
        elif self.path.startswith("/api/track"):
            # Pixel tracking fallback
            self.send_response(204)
            self.send_cors_headers()
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def render_json_stats(self):
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), SUM(is_external) FROM sessions")
        row = cur.fetchone()
        total_sessions = row[0] or 0
        ext_sessions = row[1] or 0

        cur.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
        events = dict(cur.fetchall())

        cur.execute("SELECT device_brand, device_model, os_name, browser_name, city, country, isp, created_at, last_seen FROM sessions ORDER BY created_at DESC LIMIT 50")
        recent = cur.fetchall()
        conn.close()

        payload = {
            "total_visitors": total_sessions,
            "external_visitors": ext_sessions,
            "internal_visitors": total_sessions - ext_sessions,
            "events_breakdown": events,
            "recent_sessions": recent,
            "expires_at": EXPIRATION_DATE.isoformat()
        }
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload, indent=2).encode())

    def render_dashboard(self):
        conn = get_db_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*), SUM(is_external) FROM sessions")
        row = cur.fetchone()
        tot_vis = row[0] or 0
        ext_vis = row[1] or 0
        int_vis = tot_vis - ext_vis

        # Events count
        cur.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
        ev_dict = dict(cur.fetchall())

        views = ev_dict.get("page_view", 0)
        plays = ev_dict.get("video_play", 0)
        v25 = ev_dict.get("video_progress_25", 0)
        v50 = ev_dict.get("video_progress_50", 0)
        v75 = ev_dict.get("video_progress_75", 0)
        v100 = ev_dict.get("video_ended", 0)
        slider_moves = ev_dict.get("slider_moved", 0)
        confetti = ev_dict.get("confetti_click", 0)

        # Devices
        cur.execute("SELECT device_brand, device_model, COUNT(*) as c FROM sessions GROUP BY device_brand, device_model ORDER BY c DESC LIMIT 10")
        devices = cur.fetchall()

        # Geolocation
        cur.execute("SELECT city, country, isp, COUNT(*) as c FROM sessions WHERE is_external=1 GROUP BY city, country, isp ORDER BY c DESC LIMIT 10")
        geo_list = cur.fetchall()

        # Recent events
        cur.execute("SELECT session_id, event_type, event_data, timestamp FROM events ORDER BY id DESC LIMIT 25")
        recent_events = cur.fetchall()

        conn.close()

        days_left = (EXPIRATION_DATE - datetime.datetime.now()).days

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics Cuento Firule • Sala Lila</title>
<style>
:root {{
    --bg: #0f172a;
    --card: #1e293b;
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --accent: #f59e0b;
    --accent-blue: #38bdf8;
    --accent-green: #22c55e;
    --accent-purple: #c084fc;
    --border: #334155;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
body {{ background: var(--bg); color: var(--text); padding: 24px 16px; min-height: 100vh; }}
.container {{ max-width: 1100px; margin: 0 auto; }}
header {{ margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; }}
h1 {{ font-size: 1.6rem; color: #fff; display: flex; align-items: center; gap: 10px; }}
.badge-lila {{ background: #7c3aed; color: #fff; padding: 4px 12px; border-radius: 999px; font-size: 0.85rem; font-weight: 700; }}
.timer-pill {{ background: rgba(245, 158, 11, 0.15); border: 1px solid var(--accent); color: var(--accent); padding: 6px 14px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 18px; }}
.card-label {{ font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
.card-value {{ font-size: 2rem; font-weight: 800; color: #fff; }}
.card-sub {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }}
.funnel-container {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 24px; }}
.funnel-title {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 16px; color: var(--accent-blue); }}
.funnel-step {{ margin-bottom: 12px; }}
.funnel-bar-wrap {{ background: #334155; height: 24px; border-radius: 6px; overflow: hidden; position: relative; }}
.funnel-bar {{ height: 100%; border-radius: 6px; transition: width 0.5s ease; }}
.funnel-text {{ position: absolute; left: 10px; top: 3px; font-size: 0.8rem; font-weight: 700; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.8); }}
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
th {{ color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; }}
tr:hover {{ background: rgba(255,255,255,0.02); }}
</style>
</head>
<body>
<div class="container">
    <header>
        <div>
            <h1>Telemetria Cuento Firule <span class="badge-lila">Sala Lila</span></h1>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 4px;">Monitor de impacto escolar e interaccion en tiempo real</p>
        </div>
        <div class="timer-pill">Servicio activo: restan {days_left} dias (hasta 27/12/2026)</div>
    </header>

    <div class="grid">
        <div class="card">
            <div class="card-label">Visitantes Externos (Familias)</div>
            <div class="card-value" style="color: var(--accent-green);">{ext_vis}</div>
            <div class="card-sub">Fuera de la red local del hogar</div>
        </div>
        <div class="card">
            <div class="card-label">Visitantes Totales</div>
            <div class="card-value" style="color: var(--accent-blue);">{tot_vis}</div>
            <div class="card-sub">Incluye {int_vis} pruebas internas</div>
        </div>
        <div class="card">
            <div class="card-label">Reproducciones de Video</div>
            <div class="card-value" style="color: var(--accent);">{plays}</div>
            <div class="card-sub">{v100} completaron el 100%</div>
        </div>
        <div class="card">
            <div class="card-label">Interacciones Slider Pizarra</div>
            <div class="card-value" style="color: var(--accent-purple);">{slider_moves}</div>
            <div class="card-sub">{confetti} aplausos con confeti</div>
        </div>
    </div>

    <div class="funnel-container">
        <div class="funnel-title">Retencion del Video Cuento Firule (Duracion: 2m 01s)</div>
        <div class="funnel-step">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:4px;">
                <span>Inicio de reproduccion</span>
                <span>{plays} veces (100%)</span>
            </div>
            <div class="funnel-bar-wrap">
                <div class="funnel-bar" style="width: 100%; background: #38bdf8;"></div>
            </div>
        </div>
        <div class="funnel-step">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:4px;">
                <span>25% del Cuento (El paseo de Firule)</span>
                <span>{v25} veces ({(v25/max(1, plays))*100:.1f}%)</span>
            </div>
            <div class="funnel-bar-wrap">
                <div class="funnel-bar" style="width: {(v25/max(1, plays))*100:.1f}%; background: #60a5fa;"></div>
            </div>
        </div>
        <div class="funnel-step">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:4px;">
                <span>50% del Cuento (El escape de la pantufla)</span>
                <span>{v50} veces ({(v50/max(1, plays))*100:.1f}%)</span>
            </div>
            <div class="funnel-bar-wrap">
                <div class="funnel-bar" style="width: {(v50/max(1, plays))*100:.1f}%; background: #818cf8;"></div>
            </div>
        </div>
        <div class="funnel-step">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:4px;">
                <span>75% del Cuento (La cuneta y la perrita)</span>
                <span>{v75} veces ({(v75/max(1, plays))*100:.1f}%)</span>
            </div>
            <div class="funnel-bar-wrap">
                <div class="funnel-bar" style="width: {(v75/max(1, plays))*100:.1f}%; background: #a78bfa;"></div>
            </div>
        </div>
        <div class="funnel-step">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:4px;">
                <span>100% Cierre y Aplausos de Isai (Video Completo)</span>
                <span>{v100} veces ({(v100/max(1, plays))*100:.1f}%)</span>
            </div>
            <div class="funnel-bar-wrap">
                <div class="funnel-bar" style="width: {(v100/max(1, plays))*100:.1f}%; background: #22c55e;"></div>
            </div>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 24px;">
        <div class="card">
            <div class="card-label">Modelos de Celulares y Dispositivos</div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Marca</th><th>Modelo</th><th>Visitas</th></tr></thead>
                    <tbody>
                        {"".join(f"<tr><td>{d[0]}</td><td>{d[1]}</td><td><b>{d[2]}</b></td></tr>" for d in devices) or "<tr><td colspan='3'>Sin datos aun</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="card">
            <div class="card-label">Origen Geografico (Familias Externas)</div>
            <div class="table-wrap">
                <table>
                    <thead><tr><th>Ciudad</th><th>Proveedor / Red</th><th>Visitas</th></tr></thead>
                    <tbody>
                        {"".join(f"<tr><td>{g[0]}, {g[1]}</td><td>{g[2]}</td><td><b>{g[3]}</b></td></tr>" for g in geo_list) or "<tr><td colspan='3'>Esperando escaneos fuera de la red</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-label">Ultimos Eventos Registrados</div>
        <div class="table-wrap">
            <table>
                <thead><tr><th>Hora</th><th>Tipo Evento</th><th>Sesion</th><th>Detalle</th></tr></thead>
                <tbody>
                    {"".join(f"<tr><td style='white-space:nowrap;'>{html.escape(str(e[3]))}</td><td><b>{html.escape(str(e[1]))}</b></td><td><code>{html.escape(str(e[0])[:12])}...</code></td><td>{html.escape(str(e[2]))}</td></tr>" for e in recent_events) or "<tr><td colspan='4'>Esperando actividad</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
</div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

def auto_expiry_watchdog():
    while True:
        time.sleep(3600)  # Check every hour
        if datetime.datetime.now() > EXPIRATION_DATE:
            print("[EXPIRED] 2 months have elapsed. Auto-terminating service...")
            # Reset tailscale funnel and stop systemd service
            os.system("sudo tailscale funnel reset")
            os.system("systemctl --user stop firule-tracker.service")
            os._exit(0)

if __name__ == "__main__":
    t = threading.Thread(target=auto_expiry_watchdog, daemon=True)
    t.start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), TrackerHandler)
    print(f"[*] Firule Analytics Tracker listening on 0.0.0.0:{PORT}")
    print(f"[*] Expiration Date: {EXPIRATION_DATE.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
