"""
SYMBIOSE — tests/simserver/harness.py
Harness partagé des suites du pont : pilote le serveur par les pipes (comme
SimBridge.cs côté Godot), compteur `check`/`_results`, scénario nominal. Importé
par tous les modules de section → ils écrivent dans le MÊME accumulateur, que
l'entrée `test_sim_server.py` agrège pour le bilan final.
"""
import json
import os
import subprocess
import sys

# tests/simserver/harness.py → remonter de 3 dossiers = data/code (racine d'import
# + emplacement de tools/sim_server.py). L'ex-monolithe vivait dans tests/ (2
# remontées) ; ici on en ajoute une pour le sous-paquet.
CODE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER = os.path.join(CODE_DIR, "tools", "sim_server.py")

# Tranche 7 (packaging) : si SIM_SERVER_BIN pointe un binaire gelé
# (PyInstaller), la suite ENTIÈRE tourne contre lui au lieu du script —
# mêmes 87 checks, déterminisme byte-à-byte compris. Sans la variable,
# rien ne change (script + interpréteur courant, comme avant).
SERVER_BIN = os.environ.get("SIM_SERVER_BIN")
SERVER_CMD = [SERVER_BIN] if SERVER_BIN else [sys.executable, SERVER]

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


class ServerProc:
    """Pilote le serveur par les pipes, comme SimBridge.cs le fera côté Godot."""

    def __init__(self):
        self.proc = subprocess.Popen(
            SERVER_CMD, cwd=CODE_DIR,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True)
        self.raw_lines = []          # réponses brutes (pour le déterminisme)

    def send_raw(self, line: str) -> str:
        """Écrit une ligne brute, lit UNE ligne de réponse (protocole 1↔1)."""
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        resp = self.proc.stdout.readline().rstrip("\n")
        self.raw_lines.append(resp)
        return resp

    def send(self, **msg) -> dict:
        return json.loads(self.send_raw(json.dumps(msg)))

    def close(self, timeout=10):
        self.proc.stdin.close()
        return self.proc.wait(timeout=timeout)


def run_scenario(seed: int) -> ServerProc:
    """Le scénario nominal : init → step ×4 → snapshot → quit."""
    s = ServerProc()
    s.send(cmd="init", seed=seed)
    for _ in range(4):
        s.send(cmd="step_week")
    s.send(cmd="snapshot")
    s.send(cmd="quit")
    return s
