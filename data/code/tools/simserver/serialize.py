"""
SYMBIOSE — tools/simserver/serialize.py
Sérialisation lecture-seule du moteur vers JSON : `_world_static` (partie figée,
renvoyée au init) et `_snapshot` (état hebdo). Mixin de `SimServer` (Sprint
refactor global, SS⑤). Aucune écriture dans le moteur : on LIT l'état et on le
met en forme — c'est ce qui garantit que le golden reste intact.
"""
from __future__ import annotations

from sim.engine import saison_de
from sim import vigueur as V      # état Vigueur joueur (ensure/spend/gain, D11)
# Météo PURE (sprint thermique ⑧) : helper consolidé partagé avec l'engine
# (boucle.py étape 1) + signes diégétiques + cas calme. Recalculés ici car le
# snapshot LIT l'état sans accès aux locaux du tick — fonctions pures, golden NEUTRE.
from sim.weather import weather_state, weather_signs, CALME, T_MOY
# Échantillonneur de vie macro (tranche 6·B) : fonction PURE et déterministe
# densité → entités (fields/population.py §3). L'échantillonnage se fait CÔTÉ
# SERVEUR — la vue n'a pas besoin de _hash_noise (kickoff t6 §4).
from fields.population import sample_sprites
# Sémiologie foliaire (D33) : détecteurs PURS des stresseurs chroniques, miroirs
# fidèles des seuils des mécaniques qui blessent. Remplace le bool `chlorose` du ⑨
# par la liste `leaf_symptoms`. Recalcul pur côté serveur (moteur = source de
# vérité, zéro recalcul C#) → golden NEUTRE.
from sim import semiologie
# Table « stade reproducteur visible par saison » du prototype SVG (tranche 6,
# volet A) : import OUTIL → OUTIL (render_structure est un outil, pas le
# moteur), zéro duplication — la table validée visuellement au sprint
# Croissance reste la source unique du proxy saisonnier.
from tools.render_structure import REPRO_BY_SEASON

from .version import DEFAULT_REPRO


class SerializeMixin:
    """Mise en forme JSON du monde statique et du snapshot hebdomadaire."""

    # ------------------------------------------------------- sérialisation

    def _world_static(self) -> dict:
        """Partie STATIQUE du monde (renvoyée une fois, au init) : layout des
        tuiles + maison. Tout ce qui bouge chaque semaine va dans le snapshot."""
        gs = self.engine.game_state
        house = gs["house"]
        hx0, hy0, hx1, hy1 = house.footprint_bounds
        return {
            "tiles": [
                {"id": t.tile_id, "soil": t.soil_type,
                 "rows": t.grid_rows, "cols": t.grid_cols,
                 "origin_x_cm": t.origin_x_cm, "origin_y_cm": t.origin_y_cm}
                for t in gs["tiles"]
            ],
            "house": {"footprint_cm": [hx0, hy0, hx1, hy1],
                      "height_cm": house.height_cm},
        }

    def _snapshot(self) -> dict:
        """Snapshot v0 minimal (kickoff tranche 1) : horloge + plantes vivantes.
        `week` = compteur moteur (prochaine semaine à simuler, 1 = rien simulé) ;
        year/season en sont dérivés. Par plante : position continue LOCALE à sa
        tuile (x_cm/y_cm + tile pour replacer en monde via origin_*_cm) et la
        structure de segments via structure_to_dict() (format Croissance·6, le
        même que tools/export_structure.py → PlantStructure.cs sait déjà lire)."""
        gs = self.engine.game_state
        week = gs["week"]
        week_in_year = ((week - 1) % 52) + 1
        saison = saison_de(week_in_year)
        plants = []
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            for p in tile.plants:
                cls = p.plant_class
                # Socle commun vivant/mort : l'identité (clé de diff côté vue =
                # tile|species|x|y), la position et la STRUCTURE — le bois à
                # dessiner, silhouette nue pour un squelette comme branchage pour
                # un vif. Tout le reste (organes, fruits) ne vaut que pour un vivant.
                base = {
                    "tile": tile.tile_id,
                    "species": cls.__name__,
                    "name": p.name,
                    "x_cm": p.x_cm, "y_cm": p.y_cm,
                    "stage": p.current_stage,
                    "stage_name": p.stage.name,
                    "height_cm": p.current_height,
                    "segments": p.structure_to_dict(),
                }
                # SQUELETTES post-mortem (décompo·compost ②B) : la mort ne retire
                # plus la plante — `engine._tick_skeletons` la garde TANT QU'il
                # reste du bois (seules les vivaces LIGNEUSES persistent ici ; les
                # herbacées, bois=0, sont retirées au tick même de leur mort, donc
                # jamais visibles dans un snapshot). On les EXPOSE en LECTURE pour
                # que la vue dessine la silhouette sèche/couchée. C'est de la pure
                # sérialisation (`tile.plants` contient déjà les morts) : aucune
                # écriture moteur → golden NEUTRE. `dead` est aussi posé (false) sur
                # les vivantes = drapeau explicite, lecture tolérante côté vue.
                if not p.is_alive:
                    base["dead"] = True
                    base["stade_mort"] = p.stade_mort          # "seche" | "couchee"
                    base["bois_restant"] = round(p.bois_restant, 4)
                    base["semaines_mort"] = p.semaines_mort
                    plants.append(base)
                    continue
                # Hints d'organes (tranche 6·A, kickoff §1) : les organes ne
                # sont PAS un état moteur (§J : reconstructibles à la volée) —
                # on expose le proxy SAISONNIER du prototype SVG, la vue
                # dessine. Les FLEURS restent sur ce proxy ; les FRUITS, eux,
                # ont désormais un vrai état moteur (`fruits`, ③).
                repro = REPRO_BY_SEASON.get(cls.__name__, DEFAULT_REPRO)
                base["dead"] = False
                # Sémiologie foliaire (D33, tronçon ①) : LISTE triée de symptômes
                # `[{cause, intensity}]` — généralise le bool `chlorose` du ⑨ à TOUS
                # les stresseurs chroniques (chlorose/sécheresse/asphyxie/ravageurs/
                # sénescence). Détecteurs PURS de sim/semiologie : chacun miroir du
                # SEUIL de la mécanique qui blesse (le signe ne ment pas, §2.4). La vue
                # teinte/déforme le feuillage ; elle ne relit aucun champ moteur. Liste
                # vide = plante saine. Lecture pure → golden NEUTRE (espèces neutres du
                # smoke, sols drainants : aucun symptôme).
                base["leaf_symptoms"] = semiologie.leaf_symptoms(p, eco, saison)
                base["foliage_density"] = cls.foliage_density_at(p, saison)
                base["organ"] = repro.get(saison)
                base["organ_site"] = cls.organ_site
                # Fruits traçables (③, D19) : VRAI état moteur (≠ proxy `organ`).
                # Index implicite = position dans la liste (clé du geste `manger`
                # ciblé). `segment` = ancrage structurel pour que la vue place le
                # sprite ; `maturite` pilote le rendu (vert→mûr→sur-mûr) et le gain
                # à la consommation ; `masse` la taille du sprite.
                base["fruits"] = [
                    {"segment": f.segment_id,
                     "maturite": f.maturite,
                     "masse": f.masse}
                    for f in p.fruits
                ]
                plants.append(base)
        # Vie macro (tranche 6·B, kickoff §4) : sprites échantillonnés depuis
        # les champs de population — PURE lecture (sample_sprites ne modifie
        # rien, positions par hash indépendantes de la semaine : un slot vit
        # toujours au même point, il apparaît/disparaît quand la densité
        # franchit son seuil).
        # SÉRIALISATION PAR ESPÈCE (faune ④e/⑥) : la clé est `f.spec.name` → depuis
        # la scission ④b/c/d le snapshot émet 10 clés d'espèce (puceron…cloporte) au
        # lieu des 3 anciennes guildes. Le pont accepte désormais `target.espece`
        # (⑥a, simserver/actions.py:ecraser ; `guilde` reste en repli pour la bascule
        # client). RESTE en ⑥b (vue Godot) : la TABLE sprite par espèce côté client.
        # Arrondis : x/y_frac 3 déc. (= 0,05 cm dans le plot), activite 2 —
        # et round() est déterministe, la clé de diff côté vue reste stable.
        sprites = {}
        foragers = {}
        structures = {}
        litiere = {}
        alarme = {}
        temperature = {}
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            sprites[tile.tile_id] = {
                f.spec.name: [
                    [s.row, s.col, round(s.x_frac, 3), round(s.y_frac, 3),
                     round(s.activite, 2)]
                    for s in sample_sprites(f, gs["seed"])]
                for f in eco.populations.values()}
            # Butineurs déterministes (arc pollinisation §F, 0.3.9) : agents
            # échantillonnés/marchés par engine._tick_butineurs (eco.foragers, déjà
            # rempli par le tick). Format COMPACT (cf. `sprites`) par tuile :
            # [guild, r, c, x_frac, y_frac, espèce-cible, charge(0/1)]. PURE lecture
            # → golden NEUTRE. La vue dessine l'insecte de fleur en fleur.
            foragers[tile.tile_id] = [
                [a.guild, a.row, a.col, round(a.x_frac, 3), round(a.y_frac, 3),
                 a.target, int(a.carrying)]
                for a in (eco.foragers or [])]
            # Structures posables (⑤, 0.3.5) : index implicite = position dans la
            # liste = `target.structure` des gestes. `compost_mur` = jauge mûre
            # épandable ; `contenu` = masse BRUTE en cours de maturation (Σ des
            # parcelles du contenu, 0.3.8). La vue remplit le bac/pile ∝
            # (contenu + compost_mur) → on VOIT la structure se remplir au
            # compostage (avant maturation) et se vider à l'épandage. PURE lecture.
            # Ruche (⑥, 0.4.0) : `essaim`/`miel` (0 pour bac/pile) → la vue dessine le
            # peuplement et la réserve de miel. PURE ajout de sérialisation.
            structures[tile.tile_id] = [
                {"kind": st.kind, "plot": list(st.plot),
                 "compost_mur": round(st.compost_mur, 4),
                 "contenu": round(sum(p.masse for p in st.contenu), 4),
                 "essaim": round(st.essaim, 4), "miel": round(st.miel, 4)}
                for st in eco.structures]
            # Litière typée par plot (décompo·compost ①, rendue par la vue en
            # 03·B) : la couche fraîche de nécromasse au sol. On n'expose QUE ce
            # qui se dessine — la parcelle `diffus` (exsudats racinaires, humus
            # permanent, masse souvent > 0 via croissance) n'est PAS de la litière
            # de surface : on l'écarte du tissu dominant ET du total. Format
            # COMPACT (cf. `sprites`) : par plot non vide `[r, c, tissu_dominant,
            # masse, age_sem]` — dominant = parcelle de plus grande masse hors
            # `diffus`, masse = Σ des parcelles de surface (densité ∝ masse côté
            # vue). Les plots sans litière de surface sont OMIS (liste creuse).
            # `age_sem` (rendu feuillage ⑥, 0.5.6) = ÂGE MOYEN pondéré par la masse
            # des parcelles de surface : proxy d'ÉTAT DE DÉCOMPO déjà calculé par le
            # moteur (`Parcelle.age_sem`, semaines depuis dépôt) — la vue assombrit/
            # désature la litière de feuilles à mesure qu'elle vieillit (dérive vers
            # l'humus, §6.3). TRANSPORT pur (donnée existante, aucun calcul moteur
            # nouveau) → golden NEUTRE. PURE lecture (`eco.litiere` déjà rempli par
            # le tick).
            plots = []
            for r in range(eco.rows):
                for c in range(eco.cols):
                    surface = [p for p in eco.litiere[r][c]
                               if p.tissu != "diffus" and p.masse > 0.0]
                    if not surface:
                        continue
                    dominant = max(surface, key=lambda p: p.masse)
                    total = sum(p.masse for p in surface)
                    # Âge moyen pondéré par la masse (total > 0 garanti : surface
                    # ne retient que les parcelles masse > 0). Litière fraîche
                    # (age ≈ 0) = brun-roux vif ; vieillie, elle fond dans le sol.
                    age_moy = sum(p.age_sem * p.masse for p in surface) / total
                    plots.append([r, c, dominant.tissu,
                                  round(total, 4), round(age_moy, 3)])
            litiere[tile.tile_id] = plots
            # Phéromone d'alarme apienne (⑦, §J, 0.4.1) : liste CREUSE des plots en
            # alarme `[r, c, intensite]` (foyers > 0 seulement). Godot lit l'intensité
            # au curseur → les abeilles présentes piquent (réaction temps réel, coût
            # Vigueur côté vue). PURE lecture (`eco.alarme` rempli par les déclencheurs
            # + décru par le tick) → golden NEUTRE (vide tant qu'aucune abeille écrasée
            # / aucun miel récolté nu). Champ optionnel côté vue (tolérance pré-0.4.1).
            af = getattr(eco, "alarme", None)
            foyers = []
            if af is not None:
                for r in range(eco.rows):
                    for c in range(eco.cols):
                        v = af.data[r][c]
                        if v > 0.0:
                            foyers.append([r, c, round(v, 4)])
            alarme[tile.tile_id] = foyers
            # Carte température par tuile (sprint thermique ⑧, §B) : ÉTATS
            # persistants déjà calculés par le tick → lecture DIRECTE (≠ météo
            # scalaire, recalculée par fonction pure plus bas). `snow` = manteau
            # neigeux scalaire (⑦, voile blanc ∝ snow côté vue). `t_sol` = grille 2D
            # rows×cols de la température de surface spatialisée (heatmap ⑩) ;
            # T_air uniforme N'EST PAS dupliquée par plot (elle vit dans `weather`).
            # PURE lecture (`eco.snow`/`eco.temperature_sol` remplis par le tick)
            # → golden NEUTRE. Champ optionnel côté vue (tolérance pré-0.5.0).
            temperature[tile.tile_id] = {
                "snow": round(eco.snow, 3),
                "t_sol": [[round(eco.temperature_sol.data[r][c], 2)
                           for c in range(eco.cols)] for r in range(eco.rows)],
            }
        # Météo scalaire GLOBALE du tick (sprint thermique ⑧, §A) : la météo qui a
        # produit l'état COURANT est celle de la semaine DÉJÀ simulée = `week − 1`
        # (`week` = prochaine à simuler). `weather_state` étant PURE, on la RECALCULE
        # (rien à stocker côté moteur) → golden NEUTRE. `signs` = préavis diégétique
        # des événements à venir (1-2 sem, philo #5) ; on expose le flag `signed`,
        # le filtrage par palier de maîtrise (D12) reste à la charge de la VUE.
        # À l'init (rien simulé, `last < 1`) : temps calme, normale, pas de signe.
        last = gs["week"] - 1
        if last >= 1:
            ev, t_air, nebul = weather_state(gs["seed"], last)
            signs = weather_signs(gs["seed"], last, horizon=2)
        else:
            ev, t_air, nebul, signs = CALME, T_MOY, 0.10, []
        weather = {
            "kind": ev.kind,
            "intensity": round(ev.intensity, 3),
            "scope": ev.scope,
            "nebulosite": round(nebul, 3),
            "t_air": round(t_air, 2),
            "signs": [
                {"kind": s.kind, "in_weeks": s.in_weeks,
                 "signs": list(s.signs), "signed": s.signed}
                for s in signs
            ],
        }
        # Bloc joueur (tranche 4, lecture seule) : la vue affiche la Vigueur
        # au HUD. vigueur_max passe par la façade (bonus maîtrise compris).
        # `seeds` (0.3.3) = lots PLANTABLES de la banque-joueur, {clé catalogue:
        # nombre} (lots vides masqués) — la vue propose les graines disponibles à
        # `planter`. Pur compteur : la génétique reste côté moteur (D17/D22).
        player = gs["current_player"]
        st = V.ensure_player(gs, player)
        bank = gs.get("player_seed_bank")
        seeds = {sp: len(lot) for sp, lot in bank.lots.items()
                 if lot} if bank is not None else {}
        return {"week": week, "week_in_year": week_in_year,
                "year": (week - 1) // 52 + 1, "season": saison,
                "player": {"vigueur": st["courante"],
                           "vigueur_max": V.vigueur_max(gs, player),
                           "seeds": seeds},
                "plants": plants, "sprites": sprites, "foragers": foragers,
                "structures": structures, "litiere": litiere, "alarme": alarme,
                "weather": weather, "temperature": temperature,
                "containers": self._containers_snapshot(gs, saison)}

    def _containers_snapshot(self, gs: dict, saison: str) -> list:
        """Conteneurs posés par le joueur (pots/bacs ④, 0.5.7). Index implicite =
        position dans la liste = `target.container` des gestes. Format par conteneur :
        identité (id/kind/substrat/mobile/fond_ouvert), position monde (x_cm/y_cm,
        que `deplacer_pot` change → la vue replace le pot), géométrie (rows/cols,
        volume — pilote l'effet nain) ; `plants` = la/les plante(s) du mini-sol en
        forme COMPACTE (espèce/position/structure/fruits/symptômes — assez pour la
        future vue ⑥) ; `eco_summary` = scalaires HUD au plot (0,0) du mini-sol
        (humidité/NPK/pH/microbiome/structure). PURE lecture (`gs["containers"]` déjà
        tické par la boucle 17b) → golden NEUTRE : le smoke ne pose aucun conteneur,
        la liste est VIDE → bloc `[]`. Index = `target.container` (cf. routeur)."""
        out = []
        for ctn in gs.get("containers", []):
            eco = ctn.eco
            cplants = []
            for p in ctn.plants:
                pd = {"species": p.plant_class.__name__, "name": p.name,
                      "x_cm": p.x_cm, "y_cm": p.y_cm,
                      "stage": p.current_stage, "stage_name": p.stage.name,
                      "height_cm": p.current_height,
                      "dead": not p.is_alive,
                      "segments": p.structure_to_dict()}
                if p.is_alive:
                    pd["leaf_symptoms"] = semiologie.leaf_symptoms(p, eco, saison)
                    pd["fruits"] = [{"segment": f.segment_id, "maturite": f.maturite,
                                     "masse": f.masse} for f in p.fruits]
                cplants.append(pd)
            out.append({
                "id": ctn.container_id, "kind": ctn.kind,
                "substrat": ctn.substrat, "volume": ctn.volume_litres,
                "x_cm": ctn.x_cm, "y_cm": ctn.y_cm,
                "mobile": ctn.mobile, "fond_ouvert": ctn.fond_ouvert,
                "rows": ctn.rows, "cols": ctn.cols,
                "plants": cplants,
                "eco_summary": {
                    "humidite": round(eco.humidite.at_plot(0, 0), 4),
                    "n": round(eco.n.at_plot(0, 0), 4),
                    "p": round(eco.p.at_plot(0, 0), 4),
                    "k": round(eco.k.at_plot(0, 0), 4),
                    "ph": round(eco.ph.at_plot(0, 0), 4),
                    "microbiome": round(eco.microbiome.at_plot(0, 0), 4),
                    "structure": round(eco.structure_sol.at_plot(0, 0), 4)},
            })
        return out
