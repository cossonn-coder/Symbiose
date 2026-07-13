"""
SYMBIOSE — tests/test_campagnol_uptake.py
Test dédié du CANAL CAMPAGNOL (sprint santé & résilience ③) : l'herbivorie
racinaire ne blesse plus par un `ReduceHealth` plat mais AFFAME la plante en
rabotant son UPTAKE (philo #2 : flux → contrainte → réponse). On vérifie les
quatre invariants du modèle directement sur `EcoFields.plant_uptake` :

  1. NEUTRALITÉ — `root_herbivory_memory=0` ⇒ uptake STRICTEMENT identique à
     l'appel historique (c'est ce qui garantit le golden NEUTRE hors campagnol) ;
  2. FAMINE — mémoire > 0 ⇒ l'uptake d'eau ET de N/P/K CHUTE (racines rongées) ;
  3. NICHE — une `root_loss_tolerance` d'espèce plus haute ATTÉNUE la chute
     (racines profondes / système fasciculé redondant) ;
  4. MYCORHIZE — un réseau `mycelium` présent COMPENSE une partie de la perte
     (le réseau relaie eau/nutriments que les racines n'atteignent plus).

Aucun RNG : lecture pure des champs → déterministe (philo #3). Lancement depuis
`data/code` : `python3 -m tests.test_campagnol_uptake`.
"""

from __future__ import annotations

from fields.ecofields import EcoFields


def _eco() -> EcoFields:
    """Mini-sol 1×1 gorgé de ressources (uptake non plafonné par le stock → on
    mesure bien la MODULATION racinaire, pas la loi de Liebig)."""
    e = EcoFields(tile_id="t", rows=1, cols=1)
    e.humidite.set(0, 0, 2.0)
    e.n.set(0, 0, 2.5)
    e.p.set(0, 0, 2.5)
    e.k.set(0, 0, 2.5)
    e.lumiere.set(0, 0, 0.8)
    return e


def test_neutralite_sans_campagnol():
    """mémoire = 0 ⇒ uptake bit-identique à l'appel historique (golden NEUTRE)."""
    a, b = _eco(), _eco()
    c_hist = a.plant_uptake(0, 0, 2)                                   # appel historique
    c_neutre = b.plant_uptake(0, 0, 2, root_herbivory_memory=0.0)     # défaut explicite
    assert c_hist == c_neutre, (c_hist, c_neutre)
    print(f"OK neutralité : mémoire=0 bit-identique ({c_hist})")


def test_famine_par_uptake():
    """mémoire > 0 ⇒ l'uptake d'eau ET d'azote CHUTE (chevelu racinaire rongé)."""
    sain = _eco().plant_uptake(0, 0, 2)
    ronge = _eco().plant_uptake(0, 0, 2, root_herbivory_memory=1.0)
    assert ronge["humidite"] < sain["humidite"], (sain, ronge)
    assert ronge["n"] < sain["n"], (sain, ronge)
    print(f"OK famine : eau {sain['humidite']}→{ronge['humidite']}, "
          f"N {sain['n']}→{ronge['n']}")


def test_niche_attenue():
    """Une `root_loss_tolerance` haute (racines profondes) ENCAISSE mieux la perte
    → l'uptake d'une espèce tolérante reste PLUS haut à mémoire égale."""
    fragile = _eco().plant_uptake(0, 0, 2, root_herbivory_memory=1.0,
                                  root_loss_tolerance=0.7)   # bulbeuse superficielle
    coriace = _eco().plant_uptake(0, 0, 2, root_herbivory_memory=1.0,
                                  root_loss_tolerance=1.4)   # pivot profond
    assert coriace["humidite"] > fragile["humidite"], (fragile, coriace)
    print(f"OK niche : eau fragile {fragile['humidite']} < coriace {coriace['humidite']}")


def test_mycorhize_compense():
    """Un réseau `mycelium` présent COMPENSE une part de la perte racinaire →
    l'uptake remonte par rapport au même sujet rongé sur sol non mycorhizé."""
    nu = _eco()
    myco = _eco()
    myco.mycelium.set(0, 0, 1.0)
    u_nu = nu.plant_uptake(0, 0, 2, root_herbivory_memory=1.0)
    u_myco = myco.plant_uptake(0, 0, 2, root_herbivory_memory=1.0)
    assert u_myco["humidite"] > u_nu["humidite"], (u_nu, u_myco)
    print(f"OK mycorhize : eau nu {u_nu['humidite']} < mycorhizé {u_myco['humidite']}")


if __name__ == "__main__":
    test_neutralite_sans_campagnol()
    test_famine_par_uptake()
    test_niche_attenue()
    test_mycorhize_compense()
    print("\n=== test_campagnol_uptake : 4/4 OK ===")
