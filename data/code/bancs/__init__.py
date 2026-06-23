"""
SYMBIOSE — bancs/ (paquet)
Registre des BANCS D'ESSAI : `BANCS[nom]` → fabrique `() -> (tiles, ecos, house,
banque)`. Une fabrique compose un monde paramétré qui force UNE condition
observable (cf. base.py). Le serveur (`cmd_init`) branche `config in BANCS` après
les cas `smoke`/`full` : `init config="<nom>"` monte le banc, sans toucher le
golden (les bancs ne sont jamais montés pour smoke/full).

Les tronçons ②③④ ajoutent leurs entrées ici (édaphique, climatique, biotique).
"""
from .climatique import secheresse_sable, acclimatation, ombre_dense
from .edaphique import chlorose_acidophile, asphyxie_argile, carence_npk
from .biotique import infestation_ravageur, verger_floraison, semis_tempere

BANCS = {
    "secheresse_sable": secheresse_sable,
    "acclimatation": acclimatation,
    "ombre_dense": ombre_dense,
    "chlorose_acidophile": chlorose_acidophile,
    "asphyxie_argile": asphyxie_argile,
    "carence_npk": carence_npk,
    "infestation_ravageur": infestation_ravageur,
    "verger_floraison": verger_floraison,
    "semis_tempere": semis_tempere,
}
