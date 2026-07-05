"""
SYMBIOSE — tools/simserver/perf.py
Banc d'observation perf (sprint « stabilisation perf en run éternel », tronçon ④).

Petit assembleur du bloc `perf` du snapshot : trois observables PUR-LECTURE que
l'overlay debug F4 côté Godot affiche pour vérifier, EN JEU, que la stabilisation
③ tient — que `N plantes` PLAFONNE et que `ms/tick` ne DÉRIVE plus d'année en
année (le crash du monde complet venait de N non borné, cf. 00_etat ①/③).

Règle d'or du serveur : ADAPTATEUR, pas moteur. Ce module n'écrit RIEN dans la
simulation — il lit une durée déjà chronométrée AUTOUR du tick (commands.py),
compte les plantes du snapshot et interroge l'OS pour la mémoire du process.
Golden NEUTRE par construction : le golden tourne hors serveur, ce bloc n'existe
jamais pour lui.
"""
from __future__ import annotations

# `resource` est POSIX-only. La VM (Debian) et la cible de jeu (le F5 de Nico)
# l'ont ; on blinde tout de même l'import pour ne jamais casser le snapshot si un
# jour le serveur tourne sur une plateforme sans (RSS devient simplement None).
try:
    import resource
except ImportError:            # pragma: no cover — plateforme non-POSIX
    resource = None


def rss_mo() -> float | None:
    """Mémoire résidente (RSS) du process serveur, en méga-octets — ou None si
    la plateforme ne l'expose pas.

    `ru_maxrss` est le PIC de RSS depuis le lancement (choix assumé, cf. le
    profileur ① `tools/profile_memoire.py` qui utilise la même source) : sur
    Linux il est en KILO-octets → /1024 pour des Mo. C'est l'observable qui doit
    se STABILISER une fois N borné (③) : si elle grimpe encore linéairement à N
    constant, c'est une fuite à re-investiguer (mais ① n'en a trouvé aucune)."""
    if resource is None:
        return None
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(kb / 1024.0, 1)


def perf_block(ms_tick: float | None, n_plants: int) -> dict:
    """Assemble le bloc `perf` du snapshot. `ms_tick` = durée du dernier
    tick_semaine() mesurée par commands.py (None tant que rien n'a été simulé —
    ex. le snapshot post-init) ; `n_plants` = plantes VIVANTES du snapshot ;
    `rss_mo` = pic RSS du serveur. Arrondis d'instrument, déterministes en
    valeur (la mesure de temps/mémoire ne l'est pas — c'est un compteur debug,
    hors golden)."""
    return {
        "ms_tick": None if ms_tick is None else round(ms_tick, 1),
        "n_plants": n_plants,
        "rss_mo": rss_mo(),
    }
