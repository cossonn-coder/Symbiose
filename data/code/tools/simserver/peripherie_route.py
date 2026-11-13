"""
SYMBIOSE — tools/simserver/peripherie_route.py
La CEINTURE au pont (sprint PÉRIPHÉRIE, D73, tronçon ⑦) : sérialisation du bloc
`ceinture` du snapshot + routage des SEPT gestes de paysage vers leurs façades.

Un seul module pour les deux sens, parce que c'est une seule responsabilité — « la
périphérie telle que la vue la voit et la manipule » :

  • `ceinture_block(game_state)` → les 4 secteurs en JSON, ou `None` si le monde
    n'a pas de ceinture. C'est ce bloc qui fait cesser `DecorLayer.BuildProfile`
    d'être un GÉNÉRATEUR : la vue consomme désormais la vérité Python (et **D92 se
    referme par le haut** — le hash mal brassé du C# ne sert plus que de repli).
  • `route_peripherie(...)` → les gestes `abattre`/`receper`/`eteter` (④) et
    `endiguer`/`deriver`/`entailler` + la mare (⑤), tous ciblés par un SECTEUR
    (`target.cote` ∈ 0..3), patron des routeurs existants (`structures_route`,
    `conteneurs_route`).

⚠️ La MARE ne prend PAS de verbe neuf : `creuser` est routé ici quand la cible
porte un `cote` (le clic est tombé hors du jardin), et au PLOT sinon — exactement
la décision du ⑤ (`creuser_peripherie` réemploie le verbe, ses coûts et sa fiche).

Le serveur ne réimplémente AUCUNE règle : gates d'outil, coûts, mutations et
cinétiques restent dans `sim/actions/paysage.py` + `fields/peripherie.py`. Ici, on
résout la DÉSIGNATION (un entier de côté) et on traduit le retour en JSON.
"""
from __future__ import annotations

from fields.fleurs_lisiere import (COULEURS, butineurs_par_colonie, colonies_secteur,
                                   floraison_couleur)
from fields.peripherie import COTES, NOMS_COTES
from sim import actions as A

# Verbes de paysage à cible SECTEUR exclusive. `creuser` n'y est PAS : il est
# routé ici par la FORME de sa cible (présence d'un `cote`), comme `ecraser` route
# vers une plante ou une guilde selon son target (protocole 0.3.2).
VERBES = ("abattre", "receper", "eteter", "endiguer", "deriver", "entailler")

# Façade par verbe. `creuser` → `creuser_peripherie` : même verbe côté joueur,
# autre cible côté moteur (aucun `creuser_mare` en doublon).
_FACADES = {
    "abattre": A.abattre,
    "receper": A.receper,
    "eteter": A.eteter,
    "endiguer": A.endiguer,
    "deriver": A.deriver,
    "entailler": A.entailler,
    "creuser": A.creuser_peripherie,
}

# Champs du secteur EXPOSÉS à la vue. Les huit premiers sont ceux du modèle §4.1
# (kickoff ⑦ §A) ; `entaille_cm` et `ouvrage` s'y ajoutent parce que la vue en a
# besoin pour DESSINER ce que le ⑤ a rendu possible (la cicatrice d'une falaise
# entaillée, l'ouvrage d'eau en place). Tout le reste de l'état de secteur
# (horloges, cibles de repousse, verrou de signe) est de la MÉCANIQUE : la vue n'en
# a rien à faire et l'exposer inviterait à la recalculer côté C# (invariant
# « Godot bête »).
CHAMPS_VUE = ("cote", "type", "essence", "hauteur_canopee", "densite_ligneuse",
              "souche_memory", "ligne_eau", "altitude_relative",
              "entaille_cm", "ouvrage")


def ceinture_block(game_state: dict):
    """Les 4 secteurs de la ceinture en JSON, ou `None` si le monde n'en a pas.

    OPT-IN STRICT : un monde sans `ceinture` (le smoke, un banc thématique) ne
    produit AUCUNE clé → la vue retombe sur `DecorLayer.BuildProfile(seed)`, son
    repli local. Volume négligeable (4 entrées de 10 champs + quelques colonies) —
    contrairement au bloc `sprites`, la question du format compact ne se pose pas ici.
    Depuis 0.6.4 (D124) chaque secteur porte aussi `floraison` {couleur: [0,1]} et
    `colonies` (cf. `_colonie`) ; le compte `butineurs` change chaque semaine, la
    géométrie jamais tant que la ceinture ne change pas de type.

    PURE lecture (aucune écriture moteur) → golden NEUTRE : le golden tourne hors
    serveur et n'a pas de clé `ceinture`.
    """
    ceinture = game_state.get("ceinture")
    if not ceinture:
        return None
    seed = game_state.get("seed", 0)
    wiy = (game_state.get("week", 1) - 1) % 52 + 1
    floraison = {coul: round(floraison_couleur(coul, wiy), 3) for coul in COULEURS}
    comptes = butineurs_par_colonie(game_state)
    return [{**{champ: s.get(champ) for champ in CHAMPS_VUE},
             "floraison": floraison,
             "colonies": [_colonie(col, comptes.get(col, 0))
                          for col in colonies_secteur(seed, s["cote"], s["type"])]}
            for s in ceinture]


def _colonie(col, butineurs: int) -> dict:
    """Une colonie pour la vue (0.6.4) : `u`/`depth` = repère de `DecorLayer.EdgePoint`,
    en cm ; `ru`/`rd` = demi-axes de la tache ; `graine` = hash de ses bords irréguliers."""
    return {"u": round(col.u_cm, 1), "depth": round(col.depth_cm, 1),
            "ru": round(col.rayon_u_cm, 1), "rd": round(col.rayon_d_cm, 1),
            "couleur": col.couleur, "graine": col.graine, "butineurs": butineurs}


def _cote(target: dict):
    """Le côté cardinal désigné (0..3), ou `None` si la désignation est invalide.
    `bool` est un sous-type d'`int` → exclu (un `true` JSON n'est pas un côté)."""
    cote = target.get("cote")
    if not isinstance(cote, int) or isinstance(cote, bool) or cote not in COTES:
        return None
    return cote


def _etat(secteur: dict) -> str:
    """Résumé DIAGNOSTIC d'un secteur pour le message d'ACK (lecture pure) : ce que
    le geste a réellement produit, jamais ce qu'on avait prévu. EN MOTS depuis
    GESTES LISIBLES ① (0.6.14, philo #5) : plus de centimètres ni de densité chiffrée,
    le paysage se lit dans la vue, la phrase ne fait que le nommer."""
    if secteur["type"] == "falaise":
        return "la roche à nu"
    bits = []
    if secteur["hauteur_canopee"] > 0.0 or secteur["densite_ligneuse"] > 0.0:
        bits.append("un couvert ligneux dense" if secteur["densite_ligneuse"] >= 0.5
                    else "un couvert ligneux clair")
    if secteur["ligne_eau"] != 0.0:
        bits.append("une eau haute" if secteur["ligne_eau"] > 0.0 else "une eau basse")
    return " · ".join(bits) or "rien de ligneux"


def route_peripherie(game_state: dict, player: str, verb: str, target: dict,
                     params: dict, bilan) -> dict:
    """Route un geste de paysage vers sa façade. La cible est un SECTEUR entier
    (« j'ouvre une clairière au nord ») : la granularité d'un geste, décision D-1.

    Trois refus de DÉSIGNATION avant tout appel (ne coûtent rien, la façade n'est
    même pas invoquée) : côté invalide, pas de ceinture dans ce monde, secteur
    introuvable. Les refus MÉTIER (outil manquant, rien à couper, bord à sec,
    Vigueur) sont rendus par la façade — on relaie son verdict, on ne le devine pas.
    """
    cote = _cote(target)
    if cote is None:
        return bilan(False, 0.0, 0.0,
                     f"côté de terrain invalide : {target.get('cote')!r} "
                     "(attendu 0=nord, 1=est, 2=sud, 3=ouest)")
    ceinture = game_state.get("ceinture")
    if not ceinture:
        return bilan(False, 0.0, 0.0, "ce terrain n'a pas de périphérie posée")
    secteur = next((s for s in ceinture if s["cote"] == cote), None)
    if secteur is None:
        return bilan(False, 0.0, 0.0, f"secteur introuvable : {cote}")

    nom = NOMS_COTES[cote]
    cost = A.cout_action(game_state, player, verb, A.OBJETS_TOUCHES[verb])
    ok = _FACADES[verb](game_state, player, cote)
    if not ok:
        # Un seul message pour tous les refus métier : la vue n'a pas à deviner
        # LEQUEL (outil, bord à sec, roche rasée, Vigueur). L'apprentissage passe
        # par l'encyclopédie et le carnet, pas par un diagnostic de moteur.
        return bilan(False, 0.0, 0.0,
                     f"{verb} refusé au bord {nom} — outil manquant, "
                     "rien à prendre ici, ou Vigueur insuffisante")
    return bilan(True, cost, 0.0, f"{verb} au bord {nom} : {_etat(secteur)}")
