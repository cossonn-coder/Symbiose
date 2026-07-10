"""
SYMBIOSE — tools/simserver/actions.py
Routeur des gestes joueur : la commande `action` et son aiguillage `_do_action`
(aiguillage par famille de verbe + traduction JSON). La résolution des cibles
(`_plant_at` / `_skeleton_at` / `_plot_at` / `_noter_geste_maitrise`) vit dans
`actions_cibles.py` (`CiblesMixin`), scindée au refactor de taille du sprint
équilibre-invasion. Mixin de `SimServer` (Sprint refactor global, SS⑤).

Le serveur APPELLE les façades de sim/actions.py (sprint Vigueur + D31.3) — il
ne réimplémente AUCUNE règle : validité, coût (maîtrise × urgence), effet et
plafonds restent côté moteur. Rôle de l'adaptateur : résoudre la DÉSIGNATION
(tile/plot/plante par position) et traduire le retour en JSON. Maître/esclave :
Godot envoie l'intention, ici on répond ACK/NAK + données — jamais la vue
n'écrit dans le moteur.
"""
from __future__ import annotations

from plants import PLANT_CATALOGUE  # validation d'espèce plantable (planter)
from sim import actions as A      # les 10 gestes joueur (façades, sprint Vigueur/D31.3)
from sim import vigueur as V      # état Vigueur joueur (ensure/spend/gain, D11)
from sim.magazine import acheter_au_magazine  # achat magazine (voix ①, verbe Q3)

from .conteneurs_route import route_conteneur, VERBES as CONTENEUR_VERBES
from .maitrise_pont import (
    decouvrir_a_usage,         # D60 ③ : découverte du geste à la 1ʳᵉ utilisation réussie
    crediter_usage,            # D60 ③ : preuve légère d'usage réussi
)
from sim.actions.deblocage import (   # palette de gestes ① : déblocage event-driven
    DECLENCHEURS, marquer_action, evaluer_deblocages,
)


class ActionsMixin:
    """La commande `action` et la résolution des cibles."""

    # ------------------------------------------------------------- actions

    def cmd_action(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "action avant init"}
        verb = msg.get("verb")
        target = msg.get("target") or {}
        params = msg.get("params") or {}
        if not isinstance(target, dict) or not isinstance(params, dict):
            return {"ok": False, "error": "target/params doivent être des objets"}
        # Hook C (imputation §2, voix ①) : si le geste porte sur un PLOT résoluble,
        # on l'enregistre dans la fenêtre d'imputation de la maîtrise AVANT de le
        # résoudre — pour que `detecter` (aux ticks suivants) impute au joueur la
        # levée de stagnation / la reproduction que son geste aura provoquées.
        # Opt-in joueur (hors golden). Zone (tile_id, r, c) au foyer du plot agi.
        self._noter_geste_maitrise(verb, target)
        result = self._do_action(verb, target, params)
        # Progression geste/outil/technique (D60 ③) : SEULEMENT si le geste a été
        # RÉELLEMENT appliqué (un refus métier ne prouve rien). D'abord la découverte
        # à l'usage (canal neuf Q3 : le geste + sa technique + ses outils passent au
        # palier 1), PUIS le crédit léger d'usage sur ces mêmes objets découverts. Le
        # volet SUCCÈS (poids fort) vit au tick suivant, dans `observer_apres_tick`.
        # Hors tick (opt-in joueur) → golden NEUTRE : le driver golden n'appelle jamais
        # `cmd_action`.
        if result.get("applied"):
            gs = self.engine.game_state
            player = gs["current_player"]
            decouvrir_a_usage(gs, player, verb)
            crediter_usage(gs, player, verb)
            # La 1ʳᵉ découverte à l'usage crédite un petit gain de Vigueur (§4.3,
            # même robinet que le survol d'une espèce). Le `bilan` a figé la Vigueur
            # AVANT ce gain → on rafraîchit les champs Vigueur du result pour rester
            # la source de vérité cohérente avec le snapshot joint (le `cost`/`gain`
            # nominaux du geste, eux, restent inchangés — le gain de découverte est
            # une source SÉPARÉE, pas un revenu du geste).
            result["vigueur"] = V.ensure_player(gs, player)["courante"]
            result["vigueur_max"] = V.vigueur_max(gs, player)
            # Déblocage des gestes (palette ①, D12 voie action §3.2·b) : un geste
            # DÉCLENCHEUR réussi (poser_bac/poser_pile/poser_pot/poser_tuteur/
            # poser_ruche/couper) ouvre son/ses successeur(s). On MARQUE l'action
            # PUIS on réévalue les déblocages (event-driven, hors tick). Les verbes
            # NOUVELLEMENT ouverts partent au result → notification diégétique côté
            # vue. Opt-in joueur → golden intact (cmd_action jamais appelé au golden).
            if verb in DECLENCHEURS:
                marquer_action(gs, player, verb)
            nouveaux = evaluer_deblocages(gs, player)
            if nouveaux:
                result["debloques"] = nouveaux
        # Snapshot frais TOUJOURS joint : l'effet (plante disparue, etc.) est
        # visible en un seul aller-retour — pas de 2e requête à inventer.
        return {"ok": True, "result": result, "snapshot": self._snapshot()}

    def _do_action(self, verb: str, target: dict, params: dict) -> dict:
        gs = self.engine.game_state
        player = gs["current_player"]

        def bilan(applied: bool, cost: float, gain_v: float, message: str) -> dict:
            """État Vigueur APRÈS le geste — y compris sur refus : un échec
            binaire à vide a quand même drainé (contrat de spend, philo #1)."""
            st = V.ensure_player(gs, player)
            return {"applied": applied, "cost": cost, "gain": gain_v,
                    "vigueur": st["courante"],
                    "vigueur_max": V.vigueur_max(gs, player),
                    "message": message}

        # Achat au magazine (voix ①, décision Q3) : chemin Vigueur UNIQUE, aucune
        # tuile/plot — l'espèce vient de `params.espece`. `acheter_au_magazine`
        # gate l'offre + débite la Vigueur + dépose la graine (bool, jamais
        # d'exception : refus si offre fermée ou fonds insuffisants). Le `bilan`
        # rafraîchit vigueur/vigueur_max (banque exposée au snapshot joint).
        if verb == "acheter_magazine":
            espece = params.get("espece")
            if not isinstance(espece, str):
                return bilan(False, 0.0, 0.0, f"espèce non fournie : {espece!r}")
            achete = acheter_au_magazine(gs, player, espece)
            b = bilan(achete, 0.0, 0.0,
                      f"acheté au magazine : {espece} (graine ajoutée à la banque)"
                      if achete
                      else f"achat refusé : {espece} (hors offre ou Vigueur insuffisante)")
            b["achete"] = achete
            return b

        # --- résolution de la cible, selon la famille du verbe ------------
        tiles = {t.tile_id: t for t in gs["tiles"]}

        def tile_cible():
            tile = tiles.get(target.get("tile"))
            return tile, (None if tile is None else gs["eco"][tile.tile_id])

        if verb in ("manger", "recolter", "deraciner", "tailler", "couper"):
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            plant = self._plant_at(tile, target.get("x_cm"), target.get("y_cm"))
            if plant is None:
                return bilan(False, 0.0, 0.0,
                             "aucune plante vivante à cette position")
            # Coût nominal AVANT le geste (cout_action est une lecture pure —
            # le geste recalcule le même en interne) : pour l'affichage HUD.
            cost = A.cout_action(gs, player, verb, A._objets_action(verb, plant))
            if verb == "manger":
                # Fruit ciblé (③, D19) : index dans plant.fruits du snapshot.
                # Validé AVANT la façade — un index invalide ne mange rien (et,
                # côté actions, retombe sur le mode générique). NB : bool < int.
                fidx = target.get("fruit")
                if fidx is not None:
                    if not isinstance(fidx, int) or isinstance(fidx, bool):
                        return bilan(False, 0.0, 0.0,
                                     f"fruit non entier : {fidx!r}")
                    if not 0 <= fidx < len(plant.fruits):
                        return bilan(False, 0.0, 0.0,
                                     f"fruit hors structure : {fidx} "
                                     f"(la plante porte {len(plant.fruits)} fruits)")
                g = A.manger(gs, player, plant, eco, fruit_index=fidx)
                # Gain nominal DANS le message (retour F5 Nico : « rien ne se
                # passe » = organe immature, gain ≈ 0 — qu'on le LISE).
                cible = f"fruit #{fidx}" if fidx is not None else plant.name
                return bilan(True, 0.0, g,
                             f"mangé : {cible} (+{g:.1f} Vigueur — "
                             f"gain ∝ maturité de l'organe)")
            if verb == "recolter":
                ratio = A.recolter(gs, player, plant, eco)
                msg = ("récolté : " + plant.name if ratio >= 1.0
                       else f"récolte partielle ({ratio:.0%}) : {plant.name}")
                return bilan(ratio > 0.0, cost, 0.0, msg)
            if verb == "deraciner":
                ok = A.deraciner(gs, player, plant, eco)
                return bilan(ok, cost, 0.0,
                             "déraciné : " + plant.name if ok
                             else "Vigueur insuffisante — rien déraciné")
            # couper (geste BRUT, D12 — ancêtre de tailler) : coupe SANS choisir le
            # segment (pas de `target.segment`). Réutilise le seam `tailler` avec la
            # cible par défaut (apex) → façade fait foi (validité/coût/effet). Coût
            # propre `couper` (= tailler). Marque l'action (ouvre `tailler` par la
            # chaîne sécateur→couper→tailler) + réévalue les déblocages.
            if verb == "couper":
                cost = A.cout_action(gs, player, "couper",
                                     A._objets_action("couper", plant))
                ok = A.tailler(gs, player, plant, eco, cible="apex", segment_id=None)
                return bilan(ok, cost, 0.0,
                             f"branche coupée : {plant.name}" if ok
                             else "Vigueur insuffisante — rien coupé")

            # tailler
            cible = params.get("cible", "apex")
            if cible not in ("apex", "branche"):
                return bilan(False, 0.0, 0.0,
                             f"cible de taille inconnue : {cible!r}")
            # Segment explicite (tranche 5, la branche cliquée) : validé AVANT
            # la façade — un refus de désignation ne draine pas la Vigueur.
            # NB : bool est un sous-type d'int en Python → exclu explicitement.
            seg = target.get("segment")
            if seg is not None:
                if not isinstance(seg, int) or isinstance(seg, bool):
                    return bilan(False, 0.0, 0.0,
                                 f"segment non entier : {seg!r}")
                if not 0 <= seg < len(plant.segments):
                    return bilan(False, 0.0, 0.0,
                                 f"segment hors structure : {seg} "
                                 f"(plante à {len(plant.segments)} segments)")
                if plant.segments[seg].parent is None:
                    return bilan(False, 0.0, 0.0,
                                 "le collet est protégé — rien à couper ici")
            ok = A.tailler(gs, player, plant, eco, cible=cible, segment_id=seg)
            quoi = f"segment {seg}" if seg is not None else cible
            return bilan(ok, cost, 0.0,
                         f"taillé ({quoi}) : {plant.name}" if ok
                         else "Vigueur insuffisante — rien taillé")

        # Bouturer (palette de gestes ②, protocole 0.5.24) — geste à 2 TEMPS côté
        # VUE (comme `epandre`/`deplacer_pot` : la mémoire des 2 clics vit dans Godot,
        # le serveur reste STATELESS). Un seul appel porte les DEUX cibles déjà
        # résolues : la MÈRE par position continue (`x_cm`/`y_cm`, comme tailler) et
        # le PLOT cible par `params.r`/`params.c` (le 2e clic). La façade `A.bouturer`
        # fait foi (gate bouturable/maturité/vigueur, coût, clone, stress mère). Refus
        # de désignation (mère introuvable / plot hors tuile) → ne coûte rien.
        if verb == "bouturer":
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            mother = self._plant_at(tile, target.get("x_cm"), target.get("y_cm"))
            if mother is None:
                return bilan(False, 0.0, 0.0,
                             "aucune plante-mère vivante à cette position")
            r, c = params.get("r"), params.get("c")
            if (not isinstance(r, int) or isinstance(r, bool)
                    or not isinstance(c, int) or isinstance(c, bool)
                    or not (0 <= r < tile.grid_rows)
                    or not (0 <= c < tile.grid_cols)):
                return bilan(False, 0.0, 0.0,
                             f"plot cible hors tuile : r={r!r}, c={c!r}")
            # Gate d'espèce lu EN AMONT pour un message clair (distinct de la Vigueur
            # insuffisante), sans dépense — la façade retesterait de toute façon.
            if not getattr(mother.plant_class, "bouturable", False):
                return bilan(False, 0.0, 0.0,
                             f"{mother.name} ne se bouture pas")
            cost = A.cout_action(gs, player, "bouturer",
                                 A._objets_action("bouturer", mother))
            ok = A.bouturer(gs, player, mother, tile, eco, r, c)
            return bilan(ok, cost, 0.0,
                         f"bouture de {mother.name} enracinée en ({r},{c})" if ok
                         else f"rien bouturé ({mother.name} trop jeune/épuisée "
                              "ou Vigueur insuffisante)")

        # Greffer (palette de gestes ③, protocole 0.5.25) — geste à 2 TEMPS côté VUE
        # (comme `bouturer` : la mémoire des 2 clics vit dans Godot, le serveur reste
        # STATELESS). Un seul appel porte les DEUX plantes déjà résolues : le
        # PORTE-GREFFE par position continue (`target.x_cm`/`y_cm`, comme tailler — c'est
        # lui qui RESTE, cible primaire) et le GREFFON par `params.scion_x_cm`/
        # `scion_y_cm` (le 1er clic, sur la MÊME tuile). La façade `A.greffer` fait foi
        # (gate greffable/famille, coût ÉLEVÉ, recomposition aérien/racinaire D8, greffon
        # consommé). Refus de désignation (plante introuvable) → ne coûte rien.
        if verb == "greffer":
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            rootstock = self._plant_at(tile, target.get("x_cm"), target.get("y_cm"))
            if rootstock is None:
                return bilan(False, 0.0, 0.0,
                             "aucun porte-greffe vivant à cette position")
            scion = self._plant_at(tile, params.get("scion_x_cm"),
                                   params.get("scion_y_cm"))
            if scion is None:
                return bilan(False, 0.0, 0.0,
                             "aucun greffon vivant à cette position")
            if scion is rootstock:
                return bilan(False, 0.0, 0.0,
                             "greffon et porte-greffe sont la même plante")
            # Gate lu EN AMONT pour un message clair (distinct de la Vigueur
            # insuffisante), sans dépense — la façade retesterait de toute façon.
            if not A.peut_greffer(scion, rootstock):
                return bilan(False, 0.0, 0.0,
                             f"greffe impossible : {scion.name} et {rootstock.name} "
                             "non greffables ou de familles différentes")
            cost = A.cout_action(gs, player, "greffer",
                                 A._objets_action("greffer", rootstock))
            nom_greffon = scion.name           # lu AVANT la greffe (scion consommé après)
            ok = A.greffer(gs, player, scion, rootstock, eco)
            return bilan(ok, cost, 0.0,
                         f"greffe prise : {nom_greffon} soudé sur {rootstock.name} "
                         "(couronne du greffon, racines du porte-greffe)" if ok
                         else "Vigueur insuffisante — greffe non faite")

        # Gestes sur le MILIEU désignés par POSITION continue (planter·arroser,
        # protocole 0.3.3). La cible est un POINT (x_cm/y_cm) ; on le résout en
        # plot-foyer (`_plot_at`, floor(/PLOT_CM)) car les façades écrivent au
        # plot (banque-sol pour planter, champ humidité pour arroser). Un point
        # hors tuile est un refus de désignation → ne coûte RIEN (façade jamais
        # appelée), comme un segment invalide pour tailler.
        if verb in ("planter", "arroser"):
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            rc = self._plot_at(tile, target.get("x_cm"), target.get("y_cm"))
            if rc is None:
                return bilan(False, 0.0, 0.0,
                             f"position hors tuile : x={target.get('x_cm')!r}, "
                             f"y={target.get('y_cm')!r}")
            r, c = rc
            if verb == "planter":
                species = params.get("species")
                if not isinstance(species, str) or species not in PLANT_CATALOGUE:
                    return bilan(False, 0.0, 0.0,
                                 f"espèce non plantable : {species!r}")
                # Refus « lot vide » EN AMONT (comme la façade) → message clair,
                # distinct de la Vigueur insuffisante, et aucune dépense.
                bank = gs.get("player_seed_bank")
                if bank is None or bank.count(species) == 0:
                    return bilan(False, 0.0, 0.0,
                                 f"lot vide — aucune graine de {species} en banque")
                cost = A.cout_action(gs, player, "planter",
                                     A._objets_action("planter"))
                ok = A.planter(gs, player, tile, eco, species, r, c)
                return bilan(ok, cost, 0.0,
                             f"graine déposée ({species}) en ({r},{c}) — "
                             "germera au bon moment" if ok
                             else "Vigueur insuffisante — graine conservée")
            # arroser : phase saison ⇒ urgence (× URGENCE_MULT). Accepte
            # `params.urgence` (bool) OU `params.phase == "saison"` (couture §3.1).
            urgence = bool(params.get("urgence", False)
                           or params.get("phase") == "saison")
            cost = (A.cout_action(gs, player, "arroser",
                                  A.OBJETS_TOUCHES["arroser"])
                    * (A.URGENCE_MULT if urgence else 1.0))
            h_avant = eco.humidite.at_plot(r, c)
            ok = A.arroser(gs, player, eco, r, c, urgence=urgence)
            h_apres = eco.humidite.at_plot(r, c)
            return bilan(ok, cost, 0.0,
                         f"arrosé ({r},{c}) : humidité {h_avant:.2f} → {h_apres:.2f}"
                         + (" [urgence]" if urgence else "") if ok
                         else "Vigueur insuffisante — rien arrosé")

        if verb in ("ecraser", "becher"):
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            # Écraser une PLANTE (volet 2) : routé sur la FORME du target (Q6) — la
            # plante est désignée par position (x_cm/y_cm), la guilde animale par
            # r/c+guilde. `segment` optionnel reprend `tailler` 0.2.1, MAIS le collet
            # (segment 0) est ici une cible VALIDE (défaut Q2) — on ne le rejette pas.
            if (verb == "ecraser" and target.get("guilde") is None
                    and target.get("x_cm") is not None):
                plant = self._plant_at(tile, target.get("x_cm"), target.get("y_cm"))
                if plant is None:
                    return bilan(False, 0.0, 0.0,
                                 "aucune plante vivante à cette position")
                urgence = bool(params.get("urgence", False))
                cost = (A.cout_action(gs, player, "tailler",
                                      A._objets_action("tailler", plant))
                        * (A.URGENCE_MULT if urgence else 1.0))
                seg = target.get("segment")
                if seg is not None:
                    if not isinstance(seg, int) or isinstance(seg, bool):
                        return bilan(False, 0.0, 0.0, f"segment non entier : {seg!r}")
                    if not 0 <= seg < len(plant.segments):
                        return bilan(False, 0.0, 0.0,
                                     f"segment hors structure : {seg} "
                                     f"(plante à {len(plant.segments)} segments)")
                n_avant = len(plant.segments)
                ok = A.ecraser_plante(gs, player, plant, eco,
                                      segment_id=seg, urgence=urgence)
                # Diagnostic ÉMERGENT pour le message (lecture pure) : on lit ce que
                # le geste a produit, on ne le décide pas.
                if not ok:
                    quoi = "Vigueur insuffisante — rien écrasé"
                elif not plant.is_alive:
                    quoi = "meurt"
                elif len(plant.segments) < n_avant:
                    quoi = "écimée"
                else:
                    quoi = "déformée"
                return bilan(ok, cost, 0.0,
                             f"écrasé {plant.name} : {quoi}"
                             + (" [urgence]" if urgence and ok else "")
                             if ok else quoi)
            r, c = target.get("r"), target.get("c")
            if (not isinstance(r, int) or not isinstance(c, int)
                    or not (0 <= r < tile.grid_rows)
                    or not (0 <= c < tile.grid_cols)):
                return bilan(False, 0.0, 0.0,
                             f"plot hors tuile : r={r!r}, c={c!r}")
            if verb == "ecraser":
                urgence = bool(params.get("urgence", False))
                # ESPÈCE du SPRITE cliqué (protocole ⑥, `target.espece`) : on écrase
                # ce qui est sous la souris, quelle que soit sa nature. Depuis la
                # scission ④b-d le snapshot émet des CLÉS D'ESPÈCE (puceron…cloporte),
                # plus les anciennes guildes — la clé canonique est donc `espece`.
                # `guilde` reste accepté en repli pour les clients < ⑥ (bascule
                # coordonnée : le client Godot passe à `espece` en ⑥b). Défaut puceron
                # = repli ultime des clients qui ne désignent rien.
                espece = target.get("espece", target.get("guilde", "puceron"))
                if espece not in eco.populations:
                    return bilan(False, 0.0, 0.0,
                                 f"espèce inconnue : {espece!r}")
                cost = (A.cout_action(gs, player, "ecraser")
                        * (A.URGENCE_MULT if urgence else 1.0))
                # Densité de l'espèce ciblée avant/après DANS le message (la vue
                # confirme l'effet en un aller-retour). Lecture pure, zéro règle.
                avant = eco.populations[espece].get(r, c)
                ok = A.ecraser(gs, player, eco, r, c, guilde=espece, urgence=urgence)
                apres = eco.populations[espece].get(r, c)
                return bilan(ok, cost, 0.0,
                             f"écrasé un {espece} en ({r},{c})"
                             + (" [urgence]" if urgence else "")
                             + f" — {espece} {avant:.2f} → {apres:.2f}" if ok
                             else "Vigueur insuffisante — rien écrasé")
            cost = A.cout_action(gs, player, "becher", A.OBJETS_TOUCHES["becher"])
            ok = A.becher(gs, player, eco, r, c)
            return bilan(ok, cost, 0.0,
                         f"bêché en ({r},{c})" if ok
                         else "Vigueur insuffisante — rien bêché")

        if verb == "favoriser_auxiliaire":
            tile, _eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            cost = A.cout_action(gs, player, "favoriser_auxiliaire",
                                 A.OBJETS_TOUCHES["favoriser_auxiliaire"])
            ok = A.favoriser_auxiliaire(gs, player, tile)
            return bilan(ok, cost, 0.0,
                         f"habitat auxiliaire posé sur {tile.tile_id}" if ok
                         else "échec (Vigueur insuffisante ou tiges saturées)")

        # Pailler (sprint équilibre invasion ③/⑧, D69) : geste sur le MILIEU au PLOT
        # {tile, r, c}, `params.nature` ∈ {paille, brf, aiguilles} (défaut "paille").
        # La façade REFUSE en amont si le stock de mulch de cette nature est vide
        # (aucune Vigueur dépensée) — on relaie son verdict, jamais de pré-validation
        # côté vue (Python possède la règle : stock, coût, cap du champ).
        if verb == "pailler":
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            r, c = target.get("r"), target.get("c")
            if (not isinstance(r, int) or isinstance(r, bool)
                    or not isinstance(c, int) or isinstance(c, bool)
                    or not (0 <= r < tile.grid_rows)
                    or not (0 <= c < tile.grid_cols)):
                return bilan(False, 0.0, 0.0,
                             f"plot hors tuile : r={r!r}, c={c!r}")
            nature = params.get("nature", "paille")
            if not isinstance(nature, str):
                return bilan(False, 0.0, 0.0, f"nature non textuelle : {nature!r}")
            cost = A.cout_action(gs, player, "pailler", A.OBJETS_TOUCHES["pailler"])
            avant = eco.paillage.at_plot(r, c)
            ok = A.pailler(gs, player, eco, r, c, nature=nature)
            apres = eco.paillage.at_plot(r, c)
            return bilan(ok, cost, 0.0,
                         f"paillé ({r},{c}) en {nature} : "
                         f"profondeur {avant:.2f} → {apres:.2f}" if ok
                         else f"rien paillé (stock de {nature} vide ou "
                              "Vigueur insuffisante)")

        # Broyer du bois en BRF (sprint équilibre invasion ④/⑧, D69) : geste sur le
        # MILIEU désigné par POSITION continue, comme les autres gestes sur plante — mais
        # la CIBLE est un SQUELETTE (plante MORTE avec du bois à fragmenter). `_plant_at`
        # ne retient que les VIVANTES ; on résout donc le mort par position ici. Le stock
        # `brf` produit alimente `pailler`. Façade GRADUÉE (broie une fraction du bois à
        # Vigueur partielle) + refus en amont si aucune réserve → on relaie le verdict.
        if verb == "broyer":
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            plant = self._skeleton_at(tile, target.get("x_cm"), target.get("y_cm"))
            if plant is None:
                return bilan(False, 0.0, 0.0,
                             "aucun bois à broyer ici (visez un squelette de plante ligneuse)")
            cost = A.cout_action(gs, player, "broyer", A.OBJETS_TOUCHES["broyer"])
            credit = A.broyer(gs, player, plant, eco)
            return bilan(credit > 0.0, cost, 0.0,
                         f"bois broyé : +{credit:.2f} BRF au stock de mulch" if credit > 0.0
                         else "rien broyé (plus de bois ou Vigueur insuffisante)")

        if verb == "grelinette":
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            r, c = target.get("r"), target.get("c")
            if (not isinstance(r, int) or not isinstance(c, int)
                    or not (0 <= r < tile.grid_rows)
                    or not (0 <= c < tile.grid_cols)):
                return bilan(False, 0.0, 0.0,
                             f"plot hors tuile : r={r!r}, c={c!r}")
            cost = A.cout_action(gs, player, "grelinette",
                                 A.OBJETS_TOUCHES["grelinette"])
            ok = A.grelinette(gs, player, eco, r, c)
            return bilan(ok, cost, 0.0,
                         f"sol ameubli à la grelinette en ({r},{c})" if ok
                         else "Vigueur insuffisante")

        # Structures posables & compostage (⑤, protocole 0.3.5). Toutes ciblent une
        # tuile ; poser/composter/empiler/epandre désignent un PLOT {r,c}, les gestes
        # sur une structure existante (composter/empiler/retourner/epandre) la
        # désignent par INDEX dans `eco.structures` (= ordre du snapshot). Validation
        # des bornes ICI (refus de désignation → ne coûte rien), la façade fait foi.
        if verb in ("poser_bac", "poser_pile", "composter", "empiler_bois",
                    "retourner", "epandre", "poser_ruche", "recolter_miel"):
            tile, eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")

            def plot_rc():
                """(r, c) entier dans la grille, ou (None, message)."""
                r, c = target.get("r"), target.get("c")
                if (not isinstance(r, int) or isinstance(r, bool)
                        or not isinstance(c, int) or isinstance(c, bool)
                        or not (0 <= r < tile.grid_rows)
                        or not (0 <= c < tile.grid_cols)):
                    return None, f"plot hors tuile : r={r!r}, c={c!r}"
                return (r, c), None

            def struct_cible():
                """La Structure désignée par `target.structure`, ou (None, message)."""
                idx = target.get("structure")
                if not isinstance(idx, int) or isinstance(idx, bool):
                    return None, f"structure non entier : {idx!r}"
                if not 0 <= idx < len(eco.structures):
                    return None, (f"structure hors liste : {idx} "
                                  f"({len(eco.structures)} posées sur {tile.tile_id})")
                return eco.structures[idx], None

            cost = A.cout_action(gs, player, verb, A.OBJETS_TOUCHES[verb])

            if verb in ("poser_bac", "poser_pile", "poser_ruche"):
                rc, err = plot_rc()
                if rc is None:
                    return bilan(False, 0.0, 0.0, err)
                r, c = rc
                if verb == "poser_bac":
                    s = A.poser_bac(gs, player, eco, r, c)
                    quoi = "bac à compost"
                elif verb == "poser_pile":
                    s = A.poser_pile(gs, player, eco, tile, r, c)
                    quoi = "pile à bois"
                else:
                    s = A.poser_ruche(gs, player, eco, r, c)   # ⑥ §H.1
                    quoi = "ruche"
                return bilan(s is not None, cost, 0.0,
                             f"{quoi} posé{'e' if verb == 'poser_ruche' else ''} "
                             f"en ({r},{c}) sur {tile.tile_id}"
                             if s is not None
                             else "Vigueur insuffisante — rien posé")

            struct, err = struct_cible()
            if struct is None:
                return bilan(False, 0.0, 0.0, err)
            # Récolte du miel (⑥ §I.2) : geste sur une ruche (par index), gain Vigueur
            # ∝ miel transféré, gaté par l'équipement (maîtrise §I.3). Refus de
            # désignation (pas une ruche) → ne coûte rien.
            if verb == "recolter_miel":
                if struct.kind != "ruche":
                    return bilan(False, 0.0, 0.0, "cette structure n'est pas une ruche")
                g = A.recolter_miel(gs, player, struct, eco)   # eco → alarme §J si nu
                equipe = A.equipe(gs, player)
                return bilan(g > 0.0, cost, g,
                             f"miel récolté (+{g:.1f} Vigueur"
                             f"{'' if equipe else ' — récolte partielle, sans équipement'})"
                             if g > 0.0
                             else "rien récolté (réserve vide ou Vigueur insuffisante)")
            # Cohérence kind/geste : composter→bac, empiler→pile (refus de
            # désignation, ne coûte rien). retourner/epandre marchent sur les deux.
            if verb == "composter" and struct.kind != "bac":
                return bilan(False, 0.0, 0.0, "cette structure n'est pas un bac à compost")
            if verb == "empiler_bois" and struct.kind != "pile":
                return bilan(False, 0.0, 0.0, "cette structure n'est pas une pile à bois")

            if verb == "retourner":
                ok = A.retourner(gs, player, struct)
                return bilan(ok, cost, 0.0,
                             "compost retourné (maturation accélérée)" if ok
                             else "Vigueur insuffisante — rien retourné")

            rc, err = plot_rc()
            if rc is None:
                return bilan(False, 0.0, 0.0, err)
            r, c = rc
            if verb == "composter":
                ok = A.composter(gs, player, eco, r, c, struct)
                return bilan(ok, cost, 0.0,
                             f"litière tendre compostée ({r},{c}) → bac" if ok
                             else "Vigueur insuffisante — rien composté")
            if verb == "empiler_bois":
                ok = A.empiler_bois(gs, player, eco, r, c, struct)
                return bilan(ok, cost, 0.0,
                             f"bois empilé ({r},{c}) → pile" if ok
                             else "Vigueur insuffisante — rien empilé")
            # epandre : params.q optionnel (None ⇒ tout le disponible).
            q = params.get("q")
            if q is not None and (not isinstance(q, (int, float))
                                  or isinstance(q, bool)):
                return bilan(False, 0.0, 0.0, f"quantité non numérique : {q!r}")
            epandu = A.epandre(gs, player, eco, r, c, struct, q=q)
            return bilan(epandu > 0.0, cost, 0.0,
                         f"compost épandu en ({r},{c}) : {epandu:.2f} "
                         f"(jauge restante {struct.compost_mur:.2f})" if epandu > 0.0
                         else "rien épandu (jauge vide ou Vigueur insuffisante)")

        # Conteneurs (pots/bacs ④, protocole 0.5.7) : routage délégué au module
        # `conteneurs_route` (garde ce routeur court). Pots/bacs vivent dans la liste
        # MONDE `gs["containers"]` ; pose par POSITION, déplace/plante par INDEX.
        if verb in CONTENEUR_VERBES:
            return route_conteneur(gs, player, verb, target, params, bilan)

        return bilan(False, 0.0, 0.0, f"verbe inconnu : {verb!r}")
