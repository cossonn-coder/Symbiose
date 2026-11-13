"""
SYMBIOSE — tools/simserver/automate_cmd.py
Commande pont du JARDINIER AUTOMATE (sprint jardinier_auto ⑥, vue Godot). Mixin de
`SimServer`, sœur des commandes de contrôle (palette/maitrise) : elle branche
l'automate déterministe (paquet `tools.jardinier_auto`) en OPTION F5, sans jamais
toucher au moteur.

INVARIANT H2 — l'automate joue ENTRE deux ticks, côté APPELANT : le hook réel vit
dans `cmd_step_week` (commands.py), qui appelle `self._automate.jouer_tick(engine)`
APRÈS `tick_semaine()`. Ici on ne fait que MONTER/DÉMONTER l'automate et lui pousser
des objectifs — jamais exécuter la boucle. Opt-in strict : sans `automate on`,
`self._automate` reste None → comportement F5 inchangé, snapshot inchangé, golden
INTACT (le golden tourne hors serveur, ce chemin n'existe jamais pour lui).

INVARIANT « Godot bête » : la vue envoie l'INTENTION (activer, régler le profil,
poser un objectif) ; toute la logique (tutelle, table facteur→geste, comptabilité)
vit en Python. La vue LIT ensuite le bloc `automate` du snapshot (serialize.py) et
se contente de le METTRE EN PAGE (journal/impasses + onglet objectifs).
"""
from __future__ import annotations

from tools.jardinier_auto import (JardinierAutomate, ProfilAutomate, LIBRE,
                                   marquer_jardin_cultive, Objectif,
                                   ajouter_objectif)
from tools.jardinier_auto.trace import CLE_JOURNAL
from tools.jardinier_auto.objectifs import CLE_OBJECTIFS
from bancs import BANC_PLAN_TEST
from bancs.plan_test import resoudre_plan

# Fenêtre de trace exposée au snapshot : les N dernières entrées du journal
# (gestes, impasses, conséquences). Borne le volume — un run F5 long accumule des
# milliers d'entrées, la vue n'a besoin que du défilé récent (confort de débogage).
TRACE_MAX = 60

# Champs REÇUS pour composer un ProfilAutomate (les autres sont ignorés). Miroir de
# la dataclass `ProfilAutomate` : on ne construit qu'avec des clés qu'elle connaît.
_PROFIL_CHAMPS = ("perception", "paie_vigueur", "credite_maitrise",
                  "desherbage", "part_recoltee", "ecrit_carnet")


def _profil_depuis(msg_profil: dict) -> ProfilAutomate:
    """Construit un `ProfilAutomate` depuis le dict envoyé par la vue. Défaut =
    preset LIBRE (aucune comptabilité, l'automate tient le jardin « pour voir »),
    surchargé champ par champ. Les clés inconnues sont ignorées (robustesse pont)."""
    base = {c: getattr(LIBRE, c) for c in _PROFIL_CHAMPS}
    for c in _PROFIL_CHAMPS:
        if c in msg_profil:
            base[c] = msg_profil[c]
    return ProfilAutomate(**base)


def _profil_dict(profil: ProfilAutomate) -> dict:
    """Aplati un profil en dict JSON-sérialisable (renvoyé au snapshot + à l'ACK)."""
    return {c: getattr(profil, c) for c in _PROFIL_CHAMPS}


class AutomateCmdMixin:
    """Commande `automate` : monte/démonte l'automate et pousse des objectifs.

    Ops :
      - `on`     : active l'automate avec `msg.profil` (dict, défaut LIBRE). DÉCLARE
                   le jardin courant comme cultivé (tutelle=cultivées, hors tick) →
                   l'automate soigne les cultivées, pas les férales.
      - `off`    : désactive (l'automate cesse de jouer, la trace reste lisible).
      - `objectif`: pousse un objectif `(geste, quantite, cible, id)` en phase de
                   planification (temps figé). Injectable à tout moment.
      - `status` : état courant (actif + profil) sans rien muter.
    """

    def cmd_automate(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "automate avant init"}
        op = msg.get("op")
        if op == "on":
            profil = _profil_depuis(msg.get("profil", {}))
            self._automate = JardinierAutomate(profil)
            self._automate_profil = profil
            # Tutelle=cultivées : sans déclaration, personne n'est sous tutelle (le
            # monde `full` ne marque personne). On déclare le jardin initial ICI,
            # HORS TICK — les férales de succession resteront hors du set.
            n = marquer_jardin_cultive(self.engine, self.engine.game_state["current_player"])
            return {"ok": True, "op": op, "actif": True,
                    "profil": _profil_dict(profil), "cultivees": n}
        if op == "off":
            self._automate = None
            return {"ok": True, "op": op, "actif": False}
        if op == "objectif":
            obj = Objectif(geste=msg.get("geste"), quantite=int(msg.get("quantite", 1)),
                           cible=msg.get("cible"), id=msg.get("id") or msg.get("cible"))
            ajouter_objectif(self.engine.game_state, obj)
            return {"ok": True, "op": op, "id": obj.id}
        if op == "status":
            actif = getattr(self, "_automate", None) is not None
            profil = getattr(self, "_automate_profil", None)
            return {"ok": True, "op": op, "actif": actif,
                    "profil": _profil_dict(profil) if profil else None}
        return {"ok": False, "error": f"op automate inconnue : {op!r}"}

    # ---------------------------------------------------------------- snapshot
    def automate_block(self, gs: dict) -> dict:
        """Bloc `automate` du snapshot (appelé par serialize.py SI l'automate est
        actif). PURE lecture de l'état déjà écrit par la boucle : la trace récente
        (gestes/impasses/conséquences, déjà des dicts JSON) + les objectifs actifs
        et leur progression. La vue filtre la trace par `objectif_id` pour composer
        l'onglet d'un objectif — aucune machinerie neuve côté serveur (§8)."""
        journal = gs.get(CLE_JOURNAL, [])
        reg = gs.get(CLE_OBJECTIFS, {})
        objectifs = [{"id": oid,
                      "geste": reg[oid]["objectif"].geste,
                      "quantite": reg[oid]["objectif"].quantite,
                      "cible": reg[oid]["objectif"].cible,
                      "progression": reg[oid]["progression"],
                      "accompli": reg[oid]["semaine_fin"] is not None}
                     for oid in sorted(reg)]
        return {"actif": True,
                "profil": _profil_dict(self._automate_profil),
                "trace": journal[-TRACE_MAX:],
                "objectifs": objectifs}

    # ---------------------------------------------------------------- testeur
    def cmd_plan_test(self, msg: dict) -> dict:
        """MODE TESTEUR (gestes lisibles ⑤) — LECTURE du plan de test du banc `msg.banc`
        (registre `BANC_PLAN_TEST`), RÉSOLU sur le monde courant : `[{verbe, geste, maj,
        cible, clics}]`, `clics` = points MONDE (cm) à cliquer dans l'ordre. La vue
        déroule ensuite chaque geste par le chemin du clic joueur (`action`) : ce n'est
        PAS l'automate (aucune décision ici, aucune écriture). Banc sans plan → `[]`."""
        if self.engine is None:
            return {"ok": False, "error": "plan_test avant init"}
        banc = msg.get("banc")
        plan = BANC_PLAN_TEST.get(banc, ())
        return {"ok": True, "banc": banc,
                "plan": resoudre_plan(self.engine.game_state, plan)}
