# Bismillahir Rahmanir Rahim
# El Hamdu Lillah El Hamdu Lillah El Hamdulillah
# El Hamdu Lillahi Rabbul Alemin
# Esselatu vesSelamu ala rasulina Muhammedin
"""aql.api — Faqih mini-LLM HTTP API (stdlib, bagimliliksiz).

Kullanim:
    python3 -m aql.api          # 127.0.0.1:8000
    PORT=8001 python3 -m aql.api

Uclar:
    GET  /saglik  -> {"durum":"ok"}
    POST /sor     -> {"bolum":"kelam", "soru":"..."} -> {"bolum":..., "cevap":"..."}

Web (Next.js) sunucusu bunu AQL_URL ile kullanir.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aql.llm.router import _yukle, sec

LOCK = threading.Lock()
_MOD = None


def motor():
    """Modelleri ilk istekte yukler (tek seferlik, kilitli)."""
    global _MOD
    with LOCK:
        if _MOD is None:
            _MOD = _yukle()
    return _MOD


class Handler(BaseHTTPRequestHandler):
    def _json(self, kod: int, veri: dict):
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(govde)

    def do_GET(self):
        if self.path == "/saglik":
            self._json(200, {"durum": "ok", "servis": "faqih-aql"})
        else:
            self._json(404, {"error": "bilinmeyen yol"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/sor":
            self._json(404, {"error": "bilinmeyen yol"})
            return
        try:
            uzunluk = int(self.headers.get("Content-Length", 0))
            istek = json.loads(self.rfile.read(uzunluk) or b"{}")
        except Exception:
            self._json(400, {"error": "gecersiz JSON"})
            return
        bolum = str(istek.get("bolum") or "").strip()
        soru = str(istek.get("soru") or istek.get("mesaj") or "").strip()
        if not soru:
            self._json(400, {"error": "soru bos"})
            return
        try:
            modeller = motor()
            if bolum and bolum in modeller:
                cevap = modeller[bolum].sor(soru)
                kullanilan = bolum
            else:
                kullanilan = sec(soru)
                cevap = modeller[kullanilan].sor(soru)
            self._json(200, {"bolum": kullanilan, "cevap": cevap})
        except Exception as h:
            self._json(500, {"error": str(h)})

    def log_message(self, *args):
        pass


def main():
    port = int(os.environ.get("PORT", "8000"))
    sunucu = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"[aql.api] Faqih motoru http://127.0.0.1:{port} adresinde (Bismillah)")
    sunucu.serve_forever()


if __name__ == "__main__":
    main()
