"""
SYMBIOSE — bancs/ (paquet)
Registre des BANCS D'ESSAI : `BANCS[nom]` → fabrique `() -> (tiles, ecos, house,
banque)`. Une fabrique compose un monde paramétré qui force UNE condition
observable (cf. base.py). Le serveur (`cmd_init`) branche `config in BANCS` après
les cas `smoke`/`full` : `init config="<nom>"` monte le banc, sans toucher le
golden (les bancs ne sont jamais montés pour smoke/full).

Les tronçons ②③④ ajoutent leurs entrées ici (édaphique, climatique, biotique).
"""
from .climatique import secheresse_sable

BANCS = {
    "secheresse_sable": secheresse_sable,
}
