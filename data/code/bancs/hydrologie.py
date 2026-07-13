"""
SYMBIOSE — bancs/hydrologie.py
Bancs d'essai HYDROLOGIQUES (relief & marécages).

Tronçon ③ du sprint « hydrologie & marécages ». Un monde paramétré qui FORCE une
CUVETTE GORGÉE — altitude basse, sol saturé, lame d'eau de surface au-dessus de
SEUIL_FLAQUE, mémoire de marais déjà installée — pour observer le MARÉCAGE et ses
effets émergents (décompo anaérobie ralentie → tourbe ; acidification du pH). Pure
composition de l'état moteur (aucune mécanique nouvelle) → golden NEUTRE (ces
fabriques ne sont jamais montées pour smoke/full, cf. `cmd_init`).

Deux tuiles JUMELLES (même sol, même microbiome, même pH de départ) ne différant
QUE par l'état de marais : MARAIS (mémoire pré-installée + flaque entretenue) vs
TEMOIN (sec, marais nul). L'oracle (tests/bancs/test_hydrologie.py) compare : le
marais RALENTIT la décompo (`decomp_speed`) et ACIDIFIE le pH contre le témoin, et
son état PERSISTE (hystérèse).
"""
from __future__ import annotations

from .base import build_banc_tile, monde

# Cuvette GORGÉE : altitude basse (fond de vallon), sol à saturation (les pores sont
# pleins), lame de surface franchement au-dessus de SEUIL_FLAQUE (0.10) = flaque
# installée, et mémoire de marais DÉJÀ au-dessus de MARAIS_ON (0.60) → le plot est
# déjà « noirci » en marécage. Le sol saturé + la flaque ENTRETIENNENT la mémoire
# (cible=1 tant que la lame dure) → l'état ne retombe pas pendant l'observation.
ALT_CUVETTE   = 2.0    # cm — fond de cuvette (bien plus bas que ALT_BASE=20)
HUM_SATUREE   = 3.0    # pores pleins (= HUM_CAP) → aucune infiltration ne draine la flaque
EAU_FLAQUE    = 1.2    # lame de surface franche (>> SEUIL_FLAQUE)
MARAIS_INSTALLE = 0.85  # mémoire pré-installée (> MARAIS_ON) : marécage déjà en place
PH_NEUTRE     = 6.8    # pH de départ neutre (terre) → l'acidification tourbeuse sera visible


def tourbiere():
    """Banc « tourbière » : une cuvette GORGÉE (marais installé) face à un TÉMOIN
    sec, même sol/microbiome/pH de départ. Le marais ralentit la décompo et
    acidifie le pH ; l'état PERSISTE (hystérèse). Oracle : tests/bancs/test_hydrologie.py."""
    marais, eco_m = build_banc_tile("TOURBIERE", "terre", 8, 8,
                                    humidite=HUM_SATUREE, fertilite=1.0,
                                    microbiome=0.6, ph=PH_NEUTRE,
                                    altitude=ALT_CUVETTE, eau_surface=EAU_FLAQUE,
                                    marais_memory=MARAIS_INSTALLE)
    temoin, eco_t = build_banc_tile("TEMOIN_SEC", "terre", 8, 8, 500.0, 0.0,
                                    humidite=1.2, fertilite=1.0,
                                    microbiome=0.6, ph=PH_NEUTRE)
    return monde([marais, temoin],
                 {marais.tile_id: eco_m, temoin.tile_id: eco_t})
