"""
SYMBIOSE — fields/population/registry.py
Déclaration data-driven des espèces : canaux `salt`, attractivités florales,
agents butineurs, ponts de cycle de vie, et les fabriques `build_*_specs` qui
assemblent le tout pour le `PopulationField`. Extrait de `population.py`
(scission /refactor 2026-06-30).
"""
from typing import Callable

from fields.foragers import ForagerParams
from fields.lifecycle import LifeCycleBridge
from fields.faune_encyclo import encyclo_meta
from fields.population.constants import _zero_grid, FLOWER_REF
from fields.population.spec import TrophicSpec, PollinatorSpec
from fields.population.resources import (
    _foliage_grid, _monoculture_grid, _limace_food_grid, _rosee_humide_litiere_grid,
    _foliage_solanaceae_grid, _solanaceae_grid, _soil_food_grid, _undisturbed_grid,
    _mycelium_signal, _litter_grid, _rav_fruit_signal, _espece_grid, _stability_grid,
    _auxiliaire_habitat_grid, _undisturbed_structure_grid, _merle_food_grid,
    _base_habitat_grid, _pile_grid, _ravageur_grid, _abeille_habitat_grid,
    _pollinisateur_habitat_grid, _osmie_habitat_grid,
)


# ---------------------------------------------------------------------------
# INSTANCES NON-POLLINISATRICES (chaîne trophique — CONCEPTION_VIE_MACRO.md §2.2)
# ---------------------------------------------------------------------------
# Canaux _hash_noise dédiés (décorrélés) par guilde pour les positions sprites.
_SALT_RAVAGEUR      = 0x2A0001
_SALT_PUCERON       = _SALT_RAVAGEUR   # puceron = héritier du champ ravageur (④b, continuité sprites)
_SALT_LIMACE        = 0x2A6001
_SALT_DORYPHORE     = 0x2A7001
_SALT_AUXILIAIRE    = 0x2A1001
_SALT_COCCINELLE    = _SALT_AUXILIAIRE   # coccinelle = héritière du champ auxiliaire (④c, continuité sprites)
_SALT_CHRYSOPE      = 0x2A8001
_SALT_CARABE        = 0x2A9001
_SALT_MERLE         = 0x2AA001
_SALT_HERISSON      = 0x2AB001
_SALT_POLLINISATEUR = 0x2A2001   # réutilisé par l'abeille (héritière du champ historique)
_SALT_VERS          = 0x2A3001
_SALT_LOMBRIC       = _SALT_VERS   # lombric = héritier du champ vers_de_terre (④d, continuité sprites)
_SALT_CLOPORTE      = 0x2AC001
_SALT_SYRPHE        = 0x2A4001
_SALT_PAPILLON      = 0x2A5001
_SALT_BOURDON       = 0x2AD001   # pollinisateur B précoce/frais (⑤ catalogue enrichi)
_SALT_OSMIE         = 0x2AE001   # abeille solitaire niche-bois (⑤ catalogue enrichi)


def build_population_specs() -> list[TrophicSpec]:
    """
    Construit les specs NON pollinisatrices dans l'ORDRE DE TICK = **toutes les
    PROIES avant tous les PRÉDATEURS**. Ravageurs (puceron/limace/doryphore, ④b) et
    détritivores (lombric/cloporte, ④d) tickent d'abord ; ensuite les auxiliaires
    (coccinelle/chrysope/carabe/merle/hérisson, ④c) chassent chacun SA proie
    fraîchement mise à jour (`_espece_grid`). Chaque proie lit, elle, ses prédateurs
    de la semaine PRÉCÉDENTE (ils tickent après) → décalage d'inertie proie↔prédateur
    cohérent sur TOUTE la chaîne (boom-bust). Les pollinisateurs (registre §E) sont
    ajoutés à part par `build_pollinator_specs` (le conteneur concatène) — ni
    prédateur ni proie ici, donc leur ordre de tick est golden-neutre.

    SCISSION ④d (CONCEPTION_FAUNE_DEDIEE §2) : `vers_de_terre` devient lombric +
    cloporte (`category="detritivore"`). Le détritivore n'est plus un puits isolé :
    le lombric est proie du merle/hérisson, le cloporte du carabe/hérisson → ils
    PASSENT en position proie (avant les auxiliaires) pour que leurs prédateurs les
    lisent frais, comme la chaîne ravageur→auxiliaire (④c). C'est la cause du
    re-figeage golden MAÎTRISÉ #3.
    """
    return [
        TrophicSpec(
            name="puceron", category="ravageur", salt=_SALT_PUCERON,
            resource_fn=_foliage_grid, habitat_fn=_monoculture_grid,
            # Prédateurs nommés (④c) + syrphe_larve (pont ⑤, déjà résolu).
            predators=("coccinelle", "chrysope", "syrphe_larve"),
            daylen_min=10.0, daylen_full=13.0,   # fenêtre estivale
            **encyclo_meta("puceron"),
        ),
        TrophicSpec(
            name="limace", category="ravageur", salt=_SALT_LIMACE,
            resource_fn=_limace_food_grid, habitat_fn=_rosee_humide_litiere_grid,
            predators=("carabe", "herisson"),    # ④c (habitat abreuvé par la rosée ⑤)
            # ④d : le signal fruit pourri (`_rav_fruit_signal`), porté TRANSITOIREMENT
            # par la limace en ④b, passe au CLOPORTE (détritivore dédié, doc §C13,
            # défaut « cloporte seul »). La limace n'a plus de terme-source fruit.
            daylen_min=9.0, daylen_full=12.0,    # humide/frais : fenêtre plus large/précoce
            **encyclo_meta("limace"),
        ),
        TrophicSpec(
            name="doryphore", category="ravageur", salt=_SALT_DORYPHORE,
            resource_fn=_foliage_solanaceae_grid, habitat_fn=_solanaceae_grid,
            predators=("carabe",),               # ④c (inactif jusque-là)
            daylen_min=10.0, daylen_full=13.0,   # fenêtre estivale
            **encyclo_meta("doryphore"),
        ),
        # --- Catégorie `detritivore` : 2 espèces nommées (scission ④d, doc §2) ----
        # Position PROIE (avant les auxiliaires) : lombric/cloporte sont mangés par
        # merle/hérisson/carabe → ils doivent ticker AVANT pour être lus frais.
        TrophicSpec(
            # lombric = héritier du champ `vers_de_terre` (salt identique → continuité
            # sprites) ; ressource = MO+microbiome du sol (pas la litière de surface).
            name="lombric", category="detritivore", salt=_SALT_LOMBRIC,
            resource_fn=_soil_food_grid, habitat_fn=_undisturbed_grid,
            predators=("merle", "herisson"),     # ④d : le ver n'est plus un puits isolé
            # Attraction fongivore (sprint mycélium ④) : le réseau mycélien dense
            # gonfle le détritivore du sol (collemboles brouteurs d'hyphes) — terme
            # ADDITIF, mycelium=0 ⇒ neutre. Interconnexion champignon ↔ faune (§1.1).
            signal_fn=_mycelium_signal,
            daylen_min=8.5, daylen_full=10.0,    # LARGE : sol tamponné, quasi toute l'année
            **encyclo_meta("lombric"),
        ),
        TrophicSpec(
            # cloporte = détritivore de LITIÈRE (≠ lombric, qui fait l'humus du sol).
            # Partage la ressource litière avec la limace (compétition implicite) et
            # son habitat humide. Reçoit le signal fruit POURRI (charognard, doc §C13).
            name="cloporte", category="detritivore", salt=_SALT_CLOPORTE,
            resource_fn=_litter_grid, habitat_fn=_rosee_humide_litiere_grid,
            predators=("carabe", "herisson"),    # ④d (habitat abreuvé par la rosée ⑤)
            signal_fn=_rav_fruit_signal,         # fruit pourri → cloporte (repris de la limace)
            daylen_min=9.0, daylen_full=12.0,    # humide : fenêtre large/précoce (comme la limace)
            **encyclo_meta("cloporte"),
        ),
        # --- Catégorie `auxiliaire` : 5 espèces nommées (scission ④c, doc §2) ----
        # Chacune chasse SA proie nommée (`_espece_grid`) avec SON habitat propre.
        # Sans prédateur (sommets de chaîne de jardin, doc §5.5) ; leur frein est la
        # fenêtre + l'habitat. Le fruit frais (ex-signal de l'auxiliaire) devient la
        # RESSOURCE du merle (`_merle_food_grid`, C13).
        TrophicSpec(
            name="coccinelle", category="auxiliaire", salt=_SALT_COCCINELLE,
            resource_fn=_espece_grid("puceron"), habitat_fn=_stability_grid,
            predators=(),
            daylen_min=10.0, daylen_full=13.0,   # estivale (suit le puceron)
            **encyclo_meta("coccinelle"),
        ),
        TrophicSpec(
            name="chrysope", category="auxiliaire", salt=_SALT_CHRYSOPE,
            resource_fn=_espece_grid("puceron"), habitat_fn=_auxiliaire_habitat_grid,
            predators=(),
            daylen_min=10.0, daylen_full=13.0,   # estivale
            **encyclo_meta("chrysope"),
        ),
        TrophicSpec(
            name="carabe", category="auxiliaire", salt=_SALT_CARABE,
            resource_fn=_espece_grid("limace"), habitat_fn=_undisturbed_structure_grid,
            predators=(),
            daylen_min=9.0, daylen_full=12.0,    # nocturne→large (élargie comme la limace, sa proie)
            **encyclo_meta("carabe"),
        ),
        TrophicSpec(
            name="merle", category="auxiliaire", salt=_SALT_MERLE,
            resource_fn=_merle_food_grid, habitat_fn=_base_habitat_grid,
            predators=(),
            daylen_min=8.5, daylen_full=10.0,    # toute saison (oiseau résident, fenêtre LARGE)
            **encyclo_meta("merle"),
        ),
        TrophicSpec(
            name="herisson", category="auxiliaire", salt=_SALT_HERISSON,
            resource_fn=_espece_grid("limace"), habitat_fn=_pile_grid,
            predators=(),
            daylen_min=9.0, daylen_full=12.0,    # nocturne→large
            **encyclo_meta("herisson"),
        ),
    ]


# ---------------------------------------------------------------------------
# REGISTRE DATA-DRIVEN DES POLLINISATEURS (arc pollinisation §C/§E)
# ---------------------------------------------------------------------------
# Le champ unique `pollinisateur` (proxy `_flower_grid`, stade ≥ 2) est REMPLACÉ
# par N champs PAR TYPE. Chaque type est déclaré par DONNÉE (`PollinatorSpec`) :
# sa ressource = nectar = Σ_plantes (floraison × préférence_florale[famille]) —
# la VRAIE floraison (tronçon ①) pondérée par le type (§C.1). Ajouter un type
# (bourdon, abeille solitaire…) = ajouter une entrée, sans recoder le mécanisme.
# La densité TOTALE (somme des types) est ce que lisent `pollinator_reach`
# (brassage) et la Vigueur macro — cf. EcoFields.pollinator_density.
POLLINATOR_NAMES = ("abeille", "syrphe", "papillon", "bourdon", "osmie")

# Préférences florales PAR TYPE (placeholders, calibrage post-test §E.2). Familles
# absentes → `_ATTRACT_DEFAUT`. Anémophiles (Poaceae/Fagaceae/Juglandaceae) ≈ 0.
_ATTRACT_DEFAUT  = 0.30   # fleur « générique » d'une famille non cataloguée
_ATTRACT_ABEILLE = {      # mellifères profondes / nectarifères
    "Lamiaceae": 1.0, "Boraginaceae": 1.0, "Fabaceae": 0.85, "Rosaceae": 0.80,
    "Cucurbitaceae": 0.70, "Asteraceae": 0.60, "Brassicaceae": 0.50,
    "Apiaceae": 0.45, "Solanaceae": 0.40, "Caprifoliaceae": 0.40,
    "Amaryllidaceae": 0.30, "Urticaceae": 0.0,
    "Araliaceae": 0.75, "Oleaceae": 0.60,   # lierre = manne tardive ; jasmin mellifère (⑤)
    "Poaceae": 0.0, "Fagaceae": 0.10, "Juglandaceae": 0.10,
}
_ATTRACT_SYRPHE = {       # fleurs ouvertes (composées, ombellifères)
    "Apiaceae": 1.0, "Asteraceae": 1.0, "Brassicaceae": 0.90, "Boraginaceae": 0.60,
    "Rosaceae": 0.60, "Caprifoliaceae": 0.50, "Lamiaceae": 0.40,
    "Cucurbitaceae": 0.40, "Fabaceae": 0.30, "Solanaceae": 0.30,
    "Amaryllidaceae": 0.20, "Urticaceae": 0.0,
    "Araliaceae": 0.80, "Oleaceae": 0.25,   # lierre ombelle ouverte ; jasmin tubulaire (⑤)
    "Poaceae": 0.0, "Fagaceae": 0.0, "Juglandaceae": 0.0,
}
_ATTRACT_PAPILLON = {     # fleurs tubulaires / composées riches en nectar
    "Lamiaceae": 1.0, "Asteraceae": 0.90, "Boraginaceae": 0.70, "Apiaceae": 0.50,
    "Fabaceae": 0.50, "Cucurbitaceae": 0.40, "Rosaceae": 0.40,
    "Brassicaceae": 0.30, "Solanaceae": 0.30, "Caprifoliaceae": 0.30,
    "Amaryllidaceae": 0.20, "Urticaceae": 0.0,
    "Araliaceae": 0.40, "Oleaceae": 0.90,   # jasmin tubulaire parfumé = table du papillon (⑤)
    "Poaceae": 0.0, "Fagaceae": 0.0, "Juglandaceae": 0.0,
}
_ATTRACT_BOURDON = {      # langue longue : Fabacées/Lamiacées + BUZZ Solanacées (⑤)
    "Fabaceae": 1.0, "Lamiaceae": 1.0, "Boraginaceae": 0.90, "Rosaceae": 0.70,
    "Cucurbitaceae": 0.70, "Solanaceae": 0.65, "Asteraceae": 0.55,
    "Brassicaceae": 0.45, "Apiaceae": 0.40, "Caprifoliaceae": 0.40,
    "Amaryllidaceae": 0.30, "Urticaceae": 0.0,
    "Araliaceae": 0.50, "Oleaceae": 0.55,   # langue longue → jasmin tubulaire (⑤)
    "Poaceae": 0.0, "Fagaceae": 0.10, "Juglandaceae": 0.10,
}
_ATTRACT_OSMIE = {        # abeille des vergers : Rosacées (arbres fruitiers) + Apiacées (⑤)
    "Rosaceae": 1.0, "Apiaceae": 0.85, "Brassicaceae": 0.75, "Boraginaceae": 0.65,
    "Fabaceae": 0.55, "Lamiaceae": 0.50, "Asteraceae": 0.50,
    "Cucurbitaceae": 0.40, "Caprifoliaceae": 0.40, "Solanaceae": 0.35,
    "Amaryllidaceae": 0.25, "Urticaceae": 0.0,
    "Araliaceae": 0.40, "Oleaceae": 0.35,   # grimpantes ⑤
    "Poaceae": 0.0, "Fagaceae": 0.10, "Juglandaceae": 0.10,
}


def _make_nectar_grid(attractivite: dict, defaut: float) -> Callable:
    """Fabrique la resource_fn d'un type de pollinisateur (§C.1) : nectar perçu =
    Σ_plantes vivantes en floraison (floraison × préférence[famille]) réparti sur
    l'empreinte canopée, normalisé par FLOWER_REF. REMPLACE `_flower_grid` : la
    ressource suit la VRAIE floraison (①) au lieu du proxy stade ≥ 2.

    Invariant golden : floraison = 0 partout (aucune plante en fleur) ⇒ grille
    nulle ⇒ champ pollinisateur nul (comme une absence de fleur)."""
    def _grid(eco, tile, plants) -> list[list[float]]:
        g = _zero_grid(eco.rows, eco.cols)
        for p in plants:
            if not p.is_alive or p.floraison <= 0.0:
                continue
            w = p.floraison * attractivite.get(p.plant_class.family, defaut)
            if w <= 0.0:
                continue
            for (r, c) in p.foliar_plots:
                if 0 <= r < eco.rows and 0 <= c < eco.cols:
                    g[r][c] += w
        for r in range(eco.rows):
            for c in range(eco.cols):
                g[r][c] = min(1.0, g[r][c] / FLOWER_REF)
        return g
    return _grid


# Paramètres d'agent butineur PAR TYPE (§F, tronçon ③ — placeholders calibrage).
# L'abeille : nombreuse, tournée longue, large perception (forte porteuse de pollen).
# Le syrphe : moins nombreux, tournée courte, perception serrée. Le papillon :
# peu nombreux mais bonne perception (vol large). deposit/recharge homogènes.
_FORAGER_ABEILLE  = ForagerParams(n_max=12, substeps=6, perception=2, deposit=0.5, recharge=0.5)
_FORAGER_SYRPHE   = ForagerParams(n_max=8,  substeps=4, perception=1, deposit=0.4, recharge=0.5)
_FORAGER_PAPILLON = ForagerParams(n_max=6,  substeps=5, perception=2, deposit=0.4, recharge=0.5)
# Le bourdon : peu nombreux mais TRAPU, fort porteur de pollen (dépôt élevé), longue
# tournée. L'osmie : solitaire (effectif faible) mais très efficace par fleur (scopa
# pileuse → dépôt élevé), tournée courte. Placeholders §E.2, calibrage post-test.
_FORAGER_BOURDON  = ForagerParams(n_max=8,  substeps=6, perception=2, deposit=0.6, recharge=0.5)
_FORAGER_OSMIE    = ForagerParams(n_max=5,  substeps=4, perception=2, deposit=0.6, recharge=0.5)

# Ponts de cycle de vie PAR TYPE (§D, tronçon ⑤). La chenille (→ papillon) mange le
# FEUILLAGE (`_foliage_grid`, même ressource que le ravageur — elle s'ajoute à la
# pression d'herbivorie) ; la syrphe_larve (→ syrphe) prédate le RAVAGEUR
# (`_ravageur_grid` — elle est le symétrique bénéfique). Fenêtres de PONTE estivales
# (placeholders §D.5). L'abeille n'a pas de pont (nid hors sol).
_BRIDGE_PAPILLON = LifeCycleBridge(
    larva="chenille", larva_nourrie="chenille_nourrie", adult="papillon",
    resource_fn=_foliage_grid, daylen_min=11.0, daylen_full=13.0)
_BRIDGE_SYRPHE = LifeCycleBridge(
    larva="syrphe_larve", larva_nourrie="syrphe_larve_nourrie", adult="syrphe",
    resource_fn=_ravageur_grid, daylen_min=10.5, daylen_full=12.5)


def build_pollinator_registry() -> list[PollinatorSpec]:
    """Registre §E des types de pollinisateurs (donnée pure). Trois types au
    démarrage (abeille/syrphe/papillon, §E.2), extensible par données. Source
    UNIQUE de l'attractivité florale, des fenêtres photopériodiques et des
    paramètres butineurs — lue à la fois par `build_pollinator_specs` (champs) et
    par `engine._tick_butineurs` (agents §F, qui a besoin de l'attractivité)."""
    return [
        PollinatorSpec(
            name="abeille", salt=_SALT_POLLINISATEUR,
            attractivite=_ATTRACT_ABEILLE, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_abeille_habitat_grid,    # rondelle + bump ruche peuplée (§H.2)
            daylen_min=11.5, daylen_full=14.0,   # été LARGE
            forager=_FORAGER_ABEILLE,
        ),
        PollinatorSpec(
            name="syrphe", salt=_SALT_SYRPHE,
            attractivite=_ATTRACT_SYRPHE, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_auxiliaire_habitat_grid,
            daylen_min=10.5, daylen_full=13.0,   # printemps → été (précoce)
            forager=_FORAGER_SYRPHE, bridge=_BRIDGE_SYRPHE,
        ),
        PollinatorSpec(
            name="papillon", salt=_SALT_PAPILLON,
            attractivite=_ATTRACT_PAPILLON, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_pollinisateur_habitat_grid,
            daylen_min=12.5, daylen_full=14.5,   # été
            forager=_FORAGER_PAPILLON, bridge=_BRIDGE_PAPILLON,
        ),
        # --- pollinisateurs B (catalogue enrichi ⑤) — sans pont larvaire --------
        PollinatorSpec(
            name="bourdon", salt=_SALT_BOURDON,
            attractivite=_ATTRACT_BOURDON, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_pollinisateur_habitat_grid,
            daylen_min=9.5, daylen_full=12.0,    # PRÉCOCE/frais : jours courts tolérés
            forager=_FORAGER_BOURDON,            # comble la fenêtre où l'abeille n'est pas
        ),
        PollinatorSpec(
            name="osmie", salt=_SALT_OSMIE,
            attractivite=_ATTRACT_OSMIE, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_osmie_habitat_grid,      # rondelle + niche-bois (pile, §5.3)
            daylen_min=10.0, daylen_full=12.5,   # printanier (abeille des vergers)
            forager=_FORAGER_OSMIE,
        ),
    ]


def build_lifecycle_bridges() -> list[LifeCycleBridge]:
    """Ponts de cycle de vie (§D) extraits du registre §E — source UNIQUE. Deux
    au démarrage (chenille→papillon, syrphe_larve→syrphe) ; l'abeille (bridge=None)
    est écartée. Lu par EcoFields (instanciation des champs larvaires + tick)."""
    return [ps.bridge for ps in build_pollinator_registry() if ps.bridge is not None]


def build_pollinator_specs() -> list[TrophicSpec]:
    """Registre §E → TrophicSpec prêts pour le `PopulationField` générique.
    Ressource = nectar (floraison × attractivite), habitat = rondelle dédiée, ni
    prédateur ni signal fruit. Les fenêtres photopériodiques diffèrent par type
    (l'abeille large, le syrphe précoce, le papillon estival) — placeholders §E.2.
    `**encyclo_meta` splat le blurb/graphe d'encyclopédie (⑥) — DONNÉE PURE jamais
    lue par le tick, comme pour les trophiques (golden NEUTRE)."""
    return [
        TrophicSpec(
            name=ps.name, category="pollinisateur", salt=ps.salt,
            resource_fn=_make_nectar_grid(ps.attractivite, ps.attractivite_defaut),
            habitat_fn=ps.habitat_fn, predators=(),
            daylen_min=ps.daylen_min, daylen_full=ps.daylen_full,
            **encyclo_meta(ps.name),
        )
        for ps in build_pollinator_registry()
    ]
