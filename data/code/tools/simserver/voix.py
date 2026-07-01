"""
SYMBIOSE — tools/simserver/voix.py
Les 4 commandes READ-ONLY des voix narratives (sprint UI voix narratives ①).
Spec de référence : `docs/conception/CONCEPTION_VOIX_NARRATIVES_UI.md` §3.

Mixin de `SimServer` : une commande de protocole par voix (`carnet`,
`encyclopedie`, `pages`, `magazine`). Chacune LIT `gs["current_player"]`, appelle
la fonction de la voix (déjà écrite, moteur Voix narratives) et sérialise son
retour — RIEN de plus. Aucune logique de simulation, aucun tick.

INVARIANT « Godot bête » (§1) : on relaie le corpus VERBATIM. Le pont ne concatène
pas, ne reformule pas, ne trie pas « intelligemment » — il transporte des
listes/dicts que la vue mettra en page. Le registre (naturaliste / téléologique)
est porté par le CORPUS Python, jamais par la couche vue.

Toutes ces commandes sont PURES (lecture seule) : sans couche voix / sans joueur
découvert, elles renvoient des structures vides (jamais de crash) — miroir du
no-op golden de chaque module de voix.
"""
from __future__ import annotations

from sim.carnet import carnet_lire
from sim.encyclopedie import encyclopedie_index, encyclopedie_lire
from sim.magazine import magazine_offres, magazine_fiche
from sim.pages import pages_trouvees
from sim.pages_corpus import PAGES, ORDRE


class VoixMixin:
    """Les 4 commandes de consultation des voix narratives (read-only)."""

    def cmd_carnet(self, msg: dict) -> dict:
        """Carnet auto FORMATÉ du joueur courant (§3). `msg.filtre` optionnel
        (`{concept|zone|saison}`) transmis TEL QUEL à `carnet_lire`."""
        if self.engine is None:
            return {"ok": False, "error": "carnet avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        return {"ok": True, "entrees": carnet_lire(gs, player, filtre=msg.get("filtre"))}

    def cmd_encyclopedie(self, msg: dict) -> dict:
        """Encyclopédie du joueur courant (§3) : `msg.espece` → la fiche tronquée
        au palier (N1/N2/N3) ou `null` si non découverte ; sinon l'INDEX des
        espèces découvertes (ordre du corpus)."""
        if self.engine is None:
            return {"ok": False, "error": "encyclopedie avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        espece = msg.get("espece")
        if espece:
            return {"ok": True, "fiche": encyclopedie_lire(gs, player, espece)}
        return {"ok": True, "index": encyclopedie_index(gs, player)}

    def cmd_pages(self, msg: dict) -> dict:
        """Pages secrètes TROUVÉES par le joueur courant (§3) : les ids (ordre du
        corpus, filtré aux trouvées) + le texte VERBATIM de chacune (voix/concept/
        texte du corpus). Coffret du grenier — read-only pur."""
        if self.engine is None:
            return {"ok": False, "error": "pages avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        trouvees = pages_trouvees(gs, player)
        # ORDRE = ordre éditorial du corpus ; on garde CE tri (pas d'invention),
        # restreint aux pages effectivement révélées. `sorted(trouvees)` figerait
        # un ordre alphabétique arbitraire — l'ORDRE du corpus est l'ordre voulu.
        ids = [pid for pid in ORDRE if pid in trouvees]
        pages_out = [{"id": pid, "voix": PAGES[pid]["voix"],
                      "concept": PAGES[pid]["concept"], "texte": PAGES[pid]["texte"]}
                     for pid in ids]
        return {"ok": True, "ids": ids, "pages": pages_out}

    def cmd_magazine(self, msg: dict) -> dict:
        """Magazine de botanique (§3) : `msg.espece` → la fiche PRODUIT (N1+N2, PAS
        de gs/player — argument de vente indépendant du palier joueur) ou `null` ;
        sinon les OFFRES (sœurs des familles maîtrisées, hors banque)."""
        if self.engine is None:
            return {"ok": False, "error": "magazine avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        espece = msg.get("espece")
        if espece:
            return {"ok": True, "fiche": magazine_fiche(espece)}
        return {"ok": True, "offres": magazine_offres(gs, player)}
