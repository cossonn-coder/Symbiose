"""
SYMBIOSE — tests/test_couplage.py
Tronçon ⑤ du sprint pots/bacs : COUPLAGE fond ouvert (bac ↔ tuile dessous) +
arc complet LASAGNES. On prouve l'interconnexion des acteurs (CONCEPTION §5) :

  A. drainage → tuile     : l'eau qui s'écoule du fond d'un conteneur posé monte
                            dans l'humidité du plot de tuile d'assise (pont matière).
  B. racines → tuile      : un BAC fond ouvert root-bound voit ses racines DESCENDRE
                            dans la tuile (uptake détecté là-bas) → l'effet nain est
                            LEVÉ (la croissance reprend vs un bac sans assise).
  C. microbiome/om ↔ tuile : diffusion LENTE bidirectionnelle bac↔tuile.
  D. POT fond fermé       : SEUL le drainage descend (pas de diffusion, pas de
                            racines qui sortent).

Tout est ÉMERGENT (flux/diffusion, jamais un bonus direct sur la plante — philo #2)
et DÉTERMINISTE (zéro RNG, ordre d'itération stable). Le smoke ne pose AUCUN
conteneur → golden NEUTRE (vérifié à part par test_golden).

Lancement : depuis `data/code/`, `python3 -m tests.test_couplage`.
"""

from __future__ import annotations

from copy import deepcopy

from fields.ecofields import EcoFields
from plants import PLANT_CATALOGUE
from world.container import make_container, planter_dans, ROOTBOUND_SEUIL


def _tuile() -> EcoFields:
    """Un mini-jardin de tuile 2×2 (le plot d'assise = (0,0))."""
    return EcoFields(tile_id="tuile_test", rows=2, cols=2, soil_type="terre")


def _hydrate(eco, h: float) -> None:
    for r in range(eco.rows):
        for c in range(eco.cols):
            eco.humidite.set(r, c, h)


# --------------------------------------------------------------------------- A
def test_drainage_descend_dans_la_tuile():
    """A — l'eau du fond d'un bac posé monte dans l'humidité du plot d'assise."""
    tuile = _tuile()
    _hydrate(tuile, 0.0)                       # tuile sèche au départ
    bac = make_container("bac", "terreau", 200.0, x_cm=25.0, y_cm=25.0,
                         rows=1, cols=1, tile_eco=tuile, tile_rc=(0, 0))
    _hydrate(bac.eco, 2.0)                     # bac arrosé
    hum_avant = tuile.humidite.at_plot(0, 0)
    bac.tick_chimie("ete")
    hum_apres = tuile.humidite.at_plot(0, 0)
    assert hum_apres > hum_avant, (hum_avant, hum_apres)
    print(f"OK drainage→tuile : humidité plot {hum_avant:.4f} → {hum_apres:.4f}")


def test_conteneur_detache_ne_draine_nulle_part():
    """A bis — un conteneur DÉTACHÉ (tile_eco=None) ne touche aucune tuile (no-op)."""
    bac = make_container("bac", "terreau", 200.0, x_cm=25.0, y_cm=25.0)
    _hydrate(bac.eco, 2.0)
    assert bac.tile_eco is None
    bac.tick_chimie("ete")        # ne doit lever aucune exception, rien à drainer
    print("OK conteneur détaché : aucun pont (no-op)")


# --------------------------------------------------------------------------- B
def _bac_planté(avec_assise: bool):
    """Petit bac 1×1, volume FAIBLE (confinement fort) planté d'une TOMATE (seule
    espèce procédurale du catalogue → sa hauteur RÉAGIT au `confinement`). Avec ou
    sans assise tuile. Le sol profond de la tuile est bien nourri (réservoir à
    libérer une fois les racines descendues)."""
    tuile = _tuile()
    _hydrate(tuile, 1.0)
    for champ in ("n", "p", "k"):
        f = tuile.get_field(champ)
        for r in range(2):
            for c in range(2):
                f.set(r, c, 2.5)              # sol profond bien nourri
    kw = dict(tile_eco=tuile, tile_rc=(0, 0)) if avec_assise else {}
    bac = make_container("bac", "terreau", 4.0, x_cm=25.0, y_cm=25.0,
                         rows=1, cols=1, **kw)
    bac.fond_ouvert = avec_assise
    _hydrate(bac.eco, 1.5)
    plant = planter_dans(bac, PLANT_CATALOGUE["tomate"])
    plant.current_stage = 2                  # déjà développée → pousse vite
    plant.growth_factor = 1.0
    return tuile, bac, plant


def test_racines_descendent_levent_le_nain():
    """B — un bac fond ouvert root-bound puise dans la tuile (uptake détecté) ET
    la plante grandit PLUS qu'un bac identique SANS assise (effet nain levé)."""
    # Bac couplé (fond ouvert sur la tuile).
    t_ouv, b_ouv, p_ouv = _bac_planté(avec_assise=True)
    # Bac témoin, hors-sol (même volume, même substrat, AUCUNE assise).
    _t_clos, b_clos, p_clos = _bac_planté(avec_assise=False)

    n_tuile_avant = t_ouv.n.at_plot(0, 0)
    # Assez de semaines pour atteindre le root-bound puis diverger.
    for wk in range(1, 25):
        b_ouv.tick("ete", seed=7, week=wk)
        b_clos.tick("ete", seed=7, week=wk)

    # Le root-bound a bien été atteint dans les DEUX (sinon le test ne prouve rien).
    assert p_clos.current_height / 4.0 > ROOTBOUND_SEUIL, p_clos.current_height

    # B.1 — uptake dans la TUILE : le sol profond s'est appauvri (racines descendues).
    n_tuile_apres = t_ouv.n.at_plot(0, 0)
    assert n_tuile_apres < n_tuile_avant, (n_tuile_avant, n_tuile_apres)

    # B.2 — effet nain LEVÉ : le bac couplé a poussé plus haut que le bac confiné.
    assert p_ouv.current_height > p_clos.current_height, \
        (p_ouv.current_height, p_clos.current_height)
    print(f"OK racines→tuile : N profond {n_tuile_avant:.3f}→{n_tuile_apres:.3f}, "
          f"hauteur couplé {p_ouv.current_height:.2f} > confiné "
          f"{p_clos.current_height:.2f} cm (nain levé)")


# --------------------------------------------------------------------------- C
def test_microbiome_diffuse_bac_vers_tuile():
    """C — un bac fond ouvert RICHE en microbiome ensemence la tuile pauvre (et
    réciproquement) : diffusion LENTE bidirectionnelle, masse conservée."""
    tuile = _tuile()
    tuile.microbiome.set(0, 0, 0.1)           # tuile pauvre
    bac = make_container("bac", "compost", 200.0, x_cm=25.0, y_cm=25.0,
                         rows=1, cols=1, tile_eco=tuile, tile_rc=(0, 0),
                         )
    bac.fond_ouvert = True
    bac.eco.microbiome.set(0, 0, 1.5)         # bac riche (compost)
    m_tuile0 = tuile.microbiome.at_plot(0, 0)
    m_bac0   = bac.eco.microbiome.at_plot(0, 0)
    for wk in range(6):
        bac.tick_chimie("ete")
    m_tuile1 = tuile.microbiome.at_plot(0, 0)
    m_bac1   = bac.eco.microbiome.at_plot(0, 0)
    assert m_tuile1 > m_tuile0, (m_tuile0, m_tuile1)   # la tuile se colonise
    assert m_bac1 < m_bac0, (m_bac0, m_bac1)           # le bac cède une part
    print(f"OK microbiome bac↔tuile : tuile {m_tuile0:.3f}→{m_tuile1:.3f}, "
          f"bac {m_bac0:.3f}→{m_bac1:.3f}")


# --------------------------------------------------------------------------- D
def test_pot_fond_ferme_draine_mais_ne_diffuse_pas():
    """D — un POT (fond_ouvert=False) descend SON drainage à la tuile mais NE
    diffuse PAS le microbiome (fond fermé) et ne fait pas sortir ses racines."""
    tuile = _tuile()
    _hydrate(tuile, 0.0)
    tuile.microbiome.set(0, 0, 0.1)
    pot = make_container("pot", "compost", 5.0, x_cm=25.0, y_cm=25.0,
                         tile_eco=tuile, tile_rc=(0, 0))
    assert pot.fond_ouvert is False
    _hydrate(pot.eco, 2.0)
    pot.eco.microbiome.set(0, 0, 1.5)
    hum0, m0 = tuile.humidite.at_plot(0, 0), tuile.microbiome.at_plot(0, 0)
    for wk in range(4):
        pot.tick_chimie("ete")
    hum1, m1 = tuile.humidite.at_plot(0, 0), tuile.microbiome.at_plot(0, 0)
    assert hum1 > hum0, (hum0, hum1)          # drainage transmis (fond percé)
    assert abs(m1 - m0) < 1e-12, (m0, m1)     # microbiome NON diffusé (fond fermé)
    print(f"OK pot fond fermé : humidité {hum0:.4f}→{hum1:.4f} (drainage), "
          f"microbiome inchangé {m0:.3f}=={m1:.3f}")


# --------------------------------------------------------------------------- LASAGNES
def test_lasagnes_flux_npk_croissant_et_faim_dazote():
    """Arc complet LASAGNES — un pot lasagnes LIBÈRE un flux NPK par décompo confinée
    de sa litière pré-chargée : le NPK MONTE au-dessus de son niveau initial (pic de
    minéralisation) au fil des semaines, puis se lessive faute de plante pour le
    capter. Faim d'azote : le `bois` pré-chargé est présent (immobilise N au départ)
    et se résorbe lentement. Comparé à un substrat PAUVRE (drainant minéral) qui,
    lui, n'a aucune litière à libérer."""
    lasagnes = make_container("pot", "lasagnes", 40.0, x_cm=0.0, y_cm=0.0)
    pauvre   = make_container("pot", "drainant_mineral", 40.0, x_cm=0.0, y_cm=0.0)

    def somme_npk(c):
        e = c.eco
        return e.n.at_plot(0, 0) + e.p.at_plot(0, 0) + e.k.at_plot(0, 0)

    npk0_las = somme_npk(lasagnes)
    suivi = []
    bois0 = lasagnes.eco.bois_fresh_at(0, 0)
    for wk in range(40):
        for c in (lasagnes, pauvre):         # sol maintenu humide (la décompo a besoin d'eau)
            c.eco.humidite.set(0, 0, 1.0)
        lasagnes.tick_chimie("ete")
        pauvre.tick_chimie("ete")
        suivi.append(somme_npk(lasagnes))

    # Flux CROISSANT : la litière se minéralise → le NPK PASSE au-dessus du départ
    # (pic de libération) — l'astuce « lasagne = litière pré-chargée » nourrit la plante.
    assert max(suivi) > npk0_las, (npk0_las, max(suivi))
    assert suivi[7] > suivi[0], (suivi[0], suivi[7])   # montée sur la fenêtre précoce
    # Mieux nourri que le substrat pauvre (qui n'a rien à libérer).
    assert somme_npk(lasagnes) > somme_npk(pauvre), \
        (somme_npk(lasagnes), somme_npk(pauvre))
    # Faim d'azote : le bois pré-chargé est présent et se RÉSORBE (immobilise puis libère).
    bois1 = lasagnes.eco.bois_fresh_at(0, 0)
    assert bois0 > 0.0 and bois1 < bois0, (bois0, bois1)
    print(f"OK lasagnes : ΣNPK init {npk0_las:.3f} → pic {max(suivi):.3f} "
          f"(libération) > pauvre {somme_npk(pauvre):.3f} ; bois {bois0:.2f}→{bois1:.2f}")


# --------------------------------------------------------------------------- DÉTERMINISME
def test_determinisme_couplage():
    """Deux runs identiques du couplage → état bit-identique (h1 == h2)."""
    def run():
        tuile = _tuile()
        _hydrate(tuile, 1.0)
        bac = make_container("bac", "lasagnes", 4.0, x_cm=25.0, y_cm=25.0,
                             rows=1, cols=1, tile_eco=tuile, tile_rc=(0, 0))
        bac.fond_ouvert = True
        _hydrate(bac.eco, 1.5)
        p = planter_dans(bac, PLANT_CATALOGUE["courgette"])
        p.current_stage = 2
        for wk in range(10):
            bac.tick("ete", seed=3, week=wk)
        return (round(tuile.humidite.at_plot(0, 0), 9),
                round(tuile.n.at_plot(0, 0), 9),
                round(bac.eco.microbiome.at_plot(0, 0), 9),
                round(p.current_height, 9))
    h1, h2 = run(), run()
    assert h1 == h2, (h1, h2)
    print(f"OK déterminisme couplage : {h1}")


# --------------------------------------------------------------------------- NON-RÉGRESSION
def test_tick_hydrology_retour_ne_change_rien_aux_tuiles():
    """Le RETOUR de `tick_hydrology` (perte de drainage, ajouté en ⑤) est IGNORÉ
    par les tuiles → l'humidité reste BIT-IDENTIQUE à l'appel historique."""
    a = _tuile(); b = _tuile()
    for eco in (a, b):
        _hydrate(eco, 1.2)
        eco.soil_memory.set(0, 0, 0.5)
    a.tick_hydrology("terre")                 # appel historique (retour jeté)
    pertes = b.tick_hydrology("terre")        # même appel, on lit le retour
    assert isinstance(pertes, list) and len(pertes) == 4
    for r in range(2):
        for c in range(2):
            assert abs(a.humidite.at_plot(r, c) - b.humidite.at_plot(r, c)) < 1e-15
    print("OK tick_hydrology : retour ⑤ sans effet sur les tuiles (bit-identique)")


if __name__ == "__main__":
    test_drainage_descend_dans_la_tuile()
    test_conteneur_detache_ne_draine_nulle_part()
    test_racines_descendent_levent_le_nain()
    test_microbiome_diffuse_bac_vers_tuile()
    test_pot_fond_ferme_draine_mais_ne_diffuse_pas()
    test_lasagnes_flux_npk_croissant_et_faim_dazote()
    test_determinisme_couplage()
    test_tick_hydrology_retour_ne_change_rien_aux_tuiles()
    print("\ntests/test_couplage.py — TOUS LES TESTS PASSENT")
