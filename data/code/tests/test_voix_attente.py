"""
SYMBIOSE — tests/test_voix_attente.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint FREIN REJETS FIGUIER ⑤
(absorbe la relève ligneuse ⑤) : la voix `attente` du semis ligneux ombragé.

`sim/voix_etres.besoins_plante` dit :
  (a) ligneux ombragé SOUS son `seuil_ombre` → `attente` (il attend une trouée),
      avec le nom de l'arbre qui le couvre ;
  (b) même ligneux AU-DELÀ du seuil → `ombre` (il souffre) ;
  (c) herbacée ombragée (même mémoire) → `ombre`, jamais `attente` ;
  (d) sans ombreur identifié → `attente_anonyme` ; la phrase se rend sans champ manquant.

Lancement (depuis data/code/) :
  python3 -m tests.test_voix_attente
"""

import sys

from world import Tile
from fields import init_eco
from plants import Fig, CherryTree, Comfrey
from sim import voix_etres as VE
from sim.effects.perturbations import seuil_ombre

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _monde(cls_jeune, avec_ombreur=True):
    """Un figuier mûr (si `avec_ombreur`) et une jeune plante à son pied."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=0.7, fertilite=1.0, microbiome=0.3)
    if avec_ombreur:
        mere = tile.add_plant(Fig, 10, 10)
        mere.age_years = Fig.maturity_years + 20.0
    jeune = tile.add_plant(cls_jeune, 10, 10)
    jeune.x_cm += 20.0                       # sous la couronne, pas sur le tronc
    return tile, eco, jeune


def _ctx(tile):
    """Contexte de voisinage avec des hauteurs posées (la structure procédurale d'un
    arbre non poussé mesure ~1 cm) : la mère domine (400 cm), la jeune 30 cm."""
    ctx = VE.contexte_tuile(tile)
    ctx["hauteurs"] = [(p, 400.0 if p.plant_class is Fig else 30.0) for p, _ in ctx["hauteurs"]]
    return ctx


def _themes(plant, tile, eco):
    return {t: champs for i, t, champs in VE.besoins_plante(plant, tile, eco, "ete", _ctx(tile))
            if i >= VE.SEUIL_DIRE}


def test_attente():
    print("\n[A] ligneux ombragé sous le seuil → attente")
    tile, eco, semis = _monde(CherryTree)
    s = seuil_ombre(semis)
    semis.shade_memory = s - 0.05
    th = _themes(semis, tile, eco)
    check("attente dite", "attente" in th, f"seuil {s:.2f}, thèmes {sorted(th)}")
    check("ombre tue", "ombre" not in th)
    check("le voisin est nommé", th.get("attente", {}).get("voisin") == Fig.name,
          th.get("attente"))
    phr = [p for w in range(20)
           for p in VE.phrases_plante(semis, tile, eco, "ete", 42, w, _ctx(tile))]
    check("phrase rendue avec le voisin", any("attend" in p and Fig.name.lower() in p.lower()
                                              for p in phr), phr[:2])


def test_ombre_au_dela():
    print("\n[B] ligneux au-delà du seuil → ombre")
    tile, eco, semis = _monde(CherryTree)
    semis.shade_memory = min(1.0, seuil_ombre(semis) + 0.05)
    th = _themes(semis, tile, eco)
    check("ombre dite", "ombre" in th, sorted(th))
    check("attente tue", "attente" not in th)


def test_herbacee():
    print("\n[C] herbacée ombragée → ombre")
    tile, eco, herbe = _monde(Comfrey)
    herbe.shade_memory = 0.4                 # sous le seuil d'un semis ligneux aussi
    th = _themes(herbe, tile, eco)
    check("ombre dite", "ombre" in th, sorted(th))
    check("jamais attente", not any(t.startswith("attente") for t in th))


def test_anonyme():
    print("\n[D] sans ombreur → attente_anonyme")
    tile, eco, semis = _monde(CherryTree, avec_ombreur=False)
    semis.shade_memory = seuil_ombre(semis) - 0.05
    th = _themes(semis, tile, eco)
    check("attente_anonyme dite", "attente_anonyme" in th, sorted(th))
    phr = [p for w in range(20) for p in VE.phrases_plante(semis, tile, eco, "ete", 42, w)]
    check("aucun gabarit à trou", not any("{" in p for p in phr))


if __name__ == "__main__":
    test_attente()
    test_ombre_au_dela()
    test_herbacee()
    test_anonyme()
    ko = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(ko)}/{len(_results)} verts")
    sys.exit(1 if ko else 0)
