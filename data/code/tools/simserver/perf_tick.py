"""
SYMBIOSE — tools/simserver/perf_tick.py
Sonde d'un tick : OÙ est passé le temps, et le moteur calculait-il seulement ?

📖 Le rapport perf disait « s921 : 62 s » sans permettre de trancher entre la
simulation et la machine (veille, autre processus, mémoire saturée). Chaque mesure
ci-dessous répond à une hypothèse précise :

  - `cpu_ms` : temps de calcul du processus (`process_time`). Durée du tick très
    au-dessus du CPU → le moteur ATTENDAIT : la machine l'a privé de processeur.
  - `gc_ms`, `gc_passes`, `gc_gen2` : temps passé dans le ramasse-miettes.
  - `defauts_page` : sursaut par rapport aux autres ticks → mémoire saturée. Sous
    Linux ce sont les défauts majeurs, sous Windows tous les défauts : ne comparer
    qu'à machine égale.
  - `phases`, `feuilles` : un fil annexe relève la pile du moteur toutes les 50 ms.
    `phases` = la fonction appelée par `tick_semaine`, `feuilles` = celle qui tournait.
    On échantillonne plutôt qu'on instrumente : aucune ligne du moteur ne change, et
    le coût ne dépend pas du nombre d'appels, contrairement à cProfile.
  - `echantillons` / `attendus` : très en dessous → le processus entier était gelé.
  - `machine` : charge de la machine et CPU de Godot pendant le tick, pour nommer ce
    qui prenait le processeur quand le moteur attendait (`charge_machine.py`, D127).

⚠️ Limites constatées au rejeu du 2026-11-04 :
  - un CPU élevé ne prouve PAS une cause dans la simulation. Une machine chargée le
    gonfle aussi : s260 a pris 9 763 ms puis 1 101 ms au rejeu suivant, identique par
    déterminisme [n=2 rejeux, VM chargée puis moins]. L'indice est alors une hausse
    répartie sur toutes les phases. Seul un rejeu tranche.
  - `echantillons` / `attendus` tourne autour de 0,7 sur un tick normal [n=5 ticks, VM] :
    la période réelle dépasse 50 ms. N'y voir un gel que très en dessous.

Golden NEUTRE : le golden tourne hors serveur. Le fil ne fait que lire des piles.
"""
from __future__ import annotations

import gc
import os
import sys
import threading
import time
from collections import Counter

from . import charge_machine
from .perf import defauts_de_page

PERIODE_S = 0.05
TOP_N = 5   # lignes gardées par classement : le rapport reste lisible


def _nom(code) -> str:
    """`fichier.fonction` : `run` ou `tick` seuls ne diraient pas où chercher."""
    return f"{os.path.splitext(os.path.basename(code.co_filename))[0]}.{code.co_name}"


class SondeTick:
    """Encadre un tick : `debut()`, le tick, puis `fin()` qui rend les mesures."""

    def __init__(self):
        self._actif = threading.Event()
        self._fil = None
        self._fil_tick = 0
        self._phases: Counter = Counter()
        self._feuilles: Counter = Counter()
        self._gc_ms = 0.0
        self._gc_passes = 0
        self._gc_gen2 = 0
        self._gc_t0 = 0.0
        gc.callbacks.append(self._sur_gc)

    def debut(self) -> None:
        self._fil_tick = threading.get_ident()
        self._phases = Counter()
        self._feuilles = Counter()
        self._gc_ms = 0.0
        self._gc_passes = self._gc_gen2 = 0
        self._defauts0 = defauts_de_page()
        self._heure = time.strftime("%H:%M:%S")
        self._machine0 = charge_machine.releve()
        self._cpu0 = time.process_time()
        self._mur0 = time.perf_counter()
        self._actif.set()
        if self._fil is None:   # lancé au premier tick : le golden n'en a jamais
            self._fil = threading.Thread(target=self._boucle, daemon=True,
                                         name="sonde-tick")
            self._fil.start()

    def fin(self) -> dict:
        mur = time.perf_counter() - self._mur0
        cpu = time.process_time() - self._cpu0
        machine = charge_machine.bilan(self._machine0, charge_machine.releve(), cpu)
        self._actif.clear()
        defauts = defauts_de_page()
        n = sum(self._phases.values())
        return {
            "heure": self._heure,
            "cpu_ms": round(cpu * 1000.0, 1),
            "gc_ms": round(self._gc_ms, 1),
            "gc_passes": self._gc_passes,
            "gc_gen2": self._gc_gen2,
            "defauts_page": (None if defauts is None or self._defauts0 is None
                             else defauts - self._defauts0),
            "echantillons": n,
            "attendus": int(mur / PERIODE_S),
            "phases": _classement(self._phases, n),
            "feuilles": _classement(self._feuilles, n),
            "machine": machine,
        }

    def _sur_gc(self, etape: str, info: dict) -> None:
        if not self._actif.is_set():
            return
        if etape == "start":
            self._gc_t0 = time.perf_counter()
            return
        self._gc_ms += (time.perf_counter() - self._gc_t0) * 1000.0
        self._gc_passes += 1
        if info.get("generation") == 2:
            self._gc_gen2 += 1

    def _boucle(self) -> None:
        while True:
            self._actif.wait()
            time.sleep(PERIODE_S)
            if self._actif.is_set():
                self._echantillonner()

    def _echantillonner(self) -> None:
        cadre = sys._current_frames().get(self._fil_tick)
        if cadre is None:
            return
        feuille = _nom(cadre.f_code)
        phase, fils = "hors tick", None
        while cadre is not None:
            if cadre.f_code.co_name == "tick_semaine":
                phase = _nom(fils or cadre.f_code)
                break
            fils, cadre = cadre.f_code, cadre.f_back
        self._phases[phase] += 1
        self._feuilles[feuille] += 1


# Une seule sonde par processus : un nouvel `init` ne doit empiler ni fil ni rappel GC.
SONDE_TICK = SondeTick()


def _classement(compte: Counter, total: int) -> list:
    """[[nom, part en %], …] du plus coûteux au moins coûteux, liste pour le JSON."""
    return [[nom, round(100.0 * k / total)] for nom, k in compte.most_common(TOP_N)]
