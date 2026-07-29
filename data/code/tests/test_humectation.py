"""
SYMBIOSE — tests/test_humectation.py
Test ciblé, lancé À LA DEMANDE (hors smoke test).

Couvre le SUBSTRAT d'humectation foliaire (sprint HUMECTATION FOLIAIRE ①) :
`PlantInstance.wetness_memory` intègre la durée d'humectation du FEUILLAGE (≠ humidité
du SOL), alimentée dans `_update_physiology` par la rosée captée, la pluie du tick, et
séchée par le vent et le soleil (ciel clair). Conception :
docs/vegetal/sante/conception_humectation_foliaire.md §2.1-2.3.

Au tronçon ① PERSONNE ne lit `wetness_memory` (le proxy fongique la lira au ②) ; on
teste donc la TUYAUTERIE en isolation, pas un effet écologique :
  (a) MONTÉE  — sous rosée saturante, vent nul, ciel couvert, la mémoire monte de 0 ;
  (b) DÉCROISSANCE — mouillage cessé (rosée/pluie nuls), la mémoire redescend vers 0
      (philo #4 : rien ne persiste sans entretien) ;
  (c) BORNES  — 200 tics saturés → la mémoire reste dans [0,1] ;
  (d) AÉRATION — à vent égal, un couvert DENSE (foliage_density haute) sèche MOINS
      qu'un couvert clair (le vent pénètre moins) → plus d'humectation retenue.

On pilote rosée / vent en surchargeant `eco.rosee_last.at_plot` / `eco.vent.at_plot`
(patron du test plasticité sur `humidite`), et pluie / nébulosité via les paramètres
de `_update_physiology` → déterministe, sans RNG, assertions numériques exactes.

Lancement (depuis data/code/) :
  python3 -m tests.test_humectation
"""

from world import Tile
from plants import Zucchini
from fields import init_eco
from sim.engine import Engine
from sim.effects.perturbations import fungal_disease

_EPS = 1e-9


def _lab():
    """Tuile 6×6 terre + courgette + Engine ; renvoie (engine, tile, eco, plant)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
    plant = tile.add_plant(Zucchini, 3, 3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    return Engine(gs), tile, eco, plant


def _pin_rosee(eco, val: float):
    eco.rosee_last.at_plot = lambda r, c, _v=val: _v


def _pin_vent(eco, val: float):
    eco.vent.at_plot = lambda r, c, _v=val: _v


def test_montee_sous_rosee():
    """Rosée saturante + vent nul + ciel couvert (nebulosite=1 → pas de séchage
    solaire) : `wetness_memory` monte strictement depuis 0."""
    engine, tile, eco, p = _lab()
    _pin_rosee(eco, 0.10)                 # >> ROSEE_SURFACE_REF (0.03) → signal saturé
    _pin_vent(eco, 0.0)
    assert p.wetness_memory == 0.0
    engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=0.0)
    assert p.wetness_memory > 0.0, "la mémoire ne monte pas sous rosée"
    print(f"[humectation ①·montée] PASS — wetness 0.0 → {p.wetness_memory:.4f} sous rosée")


def test_decroissance_sans_mouillage():
    """Mouillage cessé (rosée + pluie nuls) : la mémoire redescend strictement vers 0
    (décroissance garantie — philo #4). On la charge d'abord, puis on coupe l'eau."""
    engine, tile, eco, p = _lab()
    _pin_vent(eco, 0.0)
    # Charge : quelques tics mouillés
    _pin_rosee(eco, 0.10)
    for _ in range(5):
        engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=0.5)
    charge = p.wetness_memory
    assert charge > 0.0
    # Coupe l'eau : rosée + pluie nulles
    _pin_rosee(eco, 0.0)
    prev = charge
    for _ in range(5):
        engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=0.0)
        assert p.wetness_memory < prev - _EPS, "la mémoire ne décroît pas à sec"
        prev = p.wetness_memory
    assert p.wetness_memory < charge, "pas de décroissance nette"
    print(f"[humectation ①·décroissance] PASS — {charge:.4f} → {p.wetness_memory:.4f} à sec")


def test_bornes():
    """200 tics entièrement saturés (rosée + pluie fortes) : la mémoire reste dans
    [0,1] (jamais d'emballement)."""
    engine, tile, eco, p = _lab()
    _pin_rosee(eco, 1.0)
    _pin_vent(eco, 0.0)
    for _ in range(200):
        engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=1.0)
        assert 0.0 <= p.wetness_memory <= 1.0, f"hors bornes : {p.wetness_memory}"
    print(f"[humectation ①·bornes] PASS — 200 tics saturés, wetness={p.wetness_memory:.4f} ∈ [0,1]")


def test_aeration_couvert_dense_seche_moins():
    """À vent ÉGAL, un couvert DENSE (foliage_density haute) laisse moins pénétrer le
    vent → sèche moins → retient PLUS d'humectation qu'un couvert clair. On compare
    deux runs identiques ne différant que par `foliage_density`."""
    def _run(dens: float) -> float:
        engine, tile, eco, p = _lab()
        _pin_rosee(eco, 0.10)             # même apport
        _pin_vent(eco, 1.0)               # même vent, non nul (le levier d'aération)
        saved = Zucchini.foliage_density
        try:
            Zucchini.foliage_density = dens
            for _ in range(20):
                engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=0.0)
            return p.wetness_memory
        finally:
            Zucchini.foliage_density = saved

    dense = _run(0.9)
    clair = _run(0.2)
    assert dense > clair + _EPS, (
        f"le couvert dense ne retient pas plus d'humectation : dense {dense:.4f} ≤ clair {clair:.4f}")
    print(f"[humectation ①·aération] PASS — dense {dense:.4f} > clair {clair:.4f} (vent pénètre moins)")


# ---------------------------------------------------------------------------
# Tronçon ② — BASCULE DU PROXY : la pression fongique suit l'humectation FOLIAIRE
# (`wetness_memory`), plus l'humidité du SOL (`eco.humidite`). Ces tests gèlent la
# correction du bug pédagogique (arroser au pied ne doit plus rendre malade, philo #6).
# ---------------------------------------------------------------------------

def _adulte(plant):
    """Sort la plante du stade `semis` (fungal_disease l'immunise) → stade adulte."""
    plant.current_stage = 1
    return plant


def test_fungal_nul_si_feuillage_sec():
    """(a) `wetness_memory = 0` → `fungal_disease` ne déclenche JAMAIS : le facteur
    d'humectation est nul, donc p = 0 quelle que soit la graine. C'est le sens même de
    la bascule : sans eau LIQUIDE sur la feuille, pas de germination des spores."""
    _, tile, eco, p = _lab()
    _adulte(p)
    p.wetness_memory = 0.0
    fires = sum(1 for s in range(3000) if fungal_disease(p, tile, eco, s, 3))
    assert fires == 0, f"la maladie déclenche à feuillage sec ({fires} fois)"
    print("[humectation ②·feuillage-sec] PASS — 0 déclenchement sur 3000 graines à wetness=0")


def test_arroser_au_pied_ne_change_plus_la_maladie():
    """(b) NON-RÉGRESSION DU BUG PÉDAGOGIQUE : à humectation foliaire ÉGALE, changer
    l'humidité du SOL (arroser au pied) ne change PLUS le déclenchement fongique. On
    compare le motif de déclenchement sur 3000 graines entre un sol sec et un sol
    détrempé, `wetness_memory` fixée. AVANT ②, `hum_norm` en dépendait → la maladie
    montait quand on arrosait ; c'est précisément ce qu'on interdit ici."""
    _, tile, eco, p = _lab()
    _adulte(p)
    p.wetness_memory = 0.9                 # feuillage mouillé, constant
    def _motif(hum_sol):
        eco.humidite.at_plot = lambda r, c, _v=hum_sol: _v
        return [bool(fungal_disease(p, tile, eco, s, 3)) for s in range(3000)]
    sec     = _motif(0.1)                  # sol sec
    detrempe = _motif(3.0)                 # sol détrempé (arrosé au pied)
    assert sec == detrempe, "l'humidité du SOL modifie encore la pression fongique"
    assert any(sec), "le banc ne déclenche jamais — test non probant"
    print(f"[humectation ②·arroser-au-pied] PASS — motif identique sol sec/détrempé "
          f"({sum(sec)} déclenchements, indépendants de l'humidité-sol)")


def test_infection_memory_suit_l_humectation():
    """(c) `infection_memory` (qui durcit `resistance_pathogene`) suit désormais
    l'humectation FOLIAIRE, pas l'humidité du SOL. Deux runs :
      • même humidité de sol, humectation HAUTE vs BASSE → infection_memory suit ;
      • même humectation, humidité de sol différente → infection_memory INCHANGÉE."""
    def _run(rosee, hum_sol):
        engine, tile, eco, p = _lab()
        _adulte(p)
        eco.humidite.at_plot = lambda r, c, _v=hum_sol: _v
        _pin_rosee(eco, rosee)
        _pin_vent(eco, 0.0)
        for _ in range(30):
            engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=0.0)
        return p.infection_memory
    haute = _run(0.10, 1.0)                # feuillage bien mouillé
    basse = _run(0.0, 1.0)                 # feuillage sec (même sol)
    assert haute > basse + _EPS, "infection_memory ne suit pas l'humectation"
    # Découplage du sol : même humectation, humidité de sol opposée → identique.
    sol_sec     = _run(0.10, 0.1)
    sol_detrempe = _run(0.10, 3.0)
    assert abs(sol_sec - sol_detrempe) < _EPS, "infection_memory dépend encore du sol"
    print(f"[humectation ②·infection-suit-humectation] PASS — haute {haute:.4f} > basse "
          f"{basse:.4f} ; indépendante du sol ({sol_sec:.4f} == {sol_detrempe:.4f})")


# ---------------------------------------------------------------------------
# Tronçon ③ — `arroser` PIED/FEUILLAGE : le geste qui rend le dilemme jouable.
# `arroser(feuillage=False)` = comportement inchangé (sol seul) ; `feuillage=True`
# pose `eco.aspersion_last` → l'humectation foliaire monte au tick suivant. Coût
# identique dans les deux modes (§2.5, choix écologique pas économique).
# ---------------------------------------------------------------------------

from sim.actions.gestes import arroser, DOSE_ARROSAGE
from sim import vigueur as V


def test_arroser_pied_ne_mouille_pas_le_feuillage():
    """(a) `arroser(feuillage=False)` (défaut, au PIED) laisse `wetness_memory`
    INCHANGÉE au tick suivant : le sol est mouillé mais pas la canopée → aucun apport
    à l'humectation (aspersion_last reste nulle)."""
    engine, tile, eco, p = _lab()
    _pin_vent(eco, 0.0)                       # pas de séchage éolien
    assert p.wetness_memory == 0.0
    r, c = p.position
    ok = arroser(engine.game_state, "j1", eco, r, c, feuillage=False)
    assert ok, "arroser au pied a échoué (Vigueur ?)"
    assert eco.aspersion_last.at_plot(r, c) == 0.0, "le pied ne doit rien asperger"
    engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=0.0)
    assert p.wetness_memory == 0.0, "arroser au pied a mouillé le feuillage"
    print("[humectation ③·pied] PASS — arroser au pied laisse le feuillage sec (wetness=0)")


def test_arroser_feuillage_monte_l_humectation():
    """(b) `arroser(feuillage=True)` pose l'aspersion → `wetness_memory` monte
    strictement depuis 0 au tick suivant (feuillage mouillé)."""
    engine, tile, eco, p = _lab()
    _pin_vent(eco, 0.0)
    r, c = p.position
    ok = arroser(engine.game_state, "j1", eco, r, c, feuillage=True)
    assert ok
    assert abs(eco.aspersion_last.at_plot(r, c) - DOSE_ARROSAGE) < _EPS, \
        "l'aspersion foliaire n'a pas été posée"
    engine._update_physiology(tile, eco, nebulosite=1.0, pluie_event=0.0)
    assert p.wetness_memory > 0.0, "asperger le feuillage n'a pas monté l'humectation"
    print(f"[humectation ③·feuillage] PASS — aspersion → wetness 0.0 → {p.wetness_memory:.4f}")


def test_les_deux_modes_mouillent_le_sol_pareil():
    """(c) Les deux modes montent `eco.humidite` de la MÊME dose (le feuillage est un
    APPORT EN PLUS, pas un détournement) : seul le mode feuillage ajoute l'aspersion."""
    def _delta_sol(feuillage: bool) -> float:
        engine, tile, eco, p = _lab()
        r, c = p.position
        h_avant = eco.humidite.at_plot(r, c)
        arroser(engine.game_state, "j1", eco, r, c, feuillage=feuillage)
        return eco.humidite.at_plot(r, c) - h_avant
    d_pied = _delta_sol(False)
    d_feuillage = _delta_sol(True)
    assert d_pied > 0.0, "arroser n'a pas humidifié le sol"
    assert abs(d_pied - d_feuillage) < _EPS, \
        f"le sol n'est pas mouillé pareil : pied {d_pied:.4f} ≠ feuillage {d_feuillage:.4f}"
    print(f"[humectation ③·sol-égal] PASS — les deux modes montent le sol de {d_pied:.4f}")


def test_vigueur_insuffisante_ne_touche_rien():
    """(d) Vigueur insuffisante → tout-ou-rien : NI `eco.humidite` NI `eco.aspersion_last`
    ne sont touchés (le geste échoue en amont de toute écriture)."""
    engine, tile, eco, p = _lab()
    V.ensure_player(engine.game_state, "j1")["courante"] = 0.0   # à sec
    r, c = p.position
    h_avant = eco.humidite.at_plot(r, c)
    ok = arroser(engine.game_state, "j1", eco, r, c, feuillage=True)
    assert not ok, "arroser a réussi à Vigueur nulle"
    assert eco.humidite.at_plot(r, c) == h_avant, "le sol a été mouillé sans Vigueur"
    assert eco.aspersion_last.at_plot(r, c) == 0.0, "l'aspersion a été posée sans Vigueur"
    print("[humectation ③·vigueur] PASS — Vigueur nulle : ni sol ni feuillage touchés")


# ---------------------------------------------------------------------------
# Tronçon ④ — GUILDE OÏDIUM : l'exception qui interdit la solution unique.
# `oidium_disease` a le signal INVERSE du mildiou : (1 − wetness_memory) × chaleur.
# Feuillage SEC + chaleur → oïdium ; feuillage MOUILLÉ → mildiou. Aucun geste bon
# partout (le dilemme, philo #2/#6). La courgette (Cucurbitaceae, oidium=0.9) est
# le cas d'école ; une espèce à oidium=0 (tomate) n'est jamais touchée.
# ---------------------------------------------------------------------------

from plants import Tomato
from sim.effects.perturbations import oidium_disease


def _pin_temp(eco, val: float):
    eco.temperature.at_plot = lambda r, c, _v=val: _v


def test_oidium_nul_si_espece_non_sensible():
    """(a) Une espèce à `oidium_susceptibility = 0` (défaut catalogue, ici la tomate)
    n'attrape JAMAIS l'oïdium, même feuillage sec en pleine chaleur : sortie immédiate
    (coût nul, invariant golden pour toute espèce non porteuse)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
    p = _adulte(tile.add_plant(Tomato, 3, 3))
    _pin_temp(eco, 28.0)                       # chaud
    p.wetness_memory = 0.0                     # feuillage sec (signal oïdium max)
    fires = sum(1 for s in range(3000) if oidium_disease(p, tile, eco, s, 4))
    assert fires == 0, f"la tomate (oidium=0) attrape l'oïdium ({fires} fois)"
    print("[humectation ④·non-sensible] PASS — 0 déclenchement sur 3000 graines (tomate)")


def test_oidium_frappe_feuillage_sec_et_chaud():
    """(b) Feuillage SEC + chaleur : la courgette (oidium=0.9) attrape l'oïdium — le
    signal (1 − wetness) × chaleur est haut. C'est le climat de fin d'été (nuits
    humides, journées chaudes et sèches)."""
    _, tile, eco, p = _lab()                   # courgette
    _adulte(p)
    _pin_temp(eco, 28.0)                        # chaleur pleine (chaleur = 1.0)
    p.wetness_memory = 0.05                     # feuillage quasi sec
    fires = sum(1 for s in range(3000) if oidium_disease(p, tile, eco, s, 4))
    assert fires > 0, "l'oïdium ne frappe pas la courgette à feuillage sec et chaud"
    print(f"[humectation ④·sec-chaud] PASS — {fires} déclenchements oïdium sur 3000 (feuillage sec)")


def test_dilemme_humectation_inverse_les_deux_guildes():
    """(c) LE TEST DU DILEMME. Sur la MÊME courgette, à chaleur ÉGALE, on compare
    feuillage MOUILLÉ vs SEC pour les DEUX guildes :
      • feuillage MOUILLÉ → mildiou (`fungal_disease`) MONTE, oïdium S'EFFONDRE ;
      • feuillage SEC     → oïdium MONTE, mildiou s'effondre.
    Aucun état d'humectation n'écrase les deux → pas de solution unique (philo #2/#6)."""
    def _bancs(wet):
        _, tile, eco, p = _lab()
        _adulte(p)
        _pin_temp(eco, 28.0)                    # chaleur pleine pour les deux runs
        _pin_vent(eco, 0.0)                     # pas d'assèchement éolien parasite
        p.wetness_memory = wet
        mildiou = sum(1 for s in range(3000) if fungal_disease(p, tile, eco, s, 4))
        oidium  = sum(1 for s in range(3000) if oidium_disease(p, tile, eco, s, 4))
        return mildiou, oidium

    m_mouille, o_mouille = _bancs(0.95)         # feuillage détrempé
    m_sec,     o_sec     = _bancs(0.05)         # feuillage sec
    # Feuillage mouillé : le mildiou domine, l'oïdium s'effondre.
    assert m_mouille > m_sec, "le mildiou ne monte pas avec le feuillage mouillé"
    assert o_mouille < o_sec, "l'oïdium ne s'effondre pas avec le feuillage mouillé"
    # Feuillage sec : l'oïdium domine, le mildiou s'effondre.
    assert o_sec > o_mouille, "l'oïdium ne monte pas à feuillage sec"
    assert m_sec < m_mouille, "le mildiou ne s'effondre pas à feuillage sec"
    print(f"[humectation ④·dilemme] PASS — mouillé(mildiou {m_mouille}, oïdium {o_mouille}) "
          f"vs sec(mildiou {m_sec}, oïdium {o_sec}) : les guildes s'inversent")


def test_oidium_nul_au_froid():
    """(d) Le froid (T < OIDIUM_T_REF) annule la pression oïdium : `chaleur` tombe à 0
    → sortie immédiate, même feuillage sec. L'oïdium est une maladie de saison chaude."""
    _, tile, eco, p = _lab()
    _adulte(p)
    _pin_temp(eco, 10.0)                        # sous OIDIUM_T_REF (18 °C)
    p.wetness_memory = 0.0                      # feuillage sec (signal maximal SI chaud)
    fires = sum(1 for s in range(3000) if oidium_disease(p, tile, eco, s, 4))
    assert fires == 0, f"l'oïdium frappe au froid ({fires} fois)"
    print("[humectation ④·froid] PASS — 0 déclenchement sur 3000 graines à T=10 °C")


if __name__ == "__main__":
    test_montee_sous_rosee()
    test_decroissance_sans_mouillage()
    test_bornes()
    test_aeration_couvert_dense_seche_moins()
    test_fungal_nul_si_feuillage_sec()
    test_arroser_au_pied_ne_change_plus_la_maladie()
    test_infection_memory_suit_l_humectation()
    test_arroser_pied_ne_mouille_pas_le_feuillage()
    test_arroser_feuillage_monte_l_humectation()
    test_les_deux_modes_mouillent_le_sol_pareil()
    test_vigueur_insuffisante_ne_touche_rien()
    test_oidium_nul_si_espece_non_sensible()
    test_oidium_frappe_feuillage_sec_et_chaud()
    test_dilemme_humectation_inverse_les_deux_guildes()
    test_oidium_nul_au_froid()
    print("\n[humectation ①②③④] TOUS LES TESTS PASSENT")
