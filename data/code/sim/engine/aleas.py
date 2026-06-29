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
# Humidité MÉDIÉE (sprint météo→champs ①, §2) : les deltas plats humidité sont RETIRÉS
# de cette table (Canicule, Sécheresse, Pluie prolongée, Orage) — un nombre uniforme et
# instantané posé sur un champ est l'antithèse de la philo #2. Ils passent désormais par
# un FLUX : la pluie via `PLUIE_APPORT` infiltrée ∝ structure dans tick_hydrology, et
# l'assèchement de la canicule/sécheresse via l'évaporation∝T_sol DÉJÀ en place. Les
# entrées humidité d'origine sont conservées en commentaire (CLAUDE.md « ne jamais jeter »):
#   "Canicule":  Alea("Canicule",  "Humidité chute.", "humidite", -0.4, "field"),
#   "Sécheresse":Alea("Sécheresse","Humidité chute.", "humidite", -0.4, "field"),
#   "Pluie prolongée": Alea("Pluie prolongée","Humidité monte.","humidite",+0.5,"field"),
#   "Orage":     Alea("Orage",     "Pluie battante.", "humidite", +0.5, "field"),
# Restent câblés : Tempête/Orage VENT (paillage), Gelée (→ gel médié), Grêle (→ médié).
WEATHER_ALEA = {
    "Beau temps":      Alea("Beau temps",      "Aucun effet.",       "",         0.0, "none"),
    "Gelée tardive":   Alea("Gelée tardive",   "Semis touchés.",     "",        -1.0, "health"),
    # Canicule/Sécheresse : assèchement ÉMERGENT (évaporation∝T_sol). Plus de delta plat.
    "Canicule":        Alea("Canicule",        "Sol qui s'assèche.", "",         0.0, "none"),
    "Sécheresse":      Alea("Sécheresse",      "Pluie de fond tarie.","",        0.0, "none"),
    "Tempête":         Alea("Tempête",         "Paillage dispersé.", "paillage", -1,   "rondelle"),
    # Grêle : SUPPLANTÉ (sous-sprint 03). Ne passe plus par la voie `health` plate ;
    # routé via _mediated_damage (impact physique × exposition × protection). Entrée
    # conservée pour mémoire — n'est plus consultée par tick_semaine (cf. CLAUDE.md
    # « ne jamais jeter de code »).
    "Grêle":           Alea("Grêle",           "Feuillage abîmé.",   "",        -1.0, "health"),
    # Pluie prolongée : apport d'eau MÉDIÉ (PLUIE_APPORT infiltré ∝ structure). Plus de delta plat.
    "Pluie prolongée": Alea("Pluie prolongée", "Pluie infiltrée.",   "",         0.0, "none"),
    "Redoux":          Alea("Redoux",          "Aucun effet.",       "",         0.0, "none"),
    # Orage (⑦) = composite pluie battante + vent. Sa PLUIE est désormais médiée
    # (PLUIE_APPORT) ; il ne conserve ici que le VENT (paillage dispersé), appliqué
    # EN SÉQUENCE par boucle.py via ORAGE_VENT ci-dessous (option (b) du kickoff :
    # 2 aléas enchaînés, plus lisible qu'un champ `extra` sur Alea).
    "Orage":           Alea("Orage",           "Pluie battante.",    "",         0.0, "none"),
}

# Volet VENT de l'Orage (⑦), appliqué en séquence après la pluie (cf. WEATHER_ALEA
# ci-dessus). Identique au coup de vent de la Tempête (paillage −1) ; séparé pour
# que l'Orage = pluie + vent sans dupliquer l'entrée Tempête.
ORAGE_VENT = Alea("Orage (vent)", "Paillage dispersé.", "paillage", -1, "rondelle")

# Mapping alea.nom → cause CANONIQUE de symptôme foliaire ÉVÉNEMENTIEL (sémiologie ②).
# Ne mappe QUE les aléas santé à signe foliaire propre. Les aléas santé d'herbivorie
# (« Limaces », « Chenilles ») sont volontairement ABSENTS → cause "" : ils sont déjà
# couverts par le détecteur CHRONIQUE `ravageurs` (pas de double comptage). Note : gel
# et grêle passent désormais par `_mediated_damage` (mortalite.py), pas par la voie
# `health` ci-dessous — ce mapping reste défensif / forward-compat si un aléa santé
# gel/grêle réempruntait ce chemin.
EVENT_CAUSE = {"Gelée tardive": "gel", "Grêle": "grele"}
ALEAS_RAVAGEURS = [
    Alea("Pucerons",  "Fertilité réduite.", "n",         -0.3, "field"),
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

# --- Dégât MÉCANIQUE du vent (thigmomorphogénèse, sprint VENT ④, §5.2) -------
# Le vent CASSE le tissu tendre exposé, MÉDIÉ par l'étiolement et le port trapu :
#     dégât = sévérité_vent(vent_local, risée) × (étiolement / port_trapu) × (1−paillage)
# - `vent_local` (eco.vent[r,c]) intègre DÉJÀ la protection d'abri (un coin abrité
#   reçoit un vent réduit) ; la risée (pic intra-jour, gust_profile) aggrave le pic.
# - une tige ÉTIOLÉE (grêle, non sollicitée — `est_etiole`) est un bras de levier
#   fragile (susceptibilité ↑) ; un port TRAPU (port_trapu exprimé) encaisse (↓). La
#   boucle plasticité se referme : le semis endurci protège, le semis de serre casse.
# Le seuil élevé (WIND_DAMAGE_SEUIL) fait que SEULS les coups de vent (Tempête/Orage,
# risée) frappent — une brise n'abîme rien. Knobs P4, calibrage post-test.
WIND_DAMAGE_SEUIL  = 0.7    # vent_local·risée sous ce seuil → aucun dégât mécanique
WIND_SEVERITY_REF  = 0.8    # surcroît de vent_local·risée au-dessus du seuil → sév ≈ 1
WIND_ETIOLE_SUSCEPT = 1.5   # susceptibilité d'un tissu ÉTIOLÉ (vs 1.0 pour un tissu sain)


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
        muts = [ReduceHealth(p, 1, alea.nom, cause=EVENT_CAUSE.get(alea.nom, ""))
                for p in tile.plants if p.is_alive and p.stage.name == "semis"]
        log += apply_mutations(muts, game_state)
        # Mort éventuelle → squelette persistant (②B, idempotent : skip si déjà morte)
        for p in tile.plants:
            if p.health == 0:
                deposer_mort(p, eco)
    return log
