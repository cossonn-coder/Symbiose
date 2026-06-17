"""
SYMBIOSE — tests/test_lifecycle.py
Tronçon ⑤ (arc pollinisation) — ponts de cycle de vie (§D).

Deux ponts data-driven : chenille→papillon (la larve broute le feuillage, effet
+herbivorie) et syrphe_larve→syrphe (la larve prédate le ravageur, effet
−ravageur). Cycle par plot : ponte (fenêtre photopériodique) → maturation par la
nourriture → famine de l'excédent → métamorphose (larve → adulte).

Vérifications :
  A. INVARIANT §D.6 — à 0 adulte (aucune ponte), les champs larvaires restent
     STRICTEMENT nuls ; et l'herbivorie à chenille=0 lit EXACTEMENT le ravageur
     (la chenille n'ajoute rien). C'est ce qui rend le re-figeage golden MAÎTRISÉ.
  B. CYCLE — avec adultes + ressource, la chenille MONTE (ponte), MÛRIT, puis se
     MÉTAMORPHOSE (le champ papillon reçoit un terme-source). Boucle larve→adulte.
  C. FAMINE — sans ressource, une cohorte de larves DÉCLINE (boom-bust).
  D. DÉTERMINISME — deux ticks identiques donnent le même état (zéro RNG).

Lancement (depuis data/code/) :
  python3 -m tests.test_lifecycle
"""

import sys

from world import Tile
from fields import init_eco, build_lifecycle_bridges
from sim.effects.perturbations import herbivory_pressure, HERBIVORY_GAIN
from plants import Basil

ROWS, COLS = 6, 8
ETE = 25   # plein été : fenêtre de ponte ouverte pour les deux ponts


def _eco():
    tile = Tile(tile_id="TL", soil_type="terre")
    eco = init_eco("TL", ROWS, COLS, humidite=1.5, fertilite=1.0, microbiome=0.3)
    return tile, eco


def _all_zero(field) -> bool:
    return all(field.at_plot(r, c) == 0.0
               for r in range(field.rows) for c in range(field.cols))


# ---------------------------------------------------------------------------
# A. INVARIANT §D.6
# ---------------------------------------------------------------------------

def test_invariant_zero_adulte():
    """Aucun adulte (papillon/syrphe = 0) → aucune ponte → les 4 champs larvaires
    restent nuls, quelle que soit la ressource. Tick répété pour exclure une
    accumulation lente."""
    tile, eco = _eco()
    # Ressource abondante mais PAS d'adulte : la ponte est ∝ adulte → 0.
    for p in (Basil,):
        tile.add_plant(p, 2, 2)
    eco.populations["ravageur"].fill(0.8)   # ressource de la syrphe_larve
    for _ in range(20):
        eco.tick_lifecycle_bridges(tile, tile.plants, ETE)
    for name, f in eco.larvae.items():
        assert _all_zero(f), f"{name} non nul sans adulte (invariant cassé)"
    print("[lifecycle] A. invariant : 0 adulte → 0 larve (§D.6) : OK")


def test_invariant_herbivorie_chenille_zero():
    """À chenille=0, la pression d'herbivorie vaut EXACTEMENT ravageur·GAIN — la
    chenille n'ajoute rien (structure de l'invariant golden : le LECTEUR lit
    `ravageur + chenille`, identique à avant ⑤ quand chenille=0)."""
    tile, eco = _eco()
    plant = tile.add_plant(Basil, 3, 4)
    r, c = plant.position
    eco.populations["ravageur"].fill(0.5)
    assert _all_zero(eco.larvae["chenille"]), "chenille devrait être nulle au repos"
    # Pression attendue = ravageur·GAIN (chenille=0). On vérifie le SEUIL de
    # déclenchement : à 0.5·0.20=0.10 > 0.005, l'herbivorie s'exprime.
    muts = herbivory_pressure(plant, tile, {}, eco)
    eco.populations["ravageur"].fill(0.0)
    muts_zero = herbivory_pressure(plant, tile, {}, eco)
    assert muts and not muts_zero, \
        "à chenille=0, l'herbivorie doit suivre le seul ravageur"
    print("[lifecycle] A. herbivorie chenille=0 ≡ ravageur seul : OK")


def test_chenille_ajoute_herbivorie():
    """À ravageur=0 mais chenille>0, l'herbivorie s'exprime QUAND MÊME (la larve
    broute) — preuve que `ravageur + chenille` est bien lu (effet +herbivorie §D)."""
    tile, eco = _eco()
    plant = tile.add_plant(Basil, 3, 4)
    r, c = plant.position
    eco.populations["ravageur"].fill(0.0)
    eco.larvae["chenille"].fill(0.6)   # 0.6·0.20 = 0.12 > seuil
    muts = herbivory_pressure(plant, tile, {}, eco)
    assert muts, "une chenille dense doit infliger de l'herbivorie sans ravageur"
    print(f"[lifecycle] A. chenille seule mord (GAIN={HERBIVORY_GAIN}) : OK")


# ---------------------------------------------------------------------------
# B. CYCLE — ponte → maturation → métamorphose
# ---------------------------------------------------------------------------

def test_cycle_metamorphose_syrphe():
    """Avec syrphe (adultes) + ravageur (ressource/lieu de ponte de la larve), la
    syrphe_larve MONTE puis se métamorphose → le champ syrphe reçoit un terme-source
    (boucle larve→adulte). On pilote ce pont car sa ressource = le champ ravageur,
    directement remplissable (≠ chenille, dont la ressource est le feuillage vivant)."""
    tile, eco = _eco()
    eco.populations["ravageur"].fill(0.8)   # ressource + lieu de ponte de la larve
    eco.populations["syrphe"].fill(0.6)     # adultes présents → ils pondent
    larve_max = 0.0
    metamorphose = False
    for _ in range(40):
        avant = eco.populations["syrphe"].average()
        eco.populations["ravageur"].fill(0.8)   # maintien de la ressource (isolé du tick guilde)
        eco.tick_lifecycle_bridges(tile, tile.plants, ETE)
        larve_max = max(larve_max, eco.larvae["syrphe_larve"].average())
        # métamorphose détectée si le champ syrphe AUGMENTE (terme-source larvaire)
        if eco.populations["syrphe"].average() > avant + 1e-9:
            metamorphose = True
    assert larve_max > 0.0, "la syrphe_larve n'a jamais été pondue"
    assert metamorphose, "aucune métamorphose syrphe_larve→syrphe détectée"
    print(f"[lifecycle] B. cycle syrphe_larve→syrphe (pic larve {larve_max:.3f}) : OK")


# ---------------------------------------------------------------------------
# C. FAMINE
# ---------------------------------------------------------------------------

def test_famine_declin():
    """Une cohorte de larves SANS ressource décline (mortalité de famine, §D.3.4).
    On charge la chenille mais on prive de feuillage (aucune plante) → la ponte est
    nulle (pas d'adulte non plus) et la famine raboteuse fait reculer la cohorte."""
    tile, eco = _eco()           # aucune plante → ressource feuillage = 0
    eco.larvae["chenille"].fill(0.8)
    d0 = eco.larvae["chenille"].average()
    eco.tick_lifecycle_bridges(tile, tile.plants, ETE)
    d1 = eco.larvae["chenille"].average()
    assert d1 < d0, f"famine attendue (avant {d0:.3f} → après {d1:.3f})"
    print(f"[lifecycle] C. famine sans ressource ({d0:.2f}→{d1:.2f}) : OK")


# ---------------------------------------------------------------------------
# D. DÉTERMINISME
# ---------------------------------------------------------------------------

def _digest(eco) -> tuple:
    vals = []
    for name in sorted(eco.larvae):
        f = eco.larvae[name]
        vals += [round(f.at_plot(r, c), 9)
                 for r in range(f.rows) for c in range(f.cols)]
    for name in ("papillon", "syrphe"):
        f = eco.populations[name]
        vals += [round(f.at_plot(r, c), 9)
                 for r in range(f.rows) for c in range(f.cols)]
    return tuple(vals)


def test_determinisme():
    """Deux mondes identiques tickés à l'identique → même état larvaire (philo #3)."""
    def run():
        tile, eco = _eco()
        tile.add_plant(Basil, 2, 2)
        eco.populations["papillon"].fill(0.5)
        eco.populations["syrphe"].fill(0.5)
        eco.populations["ravageur"].fill(0.4)
        for _ in range(12):
            eco.tick_lifecycle_bridges(tile, tile.plants, ETE)
        return _digest(eco)
    assert run() == run(), "tick des ponts non déterministe !"
    print("[lifecycle] D. déterminisme du tick des ponts : OK")


def main():
    test_invariant_zero_adulte()
    test_invariant_herbivorie_chenille_zero()
    test_chenille_ajoute_herbivorie()
    test_cycle_metamorphose_syrphe()
    test_famine_declin()
    test_determinisme()
    print("[lifecycle] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
