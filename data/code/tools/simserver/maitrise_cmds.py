"""
SYMBIOSE — tools/simserver/maitrise_cmds.py
Commandes pont d'OBSERVATION (survol) et de DEBUG (retour F5 voix narratives).
Mixin de `SimServer`, sœur de `VoixMixin` mais côté ÉCRITURE (bornée à l'état
JOUEUR : maîtrise, pages, Vigueur de découverte — jamais le cœur écolo).

INVARIANT « Godot bête » : le C# envoie ce qu'il a (le NOM DE CLASSE de la plante
survolée, un `op` de debug) ; toute la logique (résolution nom→clé, forçage de
palier, révélation de page) vit en Python. Golden intact (pont opt-in, hors tick).
"""
from __future__ import annotations

from constants import PLOT_CM
from sim.signes import observer_signe, appris as signes_appris
from sim.signes_corpus import SIGNES, FAUNE_VU
from sim import signes_corpus as SC
from sim.champignon_encyclo import FICHES_CHAMPIGNON
from fields.population.perception import CARPO_DENS_REF
from .maitrise_pont import observer_espece, _CLE_DE_NOM
from . import debug_pont as D


class MaitriseCmdsMixin:
    """Commandes `observer` (survol) et `debug` (raccourcis de test)."""

    def cmd_observer(self, msg: dict) -> dict:
        """Observation par SURVOL (retour F5) : `msg.species` = nom de classe de la
        plante survolée (côté C#). Découvre l'espèce (idempotent). Écriture bornée à
        l'état joueur.

        Champ OPTIONNEL `signe` (PLANTE ASSEMBLÉE ⑥, rétro-compatible) : la plante
        survolée porte ce signe VISIBLE au palier courant → note au carnet (ledger),
        dédupliquée par (espèce, signe, saison). Lieu optionnel : `tile` + `x_cm`/
        `y_cm` (position de la plante, résolue en plot-foyer). Réponse enrichie de
        `signe_note` (True ssi une note a été écrite).

        INFO-BULLE DU VIVANT ③ (0.5.48, rétro-compatible) : pour une bête ou le
        champignon (clé non-plante), la réponse porte aussi `appris` (même forme
        que `player.appris` du snapshot, LECTURE PURE) — si ce survol vient de
        franchir le palier du nom, la vue nomme la bête sans attendre le snapshot.

        SOL QUI RESPIRE ⑤ (0.5.53) : `species` peut être une CLÉ D'ESPÈCE FONGIQUE
        (7ᵉ champ du carpophore) ; le lieu optionnel (`tile` + `x_cm`/`y_cm`) situe
        alors la fructification notée au carnet."""
        if self.engine is None:
            return {"ok": False, "error": "observer avant init"}
        species = msg.get("species")
        if not species:
            return {"ok": False, "error": "observer sans species"}
        gs = self.engine.game_state
        nouveau = observer_espece(gs, gs["current_player"], species, gs["week"] - 1,
                                  zone=self._zone(msg))
        rep = {"ok": True, "observed": bool(nouveau)}
        if species not in _CLE_DE_NOM:   # bête ou champignon : crédit saisonnier possible
            rep["appris"] = signes_appris(gs, gs["current_player"])
        signe = msg.get("signe")
        if signe:
            rep["signe_note"] = self._noter_signe(gs, msg, species, signe)
        return rep

    @staticmethod
    def _noter_signe(gs: dict, msg: dict, species: str, signe: str) -> bool:
        """Note de signe au ledger (⑥) : nom de classe → clé catalogue (résolution
        Python, « Godot bête ») ; nom inconnu ou signe hors corpus → aucune note.
        Semaine = la dernière simulée (`week - 1`, convention de `consigner`)."""
        espece = _CLE_DE_NOM.get(species)
        if espece is None:
            return False
        return observer_signe(gs, gs["current_player"], espece, signe,
                              MaitriseCmdsMixin._zone(msg), gs["week"] - 1)

    @staticmethod
    def _zone(msg: dict) -> tuple:
        """Lieu optionnel d'un survol : `tile` (+ `x_cm`/`y_cm` → plot-foyer), ou ()."""
        if msg.get("tile") is None:
            return ()
        if msg.get("x_cm") is not None and msg.get("y_cm") is not None:
            return (msg["tile"], int(msg["y_cm"] // PLOT_CM), int(msg["x_cm"] // PLOT_CM))
        return (msg["tile"],)

    def cmd_legende(self, msg: dict) -> dict:
        """Légende des signes (⑥), LECTURE SEULE et statique (corpus, pas d'état) :
        ce que l'info-bulle ⑦ montre AVANT apprentissage — `signes: {signe: {vu,
        concept, cause}}` et `faune: {bête: vu}`. La vue la demande une fois ; ce qui
        est appris arrive au snapshot (`player.appris`). Utilisable avant `init`.
        `cause` (⑦) = le NOM de la cause, tête de la fiche niveau 2 (« Chlorose
        ferrique : … ») — l'info-bulle ne l'affiche qu'une fois le signe APPRIS.

        INFO-BULLE DU VIVANT ① (clés AJOUTÉES, rétro-compatible) : `faune_role`
        {bête: rôle}, `champignon {vu, roles{b,r,h}}`, `voix_saine {franc, automne,
        terne}`, `abondance {libelles, quelques, nombreuses}` (bornes en nombre de
        bêtes vues dans le plot), `nourriture {libelles, suffisante, abondante}`
        (bornes MESURÉES sur `activite`), `reseau {libelles, dense}` (densité).
        SOL QUI RESPIRE ⑤ : `champignons {clé: vu}` — ce qu'on voit de CHAQUE espèce
        avant son nom (ni nom ni comestibilité : ceux-là n'arrivent qu'avec
        `player.appris.champignons`, une fois l'espèce nommée)."""
        return {"ok": True,
                "signes": {s: {"vu": c["vu"], "concept": c["concept"],
                               "cause": c["fiche"][2].split(" : ", 1)[0]}
                           for s, c in SIGNES.items()},
                "faune": dict(FAUNE_VU),
                "faune_role": dict(SC.FAUNE_ROLE),
                "champignon": {"vu": SC.CHAMPIGNON_VU,
                               "roles": dict(SC.CHAMPIGNON_ROLE)},
                "champignons": {k: f["vu"] for k, f in FICHES_CHAMPIGNON.items()},
                "voix_saine": dict(SC.VOIX_SAINE),
                "abondance": {"libelles": dict(SC.ABONDANCE),
                              "quelques": SC.ABONDANCE_QUELQUES,
                              "nombreuses": SC.ABONDANCE_NOMBREUSES},
                "nourriture": {"libelles": dict(SC.NOURRITURE),
                               "suffisante": SC.NOURRITURE_SUFFISANTE,
                               "abondante": SC.NOURRITURE_ABONDANTE},
                "reseau": {"libelles": dict(SC.RESEAU), "dense": CARPO_DENS_REF}}

    def cmd_debug(self, msg: dict) -> dict:
        """Raccourcis DEBUG (F5) : `msg.op` ∈ {palier3, observer_tout, reset}.
        Hors golden (pont opt-in). Étiqueté debug côté vue."""
        if self.engine is None:
            return {"ok": False, "error": "debug avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        op = msg.get("op")
        if op == "palier3":
            return {"ok": True, "op": op, "objets": D.forcer_palier_3(gs, player)}
        if op == "observer_tout":
            return {"ok": True, "op": op,
                    "decouvertes": D.observer_toutes_presentes(gs, player)}
        if op == "reset":
            D.reset_maitrise(gs, player)
            return {"ok": True, "op": op}
        return {"ok": False, "error": f"op debug inconnue : {op!r}"}
