"""
SYMBIOSE — fields/population/resources.py
Résolution des ressources / habitats / signaux des guildes : grilles
[rows][cols] ∈ [0,1], fonctions PURES en lecture (ne modifient aucun champ).
Inclut les constantes de calibrage propres à ces fonctions (fruit, fongivore,
rosée, scission ravageur/auxiliaire, ruche). Extrait de `population.py`
(scission /refactor 2026-06-30).
"""
from typing import Callable

from fields.population.constants import (
    _zero_grid, _clamp01, FOLIAGE_REF, FLOWER_REF, OM_REF, MONO_REF,
)


# ---------------------------------------------------------------------------
# RESSOURCE RACINAIRE DU CAMPAGNOL (sommet trophique ①, CONCEPTION §2.1)
# ---------------------------------------------------------------------------
# L'herbivore vertébré (campagnol) ne broute PAS le feuillage : il ronge les
# ORGANES SOUTERRAINS (racines, bulbes, tubercules) et la jeune écorce ligneuse au
# collet. Sa ressource se lit donc sur l'empreinte RACINAIRE des plantes
# (`p.root_plots`, mémoïsée) — pas foliaire —, pondérée par la PALATABILITÉ de
# l'organe selon la famille : les bulbes (Amaryllidaceae) et les racines charnues
# sont les mets de choix, le jeune ligneux (écorce tendre) est rongé au collet, le
# reste (herbe, feuillage) compte peu en souterrain. Placeholders, calibrage
# post-test (comme les autres guildes, §5.6). Normalisé par ROOT_REF.
ROOT_REF          = 2.0   # somme de biomasse racinaire perçue saturant la ressource
ROOT_PREF_DEFAUT  = 0.30  # palatabilité racinaire d'une famille non listée (racines fines)
# Familles à organe souterrain charnu très appété (bulbe / tubercule / racine
# pivotante) — le campagnol y creuse en priorité (§2.1).
ROOT_PREF_FAMILLE = {
    "Amaryllidaceae": 1.0,   # bulbes (ail, oignon) — mets de choix
    "Solanaceae": 0.85,      # tubercule (pomme de terre) + racines charnues
    "Fabaceae": 0.55,        # nodosités + racines tendres
    "Asteraceae": 0.50,      # racines pivotantes (pissenlit, topinambour)
    "Brassicaceae": 0.60,    # racines charnues (navet, radis)
    "Poaceae": 0.20,         # racines fibreuses fines — peu appété
}
ROOT_PREF_LIGNEUX = 0.65  # jeune écorce ligneuse annelée au collet (arbustes/arbres jeunes)
LIGNEUX_JEUNE_CM  = 250.0  # hauteur au-delà de laquelle l'écorce est trop épaisse pour être rongée


# ---------------------------------------------------------------------------
# RESSOURCE & HABITAT DES SUPER-PRÉDATEURS (sommet trophique ②, CONCEPTION §2.2)
# ---------------------------------------------------------------------------
# Rapace (aérien) et couleuvre (terrestre) vivent de la DENSITÉ de leurs proies
# (campagnol/merle pour le rapace, campagnol/limace pour la couleuvre) — pas d'une
# ressource végétale : leur `resource_fn` LIT les champs de population déjà mis à
# jour ce tick (les proies tickent AVANT, cf. registry). `_proies_grid(noms)`
# généralise `_espece_grid` à PLUSIEURS proies : somme normalisée des densités.
# Le rapace chasse à vue au-dessus du TERRAIN OUVERT (peu de canopée le gêne) et
# se poste sur un PERCHOIR haut (ligneux mûr) → `_rapace_habitat_grid`.
PROIES_REF        = 1.5   # somme de densité de proies saturant la ressource du prédateur
PERCHOIR_H_CM     = 200.0  # hauteur au-delà de laquelle un ligneux fait perchoir de chasse
RAPACE_OUVERT_W   = 0.6   # part de huntabilité = terrain dégagé (chasse à vue sur sol nu)
RAPACE_PERCHOIR_W = 0.4   # part de huntabilité = présence d'un poste d'affût haut
RAPACE_HUNT_FLOOR = 0.35  # huntabilité PLANCHER : même en zone fermée le rapace chasse un peu


# ---------------------------------------------------------------------------
# ATTRACTION ANIMALE PAR LE FRUIT TOMBÉ (décompo·compost ④, CONCEPTION §4)
# ---------------------------------------------------------------------------
# Une parcelle `fruit` (déposée par engine._tick_fruits à la chute des sur-mûrs)
# émet un signal selon son `age_sem` (succession sur le fruit), AJOUTÉ à la
# capacité de charge des guildes via `signal_fn` (terme additif, clampé) :
#   - FRAIS (age bas) → nourrit l'`auxiliaire` (frugivores, oiseaux) ;
#   - POURRI (age élevé) → appelle le `ravageur` DOMINANT (charognards, mouches)
#     + une PETITE fraction `auxiliaire` (décomposeurs : la décompo n'est jamais
#     pur déchet). Pas de 5ᵉ guilde (tranché Nico).
# Invariant golden : à ZÉRO parcelle `fruit`, sig=0 partout → capacité inchangée.
# Knobs CONSERVATIFS (un tas de fruits ne sature pas la guilde), calibrage post-test.
FRUIT_FRAIS_SEM  = 3.0   # semaines : durée de la fenêtre « frais » (frais→0 au-delà)
FRUIT_POURRI_SEM = 6.0   # semaines au-delà de FRUIT_FRAIS_SEM pour atteindre « pourri » plein
FRUIT_SIGNAL_REF = 0.45  # masse de litière `fruit` saturant l'intensité du signal (≈ 3 fruits)
FRUIT_AUX_GAIN   = 0.50  # boost max de capacité `auxiliaire` d'un tas frais plein
FRUIT_RAV_GAIN   = 0.60  # boost max de capacité `ravageur` d'un tas pourri plein
FRAC_AUX_POURRI  = 0.25  # part du signal pourri qui va AUSSI à l'auxiliaire (décomposeurs)


# ---------------------------------------------------------------------------
# ATTRACTION FONGIVORE PAR LE MYCÉLIUM (sprint mycélium ④, CONCEPTION §1.1)
# ---------------------------------------------------------------------------
# Le champ `mycelium ∈ [0,1]` (réseau fongique, acteur ① du sprint) NOURRIT une
# fraction de la faune fongivore (collemboles/détritivores qui broutent les
# hyphes) : terme ADDITIF à la capacité de charge du `lombric` (détritivore du
# sol, là où vit le réseau), via `signal_fn` — exactement le patron du fruit
# tombé (`_aux_fruit_signal`), pas un retour de la faune sur le champ (philo #2).
# Invariant golden : `mycelium = 0` partout (repos du smoke) ⇒ signal nul ⇒
# capacité strictement inchangée → golden de champ NEUTRE hors mycélium réel.
# Knob CONSERVATIF (un réseau saturé ne dépasse pas le boost du fruit frais),
# calibrage post-test.
FONGIVORE_GAIN = 0.35    # boost max de capacité `detritivore` d'un réseau plein


# ---------------------------------------------------------------------------
# FAUNE ABREUVÉE PAR LA ROSÉE (sprint météo→champs ⑤, §6)
# ---------------------------------------------------------------------------
# Interconnexion « tout coexiste » : la faune du MATIN (limace/cloporte, détritivores
# de surface) gagne un PLANCHER d'habitat les semaines à forte rosée — l'eau de surface
# du matin est leur abreuvoir. Terme ADDITIF à leur habitat ∝ la rosée liquide DÉPOSÉE
# ce tick (`eco.rosee_last`, écrite par `tick_rosee`), normalisée par ROSEE_SURFACE_REF,
# borné par ROSEE_FAUNE_HABITAT_W. Lecture PURE (la faune ne touche pas la rosée — c'est
# le CHAMP qui fait tout, philo #2). Les constantes vivent ICI (la couche `fields/
# population` n'importe PAS `ecofields` — pas de cycle). Sans rosée → terme nul → golden
# NEUTRE pour cette part. Placeholders, calibrage post-test.
ROSEE_SURFACE_REF     = 0.03   # eau liquide/plot saturant le signal de surface [→1]
ROSEE_FAUNE_HABITAT_W = 0.25   # bump max d'habitat des détritivores du matin


# ---------------------------------------------------------------------------
# PAILLAGE = ABRI POUR LA FAUNE OMBROPHILE (sprint équilibre invasion ⑥, D11)
# ---------------------------------------------------------------------------
# Le mulch (`eco.paillage ∈ [0,1]` par plot, posé au geste `pailler`) est un
# HABITAT : les guildes OMBROPHILES du sol (carabe, lombric, cloporte, hérisson,
# limace) — qui redoutent le plein soleil sans couvert — colonisent les zones
# paillées. Terme AJOUTÉ à leur terme d'habitat existant, borné [0,1] :
#     habitat(r,c) += PAILLAGE_ABRI_W · abri_w(nature) · paillage(r,c)
# La QUALITÉ d'abri dépend de la nature (`abri_w` du dict NATURES_MULCH, tronçon
# ④ — le BRF volumineux abrite mieux que la paille), lue via `eco.nature_at`
# (aucun import inverse `fields.population → ecofields` : on lit à travers `eco`).
# Lecture PURE (la faune ne touche pas le mulch — c'est le CHAMP qui fait tout,
# philo #2). La population ticke AVANT `tick_paillage` dans la boucle → elle lit
# le paillage de la semaine PRÉCÉDENTE (décalage uniforme, déterministe, pas de
# RNG neuf). Invariant golden : `paillage = 0` partout (repos du smoke — jamais de
# `pailler`) ⇒ terme nul ⇒ habitat bit-identique → `population_hash` INCHANGÉ.
# PLACEHOLDER, calibrage F5.
PAILLAGE_ABRI_W = 0.5   # bump max d'habitat sous un mulch plein de meilleure nature


def _avec_abri_paillage(base_fn: Callable) -> Callable:
    """Décore une habitat_fn d'une guilde OMBROPHILE : ajoute le refuge offert par
    le mulch à son terme d'habitat de base (borné [0,1]). Sans mulch → base_fn nue
    (golden neutre). Un seul point de couplage → data-driven, pas de branche
    dispersée par guilde (patron des wrappers `_rosee_*`)."""
    def _grid(eco, tile, plants) -> list[list[float]]:
        g = base_fn(eco, tile, plants)
        paillage = getattr(eco, "paillage", None)
        if paillage is None:                    # robustesse pré-③ (jamais en prod)
            return g
        for r in range(eco.rows):
            for c in range(eco.cols):
                depth = paillage.at_plot(r, c)
                if depth <= 0.0:
                    continue
                abri = eco.nature_at(r, c)["abri_w"]
                g[r][c] = _clamp01(g[r][c] + PAILLAGE_ABRI_W * abri * depth)
        return g
    return _grid


def _mycelium_signal(eco, tile, plants) -> list[list[float]]:
    """Attraction fongivore : le réseau `mycelium` dense gonfle la capacité du
    détritivore du sol (collemboles brouteurs d'hyphes). Borné par FONGIVORE_GAIN.
    Lecture PURE du champ (la faune ne touche pas le mycélium — c'est le CHAMP qui
    fait tout, piège du kickoff §pièges)."""
    mycel = getattr(eco, "mycelium", None)
    if mycel is None:                       # robustesse pré-① (jamais en prod)
        return _zero_grid(eco.rows, eco.cols)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = FONGIVORE_GAIN * mycel.at_plot(r, c)
    return g


# ---------------------------------------------------------------------------
# CONSTANTES DE SCISSION DU RAVAGEUR (faune nommée ④b, CONCEPTION_FAUNE_DEDIEE §2)
# ---------------------------------------------------------------------------
# Le champ unique `ravageur` se scinde en puceron / limace / doryphore. Chacun a
# SA triade (resource_fn/habitat_fn/predators) ; la catégorie `ravageur` reste la
# somme (pression herbivore subie par les plantes, C1). Placeholders, calibrage
# post-test (comme les guildes — décision §5.6).
LITTER_REF       = 2.0   # masse de litière de surface (hors `fruit`) saturant la ressource détritivore
LIMACE_LITTER_W  = 1.0   # ressource limace : litière DOMINANTE (détritivore d'abord, §2)
LIMACE_FOLIAGE_W = 0.30  # + grignotage opportuniste du feuillage tendre (secondaire)
DORY_AIL_REPULSE = 0.6   # l'ail (Amaryllidaceae) rogne l'habitat doryphore (répulsif §4.4)


# ---------------------------------------------------------------------------
# CONSTANTES DE SCISSION DE L'AUXILIAIRE (faune nommée ④c, CONCEPTION_FAUNE_DEDIEE §2)
# ---------------------------------------------------------------------------
# Le champ unique `auxiliaire` se scinde en coccinelle / chrysope / carabe / merle /
# hérisson. Chacun chasse SA proie nommée (coccinelle/chrysope→puceron,
# carabe/hérisson→limace) → les `predators` posés en ④b S'ACTIVENT, les boucles
# proie↔prédateur deviennent réelles. Habitats neufs ancrés sur les STRUCTURES
# (piles ⑤) : poser une pile de bois attire carabe + hérisson (faune↔structures §3).
PILE_HABITAT_W     = 0.40  # bump d'habitat des structures `pile` (carabe/hérisson)
MERLE_BASE_HABITAT = 0.20  # plancher d'habitat ubiquiste du merle (oiseau résident)


def _foliage_grid(eco, tile, plants) -> list[list[float]]:
    """Feuillage hôte local (ressource du ravageur) — santé × couverture canopée."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        w = p.vitalite
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] += w
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = min(1.0, g[r][c] / FOLIAGE_REF)
    return g


def _monoculture_grid(eco, tile, plants) -> list[list[float]]:
    """
    Plancher d'habitat du ravageur = monoculture (faible biodiversité locale).
    1 famille → monoculture forte ; 3+ familles → régulée par la diversité.
    """
    fams: list[list[set]] = [[set() for _ in range(eco.cols)] for _ in range(eco.rows)]
    for p in plants:
        if not p.is_alive:
            continue
        fam = p.plant_class.family
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                fams[r][c].add(fam)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            n = len(fams[r][c])
            g[r][c] = 1.0 - min(1.0, n / MONO_REF)
    return g


def _flower_grid(eco, tile, plants) -> list[list[float]]:
    """SUPPLANTÉ (arc pollinisation ② — voir `_make_nectar_grid`) : proxy
    historique « fleurs = plantes matures (stade ≥ 2) ». Remplacé par la VRAIE
    floraison (tronçon ①) pondérée par type. Conservé pour mémoire / repli.
    Fleurs en floraison (ressource du pollinisateur) — plantes matures vivantes."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 2:
            continue
        w = p.vitalite
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] += w
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = min(1.0, g[r][c] / FLOWER_REF)
    return g


def _soil_food_grid(eco, tile, plants) -> list[list[float]]:
    """
    Ressource des vers de terre = microbiome + matière organique en décomposition
    (om_fresh + om_active, part fongique incluse — cf. §6.1, pas un 5ᵉ champ).
    """
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            micro = min(1.0, eco.microbiome.at_plot(r, c) / 3.0)
            om = min(1.0, (eco.om_fresh_at(r, c)
                           + eco.om_active.at_plot(r, c)) / OM_REF)
            g[r][c] = _clamp01(0.5 * micro + 0.5 * om)
    return g


def _root_palatability(plant) -> float:
    """Palatabilité racinaire d'une plante pour le campagnol (§2.1) : préférence de
    famille (bulbe/tubercule/racine charnue) OU écorce d'un JEUNE ligneux, en gardant
    le maximum des deux. Un jeune arbre d'une famille peu appétée reste rongé au collet
    (écorce tendre) ; un vieux ligneux (écorce épaisse) retombe sur sa préférence de
    famille. Placeholder, calibrage post-test."""
    fam = plant.plant_class.family
    pref = ROOT_PREF_FAMILLE.get(fam, ROOT_PREF_DEFAUT)
    # Jeune ligneux (reconnu comme la nécromasse ligneuse, `age_curve`) à écorce
    # encore tendre → cible du collet ; au-delà de LIGNEUX_JEUNE_CM l'écorce durcit.
    if (getattr(plant.plant_class, "age_curve", None)
            and plant.current_height <= LIGNEUX_JEUNE_CM):
        pref = max(pref, ROOT_PREF_LIGNEUX)
    return pref


def _racine_grid(eco, tile, plants) -> list[list[float]]:
    """Ressource du campagnol (herbivore vertébré, ①) = biomasse racinaire perçue
    sous l'empreinte SOUTERRAINE (`p.root_plots`, mémoïsée) des plantes vivantes,
    pondérée santé × palatabilité de l'organe (`_root_palatability`), normalisée par
    ROOT_REF. Distincte du feuillage (`_foliage_grid`) : le rongeur creuse là où il y
    a des racines charnues/bulbes/écorce, pas là où il y a des feuilles."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        w = p.vitalite * _root_palatability(p)
        if w <= 0.0:
            continue
        for (r, c) in p.root_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] += w
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = min(1.0, g[r][c] / ROOT_REF)
    return g


# --- Ressources/habitats des 3 ravageurs nommés (scission ④b, doc §2) ---------

def _litter_grid(eco, tile, plants) -> list[list[float]]:
    """Litière de SURFACE en décompo d'un plot (doc §2) = Σ masses des parcelles
    HORS `fruit` (le fruit a son propre signal d'attraction), normalisée. Ressource
    détritivore : nourrit la limace (préférence) — réutilisée par le cloporte (④d)."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            masse = sum(p.masse for p in eco.litiere[r][c] if p.tissu != "fruit")
            g[r][c] = min(1.0, masse / LITTER_REF)
    return g


def _limace_food_grid(eco, tile, plants) -> list[list[float]]:
    """Ressource MIXTE de la limace (④b) : litière DOMINANTE (détritivore d'abord)
    + grignotage opportuniste du feuillage tendre. Clé du modèle B : `resource_fn`
    pilote la POPULATION (ce qui la nourrit), la catégorie `ravageur` pilote le
    DÉGÂT (ce qu'elle abîme, C1) — deux choses séparées (doc §2 « Cas limace »)."""
    litter = _litter_grid(eco, tile, plants)
    foliage = _foliage_grid(eco, tile, plants)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = _clamp01(LIMACE_LITTER_W * litter[r][c]
                               + LIMACE_FOLIAGE_W * foliage[r][c])
    return g


def _humide_litiere_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat de la limace (④b ; partagé avec le cloporte ④d) : sol HUMIDE +
    sous-litière. `humide` devient une VRAIE ressource (lecture de `eco.humidite`,
    qui existe) — gain du modèle B sur le A : la niche est réelle, pas une porte."""
    litter = _litter_grid(eco, tile, plants)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            hum = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
            g[r][c] = _clamp01(0.5 * hum + 0.5 * litter[r][c])
    return g


def _rosee_humide_litiere_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat des détritivores du MATIN (limace ④b, cloporte ④d) ABREUVÉS par la
    rosée (sprint météo→champs ⑤, §6 — interconnexion « tout coexiste »). Reprend
    `_humide_litiere_grid` (sol humide + sous-litière) et lui AJOUTE un plancher ∝ la
    rosée liquide DÉPOSÉE ce matin (`eco.rosee_last`, normalisée par ROSEE_SURFACE_REF),
    borné par ROSEE_FAUNE_HABITAT_W : l'eau de surface du matin est leur abreuvoir, les
    semaines à forte rosée la faune du matin prospère un peu mieux. Lecture PURE (la
    faune ne touche pas la rosée — c'est le CHAMP qui fait tout, philo #2). Sans rosée
    (`rosee_last` nul) → identique à `_humide_litiere_grid` → golden NEUTRE pour ce terme."""
    g = _humide_litiere_grid(eco, tile, plants)
    rosee = getattr(eco, "rosee_last", None)
    if rosee is None:                       # robustesse pré-⑤ (jamais en prod)
        return g
    for r in range(eco.rows):
        for c in range(eco.cols):
            sig = min(1.0, rosee.at_plot(r, c) / ROSEE_SURFACE_REF)
            g[r][c] = _clamp01(g[r][c] + ROSEE_FAUNE_HABITAT_W * sig)
    return g


def _foliage_solanaceae_grid(eco, tile, plants) -> list[list[float]]:
    """Feuillage des seules Solanaceae (ressource du doryphore, ④b) — `_foliage_grid`
    filtré par famille : la pression doryphore est NULLE là où aucune Solanaceae ne
    pousse (interconnexion plante-hôte ↔ ravageur spécialiste)."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        if p.plant_class.family != "Solanaceae":
            continue
        w = p.vitalite
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] += w
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = min(1.0, g[r][c] / FOLIAGE_REF)
    return g


def _solanaceae_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du doryphore (④b) = présence locale de Solanaceae, RÉDUITE par la
    présence d'ail (Amaryllidaceae répulsif, doc §4.4). L'ail n'a PAS de rondelle
    dédiée (son effet ③ est une injection microbiome) → on lit ici sa présence
    foliaire pour rogner l'habitat du ravageur de la pomme de terre."""
    solana = _zero_grid(eco.rows, eco.cols)
    ail    = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        fam = p.plant_class.family
        cible = (solana if fam == "Solanaceae"
                 else ail if fam == "Amaryllidaceae" else None)
        if cible is None:
            continue
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                cible[r][c] += p.vitalite
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            s = min(1.0, solana[r][c] / FOLIAGE_REF)
            a = min(1.0, ail[r][c] / FOLIAGE_REF)
            g[r][c] = _clamp01(s * (1.0 - DORY_AIL_REPULSE * a))
    return g


def _ravageur_grid(eco, tile, plants) -> list[list[float]]:
    """Proie animale = AGRÉGAT de la catégorie `ravageur` (puceron + limace +
    doryphore, modèle B). Depuis ④c, les auxiliaires NOMMÉS chassent chacun UNE
    proie précise (`_espece_grid`, ci-dessous) et ne lisent plus cet agrégat. Seule
    la syrphe_larve (pont ⑤) le réutilise comme proie : généraliste, elle prédate
    l'ensemble des ravageurs (doc §4 « ponts inchangés »)."""
    return [[eco.category_density("ravageur", r, c) for c in range(eco.cols)]
            for r in range(eco.rows)]


def _espece_grid(name: str) -> Callable:
    """Fabrique une resource_fn lisant le champ de population d'UNE espèce nommée
    (généralise `_ravageur_grid` à un membre unique, scission ④c). Câble chaque
    prédateur sur SA proie (coccinelle/chrysope→puceron, carabe/hérisson→limace) au
    lieu de l'agrégat de guilde → les boucles proie↔prédateur deviennent réelles.

    ROBUSTE à l'ordre des scissions : si `name` n'existe pas encore comme champ
    (catégorie pas encore scindée), la grille est NULLE — le merle/hérisson pourront
    ainsi viser `lombric` (④d) sans casser tant qu'il n'existe pas."""
    def _grid(eco, tile, plants) -> list[list[float]]:
        f = eco.populations.get(name)
        if f is None:
            return _zero_grid(eco.rows, eco.cols)
        return [[f.at_plot(r, c) for c in range(eco.cols)]
                for r in range(eco.rows)]
    return _grid


def _proies_grid(noms: tuple[str, ...], habitat_fn: Callable | None = None) -> Callable:
    """Fabrique la resource_fn d'un SUPER-PRÉDATEUR (②) : somme des densités des
    champs de population `noms` (ses proies), normalisée par PROIES_REF (généralise
    `_espece_grid` de 1 à N proies). Les proies tickent AVANT le prédateur (registry)
    → il les lit FRAÎCHES → décalage d'inertie proie↔prédateur = boom-bust.

    Le sommet est piloté PAR LE BAS : à proie absente (champ nul), la grille est nulle
    → densité prédateur nulle. Le terrain (`habitat_fn` : dégagé+perchoir pour le
    rapace, cache pour la couleuvre) ne CRÉE pas de capacité (un prédateur sans proie
    ne s'installe pas) : il MODULE (multiplie) la proie perçue — le prédateur chasse
    mieux là où le terrain lui est favorable. C'est pourquoi les specs super_predateur
    portent `habitat_w=0` : toute la capacité vient de la proie modulée ici."""
    def _grid(eco, tile, plants) -> list[list[float]]:
        g = _zero_grid(eco.rows, eco.cols)
        for nom in noms:
            f = eco.populations.get(nom)
            if f is None:                       # proie pas encore scindée → 0
                continue
            for r in range(eco.rows):
                for c in range(eco.cols):
                    g[r][c] += f.at_plot(r, c)
        hab = habitat_fn(eco, tile, plants) if habitat_fn else None
        for r in range(eco.rows):
            for c in range(eco.cols):
                v = min(1.0, g[r][c] / PROIES_REF)
                g[r][c] = v * hab[r][c] if hab else v
        return g
    return _grid


def _rapace_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """HUNTABILITÉ du rapace (②), modulateur ∈ [FLOOR, 1] de la proie perçue (pas une
    capacité indépendante — cf. `_proies_grid`) : terrain OUVERT (chasse à vue sur sol
    dégagé, rogné par la canopée dense qui masque les proies) + PERCHOIR d'affût
    (présence d'un ligneux mûr et haut, poste de guet). Un PLANCHER `RAPACE_HUNT_FLOOR`
    garantit que le rapace chasse un peu partout où il y a une proie (jamais zéro même
    en zone fermée) → il n'est jamais annulé par la seule fermeture du couvert."""
    canopee = _zero_grid(eco.rows, eco.cols)
    perchoir = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                canopee[r][c] += p.vitalite
        # Un ligneux haut fait poste d'affût sur son empreinte foliaire.
        if (getattr(p.plant_class, "age_curve", None)
                and p.current_height >= PERCHOIR_H_CM):
            for (r, c) in p.foliar_plots:
                if 0 <= r < eco.rows and 0 <= c < eco.cols:
                    perchoir[r][c] = 1.0
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            ouvert = 1.0 - min(1.0, canopee[r][c] / FOLIAGE_REF)
            hunt = RAPACE_OUVERT_W * ouvert + RAPACE_PERCHOIR_W * perchoir[r][c]
            g[r][c] = _clamp01(max(RAPACE_HUNT_FLOOR, hunt))
    return g


def _habitat_nul_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat-source NUL (grille de zéros). Sert aux SUPER-PRÉDATEURS (②) dont la
    capacité vient ENTIÈREMENT de la proie modulée par la huntabilité (`_proies_grid`
    avec `habitat_fn`), avec `habitat_w=0` : ce terme additif ne doit rien apporter
    (un prédateur sans proie ne s'installe pas). Callable propre plutôt qu'un lambda."""
    return _zero_grid(eco.rows, eco.cols)


def _stability_grid(eco, tile, plants) -> list[list[float]]:
    """Refuge de l'auxiliaire = nectar (rondelle auxiliaire) + stabilité (1−perturbation)."""
    nectar = min(1.0, tile.get_rondelle_count("auxiliaire") / 3.0)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            stability = 1.0 - eco.disturbance.at_plot(r, c)
            g[r][c] = _clamp01(0.5 * nectar + 0.5 * stability)
    return g


def _pollinisateur_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du pollinisateur = rondelle pollinisateur (terme-source uniforme).
    Habitat de l'abeille ET du papillon (arc pollinisation §E.2 ; la ruche §H, hub
    abeille, viendra en Partie II)."""
    val = min(1.0, tile.get_rondelle_count("pollinisateur") / 3.0)
    return [[val] * eco.cols for _ in range(eco.rows)]


def _auxiliaire_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du syrphe = rondelle auxiliaire (terme-source uniforme), miroir de
    `_pollinisateur_habitat_grid` (§E.2 : le syrphe niche côté auxiliaires)."""
    val = min(1.0, tile.get_rondelle_count("auxiliaire") / 3.0)
    return [[val] * eco.cols for _ in range(eco.rows)]


# Bump d'habitat abeille des RUCHES peuplées (⑥, §H.2 — placeholder calibrage). Une
# ruche peuplée devient un terme-source d'habitat LOCAL pour l'abeille → renforce la
# population qui l'a remplie (boucle vertueuse, interconnexion §H.2). Lu DIRECTEMENT
# sur `eco.structures` (duck-typé, pas d'import de l'apiculture → pas de cycle).
RUCHE_HABITAT_W = 0.40


def _abeille_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat de l'abeille = `_pollinisateur_habitat_grid` (rondelle) + bump LOCAL
    des ruches peuplées (§H.2). Sans ruche posée → identique au générique partagé
    avec le papillon → **golden NEUTRE** (le smoke n'instancie aucune ruche)."""
    g = _pollinisateur_habitat_grid(eco, tile, plants)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "ruche" and st.essaim > 0.0:
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + RUCHE_HABITAT_W * st.essaim)
    return g


def _undisturbed_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat des vers = sol NON perturbé (1 − perturbation)."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = 1.0 - eco.disturbance.at_plot(r, c)
    return g


# --- Habitats neufs des auxiliaires nommés (scission ④c, doc §2) -------------
# Ancrés sur les STRUCTURES `pile` (⑤) : lecture DIRECTE d'`eco.structures`,
# duck-typée comme `_abeille_habitat_grid` lit les ruches (pas d'import de
# l'apiculture/compost → pas de cycle de couche). À ZÉRO structure posée (cas du
# smoke golden), ces termes-sources sont nuls → golden NEUTRE pour leur part.

def _undisturbed_structure_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du carabe (④c) = sol NON perturbé + bump des structures `pile` à bois
    (faune↔structures §3 : un carabe se réfugie sous le bois mort). Sans pile posée
    → identique à `_undisturbed_grid` (le carabe vit déjà du sol stable)."""
    g = _undisturbed_grid(eco, tile, plants)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "pile":
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + PILE_HABITAT_W)
    return g


def _pile_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du hérisson (④c) = présence de structures `pile`/tas (refuge nocturne).
    Terme-source NUL sans pile posée → le hérisson dépend ENTIÈREMENT d'un aménagement
    joueur (poser une pile attire carabe + hérisson, synergie de cartes §8). Golden
    NEUTRE : le smoke n'instancie aucune structure."""
    g = _zero_grid(eco.rows, eco.cols)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "pile":
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + PILE_HABITAT_W)
    return g


def _osmie_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat de l'osmie (⑤) = rondelle pollinisateur (nichoirs posés) + bump des
    structures `pile` à bois mort : l'abeille solitaire NICHE dans les cavités du
    bois (faune↔structures §5.3 — une pile de bois lui offre des galeries). Sans
    pile ni rondelle → habitat nul (mais le nectar Rosacées/Apiacées suffit à la
    capacité additive). Golden NEUTRE pour la part `pile` : le smoke n'en pose aucune."""
    g = _pollinisateur_habitat_grid(eco, tile, plants)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "pile":
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + PILE_HABITAT_W)
    return g


def _base_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du merle (④c) = plancher constant léger (oiseau ubiquiste, présent
    toute saison ; haies/structures hautes = placeholder différé). UNIFORME → c'est
    sa NOURRITURE (fruit frais + vers) qui le concentre spatialement, pas l'habitat."""
    return [[MERLE_BASE_HABITAT] * eco.cols for _ in range(eco.rows)]


_lombric_grid = _espece_grid("lombric")


def _merle_food_grid(eco, tile, plants) -> list[list[float]]:
    """Nourriture du merle (④c) : fruit FRAIS (frugivore — `_aux_fruit_signal` repromu
    de signal additif en RESSOURCE, C13) + LOMBRIC (④d : le merle mange le ver, pas
    le cloporte prioritairement → `_espece_grid("lombric")`, non l'agrégat de
    catégorie). Borné [0,1]."""
    fruit = _aux_fruit_signal(eco, tile, plants)
    vers  = _lombric_grid(eco, tile, plants)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = _clamp01(fruit[r][c] + vers[r][c])
    return g


# --- Signal d'attraction par le fruit tombé (④, CONCEPTION §4) --------------
# Terme ADDITIF à la capacité (≠ ressource/habitat) : il APPELLE la faune sans
# rien retirer à la plante (philo #2). Lit la parcelle `fruit` du plot — unique
# par plot (fusion par tissu, acquis ①) → lecture déterministe, pas d'ordre.

def _fruit_litter(eco, r: int, c: int) -> tuple[float, float]:
    """(masse, age_sem) de la parcelle `fruit` du plot, (0, 0) si aucune."""
    for p in eco.litiere[r][c]:
        if p.tissu == "fruit":
            return p.masse, p.age_sem
    return 0.0, 0.0


def _fruit_weights(age_sem: float) -> tuple[float, float]:
    """Poids (frais, pourri) ∈ [0,1] selon l'âge : frais décroît, pourri croît."""
    frais  = _clamp01(1.0 - age_sem / FRUIT_FRAIS_SEM)
    pourri = _clamp01((age_sem - FRUIT_FRAIS_SEM) / FRUIT_POURRI_SEM)
    return frais, pourri


def _aux_fruit_signal(eco, tile, plants) -> list[list[float]]:
    """Attraction `auxiliaire` : fruit frais (frugivores) + fraction du pourri
    (décomposeurs). Borné par FRUIT_AUX_GAIN (un tas plein ne sature pas)."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            masse, age = _fruit_litter(eco, r, c)
            if masse <= 0.0:
                continue
            sig = min(1.0, masse / FRUIT_SIGNAL_REF)
            frais, pourri = _fruit_weights(age)
            g[r][c] = FRUIT_AUX_GAIN * sig * (frais + FRAC_AUX_POURRI * pourri)
    return g


def _rav_fruit_signal(eco, tile, plants) -> list[list[float]]:
    """Attraction `ravageur` : fruit pourri (charognards, mouches), DOMINANT.
    Borné par FRUIT_RAV_GAIN."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            masse, age = _fruit_litter(eco, r, c)
            if masse <= 0.0:
                continue
            sig = min(1.0, masse / FRUIT_SIGNAL_REF)
            _, pourri = _fruit_weights(age)
            g[r][c] = FRUIT_RAV_GAIN * sig * pourri
    return g
