"""
server.py — Apuração · Agita Comunicação

Servidor da nova interface (React/SPA estática). Substitui o antigo
front-end Streamlit (app.py), mantendo a mesma funcionalidade:

  • serve a SPA (Apuracao.html + app/*) e o logo
  • GET  /api/data            -> dados reais do pipeline (clusters, gráficos…)
  • POST /api/pipeline/start  -> dispara o pipeline real em background
  • GET  /api/pipeline/status -> progresso + logs em tempo real

Sem dependências externas (usa apenas a stdlib). Rode com:  py server.py
"""

import json
import shutil
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from urllib.parse import parse_qs

from src.utils.parsing import load_toml
from src.utils.pipeline_runner import PIPELINE_STEPS
from src.utils.web_data import build_app_data, build_pipeline_steps

PROJECT_ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8501

# ─────────────────────────────────────────────────────────────
# Paths (lê config/directories.toml, como o load_config original)
# ─────────────────────────────────────────────────────────────
_dirs = load_toml(PROJECT_ROOT / "config" / "directories.toml")["paths"]
PROCESSED_PATH = str(PROJECT_ROOT / _dirs["processed"])
RESULT_FILE = str(
    PROJECT_ROOT / _dirs["processed"]
    / "clusters_defined_distinguished_trends_assessed.csv"
)

# Diretórios de dados apagados ao "recomeçar do zero"
DATA_DIRS = [_dirs["raw"], _dirs["processed"], _dirs["checkpoints"], _dirs["output"]]
# Arquivo que persiste quantas etapas já concluíram (para retomar a execução)
PROGRESS_FILE = PROJECT_ROOT / _dirs["checkpoints"] / "pipeline_progress.json"

# Arquivos estáticos permitidos
STATIC_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

# ─────────────────────────────────────────────────────────────
# Estado do pipeline (compartilhado entre threads)
# ─────────────────────────────────────────────────────────────
_lock = threading.Lock()
PIPELINE = {
    "running": False,
    "finished": False,
    "error": None,
    "progress": 0,
    "logs": [],
    "steps": [],
}


def _load_progress():
    """Quantas etapas já concluíram com sucesso (persistido em disco)."""
    try:
        with PROGRESS_FILE.open("r", encoding="utf-8") as f:
            return int(json.load(f).get("last_completed", 0))
    except (OSError, ValueError, json.JSONDecodeError):
        return 0


def _save_progress(n):
    try:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PROGRESS_FILE.open("w", encoding="utf-8") as f:
            json.dump({"last_completed": int(n)}, f)
    except OSError:
        pass


def _wipe_data():
    """Apaga e recria os diretórios de dados — usado no 'recomeçar do zero'."""
    for rel in DATA_DIRS:
        d = PROJECT_ROOT / rel
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)


def _reset_pipeline_state(start_index=0):
    total = max(len(PIPELINE_STEPS), 1)
    with _lock:
        PIPELINE["running"] = True
        PIPELINE["finished"] = False
        PIPELINE["error"] = None
        PIPELINE["progress"] = round(start_index / total * 100)
        PIPELINE["logs"] = []
        PIPELINE["steps"] = [
            {**s, "state": "done" if i < start_index else ""}
            for i, s in enumerate(build_pipeline_steps())
        ]


def _log(log_type, text):
    with _lock:
        PIPELINE["logs"].append({
            "t": datetime.now().strftime("%H:%M:%S"),
            "type": log_type,
            "text": text,
        })


def _set_step(idx, state):
    with _lock:
        if 0 <= idx < len(PIPELINE["steps"]):
            PIPELINE["steps"][idx]["state"] = state


def _run_pipeline_thread(start_index=0):
    total = max(len(PIPELINE_STEPS), 1)
    if start_index > 0:
        _log("info", f"▶ Retomando o pipeline a partir da etapa {start_index + 1}")
    else:
        _log("info", "▶ Pipeline iniciado")
    try:
        for i, (step_name, script_path) in enumerate(PIPELINE_STEPS):
            if i < start_index:
                continue  # etapa já concluída em execução anterior
            _set_step(i, "active")
            _log("info", f"■ {step_name}")
            _log("", f"Running: {script_path}")

            proc = Popen(
                [sys.executable, "-u", str(script_path)],
                stdout=PIPE, stderr=STDOUT, text=True, bufsize=1,
                cwd=str(PROJECT_ROOT), encoding="utf-8", errors="replace",
            )
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip("\n")
                if line.strip():
                    _log("", line)
            proc.stdout.close()
            proc.wait()

            if proc.returncode != 0:
                _set_step(i, "")
                raise RuntimeError(f"Falha na etapa: {step_name}")

            _set_step(i, "done")
            _save_progress(i + 1)
            with _lock:
                PIPELINE["progress"] = round((i + 1) / total * 100)
            _log("ok", f"✓ {step_name} concluída")

        with _lock:
            PIPELINE["progress"] = 100
        _log("ok", "✓ Concluído. Vá para Resultados para inspecionar os clusters.")
    except Exception as e:  # noqa: BLE001 — qualquer falha vira log visível
        with _lock:
            PIPELINE["error"] = str(e)
        _log("warn", f"✕ {e}")
    finally:
        with _lock:
            PIPELINE["running"] = False
            PIPELINE["finished"] = True


def _start_pipeline(mode="resume"):
    with _lock:
        if PIPELINE["running"]:
            return False

    total = len(PIPELINE_STEPS)
    if mode == "restart":
        _wipe_data()        # apaga raw/processed/checkpoints/output
        _save_progress(0)   # recria o arquivo de progresso zerado
        start_index = 0
    else:  # resume — continua da etapa que parou
        start_index = _load_progress()
        if start_index >= total:
            start_index = 0  # tudo já concluído -> executa de novo

    _reset_pipeline_state(start_index)
    threading.Thread(
        target=_run_pipeline_thread, args=(start_index,), daemon=True
    ).start()
    return True


# ─────────────────────────────────────────────────────────────
# HTTP handler
# ─────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silencia o log padrão (ruidoso)

    # -------- helpers --------
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, rel_path):
        # impede path traversal
        target = (PROJECT_ROOT / rel_path).resolve()
        if PROJECT_ROOT not in target.parents and target != PROJECT_ROOT:
            self.send_error(403)
            return
        if not target.is_file():
            self.send_error(404)
            return
        ctype = STATIC_CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # -------- routes --------
    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/" or path == "/index.html":
            self._send_file("Apuracao.html")
            return
        if path == "/api/data":
            try:
                data = build_app_data(RESULT_FILE, PROCESSED_PATH)
                self._send_json(data)
            except Exception as e:  # noqa: BLE001
                self._send_json({"hasData": False, "error": str(e)}, status=500)
            return
        if path == "/api/pipeline/status":
            last_completed = _load_progress()
            with _lock:
                self._send_json({
                    "running": PIPELINE["running"],
                    "finished": PIPELINE["finished"],
                    "error": PIPELINE["error"],
                    "progress": PIPELINE["progress"],
                    "logs": list(PIPELINE["logs"]),
                    "steps": list(PIPELINE["steps"]),
                    "lastCompleted": last_completed,
                    "totalSteps": len(PIPELINE_STEPS),
                })
            return

        # estáticos: /app/..., /logoofcapudados.png, etc.
        self._send_file(path.lstrip("/"))

    def do_POST(self):
        parts = self.path.split("?", 1)
        path = parts[0]
        if path == "/api/pipeline/start":
            qs = parse_qs(parts[1]) if len(parts) > 1 else {}
            mode = qs.get("mode", ["resume"])[0]
            if mode not in ("resume", "restart"):
                mode = "resume"
            started = _start_pipeline(mode)
            self._send_json({"started": started})
            return
        self.send_error(404)


def main():
    print("=" * 56)
    print("  Apuração · Agita Comunicação")
    print(f"  Servindo em  http://{HOST}:{PORT}")
    print("  (Ctrl+C para encerrar)")
    print("=" * 56)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
