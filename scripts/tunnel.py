#!/usr/bin/env python3
"""
Runner resiliente de Cloudflare Quick Tunnel para macOS / Redes con DNS multi-IP.
Crea la sesión efímera en api.trycloudflare.com con fallback de IPs y ejecuta cloudflared.
"""
import base64
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
URL_FILE = os.path.join(LOG_DIR, "tunnel_url.txt")
PID_FILE = os.path.join(LOG_DIR, "tunnel.pid")

CANDIDATE_IPS = ["104.16.231.132", "104.16.230.132", "api.trycloudflare.com"]

def create_quick_tunnel():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for ip in CANDIDATE_IPS:
        url = f"https://{ip}/tunnel"
        req = urllib.request.Request(
            url,
            data=b"",
            headers={"Host": "api.trycloudflare.com", "User-Agent": "cloudflared/2026.10.7"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                data = json.loads(resp.read().decode())
                if data.get("success") and "result" in data:
                    return data["result"]
        except Exception:
            continue
    raise RuntimeError("No fue posible contactar a api.trycloudflare.com a través de los nodos de red disponibles.")

def main():
    print("▸ Solicitando túnel a Cloudflare...")
    res = create_quick_tunnel()
    hostname = res["hostname"]
    public_url = f"https://{hostname}"
    print(f"✅ Túnel asignado: {public_url}")

    with open(URL_FILE, "w") as f:
        f.write(public_url + "\n")

    token_data = {"a": res["account_tag"], "t": res["id"], "s": res["secret"]}
    token = base64.b64encode(json.dumps(token_data).encode()).decode()

    cmd = [
        "cloudflared", "tunnel",
        "--logfile", "/tmp/cloudflared.log",
        "run",
        "--url", "http://localhost:5173",
        "--token", token
    ]

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print("▸ Iniciando cloudflared tunnel daemon...")
    sys.stdout.flush()
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()
