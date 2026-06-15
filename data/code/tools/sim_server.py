"""
SYMBIOSE — tools/sim_server.py
Serveur de simulation : le moteur Python derrière un pont JSON stdin/stdout.

Sprint Intégration Godot ↔ Python, tranche 1 (Option B actée : Python = moteur,
Godot = vue). Godot lance ce script en SOUS-PROCESS et lui parle par les pipes —
schéma UART logiciel : stdin = Godot→Python, stdout = Python→Godot, framing par
délimiteur `\n` (1 ligne = 1 message JSON complet, JSON compact n'émet jamais de
`\n` littéral). Maître/esclave strict : Godot envoie une commande, ce serveur
répond UNE ligne, jamais de message spontané → pas de concurrence, déterminisme
préservé.

ADAPTATEUR, pas moteur : on importe le moteur comme le font main.py et
tests/test_golden.py, on ne modifie RIEN de sa logique → golden intact par
construction. Si Godot a besoin d'une donnée absente, on l'ajoute au SNAPSHOT
(lecture seule), jamais au tick.

> Refactor structurel (Sprint refactor global, SS⑤) : ce FICHIER reste l'entrée
> exécutée par Godot (chemin/nom inchangés côté `SimBridge.cs` + `.spec`
> PyInstaller), mais n'est plus qu'un MINCE point d'entrée. La logique vit dans
> le paquet voisin `tools/simserver/` (version, commands, actions, serialize,
> server) — `SimServer`, `main`, `ENGINE_VERSION` y sont ré-exportés.

Protocole v1 (requête → réponse, champ `cmd` obligatoire) :
  → {"cmd": "init", "seed": 42, "config": "smoke"}   # ou "full" (monde 20×20 m)
  ← {"ok": true, "engine_version": "...", "world": {tuiles + maison, statique}}
  → {"cmd": "step_week"}
  ← {"ok": true, "snapshot": {...}}
  → {"cmd": "snapshot"}
  ← {"ok": true, "snapshot": {...}}
  → {"cmd": "action", "verb": "manger", "target": {...}, "params": {...}}
  ← {"ok": true, "result": {"applied": bool, "cost": x, "gain": x,
                            "vigueur": x, "vigueur_max": x, "message": "..."},
     "snapshot": {...}}     # snapshot frais TOUJOURS joint (effet visible en 1 aller-retour)
  → {"cmd": "fields"}                                # mode debug (t6·C)
  ← {"ok": true, "fields": [noms…]}                  # registre découvert
  → {"cmd": "fields", "field": "microbiome"}
  ← {"ok": true, "field": "...", "tiles": {tid: {rows, cols, values}}}
     # values = liste row-major ; le snapshot hebdo n'embarque PAS les
     # grilles (volume) — la vue ne les demande que si l'overlay est ON.
  → {"cmd": "quit"}
  ← {"ok": true}
Cibles d'action (tranche 4, décision kickoff : désignation NON-AMBIGUË, le
serveur fait foi — Godot transmet l'INTENTION, Python possède les RÈGLES) :
  plante : {"tile": "T3", "x_cm": …, "y_cm": …}   # position LOCALE tuile, ±0.1 cm
           (le snapshot n'expose pas d'id moteur et les plantes ne bougent
            jamais : la position EST l'identité — déjà la clé du diff t3)
           + pour `tailler` (tranche 5) : champ OPTIONNEL "segment": i =
           l'index dans `segments` du snapshot (= ordre structure_to_dict(),
           stable et déterministe) — la branche cliquée. Validé ICI (bornes,
           collet protégé) AVANT d'appeler la façade : un segment invalide est
           un refus métier qui ne coûte RIEN. Absent → repli params.cible.
           + pour `ecraser` une PLANTE (volet 2) : MÊME cible position (+ `segment`
           optionnel, mais le collet 0 est ici VALIDE, défaut Q2). Le routage
           plante/guilde se fait sur la FORME du target (Q6) : position → plante.
  plot   : {"tile": "T3", "r": 2, "c": 5}          # becher, ecraser (guilde animale)
  point  : {"tile": "T3", "x_cm": …, "y_cm": …}    # planter, arroser (position LOCALE
           tuile) — résolue en plot-foyer côté serveur (floor(/PLOT_CM)) : les
           gestes de milieu écrivent au plot (banque-sol / champ humidité). Hors
           tuile = refus de désignation (ne coûte rien).
  tuile  : {"tile": "T3"}                          # favoriser_auxiliaire
  rien   : {}                                      # grelinette
  params : {"cible": "apex"|"branche"} (tailler) ; {"urgence": bool} (ecraser —
           true si phase Saison côté vue : la couture préparation/réaction §3.1) ;
           {"species": "clé catalogue"} (planter, OBLIGATOIRE) ; {"urgence": bool}
           ou {"phase": "saison"} (arroser — réaction en phase Saison)
Refus métier (verbe inconnu, cible introuvable, Vigueur insuffisante) →
{"ok": true, "result": {"applied": false, "message": …}} : le geste a échoué
mais le PROTOCOLE a réussi. {"ok": false} reste réservé aux commandes
malformées — même règle v0, le serveur ne crashe jamais et répond toujours.
EOF sur stdin (Godot mort sans `quit`) → sortie propre.

Usage (depuis data/code/, ou n'importe où — bootstrap sys.path ci-dessous) :
  python3 tools/sim_server.py     # puis taper les commandes JSON à la main
  python3 -m tools.sim_server
Test : python3 -m tests.test_sim_server
"""
from __future__ import annotations
import os
import sys

# Bootstrap : lancé en script direct (`python3 tools/sim_server.py`), sys.path[0]
# est tools/ → les imports absolus du moteur (plants, sim, …) échoueraient. On
# remonte à data/code/ comme racine d'import (sans effet en mode -m). DOIT
# précéder l'import de tools.simserver, qui tire transitivement le moteur.
_CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

# API ré-exportée depuis le paquet (compat des importeurs éventuels).
from tools.simserver import SimServer, main, ENGINE_VERSION  # noqa: E402,F401


if __name__ == "__main__":
    sys.exit(main())
