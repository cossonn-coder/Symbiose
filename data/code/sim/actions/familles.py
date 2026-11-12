"""
SYMBIOSE — sim/actions/familles.py
FAMILLES de gestes (sprint ACCÈS AUX GESTES ③, conception
`docs/joueur/gestes/conception_refonte_palette.md` §3.5).

DONNÉE PURE : aucun import, aucune logique. Le tiroir de la palette range les
gestes par famille ; pour que la vue ne redécide jamais du rangement, la table vit
ICI (Python source de vérité) et part telle quelle au pont (`BLOC_FAMILLES`).

Ne pas confondre avec `palette.FAMILLE_CIBLE`, qui classe un geste par NATURE DE
CIBLE (plante, plot, structure…) pour valider une macro. Ici on classe par USAGE
au jardin : c'est un rangement d'étagère, pas une règle de jeu.

Le test `tests/test_pressentis.py` vérifie que chaque verbe de `COUTS` (et chaque
verbe gaté de `GESTE_UNLOCK`) a une famille connue. Un `dict` garantit de lui-même
qu'un verbe n'en a qu'UNE.
"""
from __future__ import annotations

# Ordre d'AFFICHAGE du tiroir (du geste le plus nu au plus lourd : la main, puis
# le sol, puis ce qu'on y met, puis ce qu'on bâtit, puis le paysage alentour).
FAMILLES: tuple[str, ...] = (
    "main", "sol", "semis", "taille", "eau", "compost", "structures", "paysage",
)

# Famille → ses gestes, dans l'ordre d'affichage À L'INTÉRIEUR de la famille.
# C'est la forme lisible (celle de la conception §3.5) ; `FAMILLE_GESTE` en dérive.
_GESTES_PAR_FAMILLE: dict[str, tuple[str, ...]] = {
    "main":       ("recolter", "manger", "glaner", "ecraser", "favoriser_auxiliaire"),
    "sol":        ("becher", "grelinette", "creuser", "drainer", "deraciner"),
    "semis":      ("planter", "bouturer", "greffer", "planter_conteneur"),
    "taille":     ("pincer", "arracher", "couper", "tailler"),
    "eau":        ("arroser",),
    "compost":    ("poser_bac", "poser_pile", "composter", "retourner", "epandre",
                   "empiler_bois", "pailler", "broyer"),
    "structures": ("poser_pot", "poser_bac_culture", "deplacer_pot",
                   "poser_tuteur", "poser_treillis", "poser_pergola", "palisser",
                   "poser_perchoir", "poser_voile", "poser_cloche", "poser_ombriere",
                   "poser_ruche", "recolter_miel"),
    "paysage":    ("abattre", "receper", "eteter", "endiguer", "deriver", "entailler"),
}

# Verbe → famille (la table que lit le pont). Dérivée, jamais saisie deux fois.
FAMILLE_GESTE: dict[str, str] = {
    verbe: famille
    for famille in FAMILLES
    for verbe in _GESTES_PAR_FAMILLE[famille]
}


# Forme d'EXPO au pont : `{ordre: [familles…], gestes: {famille: [verbes…]}}`.
# Pourquoi des LISTES et pas `{verbe: famille}` : le serveur sérialise en clés
# TRIÉES (`sort_keys`, déterminisme du pont), un dict perdrait donc l'ordre
# d'affichage ; une liste le garde. La vue en déduit verbe → famille d'une boucle.
# Statique (ne dépend ni du joueur ni du monde) → construite UNE fois à l'import,
# le snapshot la réutilise telle quelle.
BLOC_FAMILLES: dict = {
    "ordre": list(FAMILLES),
    "gestes": {famille: list(_GESTES_PAR_FAMILLE[famille]) for famille in FAMILLES},
}
