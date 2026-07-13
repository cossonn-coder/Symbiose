"""
SYMBIOSE — tests/diag_morts_field.py
DIAGNOSTIC réutilisable (PAS un test pass/fail) — lancé À LA DEMANDE.

Question : « de quoi meurt une plante ANNUELLE quand on pousse UN champ
écologique à un extrême ? ». Pour chaque scénario on isole un seul facteur :
tuile 6×6 terre, climat de LABORATOIRE (météo douce constante, ni pluie ni gel
sauf le scénario gel), germination spontanée coupée, aléas ravageurs neutralisés
(sauf le scénario qui injecte le champ ravageur directement). Le champ ciblé est
CLAMPÉ à sa valeur extrême AVANT chaque tick, puis on lit la cause + la semaine
+ l'âge de la mort de NOTRE plante (3,3).

Subtilité de détection : une mort « squelette » (hiver annuel, conflit) met
`plant.morte=True` SANS mettre `vitalite=0` ; `is_alive` ne teste que la vitalité.
On détecte donc la mort par `plant.morte or plant.vitalite <= 0`.

Leçon attendue : seuls l'EAU (excès/défaut), le FROID et la PRESSION BIOTIQUE
tuent directement ; NPK / pH / structure / lumière agissent sur la CROISSANCE,
pas sur la survie (la plante stagne puis meurt à l'hiver, fin de cycle annuel).

Lancement (depuis data/code/) :
  python3 -m tests.diag_morts_field
"""

import re

import sim.engine.boucle as _boucle
from sim.weather import WeatherEvent
from world import Tile
from plants import Zucchini
from fields import init_eco
from sim.engine import Engine


def _make_meteo(temp):
    """Générateur de météo de labo : beau temps constant, température imposée,
    nébulosité claire neutre. Remplace `weather_state` (pas de pluie → pas
    d'asphyxie « parasite » ; gel uniquement si temp < 0)."""
    calme = WeatherEvent("Beau temps", 0.0, 1, "global")
    return lambda seed, week: (calme, temp, 0.1)


def _mort(plant) -> bool:
    """Vrai dès que la plante est morte, quelle que soit la VOIE : santé à 0
    (fonte, gel, herbivorie, sécheresse, asphyxie…) OU drapeau squelette `morte`
    (hiver annuel, conflit, qui ne passent pas par vitalite=0)."""
    return plant.morte or plant.vitalite <= 0


def _classify(log, tag):
    """Lit la cause de mort dans le log de la semaine du décès, ciblée sur
    l'identité « nom@(r, c) » de NOTRE plante."""
    for line in log:
        if tag not in line:
            continue
        if "sénescence" in line:        return "sénescence"
        if "asphyxié" in line:          return "asphyxie (excès d'eau)"
        if "(annual)" in line:          return "hiver — fin de cycle annuel"
        if "(conflit)" in line:         return "conflit spatial"
        m = re.search(r"\[([^\]]+)\].*meurt", line)   # ReduceHealth : [reason] → meurt
        if m:                           return m.group(1)
        if "meurt" in line:             return line.strip()
    return None


def run(name, fields=None, temp=15.0, ravageur=0.0, max_weeks=60,
        plant_cls=Zucchini):
    """Un scénario : `fields` = dict {nom_champ: valeur} clampé à chaque tick ;
    `temp` = température météo imposée ; `ravageur` > 0 = densité de ravageur
    injectée (auxiliaires mis à 0). Renvoie (nom, cause, semaine, âge_ans)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # pas d'adventices
    _boucle.weather_state = _make_meteo(temp)
    # Neutralise l'aléa ravageur saisonnier aléatoire (sinon un coup de Limaces
    # devance le facteur testé) : on ne garde que « Calme ».
    _boucle.ALEAS_RAVAGEURS = [a for a in _boucle.ALEAS_RAVAGEURS
                              if a.nom == "Calme"] or _boucle.ALEAS_RAVAGEURS[:1]

    plant = tile.add_plant(plant_cls, 3, 3)
    tag = f"{plant.name}@{plant.position}"
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    engine = Engine(gs)

    fields = fields or {}

    def clamp():
        for fname, val in fields.items():
            f = eco.get_field(fname)
            for r in range(6):
                for c in range(6):
                    f.set(r, c, val)
        if ravageur > 0:
            for pf in eco.category_fields("ravageur"):
                for r in range(6):
                    for c in range(6):
                        pf.set(r, c, ravageur)
            for pf in eco.category_fields("auxiliaire"):
                for r in range(6):
                    for c in range(6):
                        pf.set(r, c, 0.0)

    for wk in range(max_weeks):
        clamp()
        log = engine.tick_semaine()
        if _mort(plant):
            return name, _classify(log, tag) or "indéterminée", wk + 1, plant.age_years
        gs["log"].clear()
    return name, "survit (stagne, jamais morte)", max_weeks, plant.age_years


SCENARIOS = [
    ("CONTROLE (tout neutre)",          dict()),
    ("humidité=3.0 (sol gorgé)",        dict(fields={"humidite": 3.0})),
    ("humidité=0.0 (sécheresse)",       dict(fields={"humidite": 0.0})),
    ("température=-5°C (gel)",           dict(temp=-5.0)),
    ("ravageur saturé + 0 auxiliaire",  dict(ravageur=1.0, fields={"microbiome": 0.05})),
    ("microbiome=0 + humidité=2.2",     dict(fields={"microbiome": 0.0, "humidite": 2.2})),
    ("NPK=0 (famine nutritive)",        dict(fields={"n": 0.0, "p": 0.0, "k": 0.0})),
    ("pH=4.0 (très acide)",             dict(fields={"ph": 4.0})),
    ("pH=8.5 (très alcalin)",           dict(fields={"ph": 8.5})),
    ("structure=0 + humidité=2.2",      dict(fields={"structure_sol": 0.0, "humidite": 2.2})),
    ("lumière=0 (ombre totale)",        dict(fields={"lumiere": 0.0})),
    ("disturbance=1.0 (perturbation)",  dict(fields={"disturbance": 1.0})),
]


def main():
    print(f"{'SCÉNARIO':<34} | {'CAUSE DE MORT':<32} | {'SEM.':>5} | {'ÂGE(ans)':>8}")
    print("-" * 92)
    for nm, kw in SCENARIOS:
        name, cause, wk, age = run(nm, **kw)
        print(f"{name:<34} | {cause:<32} | {wk:>5} | {age:>8.2f}")


if __name__ == "__main__":
    main()
