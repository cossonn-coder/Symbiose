"""
SYMBIOSE — sim/engine/aleas.py
Aléas écologiques (météo & ravageurs) et leur application au milieu.

Contient le type `Alea`, les catalogues (météo historique + couplage
`WeatherEvent.kind → effet`, ravageurs), les constantes du dégât MÉDIÉ
(gel/grêle, philo #2) et la fonction `appliquer_alea` qui traduit un aléa en
mutations sur la tuile / les champs. La logique de dégât médié elle-même
(`_mediated_damage`) vit dans `mortalite.py` (c'est une réponse des plantes),
mais ses constantes de calibrage sont rassemblées ici, près des aléas qui les
déclenchent.
"""

from __future__ import annotations
from dataclasses import dataclass
from sim.effects import (apply_mutations, AddRondelle, RemoveRondelle,
                         ReduceHealth, deposer_mort)


@dataclass
class Alea:
    nom: str; description: str
    variable: str; delta: float; mode: str = "field"

# Ancien catalogue météo, conservé pour mémoire. SUPPLANTÉ (sous-sprint 01) par
# weather_at(seed, week) + WEATHER_ALEA ci-dessous : le tirage n'est plus un
# random.choice live mais une fonction pure déterministe (CONCEPTION_METEO.md §0).
ALEAS_METEO = [
    Alea("Canicule",     "Humidité chute.",    "humidite",  -0.4, "field"),
    Alea("Pluies",       "Humidité monte.",     "humidite",  +0.5, "field"),
    Alea("Gelée tardive","Semis touchés.",      "",          -1.0, "health"),
    Alea("Beau temps",   "Aucun effet.",        "",           0.0, "none"),
    Alea("Vent fort",    "Paillage dispersé.",  "paillage",  -1,   "rondelle"),
    Alea("Brouillard",   "Risque maladie.",     "maladie",   +1,   "rondelle"),
]

# Couplage PROVISOIRE (sous-sprint 01) : WeatherEvent.kind → effet Alea EXISTANT.
# On réutilise STRICTEMENT les effets déjà en place (humidité/paillage/santé)
# pour préserver le couplage le temps de la déterminisation. Plusieurs kinds du
# catalogue §1.3 mappent sur le même effet faute de mieux (Sécheresse≈Canicule,
# Grêle≈dégât santé, Redoux=neutre) : la température (02) et les réponses médiées
# par gène (03) remplaceront ces mappings approximatifs.
WEATHER_ALEA = {
    "Beau temps":      Alea("Beau temps",      "Aucun effet.",       "",         0.0, "none"),
    "Gelée tardive":   Alea("Gelée tardive",   "Semis touchés.",     "",        -1.0, "health"),
    "Canicule":        Alea("Canicule",        "Humidité chute.",    "humidite", -0.4, "field"),
    "Sécheresse":      Alea("Sécheresse",      "Humidité chute.",    "humidite", -0.4, "field"),
    "Tempête":         Alea("Tempête",         "Paillage dispersé.", "paillage", -1,   "rondelle"),
    # Grêle : SUPPLANTÉ (sous-sprint 03). Ne passe plus par la voie `health` plate ;
    # routé via _mediated_damage (impact physique × exposition × protection). Entrée
    # conservée pour mémoire — n'est plus consultée par tick_semaine (cf. CLAUDE.md
    # « ne jamais jeter de code »).
    "Grêle":           Alea("Grêle",           "Feuillage abîmé.",   "",        -1.0, "health"),
    "Pluie prolongée": Alea("Pluie prolongée", "Humidité monte.",    "humidite", +0.5, "field"),
    "Redoux":          Alea("Redoux",          "Aucun effet.",       "",         0.0, "none"),
}
ALEAS_RAVAGEURS = [
    Alea("Pucerons",  "Fertilité réduite.", "fertilite", -0.3, "field"),
    Alea("Limaces",   "Semis grignotés.",   "",          -1.0, "health"),
    Alea("Doryphores","Maladie augmente.",  "maladie",    +1,  "rondelle"),
    Alea("Calme",     "Aucun ravageur.",    "",            0.0, "none"),
    Alea("Chenilles", "Feuillage abîmé.",  "",           -1.0, "health"),
]

# --- Réponses médiées par le milieu (CONCEPTION_METEO.md §2.3) -------------
# Gel et grêle ne frappent plus « à plat » (ancienne voie `health`, à la limite
# de la philo #2). Le dégât subi par un individu ÉMERGE de son état et de son
# génotype :
#     dégât = sévérité_milieu × susceptibilité_génétique × (1 − protection)
# Deux semis voisins réagissent différemment selon leur gène de rusticité et le
# paillage local. Conséquence émergente recherchée : sur plusieurs générations,
# le gel élague les lignées peu rustiques → sélection naturelle du froid (philo
# #2/#7), sans aucun bonus/malus direct.
TEMP_FROST_DAMAGE  = 0.0    # °C — sous ce seuil, le tissu tendre exposé gèle
FROST_SEVERITY_REF = 6.0    # °C sous 0 donnant une sévérité de référence ≈ 1
HAIL_SEVERITY_REF  = 1.45   # intensité (σ) de grêle donnant une sévérité ≈ 1
PAILLAGE_PROTECT   = 0.25   # chaque rondelle paillage retire 25 % du dégât (cap 1)
DAMAGE_STEP        = 0.55   # dégât effectif → points de santé perdus (floor)


def appliquer_alea(alea, tile, eco, game_state):
    log = []
    if alea.mode == "none": return log
    if alea.mode == "field":
        eco.apply_weather(alea.variable, alea.delta)
        sign = "+" if alea.delta > 0 else ""
        log.append(f"    → {alea.variable} {sign}{alea.delta:.2f} (champ)")
    elif alea.mode == "rondelle":
        amt = int(abs(alea.delta))
        muts = []
        if alea.delta > 0:
            muts.append(AddRondelle(tile.tile_id, alea.variable, amt, alea.nom))
        else:
            cur = tile.get_rondelle_count(alea.variable)
            if cur > 0:
                muts.append(RemoveRondelle(tile.tile_id, alea.variable, min(amt,cur), alea.nom))
        log += apply_mutations(muts, game_state)
    elif alea.mode == "health":
        # Cible les vrais semis (stade nommé "semis"), pas l'index 0 — sinon le
        # stade perpétuel des pérennes ligneuses ("arbre", index 0) serait frappé
        # comme un semis fragile à chaque saison (D27).
        muts = [ReduceHealth(p, 1, alea.nom)
                for p in tile.plants if p.is_alive and p.stage.name == "semis"]
        log += apply_mutations(muts, game_state)
        # Mort éventuelle → squelette persistant (②B, idempotent : skip si déjà morte)
        for p in tile.plants:
            if p.health == 0:
                deposer_mort(p, eco)
    return log
