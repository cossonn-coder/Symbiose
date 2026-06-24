"""
SYMBIOSE — tests/test_conteneur.py
Tronçon ② du sprint pots/bacs : le CONTENEUR (`EcoFields` miniature) + sa fabrique
`make_container` (recette substrat) + son tick chimique ISOLÉ `tick_chimie`.

On valide la CHIMIE d'un pot seul (pas de plante : uptake/confinement = ③) :
  - la recette initialise correctement les champs (NPK/microbiome/structure/pH) ;
  - la litière pré-chargée (lasagnes/mycélium) se DÉCOMPOSE dans le temps
    (om_fresh décroît, NPK monte) — l'astuce « lasagne = litière pré-chargée » ;
  - le substrat `mycelium_use` provoque une faim d'azote initiale (substrat frais
    immobilise N) puis se libère ;
  - `terre_jardin` (herite_tuile) COPIE le plot de tuile source ;
  - le DRAINAGE du substrat est bien appliqué (drainant sèche plus vite que terreau) ;
  - DÉTERMINISME : deux ticks identiques produisent le même état (h1 == h2).

Lancement : depuis `data/code/`, `python3 -m tests.test_conteneur`.
"""

from __future__ import annotations

from world.container import make_container
from world import get_substrat


def _hydrate(ctn, h: float) -> None:
    """Arrose uniformément le mini-sol (les pots partent secs : humidité 0)."""
    for r in range(ctn.eco.rows):
        for c in range(ctn.eco.cols):
            ctn.eco.humidite.set(r, c, h)


def _npk(ctn, r=0, c=0):
    return (ctn.eco.n.at_plot(r, c),
            ctn.eco.p.at_plot(r, c),
            ctn.eco.k.at_plot(r, c))


def test_recette_initialise_champs():
    """make_container applique EXACTEMENT les valeurs de la recette §2."""
    rec = get_substrat("compost")
    ctn = make_container("pot", "compost", 5.0, x_cm=0.0, y_cm=0.0)
    n, p, k = _npk(ctn)
    assert (n, p, k) == rec.npk_init, (n, p, k)
    assert abs(ctn.eco.microbiome.at_plot(0, 0) - rec.microbiome_init) < 1e-9
    assert abs(ctn.eco.structure_sol.at_plot(0, 0) - rec.structure_init) < 1e-9
    assert abs(ctn.eco.ph.at_plot(0, 0) - rec.ph_init) < 1e-9
    assert ctn.mobile is True and ctn.kind == "pot"
    print("OK recette compost initialise les champs")


def test_bac_immobile():
    """Un bac est immobile (mobile=False) et peut être N×M."""
    bac = make_container("bac", "terreau", 200.0, 0.0, 0.0, rows=2, cols=2)
    assert bac.mobile is False
    assert bac.eco.rows == 2 and bac.eco.cols == 2
    print("OK bac 2×2 immobile")


def test_lasagnes_litiere_se_decompose():
    """La litière pré-chargée des lasagnes se DÉCOMPOSE (cascade confinée
    om_fresh→active→stable→NPK, zéro nouveau modèle) :
      - om_fresh décroît (la litière se consume) ;
      - om_active monte (humification : la matière mûrit en réserve) ;
      - le NPK est LIBÉRÉ (minéralisation) — visible à court terme, avant que le
        lessivage différencié (N très mobile) n'emporte le surplus non consommé
        (pas de plante pour le prélever en ②). On mesure donc le pic de libération
        à 5 semaines, pas l'asymptote."""
    ctn = make_container("pot", "lasagnes", 20.0, 0.0, 0.0)
    _hydrate(ctn, 0.8)
    fresh0 = ctn.eco.om_fresh_at(0, 0)
    active0 = ctn.eco.om_active.at_plot(0, 0)
    assert fresh0 > 0.0, "lasagnes doit pré-charger de la litière"
    npk0 = sum(_npk(ctn))
    for _ in range(5):
        ctn.tick_chimie("ete")
    npk_pic = sum(_npk(ctn))
    assert npk_pic > npk0, (npk0, npk_pic)          # NPK libéré à court terme
    for _ in range(35):
        ctn.tick_chimie("ete")
    fresh1 = ctn.eco.om_fresh_at(0, 0)
    active1 = ctn.eco.om_active.at_plot(0, 0)
    assert fresh1 < fresh0, (fresh0, fresh1)        # la litière s'est consumée
    assert active1 > active0, (active0, active1)    # humification (réserve qui monte)
    print(f"OK lasagnes : om_fresh {fresh0:.2f}→{fresh1:.2f}, "
          f"om_active {active0:.2f}→{active1:.2f}, NPK Σ pic {npk0:.2f}→{npk_pic:.2f}")


def test_mycelium_faim_azote():
    """Le substrat `mycelium_use` pré-charge le tissu C-riche `substrat` → faim
    d'azote initiale (azote ASSIMILABLE bridé tant qu'il reste du substrat frais),
    puis le substrat se décompose et le bridage se lève."""
    from fields.ecofields.nutriments import immobilise_n
    ctn = make_container("pot", "mycelium_use", 10.0, 0.0, 0.0)
    _hydrate(ctn, 0.8)
    immob0 = immobilise_n(ctn.eco.bois_fresh_at(0, 0))
    assert immob0 > 0.0, "substrat frais doit immobiliser de l'azote"
    # Le substrat se décompose : la masse C-riche fraîche décroît dans le temps,
    # donc l'azote immobilisé (∝ masse) diminue → la faim se lève (libération §2).
    for _ in range(60):
        ctn.tick_chimie("ete")
    immob1 = immobilise_n(ctn.eco.bois_fresh_at(0, 0))
    assert immob1 < immob0, (immob0, immob1)
    print(f"OK mycelium_use : N immobilisé {immob0:.3f}→{immob1:.3f} (faim levée)")


def test_terre_jardin_herite_tuile():
    """`terre_jardin` copie le plot de tuile source (pont §6)."""
    from fields.ecofields import EcoFields, Parcelle
    tile_eco = EcoFields(tile_id="tuile_test", rows=2, cols=2)
    tile_eco.n.set(1, 1, 2.7)
    tile_eco.microbiome.set(1, 1, 1.3)
    tile_eco.ph.set(1, 1, 5.9)
    tile_eco.deposer_litiere(1, 1, "feuille", 1.4)
    ctn = make_container("pot", "terre_jardin", 30.0, 0.0, 0.0,
                         tile_eco=tile_eco, tile_rc=(1, 1))
    assert abs(ctn.eco.n.at_plot(0, 0) - 2.7) < 1e-9
    assert abs(ctn.eco.microbiome.at_plot(0, 0) - 1.3) < 1e-9
    assert abs(ctn.eco.ph.at_plot(0, 0) - 5.9) < 1e-9
    assert abs(ctn.eco.om_fresh_at(0, 0) - 1.4) < 1e-9
    # Isolation : la copie est PROFONDE (pas le même objet Parcelle).
    src = tile_eco.litiere[1][1][-1]
    dst = ctn.eco.litiere[0][0][-1]
    assert src is not dst and src.tissu == dst.tissu == "feuille"
    print("OK terre_jardin copie le plot de tuile (copie profonde isolée)")


def test_drainage_substrat_applique():
    """Le drainage du substrat pilote l'assèchement : à apport égal, un pot
    drainant minéral (drainage 0.975) sèche plus vite qu'un terreau (0.990)."""
    drainant = make_container("pot", "drainant_mineral", 5.0, 0.0, 0.0)
    terreau  = make_container("pot", "terreau", 5.0, 0.0, 0.0)
    _hydrate(drainant, 1.0)
    _hydrate(terreau, 1.0)
    for _ in range(10):
        drainant.tick_chimie("ete")
        terreau.tick_chimie("ete")
    hd = drainant.eco.humidite.at_plot(0, 0)
    ht = terreau.eco.humidite.at_plot(0, 0)
    assert hd < ht, (hd, ht)
    print(f"OK drainage : drainant_mineral {hd:.3f} < terreau {ht:.3f}")


def test_determinisme():
    """Deux conteneurs identiques tickés pareil → même état (zéro RNG)."""
    a = make_container("pot", "lasagnes", 20.0, 0.0, 0.0)
    b = make_container("pot", "lasagnes", 20.0, 0.0, 0.0)
    _hydrate(a, 0.7)
    _hydrate(b, 0.7)
    for _ in range(30):
        a.tick_chimie("printemps")
        b.tick_chimie("printemps")
    sa, sb = a.eco.summary(), b.eco.summary()
    assert sa == sb, (sa, sb)
    print("OK déterminisme : deux mini-sols identiques restent égaux")


if __name__ == "__main__":
    test_recette_initialise_champs()
    test_bac_immobile()
    test_lasagnes_litiere_se_decompose()
    test_mycelium_faim_azote()
    test_terre_jardin_herite_tuile()
    test_drainage_substrat_applique()
    test_determinisme()
    print("\n=== test_conteneur : TOUS OK ===")
