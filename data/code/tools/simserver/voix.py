"""
SYMBIOSE — tools/simserver/voix.py
Les 4 commandes READ-ONLY des voix narratives (sprint UI voix narratives ①).
Spec de référence : `docs/narration/voix/conception_voix_narratives_ui.md` §3.

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
from sim.magazine import magazine_offres, magazine_fiche, magazine_articles
from sim.outils import (
    OUTILS, MATERIAUX, offre_outils, offre_materiaux, _possede,
)   # Atelier (acquisition des moyens d'agir ②/③) : registres + offres + possession
from sim.pages import pages_trouvees
from sim.pages_corpus import PAGES, ORDRE
from sim.aide import aide_espece


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
        """Encyclopédie multi-règnes du joueur courant (D60 §5) : `msg.cle` (ou son
        alias hérité `msg.espece`) → la fiche DISPATCHÉE par type (plante N1/N2/N3,
        animal/champignon mono-niveau, …) ou `null` si non découverte ; sinon
        l'INDEX des entrées découvertes, TAGUÉES par type, éventuellement restreint
        à `msg.type` (un des 7 onglets). Le pont relaie, ne classe pas (la
        classification vit en Python source de vérité)."""
        if self.engine is None:
            return {"ok": False, "error": "encyclopedie avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        cle = msg.get("cle") or msg.get("espece")   # `espece` = repli client C# existant
        if cle:
            return {"ok": True, "fiche": encyclopedie_lire(gs, player, cle)}
        return {"ok": True, "index": encyclopedie_index(gs, player, msg.get("type"))}

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
        sinon les OFFRES (sœurs des familles maîtrisées, hors banque) + les
        ARTICLES champignons des espèces nommées (sol qui respire ⑤, 0.5.53 —
        rétro-compatible : clé en plus)."""
        if self.engine is None:
            return {"ok": False, "error": "magazine avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        espece = msg.get("espece")
        if espece:
            return {"ok": True, "fiche": magazine_fiche(espece)}
        return {"ok": True, "offres": magazine_offres(gs, player),
                "articles": magazine_articles(gs, player)}

    def cmd_atelier(self, msg: dict) -> dict:
        """L'ATELIER de la maison normande (acquisition des moyens d'agir ②/③) : la
        VITRINE lecture-seule des OUTILS et MATÉRIAUX à acquérir contre Vigueur, plus
        l'état de POSSESSION des outils (pour que la vue masque/révèle la chaîne taille).
        Read-only pur — l'ACQUISITION passe par les verbes `acheter_outil`/
        `acheter_materiau` de la commande `action` (chemin Vigueur unique). Miroir de
        `cmd_magazine` : ici on n'a pas de « fiche produit » distincte, on expose le
        registre complet (marqueur/dose/coût) que la vue met en page.

        `outils` = liste de {cle, cout_vigueur, possede} pour les outils OFFERTS ;
        `materiaux` = liste de {cle, nature, dose, cout_vigueur} pour les matériaux
        OFFERTS. « Godot bête » : la vue LIT ces champs, ne calcule ni coût ni
        possession (Python source de vérité). Le coût reste un placeholder de
        calibrage F5 (comme le magazine)."""
        if self.engine is None:
            return {"ok": False, "error": "atelier avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        # Possession = le MARQUEUR de l'outil est posé (`outils._possede`, lecture pure
        # de `actions_faites`) — la même question que se pose `acquerir_outil` pour
        # refuser un second achat. Avant le sprint ACCÈS AUX GESTES ② elle n'était
        # calculée que pour le sécateur (dérivée de `couper` ouvert) et valait False en
        # dur pour tous les autres : la vitrine reproposait un outil déjà acheté.
        outils = [
            {"cle": cle,
             "cout_vigueur": OUTILS[cle]["cout_vigueur"],
             "possede": _possede(gs, player, OUTILS[cle]["marqueur"])}
            for cle in offre_outils(gs, player)
        ]
        materiaux = [
            {"cle": cle,
             "nature": MATERIAUX[cle]["nature"],
             "dose": round(MATERIAUX[cle]["dose"], 4),
             "cout_vigueur": MATERIAUX[cle]["cout_vigueur"]}
            for cle in offre_materiaux(gs, player)
        ]
        return {"ok": True, "outils": outils, "materiaux": materiaux}

    def cmd_aide(self, msg: dict) -> dict:
        """Aide (retour F5, « debug d'abord ») : `msg.espece` → remèdes des
        problèmes récents de l'espèce (corpus Python), chacun avec son `concept`
        et `debloque` (concept maîtrisé). Read-only (ledger + maîtrise)."""
        if self.engine is None:
            return {"ok": False, "error": "aide avant init"}
        espece = msg.get("espece")
        if not espece:
            return {"ok": False, "error": "aide sans espece"}
        gs = self.engine.game_state
        return {"ok": True, "aide": aide_espece(gs, gs["current_player"], espece)}
