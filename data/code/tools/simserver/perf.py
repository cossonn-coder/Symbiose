"""
SYMBIOSE — tools/simserver/perf.py
Banc d'observation perf (sprint « stabilisation perf en run éternel », tronçon ④).

Petit assembleur du bloc `perf` du snapshot : trois observables PUR-LECTURE que
l'overlay debug F4 côté Godot affiche pour vérifier, EN JEU, que la stabilisation
③ tient — que `N plantes` PLAFONNE et que `ms/tick` ne DÉRIVE plus d'année en
année (le crash du monde complet venait de N non borné, cf. 00_etat ①/③).

Règle d'or du serveur : ADAPTATEUR, pas moteur. Ce module n'écrit RIEN dans la
simulation — il lit une durée déjà chronométrée AUTOUR du tick (commands.py),
compte les plantes du snapshot et interroge l'OS pour la mémoire du process.
Golden NEUTRE par construction : le golden tourne hors serveur, ce bloc n'existe
jamais pour lui.
"""
from __future__ import annotations

import json
import os
import platform
import sys

# `resource` est POSIX-only. La VM (Debian) et la cible de jeu (le F5 de Nico)
# l'ont ; on blinde tout de même l'import pour ne jamais casser le snapshot si un
# jour le serveur tourne sur une plateforme sans (RSS devient simplement None).
try:
    import resource
except ImportError:            # pragma: no cover — plateforme non-POSIX
    resource = None


def rss_mo() -> float | None:
    """Mémoire résidente (RSS) du process serveur, en méga-octets — ou None si
    la plateforme ne l'expose pas.

    `ru_maxrss` est le PIC de RSS depuis le lancement (choix assumé, cf. le
    profileur ① `tools/profile_memoire.py` qui utilise la même source) : sur
    Linux il est en KILO-octets → /1024 pour des Mo. C'est l'observable qui doit
    se STABILISER une fois N borné (③) : si elle grimpe encore linéairement à N
    constant, c'est une fuite à re-investiguer (mais ① n'en a trouvé aucune)."""
    if resource is None:
        return None
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(kb / 1024.0, 1)


def perf_block(ms_tick: float | None, n_plants: int) -> dict:
    """Assemble le bloc `perf` du snapshot. `ms_tick` = durée du dernier
    tick_semaine() mesurée par commands.py (None tant que rien n'a été simulé —
    ex. le snapshot post-init) ; `n_plants` = plantes VIVANTES du snapshot ;
    `rss_mo` = pic RSS du serveur. Arrondis d'instrument, déterministes en
    valeur (la mesure de temps/mémoire ne l'est pas — c'est un compteur debug,
    hors golden)."""
    return {
        "ms_tick": None if ms_tick is None else round(ms_tick, 1),
        "n_plants": n_plants,
        "rss_mo": rss_mo(),
    }


def interpreteur() -> dict:
    """Quel Python fait tourner le moteur (FLUIDITÉ PC ①, D116) : version et
    exécutable lancés par le pont. Au PC de Nico, `python` peut être un autre
    interpréteur que celui de la VM (version, build) — le rapport de banc doit le
    dire pour comparer les ticks. Binaire gelé (PyInstaller) : `executable` = le
    binaire lui-même. Lu UNE fois à l'init → coût nul, golden NEUTRE (hors tick)."""
    return {"version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable}


# --- Capture des pires ticks (demande Nico 2026-07-05) -----------------------
# « La simu sauvegarde les perfs les plus mauvaises (ticks les plus longs) et
# l'état global à ce moment. » Objectif : investiguer QUELLE configuration coûte
# cher sans rejouer six ans à la main. Deux étages complémentaires :
#   - le PROFILEUR headless (tools/profile_monde.py) dit quelle PHASE coûte ;
#   - ce traqueur dit, EN JEU, quelle CONFIGURATION (compteurs par tuile/espèce/
#     segments) accompagnait le pire tick. Dump diagnostique LÉGER, non
#     rechargeable (choix Nico) — assez pour comprendre, pas pour recharger.
# Purement observationnel côté serveur → golden NEUTRE (le golden tourne hors
# serveur, ce code n'existe jamais pour lui).

# Dossier des dumps sur disque (artefacts runtime, gitignorés). Relatif au cwd du
# serveur (data/code/, cf. lancement du pont).
PERF_DUMP_DIR = "perf_dumps"


def diagnostic(engine, ms_tick: float) -> dict:
    """État global CONDENSÉ au tick courant : de quoi comprendre pourquoi il a
    coûté cher (répartition des plantes et des segments — les deux moteurs du
    coût lumière+empreintes, cf. profile_monde). Lit directement `game_state`
    (pas le snapshot sérialisé) : self-suffisant et bon marché. Appelé RAREMENT
    (nouveau record uniquement) → coût négligeable, `len(p.segments)` = O(1)."""
    gs = engine.game_state
    # Le tick mesuré est la semaine qu'on VIENT de simuler : `week` est déjà
    # incrémenté (boucle.py) → la semaine du tick est `week - 1` (cf. commands.py).
    week = gs["week"] - 1
    par_tuile: dict[str, dict] = {}
    par_espece: dict[str, int] = {}
    n_plants = n_segments = 0
    for tile in gs["tiles"]:
        tp = ts = 0
        for p in tile.plants:
            if not p.is_alive:
                continue
            tp += 1
            ts += len(p.segments)
            nom = p.plant_class.__name__
            par_espece[nom] = par_espece.get(nom, 0) + 1
        par_tuile[tile.tile_id] = {"plants": tp, "segments": ts}
        n_plants += tp
        n_segments += ts
    return {
        "ms_tick": round(ms_tick, 1),
        "week": week, "year": (week - 1) // 52 + 1,
        "n_plants": n_plants, "n_segments": n_segments,
        "rss_mo": rss_mo(),
        "par_tuile": par_tuile,
        # Espèces triées par abondance décroissante : le coupable saute aux yeux.
        "par_espece": dict(sorted(par_espece.items(), key=lambda kv: -kv[1])),
    }


class WorstTicks:
    """Garde en mémoire les K pires ticks (durée décroissante), chacun avec son
    dump diagnostique. Chaque NOUVEAU record absolu est aussi écrit sur disque
    (JSON lisible) pour analyse hors ligne. Mémoire bornée à K → coût run-éternel
    nul. Alimenté après chaque tick par `consider`."""

    def __init__(self, k: int = 5):
        self.k = k
        self.dumps: list[dict] = []   # triés par ms_tick décroissant

    def consider(self, ms_tick: float | None, engine) -> dict | None:
        """Soumet la durée du dernier tick. Ne construit le dump (coûteux) QUE si
        le tick entre dans le top-K — les ticks ordinaires ne paient rien. Écrit
        sur disque seulement pour un nouveau record ABSOLU (rang 0) → peu de
        fichiers, chacun un vrai pire cas. Retourne le dump créé, ou None."""
        if ms_tick is None:
            return None
        # Rejeté d'emblée s'il ne bat même pas la moins pire des K entrées.
        if len(self.dumps) >= self.k and ms_tick <= self.dumps[-1]["ms_tick"]:
            return None
        is_record = not self.dumps or ms_tick > self.dumps[0]["ms_tick"]
        dump = diagnostic(engine, ms_tick)
        self.dumps.append(dump)
        self.dumps.sort(key=lambda d: -d["ms_tick"])
        del self.dumps[self.k:]
        if is_record:
            self._persist(dump)
        return dump

    def _persist(self, dump: dict) -> None:
        """Écrit le dump en JSON lisible. Le disque n'est pas critique (le top-K
        mémoire suffit au rapport) → toute erreur d'I/O est avalée."""
        try:
            os.makedirs(PERF_DUMP_DIR, exist_ok=True)
            path = os.path.join(
                PERF_DUMP_DIR,
                f"pire_s{dump['week']:04d}_{int(dump['ms_tick'])}ms.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(dump, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
