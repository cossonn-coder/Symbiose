"""
SYMBIOSE — tools/simserver/courrier.py
La commande READ-ONLY du COURRIER (quêtes D79, tronçon ⑤) + le DRIVER des quêtes.
Spec : `docs/joueur/automate/conception_quetes.md` (§ vue) ; kickoff
`sprints/joueur/automate/sprint_quetes/05_vue_godot_courrier.md`.

Mixin de `SimServer`, sœur de `voix.py` (mêmes principes) :

  - `cmd_courrier` : commande de protocole read-only qui relaie l'état des lettres
    (`sim.quetes.etat_courrier`) au panneau courrier Godot. « Godot bête » : tout est
    calculé en Python (avancement DIÉGÉTIQUE, coche, atteignabilité) ; la vue met en
    page. Le CHIFFRE exact n'est joint que si `msg.debug` (V2/#5). Ouvrir le panneau
    ÉVALUE les quêtes d'état sur le snapshot courant (hors tick, point d'évaluation
    légitime) — c'est `etat_courrier` qui le fait, pas ce mixin.

  - `avancer_quetes` : le DRIVER, appelé HORS TICK par `cmd_step_week` (après la
    simulation), qui fait VIVRE les quêtes du joueur au fil des semaines —
    ouverture des lettres mûres, clôture des quêtes d'état comblées, versement
    (idempotent) des récompenses. Les quêtes CUMULÉES se closent, elles, au HOOK
    geste (`sim.actions`/`plante_route`), pas ici.

OPT-IN vis-à-vis du golden : le golden écologique tourne HORS serveur (jamais de
`cmd_step_week`/`cmd_courrier`) → ce mixin n'est jamais appelé → golden intact. Les
fonctions moteur sous-jacentes sont elles-mêmes opt-in strict (aucune clé `quetes`
sans lettre posée).
"""
from __future__ import annotations

from sim import quetes


class CourrierMixin:
    """La commande courrier (read-only) + le driver des quêtes (hors tick)."""

    def cmd_courrier(self, msg: dict) -> dict:
        """Les LETTRES du joueur courant (D79 ⑤) : actives + accomplies, avec leur
        avancement DIÉGÉTIQUE et leur coche. `msg.debug` (bool) → joint le chiffre
        exact (progression/condition, mode debug seulement, #5). Read-only côté
        protocole ; l'ouverture peut clore une quête d'état comblée (évaluation
        légitime hors tick), jamais verser de récompense (le driver s'en charge)."""
        if self.engine is None:
            return {"ok": False, "error": "courrier avant init"}
        gs = self.engine.game_state
        lettres = quetes.etat_courrier(gs, debug=bool(msg.get("debug")))
        return {"ok": True, "lettres": lettres}

    def avancer_quetes(self, game_state: dict, player: str) -> None:
        """DRIVER des quêtes, appelé par `cmd_step_week` APRÈS le tick (hors tick,
        côté serveur — opt-in : le golden ne passe jamais par là). Ordre déterministe
        (les fonctions moteur trient les ids en interne) :
          1. `evaluer_declencheurs` — ouvre les lettres du corpus dont le déclencheur
             (palier de maîtrise / jalon de saison) est mûr, dans la limite du plafond ;
          2. `evaluer_etat` — clôt les quêtes d'ÉTAT comblées sur le snapshot courant
             (les cumulées se closent au hook geste, pas ici) ;
          3. `remettre_recompenses` — verse (idempotent) les récompenses des quêtes
             accomplies pas encore honorées.
        No-op strict tant qu'aucune lettre n'est mûre (opt-in) → golden intact."""
        quetes.evaluer_declencheurs(game_state, player)
        quetes.evaluer_etat(game_state)
        quetes.remettre_recompenses(game_state, player)
