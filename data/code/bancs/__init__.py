"""
SYMBIOSE — bancs/ (paquet)
Registre des BANCS D'ESSAI : `BANCS[nom]` → fabrique `() -> (tiles, ecos, house,
banque)`. Une fabrique compose un monde paramétré qui force UNE condition
observable (cf. base.py). Le serveur (`cmd_init`) branche `config in BANCS` après
les cas `smoke`/`full` : `init config="<nom>"` monte le banc, sans toucher le
golden (les bancs ne sont jamais montés pour smoke/full).

Les tronçons ②③④ ajoutent leurs entrées ici (édaphique, climatique, biotique).
"""
from .climatique import (secheresse_sable, acclimatation, ombre_dense,
                         pluie_thermique, germination_multifacteur)
from .edaphique import (chlorose_acidophile, asphyxie_argile, carence_npk,
                       rotation_inoculum)
from .hydrologie import tourbiere
from .biotique import (infestation_ravageur, verger_floraison, semis_tempere,
                       etalement_floraison, grimpantes, floraison_saisons)
from .succession import succession_bascule
from .croissance import vieux_pommier
from .luxuriance import luxuriance
from .diversite import diversite_fondatrice
from .modele_spatial import modele_spatial
from . import palette_gestes as _palette_gestes

BANCS = {
    "secheresse_sable": secheresse_sable,
    "acclimatation": acclimatation,
    "ombre_dense": ombre_dense,
    "pluie_thermique": pluie_thermique,
    "germination_multifacteur": germination_multifacteur,
    "chlorose_acidophile": chlorose_acidophile,
    "asphyxie_argile": asphyxie_argile,
    "carence_npk": carence_npk,
    "rotation_inoculum": rotation_inoculum,
    "tourbiere": tourbiere,
    "infestation_ravageur": infestation_ravageur,
    "verger_floraison": verger_floraison,
    "semis_tempere": semis_tempere,
    "etalement_floraison": etalement_floraison,
    "floraison_saisons": floraison_saisons,
    "grimpantes": grimpantes,
    "succession_bascule": succession_bascule,
    "vieux_pommier": vieux_pommier,
    "luxuriance": luxuriance,
    "diversite_fondatrice": diversite_fondatrice,
    "modele_spatial": modele_spatial,
    "palette_gestes": _palette_gestes.palette_gestes,
}

# Hook POST-INIT par banc (palette de gestes ⑤) : callback OPTIONNEL `(game_state,
# player) -> None` appelé par `cmd_init` APRÈS la construction du moteur ET l'opt-in
# Vigueur — le SEUL point où l'état JOUEUR (maîtrise, gestes débloqués) existe (la
# fabrique de banc ne renvoie que le monde, pas le game_state). Le banc « palette »
# s'en sert pour OUVRIR d'emblée les gestes savants (bouturer/greffer) sans jouer
# jusqu'à la maîtrise réelle. Banc sans hook → absent → cmd_init ne fait rien de plus
# (comportement inchangé, golden NEUTRE : smoke/full ne sont pas des bancs).
BANC_POST_INIT = {"palette_gestes": _palette_gestes.post_init}

# Semaine de départ par banc (retour F5 Nico 2026-07-04). La plupart démarrent à
# `week=1` (début printemps) — repli par défaut. `grimpantes` observe des FRILEUSES
# (haricot/jasmin) qu'un départ début printemps fige sous le seuil de croissance
# (~5 °C) pendant des semaines : on le décale à MI-PRINTEMPS (T ~6 °C) pour voir la
# grimpe tout de suite. Lu par `cmd_init` (banc absent → 1 → comportement inchangé,
# golden NEUTRE : smoke/full ne sont pas des bancs).
# `diversite_fondatrice` sème du TOURNESOL (t_germ_opt=20, sol chaud requis) : un
# départ début printemps fige la levée sous le seuil thermique pendant des semaines.
# Décalé MI-PRINTEMPS pour voir la désynchronisation des rythmes tout de suite.
BANC_WEEK_DEPART = {"grimpantes": 9, "luxuriance": 9, "diversite_fondatrice": 9}


def banc_categorie(nom: str) -> str:
    """Catégorie d'un banc = le MODULE thématique d'où vient sa fabrique
    (`bancs.climatique` → "climatique"). DÉRIVÉE, pas maintenue à la main : un
    banc neuf hérite tout seul de la catégorie de son fichier, aucune table à
    resynchroniser (le piège des menus qui mentent, D47). Repli "divers" si le
    module n'est pas résolvable (fabrique anonyme, lambda…)."""
    fabrique = BANCS.get(nom)
    module = getattr(fabrique, "__module__", "") or ""
    cat = module.rsplit(".", 1)[-1]
    return cat if cat and cat != "__init__" else "divers"
