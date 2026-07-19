"""
SYMBIOSE — tests/test_gestes_manuels.py
Suite ciblée du tronçon ① « acquisition des moyens d'agir » : les gestes manuels
de BASE `pincer` (DOUX) et `arracher` (NET) — le bas du gradient
`pincer < arracher < couper/tailler` (spec §A). On vérifie ici les CONTRATS de
chaque geste (coût, effet structurel, différenciateur main/outil `erode`), pas le
golden ÉCOLO (testé à part). Réutilise le harness partagé des suites Vigueur
(fabriques de monde, `check`).

Usage (depuis data/code/) :
  python3 -m tests.test_gestes_manuels
"""
from fields import VITALITE_STEP
from sim.growth import COUPE_NETTE
from sim import vigueur as V
from sim import actions as ACT

from tests.vigueur.harness import check, _gs_with, _construire, _results
from plants import Sunflower


def test_pincer():
    print("\n[①a] pincer : DOUX — auxine ↓, aucun retrait, coût FAIBLE")
    gs, tile, eco = _gs_with((Sunflower, 2, 2))
    plant = _construire(tile.plants[0], 12)   # chaîne de segments + auxine réelle
    check("pincer < COUPE_NETTE (régime DOUX)", ACT.PINCER_INTENSITE < COUPE_NETTE,
          f"intensité={ACT.PINCER_INTENSITE}")
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    n_av = len(plant.segments)
    # Auxine du segment que la façade ciblera (apex meneur, cible='apex') avant le
    # geste (le seam DOUX la baisse) — on relit après pour la comparer.
    from sim.actions.gestes import _segment_cible
    cible_idx = _segment_cible(plant, "apex")
    aux_av = plant.segments[cible_idx].auxin if cible_idx is not None else None
    ok = ACT.pincer(gs, "joueur_1", plant, eco)
    check("pincer payé → succès", ok)
    check("coût FAIBLE débité", st["courante"] == 100.0 - ACT.FAIBLE,
          f"courante={st['courante']}")
    check("AUCUN segment retiré (DOUX)", len(plant.segments) == n_av,
          f"{n_av} → {len(plant.segments)}")
    if cible_idx is not None:
        check("auxine du segment ciblé baissée (débourrement émergent)",
              plant.segments[cible_idx].auxin < aux_av,
              f"{aux_av:.3f} → {plant.segments[cible_idx].auxin:.3f}")
    check("vitalité intacte (pincer ne stresse pas)", plant.vitalite == 1.0,
          f"vitalité={plant.vitalite}")
    # Objets : famille taille SANS outil (la maîtrise taille atténue, aucun outil).
    objets = ACT._objets_action("pincer", plant)
    check("objets = taille (SANS sécateur) + clé d'espèce",
          "taille" in objets and "sécateur" not in objets and "tournesol" in objets,
          f"objets={objets}")


def test_pincer_binaire():
    print("\n[①b] pincer : binaire — Vigueur insuffisante → rien pincé")
    gs, tile, eco = _gs_with((Sunflower, 2, 2))
    plant = _construire(tile.plants[0], 12)
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = ACT.FAIBLE - 1.0
    from sim.actions.gestes import _segment_cible
    cible_idx = _segment_cible(plant, "apex")
    aux_av = plant.segments[cible_idx].auxin
    n_av = len(plant.segments)
    ok = ACT.pincer(gs, "joueur_1", plant, eco)
    check("pincer à vide → échec (binaire)", not ok)
    check("auxine intacte à l'échec", plant.segments[cible_idx].auxin == aux_av)
    check("structure intacte à l'échec", len(plant.segments) == n_av)
    check("Vigueur drainée à 0", st["courante"] == 0.0, f"courante={st['courante']}")


def test_arracher():
    print("\n[①c] arracher : NET — écime + litière `bois` + `erode`, coût ELEVE, "
          "aucun gain")
    gs, tile, eco = _gs_with((Sunflower, 2, 2))
    plant = _construire(tile.plants[0], 12)
    check("tournesol a une chaîne (≥ 2 segments)", len(plant.segments) >= 2,
          f"{len(plant.segments)} segments")
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    n_av = len(plant.segments)
    vit_av = plant.vitalite
    r, c = plant.position[0], plant.position[1]
    # Litière totale du plot AVANT (le tournesol est le seul déposant ici → toute
    # hausse est le `bois` arraché, MÊME calcul que `tailler`). On désigne un segment
    # INTERNE À LONGUEUR (l'apex meneur est un bourgeon de longueur 0 → 0 bois, comme
    # pour `tailler` : c'est le sous-arbre RETIRÉ qui pèse) pour exercer le dépôt.
    lit_av = eco.om_fresh_at(r, c)
    seg_avec_bois = next(i for i, s in enumerate(plant.segments)
                         if s.parent is not None and s.length_cm > 0.0)
    ok = ACT.arracher(gs, "joueur_1", plant, eco, segment_id=seg_avec_bois)
    check("arracher payé → succès", ok)
    # Coût ELEVE débité, AUCUN gain (contraste avec tailler qui rend ∝ maturité).
    check("coût ELEVE débité, aucun gain", st["courante"] == 100.0 - ACT.ELEVE,
          f"courante={st['courante']}")
    check("écimage NET : sous-arbre retiré (segments < avant)",
          len(plant.segments) < n_av, f"{n_av} → {len(plant.segments)}")
    # `erode` divise le pas par la constitution d'espèce (résilience) : on suit la
    # constitution, pas le pas brut (sinon on figerait une magnitude arbitraire).
    erosion = VITALITE_STEP / plant.plant_class.resilience_base
    check("vitalité ÉRODÉE (différenciateur main/outil)",
          abs(plant.vitalite - (vit_av - erosion)) < 1e-9,
          f"vitalité {vit_av:.3f} → {plant.vitalite:.3f}")
    # Litière déposée au plot (masse > 0, comme tailler).
    lit_ap = eco.om_fresh_at(r, c)
    check("litière `bois` déposée au plot", lit_ap > lit_av,
          f"{lit_av:.3f} → {lit_ap:.3f}")
    objets = ACT._objets_action("arracher", plant)
    check("objets = taille (SANS sécateur) + clé d'espèce",
          "taille" in objets and "sécateur" not in objets and "tournesol" in objets,
          f"objets={objets}")


def test_arracher_binaire():
    print("\n[①d] arracher : binaire — Vigueur insuffisante → structure ET "
          "vitalité intactes")
    gs, tile, eco = _gs_with((Sunflower, 2, 2))
    plant = _construire(tile.plants[0], 12)
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = ACT.ELEVE - 1.0
    n_av, vit_av = len(plant.segments), plant.vitalite
    ok = ACT.arracher(gs, "joueur_1", plant, eco)
    check("arracher à vide → échec (binaire)", not ok)
    check("structure intacte à l'échec", len(plant.segments) == n_av,
          f"{n_av} → {len(plant.segments)}")
    check("vitalité intacte à l'échec (pas d'erode sur refus)",
          plant.vitalite == vit_av, f"vitalité={plant.vitalite}")
    check("Vigueur drainée à 0", st["courante"] == 0.0, f"courante={st['courante']}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Gestes manuels pincer + arracher (acquisition ①)")
    print("=" * 60)
    test_pincer()
    test_pincer_binaire()
    test_arracher()
    test_arracher_binaire()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
