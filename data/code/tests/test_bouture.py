"""
SYMBIOSE — tests/test_bouture.py
Golden JOUEUR du geste BOUTURER (palette de gestes, tronçon ②). Distinct du golden
ÉCOLOGIQUE (`tests/test_golden.py`) : le geste est event-driven, AU-DESSUS du tick,
et n'y participe jamais (aucune espèce bouturable n'est semée par le smoke). Ici on
POSE un monde minimal, on rend une mère mûre et on vérifie le contrat du geste
SANS RNG (bouturer est un acte joueur déterministe, philo #3).

Vérifie :
  1. Mère mûre BOUTURABLE + Vigueur suffisante → un CLONE apparaît sur le plot cible,
     gènes IDENTIQUES à la mère, Vigueur joueur DÉBITÉE, `stress_memory` mère MONTÉE,
     marqueur `bouture_spontanee` posé (voie émergente D12).
  2. Espèce NON bouturable → refus SANS dépense (Vigueur intacte, aucun clone).
  3. Mère TROP JEUNE (pas au dernier stade) → refus SANS dépense.
  4. Mère MORTE → refus SANS dépense.
  5. Vigueur INSUFFISANTE → aucun clone posé (binaire tout-ou-rien), mais la Vigueur
     est drainée (contrat de `spend`).
  6. Le flag `bouturable` par défaut est False (aucune espèce non marquée n'est
     bouturable) → cohérence avec le golden NEUTRE.
  7. `bouturer` est classé "geste" par `encyclopedie_types.type_de` et a sa fiche.
"""
from __future__ import annotations

from world import Tile
from fields import init_eco
from plants import Tomato
from plants.species.aromatiques import Mint
from sim import vigueur as V
from sim import actions as A
from sim.actions import deblocage as D
import sim.encyclopedie_types as ET

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _monde(espece, r=2, c=2):
    """Monde minimal : 1 tuile fertile, une plante de `espece` au dernier stade."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 8, 8, humidite=1.5, fertilite=1.0, microbiome=0.5)
    mother = tile.add_plant(espece, r, c)
    mother.current_stage = len(espece.growth_stages) - 1   # mûre
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": [], "seed": 0x5AB1057E}
    V.ensure_player(gs, "j1")   # avatar plein (courante = max_base)
    return gs, tile, eco, mother


def test_bouture_reussie():
    print("\n[1] mère mûre bouturable + Vigueur pleine → clone posé")
    gs, tile, eco, mother = _monde(Mint)
    mother.genes = {"vigueur": 1.2, "tolerance_ombre": 0.8}
    v_avant = V.ensure_player(gs, "j1")["courante"]
    stress_avant = mother.stress_memory
    n_avant = len(tile.plants)
    ok = A.bouturer(gs, "j1", mother, tile, eco, 5, 5)
    check("bouturer → True", ok)
    check("un plant de plus sur la tuile", len(tile.plants) == n_avant + 1,
          f"{len(tile.plants)}")
    clone = tile.plants[-1]
    check("clone = même espèce", clone.plant_class is Mint)
    check("clone au plot cliqué", clone.position == (5, 5), f"{clone.position}")
    check("clone : gènes IDENTIQUES (copie, pas de brassage)",
          clone.genes == mother.genes and clone.genes is not mother.genes,
          f"{clone.genes}")
    check("Vigueur joueur débitée",
          V.ensure_player(gs, "j1")["courante"] < v_avant,
          f"{v_avant} → {V.ensure_player(gs, 'j1')['courante']}")
    check("stress_memory mère montée",
          mother.stress_memory > stress_avant,
          f"{stress_avant} → {mother.stress_memory}")
    check("marqueur bouture_spontanee posé (voie émergente D12)",
          D._a_evenement(gs, "j1", "bouture_spontanee"))


def test_refus_non_bouturable():
    print("\n[2] espèce NON bouturable → refus sans dépense")
    gs, tile, eco, mother = _monde(Tomato)
    check("Tomato.bouturable == False (défaut)", Tomato.bouturable is False)
    v_avant = V.ensure_player(gs, "j1")["courante"]
    n_avant = len(tile.plants)
    ok = A.bouturer(gs, "j1", mother, tile, eco, 5, 5)
    check("bouturer → False", not ok)
    check("aucun clone", len(tile.plants) == n_avant)
    check("Vigueur INTACTE (refus en amont)",
          V.ensure_player(gs, "j1")["courante"] == v_avant)


def test_refus_trop_jeune():
    print("\n[3] mère trop jeune (pas au dernier stade) → refus sans dépense")
    gs, tile, eco, mother = _monde(Mint)
    mother.current_stage = 0   # semis
    v_avant = V.ensure_player(gs, "j1")["courante"]
    n_avant = len(tile.plants)
    ok = A.bouturer(gs, "j1", mother, tile, eco, 5, 5)
    check("bouturer → False (immature)", not ok)
    check("aucun clone", len(tile.plants) == n_avant)
    check("Vigueur intacte", V.ensure_player(gs, "j1")["courante"] == v_avant)


def test_refus_morte():
    print("\n[4] mère morte → refus sans dépense")
    gs, tile, eco, mother = _monde(Mint)
    mother.health = 0
    v_avant = V.ensure_player(gs, "j1")["courante"]
    n_avant = len(tile.plants)
    ok = A.bouturer(gs, "j1", mother, tile, eco, 5, 5)
    check("bouturer → False (morte)", not ok)
    check("aucun clone", len(tile.plants) == n_avant)
    check("Vigueur intacte", V.ensure_player(gs, "j1")["courante"] == v_avant)


def test_vigueur_insuffisante():
    print("\n[5] Vigueur insuffisante → binaire tout-ou-rien (clone non posé)")
    gs, tile, eco, mother = _monde(Mint)
    V.ensure_player(gs, "j1")["courante"] = 1.0   # bien en deçà du coût MODERE (15)
    n_avant = len(tile.plants)
    ok = A.bouturer(gs, "j1", mother, tile, eco, 5, 5)
    check("bouturer → False (Vigueur insuffisante)", not ok)
    check("aucun clone (tout-ou-rien)", len(tile.plants) == n_avant)
    check("Vigueur drainée (contrat spend)",
          V.ensure_player(gs, "j1")["courante"] == 0.0,
          f"{V.ensure_player(gs, 'j1')['courante']}")


def test_flag_defaut_neutre():
    print("\n[6] flag bouturable défaut False → golden NEUTRE cohérent")
    from plants.base.familles import PlantBase
    check("PlantBase.bouturable défaut False", PlantBase.bouturable is False)
    check("Mint marquée bouturable", Mint.bouturable is True)


def test_geste_classe_et_fiche():
    print("\n[7] bouturer classé geste + fiche encyclopédie présente")
    from sim.geste_corpus import FICHES_GESTE
    from sim.technique_corpus import FICHES_TECHNIQUE
    check("type_de('bouturer') == 'geste'", ET.type_de("bouturer") == "geste")
    check("type_de('bouture') == 'technique'", ET.type_de("bouture") == "technique")
    check("fiche geste bouturer = 3 niveaux",
          set(FICHES_GESTE.get("bouturer", {})) == {1, 2, 3})
    check("fiche technique bouture = 3 niveaux",
          set(FICHES_TECHNIQUE.get("bouture", {})) == {1, 2, 3})


def run():
    test_bouture_reussie()
    test_refus_non_bouturable()
    test_refus_trop_jeune()
    test_refus_morte()
    test_vigueur_insuffisante()
    test_flag_defaut_neutre()
    test_geste_classe_et_fiche()
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    print(f"\n=== BOUTURE : {ok}/{total} ===")
    return ok == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
