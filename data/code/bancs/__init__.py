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
from .edaphique import chlorose_acidophile, asphyxie_argile, carence_npk
from .biotique import (infestation_ravageur, verger_floraison, semis_tempere,
                       etalement_floraison, grimpantes)
from .succession import succession_bascule

BANCS = {
    "secheresse_sable": secheresse_sable,
    "acclimatation": acclimatation,
    "ombre_dense": ombre_dense,
    "pluie_thermique": pluie_thermique,
    "germination_multifacteur": germination_multifacteur,
    "chlorose_acidophile": chlorose_acidophile,
    "asphyxie_argile": asphyxie_argile,
    "carence_npk": carence_npk,
    "infestation_ravageur": infestation_ravageur,
    "verger_floraison": verger_floraison,
    "semis_tempere": semis_tempere,
    "etalement_floraison": etalement_floraison,
    "grimpantes": grimpantes,
    "succession_bascule": succession_bascule,
}

# Semaine de départ par banc (retour F5 Nico 2026-07-04). La plupart démarrent à
# `week=1` (début printemps) — repli par défaut. `grimpantes` observe des FRILEUSES
# (haricot/jasmin) qu'un départ début printemps fige sous le seuil de croissance
# (~5 °C) pendant des semaines : on le décale à MI-PRINTEMPS (T ~6 °C) pour voir la
# grimpe tout de suite. Lu par `cmd_init` (banc absent → 1 → comportement inchangé,
# golden NEUTRE : smoke/full ne sont pas des bancs).
BANC_WEEK_DEPART = {"grimpantes": 9}
