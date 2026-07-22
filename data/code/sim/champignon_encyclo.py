"""
SYMBIOSE — sim/champignon_encyclo.py
Fiche générique de l'ENCYCLOPÉDIE du règne fongique (D60, tronçon ①).
Spec : `docs/faune/vie_macro/conception_vie_macro_identifiable.md` §3.1(Q2).

DÉCISION FIGÉE (Q2) : le champignon = UNE seule entrée générique
« réseau mycélien ». Le snapshot (`serialize.sample_carpophores`) ne rend
qu'un acteur `mycelium` générique — pas d'espèces fongiques. Le survol d'un
carpophore (tronçon ②) découvre donc cette fiche unique.

Miroir minimal de `fields/faune_encyclo.py` (blurb + graphe d'interconnexions),
en DONNÉE PURE : jamais lue par le tick → golden NEUTRE, aucun import (aucun
cycle de couche). Voix « naturaliste qui observe » (philo #5) : le blurb dit ce
qu'on VOIT (le carpophore, la trame blanche du sol), l'interconnexion relie le
champignon aux acteurs qu'il touche réellement dans la simulation (bois mort
qu'il décompose, humus stable qu'il lie, racines qu'il mycorhize — les 3 rôles
du sprint mycélium).

MONO-NIVEAU (comme la faune, §3.1) : le champignon n'a pas de progression de
palier propre (`detecter` ne crédite ni la faune ni le champignon) → il reste
plafonné à palier 1 = cette seule fiche.
"""
from __future__ import annotations

# Clé unique du règne fongique dans l'encyclopédie (source de vérité — reprise
# par `encyclopedie_types.type_de` et par le survol carpophore du tronçon ②).
CLE_CHAMPIGNON = "champignon"

# Fiche générique (blurb + interconnexions), même forme que `faune_encyclo`.
_FICHE = {
    "blurb": (
        "Sous les carpophores éphémères qui percent la litière court une trame "
        "blanche invisible : le mycélium tisse le sol, décompose le bois mort, "
        "lie l'humus et relie les racines entre elles.",
    ),
    # Éléments du milieu que le réseau fongique touche RÉELLEMENT (les 3 rôles :
    # saprophyte du bois, liant de l'humus stable, mycorhize des racines).
    "interconnexions": ("bois_mort", "humus", "racines"),
}


def encyclo_meta() -> dict:
    """Métadonnée de la fiche champignon générique (mono-niveau). Aucune clé en
    argument : il n'existe qu'UNE fiche fongique (Q2). Renvoie `{blurb,
    interconnexions}`, prêt à dispatcher dans `encyclopedie_lire`."""
    return {"blurb": _FICHE["blurb"][0], "interconnexions": _FICHE["interconnexions"]}
