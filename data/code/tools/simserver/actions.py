"""
SYMBIOSE — tools/simserver/actions.py
Routeur des gestes joueur : la commande `action` et son aiguillage `_do_action`
(résolution de la cible tile/plot/plante-par-position + traduction JSON), plus
les deux résolveurs `_plant_at` / `_plot_at`. Mixin de `SimServer` (Sprint
refactor global, SS⑤).

Le serveur APPELLE les façades de sim/actions.py (sprint Vigueur + D31.3) — il
ne réimplémente AUCUNE règle : validité, coût (maîtrise × urgence), effet et
plafonds restent côté moteur. Rôle de l'adaptateur : résoudre la DÉSIGNATION
(tile/plot/plante par position) et traduire le retour en JSON. Maître/esclave :
Godot envoie l'intention, ici on répond ACK/NAK + données — jamais la vue
n'écrit dans le moteur.
"""
from __future__ import annotations

from constants import PLOT_CM     # échelle plot (position continue → plot-foyer)
from plants import PLANT_CATALOGUE  # validation d'espèce plantable (planter)
from sim import actions as A      # les 10 gestes joueur (façades, sprint Vigueur/D31.3)
from sim import vigueur as V      # état Vigueur joueur (ensure/spend/gain, D11)

from .version import PLANT_EPSILON_CM


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
        result = self._do_action(verb, target, params)
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

        # --- résolution de la cible, selon la famille du verbe ------------
        tiles = {t.tile_id: t for t in gs["tiles"]}

        def tile_cible():
            tile = tiles.get(target.get("tile"))
            return tile, (None if tile is None else gs["eco"][tile.tile_id])

        if verb in ("manger", "recolter", "deraciner", "tailler"):
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

        if verb == "grelinette":
            cost = A.cout_action(gs, player, "grelinette",
                                 A.OBJETS_TOUCHES["grelinette"])
            ok = A.grelinette(gs, player)
            return bilan(ok, cost, 0.0,
                         "sol ameubli à la grelinette" if ok
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

        return bilan(False, 0.0, 0.0, f"verbe inconnu : {verb!r}")

    @staticmethod
    def _plant_at(tile, x_cm, y_cm, eps: float = PLANT_EPSILON_CM):
        """La plante VIVANTE de la tuile à ±eps de (x_cm, y_cm) locale, ou None.
        La position est l'identité (kickoff §8) : pas d'id inventé."""
        if not isinstance(x_cm, (int, float)) or not isinstance(y_cm, (int, float)):
            return None
        for p in tile.plants:
            if (p.is_alive and p.x_cm is not None
                    and abs(p.x_cm - x_cm) <= eps
                    and abs(p.y_cm - y_cm) <= eps):
                return p
        return None

    @staticmethod
    def _plot_at(tile, x_cm, y_cm):
        """Le plot-foyer (r, c) d'une position LOCALE continue, ou None si hors
        tuile. Même convention que `PlantInstance.plot_foyer` (canon moteur) :
        `(int(y // PLOT_CM), int(x // PLOT_CM))` — y→ligne, x→colonne. Sert aux
        gestes de milieu désignés par point (planter·arroser). NB : bool est un
        sous-type d'int → exclu (un `true` JSON n'est pas une coordonnée)."""
        if (not isinstance(x_cm, (int, float)) or isinstance(x_cm, bool)
                or not isinstance(y_cm, (int, float)) or isinstance(y_cm, bool)):
            return None
        r, c = int(y_cm // PLOT_CM), int(x_cm // PLOT_CM)
        if 0 <= r < tile.grid_rows and 0 <= c < tile.grid_cols:
            return (r, c)
        return None
