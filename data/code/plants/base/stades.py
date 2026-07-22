"""
SYMBIOSE — plants/base/stades.py
Unités de la morphologie : stade de croissance, segment de structure procédurale,
fruit traçable + dérivation des sites reproducteurs. Couche basse de `plants.base`
(aucune dépendance interne au paquet).
"""

from __future__ import annotations
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# STADE DE CROISSANCE
# ---------------------------------------------------------------------------

@dataclass
class GrowthStage:
    name: str                        # "semis", "jeune", "adulte", "mature"
    duration_weeks: int              # durée minimale avant passage au stade suivant (0 = vivace)
    strate: str                      # "haute","moyenne","basse","sol","grimpante"
    vigueur_cost: int = 0            # coût Vigueur pour atteindre ce stade
    effects: list[dict] = field(default_factory=list)  # effets data-driven du stade
    callback: str | None = None      # clé dans EFFECT_REGISTRY si effet complexe
    # Empreintes métriques (cm) — None ⇒ défaut de la strate (STRATE_DEFAULTS)
    canopy_height: float | None = None   # hauteur potentielle de la canopée
    canopy_radius: float | None = None   # rayon de la canopée (ombre + foliar_plots)
    root_radius:   float | None = None   # rayon racinaire (uptake + root_plots)

# ---------------------------------------------------------------------------
# SEGMENT — unité de la structure morphologique (croissance procédurale)
# ---------------------------------------------------------------------------
#
# D29 réorienté (croissance procédurale, tronçon 1). Une plante n'est plus
# décrite par son seul stade : elle porte un ARBRE de segments enraciné au
# collet (docs/vegetal/croissance/conception_croissance.md §C). Pour CE tronçon la structure est
# INERTE — elle pousse à côté (sim/growth.py) mais n'est PAS encore lue par
# l'empreinte (height_at vient toujours des stades). Le câblage = tronçon 2.
#
# Représentation actée : base + direction + longueur (l'extrémité = base +
# dir·length_cm). `has_bud` (bourgeon axillaire dormant) matérialise le §D.3 :
# un segment porte un bourgeon qui peut débourrer une fois quand l'auxine
# locale tombe sous le seuil. `organs` reste vide ici (tronçon 5).

@dataclass
class Segment:
    parent: int | None               # index du segment porteur (None = collet)
    base: tuple                      # (x_cm, y_cm, z_cm) — origine
    dir: tuple                       # vecteur directeur unitaire 3D
    length_cm: float                 # longueur courante
    thickness_cm: float              # épaisseur (épaissit avec l'âge → vieux bois)
    age_weeks: int                   # âge du segment
    auxin: float                     # niveau d'auxine local [0,1] (cf. growth §D.1)
    is_apex: bool                    # True si extrémité de croissance active
    has_bud: bool = True             # bourgeon axillaire dormant (consommé au débourrement)
    organs: list = field(default_factory=list)  # feuilles/fleurs/fruits (tronçon 5)

    # --- Sérialisation (croissance procédurale, tronçon 6 — §J) ---
    # Contrat borné : on ne sérialise QUE le bois (les 9 champs structurels). Les
    # `organs` (feuilles/fleurs/fruits) sont régénérés à la volée par le rendu
    # (tronçon 5) → JAMAIS stockés = l'« option d'allègement » §J, satisfaite par
    # construction. JSON-friendly : `base`/`dir` deviennent des listes, restituées
    # en tuples au chargement (round-trip fidèle, cf. tests/test_croissance.py).
    def to_dict(self) -> dict:
        return {
            "parent": self.parent,
            "base": list(self.base),
            "dir": list(self.dir),
            "length_cm": self.length_cm,
            "thickness_cm": self.thickness_cm,
            "age_weeks": self.age_weeks,
            "auxin": self.auxin,
            "is_apex": self.is_apex,
            "has_bud": self.has_bud,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Segment":
        return cls(
            parent=d["parent"],
            base=tuple(d["base"]),
            dir=tuple(d["dir"]),
            length_cm=d["length_cm"],
            thickness_cm=d["thickness_cm"],
            age_weeks=d["age_weeks"],
            auxin=d["auxin"],
            is_apex=d["is_apex"],
            has_bud=d.get("has_bud", True),
        )

# ---------------------------------------------------------------------------
# FRUIT — organe reproducteur traçable (décompo·compost ③, absorbe D19)
# ---------------------------------------------------------------------------
#
# Un fruit cesse d'être un PROXY DE RENDU saisonnier (REPRO_BY_SEASON, côté
# tools/render_structure) : il devient un ÉTAT MOTEUR réel porté par la plante.
# Il naît à la nouaison, mûrit semaine après semaine (engine._tick_fruits), se
# mange UN par UN (actions.manger ciblé → déplétion = D19) et tombe en litière
# `fruit` s'il n'est pas cueilli (chute → deposer_litiere → cascade fertilité).
#
# `segment_id` = index, AU MOMENT DE LA NOUAISON, du segment porteur dans
# `plant.segments` (repère pour la VUE ⑥ qui placera le sprite ; les indices
# pouvant glisser ensuite avec la croissance, c'est un repère best-effort,
# réconcilié quand Godot reprendra). Le MOTEUR ne lit JAMAIS segment_id : seules
# `masse` (litière à la chute) et `maturite` (gain de `manger`, seuil de chute)
# pèsent sur la simulation → déterminisme et golden indépendants de la structure.

@dataclass
class Fruit:
    segment_id: int       # index du segment porteur à la nouaison (repère VUE)
    maturite: float       # 0→1 (mûr), puis >1 = sur-mûr (tombe au-delà du seuil)
    masse:    float       # masse de litière `fruit` déposée à la chute

# Plafond d'organes reproducteurs portés simultanément (anti-fouillis ET borne de
# la dérive litière). Aligné sur le MAX_FRUITS du rendu (tools/render_structure) ;
# constante côté plants (couche basse) pour que `sim` et `tools` la partagent sans
# que `sim` importe `tools` (frontière de couches, CLAUDE.md).
MAX_ORGANS = 10

def organ_sites(plant) -> list:
    """Sites reproducteurs d'une plante = (index de segment porteur, position 3D
    cm en repère tuile-local). PURE géométrie déterministe sur `plant.segments`
    (zéro RNG) selon le profil `organ_site` de l'espèce :
      - `terminal` : tous les apex (bouts de flèche) ;
      - `lateral`  : les apex SAUF le meneur (cime) → fructification sur rameaux.
    Plafonné/sous-échantillonné à MAX_ORGANS (régulier). Source unique des sites,
    partagée par engine._tick_fruits (état moteur) — miroir de la dérivation
    visuelle `_organ_sites` du rendu (tools), qui reste le proxy de la VUE."""
    apex_idx = [i for i, s in enumerate(plant.segments) if s.is_apex]
    if not apex_idx:
        return []
    if plant.plant_class.organ_site == "lateral" and len(apex_idx) > 1:
        def _tip_z(i):
            s = plant.segments[i]
            return s.base[2] + s.dir[2] * s.length_cm
        leader = max(apex_idx, key=_tip_z)
        rest = [i for i in apex_idx if i != leader]
        apex_idx = rest or apex_idx
    sites = []
    for i in apex_idx:
        s = plant.segments[i]
        tip = (s.base[0] + s.dir[0] * s.length_cm,
               s.base[1] + s.dir[1] * s.length_cm,
               s.base[2] + s.dir[2] * s.length_cm)
        sites.append((i, tip))
    if len(sites) > MAX_ORGANS:
        step = len(sites) / MAX_ORGANS
        sites = [sites[int(k * step)] for k in range(MAX_ORGANS)]
    return sites
