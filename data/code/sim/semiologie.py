"""
SYMBIOSE — sim/semiologie.py
Sémiologie foliaire (dette D33) — TRONÇON ① : détecteurs CHRONIQUES purs.
Spec : docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md (§2.1-2.4, §5, §6).

Une plante qui souffre le MONTRE sur son feuillage, et chaque cause a un signe
distinct : pas une jauge de santé unique mais un VOCABULAIRE (voir le signe →
formuler une hypothèse → consulter → trouver la cause ; philo #5/#6).

Ce module ne fait que LIRE l'état persistant du moteur à l'instant du snapshot —
ZÉRO écriture, exactement comme l'indice chlorose du ⑨ et la façade
`vigueur_plante`. C'est ce qui garantit le golden NEUTRE : le tick n'appelle
jamais ce module, il est consommé par `tools/simserver/serialize._snapshot`.

INVARIANT central (§2.4, DRY) : chaque détecteur RÉUTILISE le SEUIL MÊME de la
mécanique qui blesse, pour que le signe ne puisse jamais MENTIR par rapport à la
simulation. Le feuillage jaunit/se crible exactement quand le tissu souffre —
pas avant, pas après. La forme générale est une rampe :

    intensité = clamp01((mesure − seuil_apparition) / (seuil_plein − seuil_apparition))

Deux régimes (depuis le tronçon ②) :
- CHRONIQUE : détecteurs PURS recalculés à la volée (état persistant relu).
- ÉVÉNEMENTIEL : marques maladie/gel/grêle MÉMORISÉES et décroissantes sur la
  plante (PlantInstance.symptom_marks), écrites par les ReduceHealth à cause typée
  et estompées au tick. L'agrégateur `leaf_symptoms` FUSIONNE les deux avant le tri.
Cette fusion ne CHANGE pas le golden : les marques ne sont pas dans _PLANT_ATTRS et
ne rebouclent jamais sur santé/croissance — pur affichage (cf. §5 conception).
"""
from __future__ import annotations

import math

# Seuils RÉUTILISÉS des mécaniques qui blessent (DRY §2.4) — jamais de doublon de
# nombre : on importe la constante de calibrage de la mécanique elle-même.
#   chlorose  : CHLOROSE_PH / SEUIL_ACIDOPHILE — miroir de vigueur_plante.qi_local
#   asphyxie  : ASPHYXIE_HEALTH_SEUIL — seuil de la voie santé (mortalite.py)
#   senescence: SENESCENCE_ONSET — début du déclin sénescent (mortalite.py)
#   chlorose plein : PH_MAX — plafond physique du champ pH (rampe 7.6 → 8.5)
from fields.ecofields import (CHLOROSE_PH, SEUIL_ACIDOPHILE, PH_MAX,
                             ASPHYXIE_HEALTH_SEUIL, SENESCENCE_ONSET)
# Mêmes seuils que la mécanique de DÉGÂT correspondante (sim, même couche) :
#   DROUGHT_DAMAGE_THRESHOLD — drought_memory au-delà de laquelle le tissu souffre
#   HERBIVORY_GAIN — gain densité→pression, sert à exprimer le floor du détecteur
from sim.effects.perturbations import DROUGHT_DAMAGE_THRESHOLD, HERBIVORY_GAIN

# Densité locale `ravageur + chenille` sous laquelle `herbivory_pressure` ne fait
# RIEN (son garde-fou `if pressure < 0.005`, avec pression = densité·HERBIVORY_GAIN).
# On exprime ce floor à partir du gain pour rester DRY : le signe ravageurs
# apparaît exactement au seuil où la morsure commence à compter.
RAVAGEURS_FLOOR = 0.005 / HERBIVORY_GAIN   # ≈ 0.025


def _ramp(mesure: float, apparition: float, plein: float) -> float:
    """Rampe linéaire bornée [0,1] : 0 sous `apparition`, 1 à `plein` (§2.4).
    Forme commune à tous les détecteurs — le seuil d'apparition est TOUJOURS celui
    de la mécanique qui blesse (DRY)."""
    if mesure <= apparition:
        return 0.0
    if plein <= apparition:
        return 1.0
    return min(1.0, (mesure - apparition) / (plein - apparition))


# ─────────────────────────── détecteurs chroniques ───────────────────────────
# Signature uniforme `(plant, eco, saison) -> float` (intensité [0,1], 0 = absent).
# `saison` n'est lu par aucun détecteur chronique aujourd'hui mais fait partie du
# contrat (le ② / la distinction sénescence vs couleur d'automne pourront s'en servir).

def chlorose(plant, eco, saison) -> float:
    """Chlorose ferrique : une espèce ACIDOPHILE (`ph_opt` sous SEUIL_ACIDOPHILE)
    sur sol trop ALCALIN voit le fer se bloquer → le limbe jaunit entre les
    nervures. MÊME prédicat que `qi_local` (pH local = moyenne sous l'empreinte
    racinaire, repli plot-foyer), passé de bool à RAMPE sur [CHLOROSE_PH, PH_MAX].
    Espèce neutre (`ph_opt` ≥ 5.5) ⇒ 0 → aucun signe au smoke (golden NEUTRE)."""
    cls = plant.plant_class
    if cls.ph_opt >= SEUIL_ACIDOPHILE:
        return 0.0
    plots = plant.root_plots or [plant.plot_foyer]
    ph_loc = sum(eco.ph.at_plot(r, c) for (r, c) in plots) / len(plots)
    return _ramp(ph_loc, CHLOROSE_PH, PH_MAX)


def secheresse(plant, eco, saison) -> float:
    """Stress hydrique sévère : turgescence perdue → feuilles flétries, désaturées.
    Miroir de `drought_stress_damage` — même `drought_memory` (intégration lente du
    déficit) et même seuil DROUGHT_DAMAGE_THRESHOLD : le signe apparaît quand un
    stress INSTALLÉ (pas une semaine sèche isolée) commence à abîmer le tissu.
    Couvre la canicule (qui n'est qu'une chute d'humidité). Plein à mémoire saturée."""
    return _ramp(plant.drought_memory, DROUGHT_DAMAGE_THRESHOLD, 1.0)


def asphyxie(plant, eco, saison) -> float:
    """Asphyxie racinaire (engorgement) : racines en anoxie → feuillage terne,
    brunâtre, jaunissement mou (sans le contraste net de la chlorose). Miroir de la
    voie santé `_tick_senescence_health` — même `asphyxie_memory` et même seuil
    ASPHYXIE_HEALTH_SEUIL : le signe apparaît quand l'excès d'eau SOUTENU se met à
    faire chuter la santé. Réversible (un assèchement vide la mémoire)."""
    return _ramp(plant.asphyxie_memory, ASPHYXIE_HEALTH_SEUIL, 1.0)


def ravageurs(plant, eco, saison) -> float:
    """Herbivorie : signe de FORME (pas de couleur) — limbe criblé, troué, mordu.
    Miroir de `herbivory_pressure` : MÊME densité locale lue (`ravageur` visible +
    `chenille`, larve du papillon). Le champ ravageur intègre déjà sa régulation par
    les auxiliaires → lire cette densité, c'est lire une pression DÉJÀ régulée.
    Apparition au floor du mécanisme, plein à champ saturé."""
    r, c = plant.position
    rav = eco.category_density("ravageur", r, c) if eco else 0.0
    chen = (eco.larvae["chenille"].at_plot(r, c)
            if eco and "chenille" in getattr(eco, "larvae", {}) else 0.0)
    return _ramp(rav + chen, RAVAGEURS_FLOOR, 1.0)


def senescence(plant, eco, saison) -> float:
    """Sénescence : jaunissement-rougissement de FIN DE VIE (à distinguer du
    rougeoiement saisonnier d'automne, géré ailleurs par la couleur de saison).
    Miroir EXACT de la pression de sénescence D27 de `_tick_senescence_health` :
    rampe de l'âge relatif à la longévité au-delà de SENESCENCE_ONSET·longévité.
    Cette même pression PILOTE le déclin de santé de fin de vie dans le moteur — le
    signe en est la lecture visible. Annuelles (longévité = ∞) ⇒ 0 (elles meurent à
    l'hiver, pas de vieillissement sénescent)."""
    L = plant.plant_class.longevity()
    if L == math.inf:
        return 0.0
    denom = (1.0 - SENESCENCE_ONSET) * L
    if denom <= 0.0:
        return 0.0
    return max(0.0, min(1.0, (plant.age_years - SENESCENCE_ONSET * L) / denom))


# ───────────────────────────── agrégateur trié ───────────────────────────────
# Registre des détecteurs chroniques (extensible : carence_n/_k, etiolement…
# s'ajouteront ici sans toucher le schéma snapshot — §7).
DETECTEURS = (
    ("chlorose", chlorose),
    ("secheresse", secheresse),
    ("asphyxie", asphyxie),
    ("ravageurs", ravageurs),
    ("senescence", senescence),
)

# Priorité fixe de DÉPARTAGE à intensité égale (§2.3), du plus aigu/diagnostique
# au plus lent. Numéro bas = plus prioritaire. Couvre déjà les causes
# ÉVÉNEMENTIELLES (maladie/gel/grele) que le ② viendra fusionner.
PRIORITE = {
    "asphyxie": 0, "secheresse": 1, "maladie": 2, "ravageurs": 3,
    "gel": 4, "grele": 5, "chlorose": 6, "senescence": 7,
}


def leaf_symptoms(plant, eco, saison) -> list[dict]:
    """Collecte les symptômes CHRONIQUES d'intensité non nulle et les TRIE par
    `(intensité décroissante, priorité fixe)` (§2.2/§2.3). Liste vide = plante
    saine (pas de cause factice). Cumul multi-signes assumé (choix Nico). Intensité
    arrondie à 3 décimales pour un diff snapshot stable (déterminisme philo #3)."""
    syms = []
    for cause, detecteur in DETECTEURS:
        i = round(detecteur(plant, eco, saison), 3)
        if i > 0.0:
            syms.append({"cause": cause, "intensity": i})
    # Marques ÉVÉNEMENTIELLES (② — maladie/gel/grêle) : mémorisées et décroissantes
    # sur la plante (PlantInstance.symptom_marks, écrites par les ReduceHealth à
    # cause typée). On les FUSIONNE ici avec les détecteurs chroniques AVANT le tri.
    # Causes disjointes des chroniques par construction → pas de doublon ; PRIORITE
    # les couvre déjà (§2.3). Cause inconnue tolérée (ignorée du tri si absente).
    for cause, mark in plant.symptom_marks.items():
        i = round(mark, 3)
        if i > 0.0 and cause in PRIORITE:
            syms.append({"cause": cause, "intensity": i})
    syms.sort(key=lambda s: (-s["intensity"], PRIORITE[s["cause"]]))
    return syms
