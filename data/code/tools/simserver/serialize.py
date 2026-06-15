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
# Échantillonneur de vie macro (tranche 6·B) : fonction PURE et déterministe
# densité → entités (fields/population.py §3). L'échantillonnage se fait CÔTÉ
# SERVEUR — la vue n'a pas besoin de _hash_noise (kickoff t6 §4).
from fields.population import sample_sprites
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
            for p in tile.plants:
                if not p.is_alive:
                    continue
                cls = p.plant_class
                # Hints d'organes (tranche 6·A, kickoff §1) : les organes ne
                # sont PAS un état moteur (§J : reconstructibles à la volée) —
                # on expose le proxy SAISONNIER du prototype SVG, la vue
                # dessine. Le vrai état reproducteur (maturité réelle,
                # déplétion par `manger`) = D19/D33, sprints moteur dédiés.
                repro = REPRO_BY_SEASON.get(cls.__name__, DEFAULT_REPRO)
                plants.append({
                    "tile": tile.tile_id,
                    "species": cls.__name__,
                    "name": p.name,
                    "x_cm": p.x_cm, "y_cm": p.y_cm,
                    "stage": p.current_stage,
                    "stage_name": p.stage.name,
                    "height_cm": p.current_height,
                    "foliage_density": cls.foliage_density_at(p, saison),
                    "organ": repro.get(saison),
                    "organ_site": cls.organ_site,
                    "segments": p.structure_to_dict(),
                    # Fruits traçables (③, D19) : VRAI état moteur (≠ proxy
                    # `organ`). Index implicite = position dans la liste (clé du
                    # geste `manger` ciblé). `segment` = ancrage structurel pour
                    # que la vue place le sprite ; `maturite` pilote le rendu
                    # (vert→mûr→sur-mûr) et le gain à la consommation.
                    "fruits": [
                        {"segment": f.segment_id,
                         "maturite": f.maturite,
                         "masse": f.masse}
                        for f in p.fruits
                    ],
                })
        # Vie macro (tranche 6·B, kickoff §4) : sprites échantillonnés depuis
        # les 4 champs de population — PURE lecture (sample_sprites ne modifie
        # rien, positions par hash indépendantes de la semaine : un slot vit
        # toujours au même point, il apparaît/disparaît quand la densité
        # franchit son seuil). Format compact par guilde, cf. ENGINE_VERSION.
        # Arrondis : x/y_frac 3 déc. (= 0,05 cm dans le plot), activite 2 —
        # et round() est déterministe, la clé de diff côté vue reste stable.
        sprites = {}
        structures = {}
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            sprites[tile.tile_id] = {
                f.spec.name: [
                    [s.row, s.col, round(s.x_frac, 3), round(s.y_frac, 3),
                     round(s.activite, 2)]
                    for s in sample_sprites(f, gs["seed"])]
                for f in eco.populations.values()}
            # Structures posables (⑤, 0.3.5) : index implicite = position dans la
            # liste = `target.structure` des gestes. `compost_mur` = jauge mûre
            # épandable. PURE lecture (la vue dessine bac/pile + jauge en ⑥).
            structures[tile.tile_id] = [
                {"kind": st.kind, "plot": list(st.plot),
                 "compost_mur": round(st.compost_mur, 4)}
                for st in eco.structures]
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
                "plants": plants, "sprites": sprites,
                "structures": structures}
