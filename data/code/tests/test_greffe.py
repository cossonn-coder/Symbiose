"""
SYMBIOSE — tests/test_greffe.py
Golden JOUEUR du geste GREFFER (palette de gestes, tronçon ③). Distinct du golden
ÉCOLOGIQUE (`tests/test_golden.py`) : le geste est event-driven, AU-DESSUS du tick,
et n'y participe jamais (aucune espèce greffable n'est greffée par le smoke). Ici on
POSE un monde minimal, on pose un greffon + un porte-greffe, et on vérifie le contrat
du geste SANS RNG (greffer est un acte joueur déterministe, philo #3).

Vérifie :
  1. Greffon + porte-greffe de MÊME FAMILLE, tous deux greffables, Vigueur suffisante
     → le porte-greffe ADOPTE la `plant_class` du greffon + ses gènes AÉRIENS, CONSERVE
     ses gènes RACINAIRES + son établissement (âge/stade/position), le greffon est
     CONSOMMÉ (mort), la Vigueur joueur est DÉBITÉE.
  2. Familles DIFFÉRENTES → refus SANS dépense (Vigueur intacte, rien changé).
  3. Espèce NON greffable → refus SANS dépense.
  4. Greffon ou porte-greffe MORT → refus SANS dépense.
  5. Vigueur INSUFFISANTE → binaire tout-ou-rien (rien greffé), mais Vigueur drainée
     (contrat de `spend`).
  6. Le flag `greffable` par défaut est False → cohérence avec le golden NEUTRE.
  7. `greffer` est classé "geste" et `greffe` "technique" par `encyclopedie_types`,
     et chacun a sa fiche 3 niveaux.
  8. Partition des gènes AÉRIEN/RACINAIRE : union = GENE_NAMES, disjointes (D8).
"""
from __future__ import annotations

from world import Tile
from fields import init_eco
from plants import Tomato
from plants.perennials import AppleTree, CherryTree, Fig
from plants.genetics import GENE_NAMES
from sim import vigueur as V
from sim import actions as A
from sim.actions.greffe import GENES_AERIENS, GENES_RACINAIRES
import sim.encyclopedie_types as ET

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _monde(esp_greffon, esp_portegreffe):
    """Monde minimal : 1 tuile fertile, un greffon et un porte-greffe déjà mûrs."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 8, 8, humidite=1.5, fertilite=1.0, microbiome=0.5)
    scion = tile.add_plant(esp_greffon, 2, 2)
    rootstock = tile.add_plant(esp_portegreffe, 5, 5)
    for p in (scion, rootstock):
        p.current_stage = len(p.plant_class.growth_stages) - 1
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": [], "seed": 0x5AB1057E}
    V.ensure_player(gs, "j1")   # avatar plein (courante = max_base)
    return gs, tile, eco, scion, rootstock


def test_greffe_reussie():
    print("\n[1] greffon + porte-greffe même famille, greffables → recomposition D8")
    gs, tile, eco, scion, rootstock = _monde(AppleTree, CherryTree)
    # Gènes DISTINCTS pour tracer la source de chaque organe après greffe.
    scion.genes = {g: 0.2 for g in GENE_NAMES}       # greffon = tout à 0.2
    rootstock.genes = {g: 0.9 for g in GENE_NAMES}   # porte-greffe = tout à 0.9
    stage_avant = rootstock.current_stage
    pos_avant = rootstock.position
    v_avant = V.ensure_player(gs, "j1")["courante"]
    ok = A.greffer(gs, "j1", scion, rootstock, eco)
    check("greffer → True", ok)
    check("porte-greffe adopte plant_class du greffon (identité aérienne)",
          rootstock.plant_class is AppleTree)
    check("gènes AÉRIENS pris du greffon (0.2)",
          all(rootstock.gene(g) == 0.2 for g in GENES_AERIENS),
          f"{ {g: rootstock.gene(g) for g in GENES_AERIENS} }")
    check("gènes RACINAIRES conservés du porte-greffe (0.9)",
          all(rootstock.gene(g) == 0.9 for g in GENES_RACINAIRES),
          f"{ {g: rootstock.gene(g) for g in GENES_RACINAIRES} }")
    check("établissement conservé : stade INCHANGÉ",
          rootstock.current_stage == stage_avant, f"{rootstock.current_stage}")
    check("établissement conservé : position INCHANGÉE",
          rootstock.position == pos_avant, f"{rootstock.position}")
    check("greffon CONSOMMÉ (mort)", not scion.is_alive)
    check("Vigueur joueur débitée",
          V.ensure_player(gs, "j1")["courante"] < v_avant,
          f"{v_avant} → {V.ensure_player(gs, 'j1')['courante']}")


def test_refus_familles_differentes():
    print("\n[2] familles différentes → refus sans dépense")
    gs, tile, eco, scion, rootstock = _monde(Fig, CherryTree)  # Moraceae vs Rosaceae
    v_avant = V.ensure_player(gs, "j1")["courante"]
    classe_avant = rootstock.plant_class
    ok = A.greffer(gs, "j1", scion, rootstock, eco)
    check("greffer → False (familles incompatibles)", not ok)
    check("porte-greffe INCHANGÉ", rootstock.plant_class is classe_avant)
    check("greffon INTACT (vivant)", scion.is_alive)
    check("Vigueur INTACTE (refus en amont)",
          V.ensure_player(gs, "j1")["courante"] == v_avant)


def test_refus_non_greffable():
    print("\n[3] espèce non greffable → refus sans dépense")
    gs, tile, eco, scion, rootstock = _monde(Tomato, Tomato)
    check("Tomato.greffable == False (défaut)",
          getattr(Tomato, "greffable", False) is False)
    v_avant = V.ensure_player(gs, "j1")["courante"]
    ok = A.greffer(gs, "j1", scion, rootstock, eco)
    check("greffer → False (non greffable)", not ok)
    check("Vigueur intacte", V.ensure_player(gs, "j1")["courante"] == v_avant)


def test_refus_mort():
    print("\n[4] greffon ou porte-greffe mort → refus sans dépense")
    gs, tile, eco, scion, rootstock = _monde(AppleTree, CherryTree)
    scion.vitalite = 0.0   # greffon mort
    v_avant = V.ensure_player(gs, "j1")["courante"]
    classe_avant = rootstock.plant_class
    ok = A.greffer(gs, "j1", scion, rootstock, eco)
    check("greffer → False (greffon mort)", not ok)
    check("porte-greffe inchangé", rootstock.plant_class is classe_avant)
    check("Vigueur intacte", V.ensure_player(gs, "j1")["courante"] == v_avant)


def test_vigueur_insuffisante():
    print("\n[5] Vigueur insuffisante → binaire tout-ou-rien (rien greffé)")
    gs, tile, eco, scion, rootstock = _monde(AppleTree, CherryTree)
    V.ensure_player(gs, "j1")["courante"] = 1.0   # bien en deçà du coût ÉLEVÉ
    classe_avant = rootstock.plant_class
    ok = A.greffer(gs, "j1", scion, rootstock, eco)
    check("greffer → False (Vigueur insuffisante)", not ok)
    check("porte-greffe inchangé (tout-ou-rien)",
          rootstock.plant_class is classe_avant)
    check("greffon intact (greffe non faite)", scion.is_alive)
    check("Vigueur drainée (contrat spend)",
          V.ensure_player(gs, "j1")["courante"] == 0.0,
          f"{V.ensure_player(gs, 'j1')['courante']}")


def test_flag_defaut_neutre():
    print("\n[6] flag greffable défaut False → golden NEUTRE cohérent")
    from plants.base.familles import PlantBase
    check("PlantBase.greffable défaut False", PlantBase.greffable is False)
    check("AppleTree marquée greffable", AppleTree.greffable is True)


def test_geste_classe_et_fiche():
    print("\n[7] greffer classé geste + greffe technique + fiches présentes")
    from sim.geste_corpus import FICHES_GESTE
    from sim.technique_corpus import FICHES_TECHNIQUE
    check("type_de('greffer') == 'geste'", ET.type_de("greffer") == "geste")
    check("type_de('greffe') == 'technique'", ET.type_de("greffe") == "technique")
    check("type_de('greffoir') == 'outil'", ET.type_de("greffoir") == "outil")
    check("fiche geste greffer = 3 niveaux",
          set(FICHES_GESTE.get("greffer", {})) == {1, 2, 3})
    check("fiche technique greffe = 3 niveaux",
          set(FICHES_TECHNIQUE.get("greffe", {})) == {1, 2, 3})


def test_partition_genes():
    print("\n[8] partition aérien/racinaire (D8) : union = GENE_NAMES, disjointes")
    check("union AÉRIEN ∪ RACINAIRE == GENE_NAMES",
          GENES_AERIENS | GENES_RACINAIRES == set(GENE_NAMES))
    check("intersection vide (aucun gène des deux côtés)",
          not (GENES_AERIENS & GENES_RACINAIRES))


def run():
    test_greffe_reussie()
    test_refus_familles_differentes()
    test_refus_non_greffable()
    test_refus_mort()
    test_vigueur_insuffisante()
    test_flag_defaut_neutre()
    test_geste_classe_et_fiche()
    test_partition_genes()
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    print(f"\n=== GREFFE : {ok}/{total} ===")
    return ok == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
