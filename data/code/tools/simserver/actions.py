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
from sim.outils import acquerir_outil, acquerir_materiau  # Atelier : outil (D82, ②) + matériau mulch (③, canal 3)

from .conteneurs_route import route_conteneur, VERBES as CONTENEUR_VERBES
from .multiplication_route import (
    route_multiplication, VERBES as MULTIPLICATION_VERBES,
)
from .peripherie_route import route_peripherie, VERBES as PERIPHERIE_VERBES
from .plante_route import route_plante, VERBES as PLANTE_VERBES
from .pont_delta import mode_delta   # segments en delta, opt-in (0.6.0)
from .structures_route import route_structure, VERBES as STRUCTURE_VERBES
from .maitrise_pont import (
    decouvrir_a_usage,         # D60 ③ : découverte du geste à la 1ʳᵉ utilisation réussie
    crediter_usage,            # D60 ③ : preuve légère d'usage réussi
)
from sim.actions.deblocage import (   # palette de gestes ① : déblocage event-driven
    DECLENCHEURS, marquer_action, evaluer_deblocages,
    VERBES_COMPTES, compter_geste,    # accès aux gestes ① : forme `("compte", verbe, n)`
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
            # Accès aux gestes ① : certaines PORTES de technique comptent les réussites
            # d'un geste de base (« trois glanages » découvre le compostage). On ne
            # compte que les verbes cités par une condition `compte` (dérivé des tables).
            if verb in VERBES_COMPTES:
                compter_geste(gs, player, verb)
            nouveaux = evaluer_deblocages(gs, player)
            if nouveaux:
                result["debloques"] = nouveaux
        # Snapshot frais TOUJOURS joint : l'effet (plante disparue, etc.) est
        # visible en un seul aller-retour — pas de 2e requête à inventer.
        return {"ok": True, "result": result,
                "snapshot": self._snapshot(mode_delta(self, msg))}

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

        # Acquisition d'un OUTIL à l'Atelier (D82, tronçon ②) : chemin Vigueur
        # UNIQUE, aucune tuile/plot — l'outil vient de `params.outil`.
        # `acquerir_outil` gate l'offre + (idempotence) + débite la Vigueur + pose
        # le marqueur `posseder_secateur` + rouvre la chaîne taille (`couper`→
        # `tailler`) via `evaluer_deblocages` (bool, jamais d'exception : refus si
        # hors offre, outil déjà possédé, ou fonds insuffisants). Le `bilan`
        # rafraîchit vigueur/vigueur_max ; `cmd_action` réévaluera de toute façon
        # les déblocages en aval (verb `posseder_secateur` non déclencheur — le
        # marquage/rouverture se fait ici, dans la façade). Miroir d'`acheter_magazine`.
        if verb == "acheter_outil":
            outil = params.get("outil")
            if not isinstance(outil, str):
                return bilan(False, 0.0, 0.0, f"outil non fourni : {outil!r}")
            achete = acquerir_outil(gs, player, outil)
            b = bilan(achete, 0.0, 0.0,
                      f"{outil} acquis à l'atelier"
                      if achete
                      else f"acquisition refusée : {outil} "
                           "(hors offre, déjà possédé ou Vigueur insuffisante)")
            b["achete"] = achete
            return b

        # Acquisition d'un MATÉRIAU (mulch) à l'Atelier (moyens d'agir ③, canal 3) :
        # chemin Vigueur UNIQUE, aucune tuile/plot — le matériau vient de
        # `params.materiau`. `acquerir_materiau` gate l'offre + débite la Vigueur +
        # crédite le STOCK de mulch de sa nature (bool, jamais d'exception : refus si
        # hors offre ou fonds insuffisants). Import EXTERNE parallèle au magazine de
        # graines (miroir d'`acheter_outil`, mais consommable → PAS idempotent).
        if verb == "acheter_materiau":
            materiau = params.get("materiau")
            if not isinstance(materiau, str):
                return bilan(False, 0.0, 0.0, f"matériau non fourni : {materiau!r}")
            achete = acquerir_materiau(gs, player, materiau)
            b = bilan(achete, 0.0, 0.0,
                      f"{materiau} acquis à l'atelier (mulch ajouté au stock)"
                      if achete
                      else f"acquisition refusée : {materiau} "
                           "(hors offre ou Vigueur insuffisante)")
            b["achete"] = achete
            return b

        # Gestes de PAYSAGE sur la ceinture (PÉRIPHÉRIE ④⑤, protocole 0.5.41) :
        # routage délégué à `peripherie_route` (garde ce routeur court). La cible
        # n'est ni une tuile ni un plot mais un SECTEUR cardinal (`target.cote` ∈
        # 0..3) — la ceinture n'appartient à aucune tuile. Placé AVANT la famille
        # `creuser`/`drainer` : `creuser` est routé ici quand la cible porte un
        # `cote` (clic hors jardin → mare de bordure) et au PLOT sinon, sur la forme
        # du target comme `ecraser` (0.3.2). Aucun `creuser_mare` en doublon.
        if verb in PERIPHERIE_VERBES or (verb == "creuser" and "cote" in target):
            return route_peripherie(gs, player, verb, target, params, bilan)

        # --- résolution de la cible, selon la famille du verbe ------------
        tiles = {t.tile_id: t for t in gs["tiles"]}

        def tile_cible():
            tile = tiles.get(target.get("tile"))
            return tile, (None if tile is None else gs["eco"][tile.tile_id])

        # Gestes sur une PLANTE VIVANTE désignée par position (manger/recolter/
        # deraciner/couper/pincer/arracher/tailler) : routage délégué au module
        # `plante_route` (garde ce routeur court). `_plant_at` passé en résolveur ;
        # les façades `sim/actions` font foi (validité, coût, effet).
        if verb in PLANTE_VERBES:
            return route_plante(gs, player, verb, target, params,
                                bilan, self._plant_at)

        # Multiplication végétative (palette de gestes ②③, protocoles 0.5.24/0.5.25) :
        # `bouturer`/`greffer`, gestes à 2 TEMPS côté VUE (serveur STATELESS). Routage
        # délégué au module `multiplication_route` (garde ce routeur court). Résolution
        # des plantes par POSITION via `_plant_at` passé en résolveur ; les façades
        # `A.bouturer`/`A.greffer` font foi (gates, coûts, effets).
        if verb in MULTIPLICATION_VERBES:
            return route_multiplication(gs, player, verb, target, params,
                                        bilan, self._plant_at)

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
                # Placement sous-plot (① MODÈLE SPATIAL) : on transmet le PIXEL
                # CLIQUÉ tuile-local — la plante germera PILE là, pas au centre du
                # plot. `(r, c)` reste la clé de niche/FIFO (dérivé par `_plot_at`).
                ok = A.planter(gs, player, tile, eco, species, r, c,
                               x_cm=target.get("x_cm"), y_cm=target.get("y_cm"))
                return bilan(ok, cost, 0.0,
                             f"graine déposée ({species}) en ({r},{c}) — "
                             "germera au bon moment" if ok
                             else "Vigueur insuffisante — graine conservée")
            # arroser : phase saison ⇒ urgence (× URGENCE_MULT). Accepte
            # `params.urgence` (bool) OU `params.phase == "saison"` (couture §3.1).
            urgence = bool(params.get("urgence", False)
                           or params.get("phase") == "saison")
            # Mode ASPERSION (③, §2.5) : `params.feuillage` mouille le FEUILLAGE en plus
            # du sol (mildiou ↑) ; défaut False = arrosage AU PIED (le bon geste). Coût
            # identique dans les deux modes (le choix est écologique, pas économique).
            feuillage = bool(params.get("feuillage", False))
            cost = (A.cout_action(gs, player, "arroser",
                                  A.OBJETS_TOUCHES["arroser"])
                    * (A.URGENCE_MULT if urgence else 1.0))
            h_avant = eco.humidite.at_plot(r, c)
            ok = A.arroser(gs, player, eco, r, c, urgence=urgence, feuillage=feuillage)
            h_apres = eco.humidite.at_plot(r, c)
            return bilan(ok, cost, 0.0,
                         f"arrosé ({r},{c}) : humidité {h_avant:.2f} → {h_apres:.2f}"
                         + (" [feuillage]" if feuillage else "")
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

        # Glaner la litière tendre (moyens d'agir ③, canal 1) : geste sur le MILIEU au
        # PLOT {tile, r, c}, patron `becher`. Ramasse feuilles/fleurs/herbacées/fruits
        # tombés → crédite le stock nature `feuilles`. La façade REFUSE en amont si le
        # plot n'a rien de tendre (aucune Vigueur dépensée) → on relaie son verdict.
        # Lève l'impasse `RAVITAILLEMENT_MANQUANT` : source de mulch sans outil ni culture.
        if verb == "glaner":
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
            cost = A.cout_action(gs, player, "glaner", A.OBJETS_TOUCHES["glaner"])
            credit = A.glaner(gs, player, eco, r, c)
            return bilan(credit > 0.0, cost, 0.0,
                         f"litière glanée ({r},{c}) : +{credit:.2f} feuilles au stock"
                         if credit > 0.0
                         else f"rien à glaner en ({r},{c}) (sol propre) "
                              "ou Vigueur insuffisante")

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

        # Terrassement (sprint hydrologie & marécages ⑦) : gestes sur le MILIEU au PLOT
        # {tile, r, c}, patron `grelinette`. `creuser` abaisse l'altitude (cuvette qui
        # accumule l'eau au ruissellement ②) + perturbe le microbiome ; `drainer` vide la
        # flaque (`eau_surface`) et fait reculer `marais_memory` (assèchement forcé ③). Les
        # façades `A.creuser`/`A.drainer` font foi (coût, effet, bornes des champs). Message
        # DIAGNOSTIC en lecture pure (avant/après du champ agi), on lit ce que le geste a fait.
        if verb in ("creuser", "drainer"):
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
            cost = A.cout_action(gs, player, verb, A.OBJETS_TOUCHES[verb])
            if verb == "creuser":
                alt_avant = eco.altitude.at_plot(r, c)
                ok = A.creuser(gs, player, eco, r, c)
                alt_apres = eco.altitude.at_plot(r, c)
                return bilan(ok, cost, 0.0,
                             f"cuvette creusée ({r},{c}) : altitude "
                             f"{alt_avant:.1f} → {alt_apres:.1f} cm" if ok
                             else "Vigueur insuffisante — rien creusé")
            lame_avant = eco.eau_surface.at_plot(r, c)
            mem_avant = eco.marais_memory.at_plot(r, c)
            ok = A.drainer(gs, player, eco, r, c)
            mem_apres = eco.marais_memory.at_plot(r, c)
            return bilan(ok, cost, 0.0,
                         f"drainé ({r},{c}) : flaque {lame_avant:.2f} → 0.00, "
                         f"marais {mem_avant:.2f} → {mem_apres:.2f}" if ok
                         else "Vigueur insuffisante — rien drainé")

        # Perchoir à oiseaux (zoochorie ④, protocole 0.6.11) : POSITION tuile-locale
        # {tile, x_cm, y_cm}, comme `planter`. Hors tuile → refus sans coût. La façade
        # fait foi (coût, pose binaire). NB : poser_tuteur/treillis/pergola n'ont pas
        # (encore) de route au pont — même branche le jour où la vue les enverra.
        if verb == "poser_perchoir":
            tile, _eco = tile_cible()
            if tile is None:
                return bilan(False, 0.0, 0.0,
                             f"tuile introuvable : {target.get('tile')!r}")
            if self._plot_at(tile, target.get("x_cm"), target.get("y_cm")) is None:
                return bilan(False, 0.0, 0.0,
                             f"position hors tuile : x={target.get('x_cm')!r}, "
                             f"y={target.get('y_cm')!r}")
            cost = A.cout_action(gs, player, verb, A.OBJETS_TOUCHES[verb])
            sup = A.poser_perchoir(gs, player, tile, float(target["x_cm"]),
                                   float(target["y_cm"]))
            return bilan(sup is not None, cost, 0.0,
                         "perchoir planté — les oiseaux viendront s'y poser"
                         if sup is not None else "Vigueur insuffisante — rien posé")

        # Structures posables & compostage (⑤, protocole 0.3.5 ; ruche ⑥ §H/§I) :
        # routage délégué au module `structures_route` (garde ce routeur court).
        # Poser désigne un PLOT {r,c}, les gestes sur structure existante la
        # désignent par INDEX dans `eco.structures` ; les façades font foi.
        if verb in STRUCTURE_VERBES:
            return route_structure(gs, player, verb, target, params, bilan)

        # Conteneurs (pots/bacs ④, protocole 0.5.7) : routage délégué au module
        # `conteneurs_route` (garde ce routeur court). Pots/bacs vivent dans la liste
        # MONDE `gs["containers"]` ; pose par POSITION, déplace/plante par INDEX.
        if verb in CONTENEUR_VERBES:
            return route_conteneur(gs, player, verb, target, params, bilan)

        return bilan(False, 0.0, 0.0, f"verbe inconnu : {verb!r}")
