"""
SYMBIOSE — tests/test_vent.py
Test de la MASSE D'AIR pure (sprint VENT & ÉVAPOTRANSPIRATION, tronçon ①).
Spec : `docs/champs/climat/conception_vent_evapotranspiration.md` §2 + kickoff
`sprints/sprint_vent_evapotranspiration/t1_vent_masse_air.md`.

Vérifie que `sim/wind.py` est :
  A. DÉTERMINISTE  — même (seed, week) → même état, runs répétés identiques ;
  B. BORNÉ         — force ≥ 0, direction ∈ [0, 2π), nébulosité ∈ [0, 1],
                     profil de risées de longueur SUBTICKS ;
  C. SAISONNIER    — la force moyenne de l'HIVER > celle de l'ÉTÉ (automne/hiver
                     plus venteux, §2.1) ;
  D. RÉACTIF À LA MÉTÉO — une Tempête force une force HAUTE ;
  E. CÂBLÉ (tronçon ②) — la boucle lit `wind_at` et injecte la masse d'air dans
                     l'évaporation enrichie (`tick_hydrology`). Au ① ce test
                     vérifiait l'ISOLEMENT (module non câblé, golden neutre) ; le ②
                     câble le vent → re-figeage golden LARGE annoncé.

Déterminisme total (fonctions pures, aucun RNG live).
Usage (depuis data/code/) :
  python3 -m tests.test_vent
"""
import math

from sim.weather import weather_at
from sim.wind import (
    wind_at, gust_profile, nebulosite_dynamique, WindState, SUBTICKS,
)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


SEED = 12345


# --- A. Déterminisme -------------------------------------------------------
def test_determinisme():
    for week in (1, 7, 52, 53, 137, 999):
        a = wind_at(SEED, week)
        b = wind_at(SEED, week)
        check(f"wind_at reproductible s{week}", a == b, f"{a}")
    check("gust_profile reproductible",
          gust_profile(SEED, 40) == gust_profile(SEED, 40))
    check("nebulosite_dynamique reproductible",
          nebulosite_dynamique(SEED, 40) == nebulosite_dynamique(SEED, 40))
    # Deux seeds différents → régimes de vent dominants différents (terrains uniques).
    d1 = wind_at(SEED, 10).direction
    d2 = wind_at(SEED + 1, 10).direction
    check("seed différent → direction différente", d1 != d2, f"{d1} vs {d2}")


# --- B. Bornes -------------------------------------------------------------
def test_bornes():
    ok_force = ok_dir = ok_neb = True
    for week in range(1, 261):   # 5 ans
        w = wind_at(SEED, week)
        if not (isinstance(w, WindState) and w.force >= 0.0):
            ok_force = False
        if not (0.0 <= w.direction < 2.0 * math.pi):
            ok_dir = False
        neb = nebulosite_dynamique(SEED, week)
        if not (0.0 <= neb <= 1.0):
            ok_neb = False
    check("force ≥ 0 sur 5 ans", ok_force)
    check("direction ∈ [0, 2π) sur 5 ans", ok_dir)
    check("nébulosité ∈ [0, 1] sur 5 ans", ok_neb)
    prof = gust_profile(SEED, 40)
    check("profil de risées = SUBTICKS facteurs", len(prof) == SUBTICKS, f"{prof}")
    check("profil de risées > 0", all(f > 0 for f in prof))


# --- C. Saisonnalité (hiver plus venteux que l'été) ------------------------
def _force_moyenne_fond(seed, semaines):
    # Force de FOND seule (on évite les semaines à événement venteux qui écraseraient
    # le signal saisonnier). On échantillonne et on moyenne.
    vals = []
    for w in semaines:
        ev = weather_at(seed, w)
        if ev.kind in ("Tempête", "Orage"):
            continue
        vals.append(wind_at(seed, w).force)
    return sum(vals) / len(vals)


def test_saisonnalite():
    # Hiver ≈ semaines 40-52, été ≈ semaines 14-26, sur plusieurs années.
    hiver = [y * 52 + w for y in range(8) for w in range(40, 53)]
    ete = [y * 52 + w for y in range(8) for w in range(14, 27)]
    f_hiver = _force_moyenne_fond(SEED, hiver)
    f_ete = _force_moyenne_fond(SEED, ete)
    check("hiver plus venteux que l'été", f_hiver > f_ete,
          f"hiver={f_hiver:.3f} > été={f_ete:.3f}")


# --- D. Réactivité à la météo ----------------------------------------------
def test_evenement_venteux():
    # On cherche une vraie Tempête dans le flux et on vérifie une force HAUTE.
    tempete_week = next(
        (w for w in range(1, 5000) if weather_at(SEED, w).kind == "Tempête"),
        None,
    )
    check("une Tempête existe dans le flux", tempete_week is not None)
    if tempete_week is not None:
        f = wind_at(SEED, tempete_week).force
        check("Tempête → force haute (> 0.7)", f > 0.7, f"force={f:.3f}")


# --- E. Câblage du vent dans l'évaporation (tronçon ②) ---------------------
def test_cable_evapotranspiration():
    # Au tronçon ① le module était GOLDEN-NEUTRE (preuve d'isolement : la boucle
    # n'importait pas sim.wind). Le tronçon ② le CÂBLE : la masse d'air pilote
    # désormais l'évaporation enrichie (§3) → ce test bascule de « non câblé » à
    # « câblé » (le golden re-fige LARGE, annoncé). On vérifie que la boucle lit
    # bien la force de masse d'air et l'injecte dans l'hydrologie.
    import sim.engine.boucle as boucle
    src_b = open(boucle.__file__).read()
    check("boucle.py câble wind_at (masse d'air)", "wind_at" in src_b)
    check("boucle.py passe vent_masse_air à tick_hydrology",
          "vent_masse_air=" in src_b)


# --- F. Champ d'abri spatial (tronçon ③) -----------------------------------
def test_abri_spatial():
    """`eco.vent` spatialisé (§4) : un obstacle (la maison) réduit le vent dans son
    SILLAGE sous le vent, et le sillage SUIT la direction du vent. CACHE : à
    (obstacles, direction) inchangés, pas de recalcul (signature stable)."""
    from fields.ecofields import init_eco
    from world.building import House
    from fields.abri import compute_abri, _signature, _obstacles

    eco = init_eco("t", 40, 40)            # tuile assez large pour loger un sillage
    house = House()
    force = 0.8

    # Vent venant du NORD (direction ≈ 0 dans le repère `wind_at`/`_direction_at`).
    compute_abri(eco, [], house, (0.0, 0.0), 0.0, force)
    vals_nord = [eco.vent.at_plot(r, c) for r in range(40) for c in range(40)]
    n_abrite_nord = sum(1 for v in vals_nord if v < force - 1e-9)
    check("un obstacle abrite des plots (vent < masse d'air)", n_abrite_nord > 0,
          f"{n_abrite_nord} plots abrités")
    check("le vent reste borné ≥ 0", all(v >= 0.0 for v in vals_nord))
    # Venturi : certains plots dépassent la masse d'air (goulet en frange de sillage).
    check("venturi : des plots accélérés (> masse d'air)",
          any(v > force + 1e-9 for v in vals_nord))

    # Le sillage SUIT la direction : tourner le vent change la carte d'abri.
    compute_abri(eco, [], house, (0.0, 0.0), math.pi / 2.0, force)
    vals_est = [eco.vent.at_plot(r, c) for r in range(40) for c in range(40)]
    check("changer la direction déplace le sillage", vals_nord != vals_est)

    # Cache : même signature à direction quasi identique (sous le pas angulaire).
    obs = _obstacles([], house, (0.0, 0.0))
    check("cache stable sous le pas angulaire",
          _signature(obs, 0.0) == _signature(obs, 0.05))
    check("cache invalidé au-delà du pas angulaire",
          _signature(obs, 0.0) != _signature(obs, 1.0))

    # Force nulle (calme) → champ NUL partout (golden-safe : évaporation inchangée).
    compute_abri(eco, [], house, (0.0, 0.0), 0.0, 0.0)
    check("vent calme → champ nul",
          all(eco.vent.at_plot(r, c) == 0.0 for r in range(40) for c in range(40)))


# --- G. Pollinisation & dispersion anémophiles (tronçon ⑤, §5.3) -----------
def test_anemophilie_noue_sans_butineur():
    """Une espèce ANÉMOPHILE en fleur reçoit du `pollen_recu` du VENT (sans aucun
    insecte) ∝ vent local × congénères en amont → elle NOUE. Calme → pas de pollen
    → pas de fruit (le vent EST le vecteur)."""
    from world import Tile
    from plants import AppleTree, organ_sites
    from plants.base import Segment
    from fields import init_eco
    from sim.engine import Engine

    def _monde_anemo(force):
        tile = Tile(tile_id="A", soil_type="terre", grid_rows=6, grid_cols=6)
        eco = init_eco("A", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
        eco.seed_bank.germination_candidates = lambda *a, **k: []
        eco.vent.fill(force)                      # vent local uniforme
        # Deux pommiers conspécifiques (émetteur + cible) en mode anémophile.
        mere = tile.add_plant(AppleTree, 2, 2)
        pere = tile.add_plant(AppleTree, 2, 4)
        for p in (mere, pere):
            p.age_years = 6.0
            p.segments = [Segment(parent=None, base=(0,0,100+30*i), dir=(0,0,1),
                                  length_cm=50, thickness_cm=2, age_weeks=10,
                                  auxin=0.5, is_apex=True) for i in range(3)]
        gs = {"tiles": [tile], "eco": {"A": eco}, "scores": {},
              "current_player": "j", "week": 1, "log": []}
        eng = Engine(gs)
        return tile, eco, mere, eng

    orig = AppleTree.pollination_mode
    try:
        AppleTree.pollination_mode = "wind"
        # Vent présent : la cible reçoit du pollen → noue.
        tile, eco, mere, eng = _monde_anemo(0.6)
        mere.floraison = 1.0; pere = tile.plants[1]; pere.floraison = 1.0
        eng._tick_anemophilie(tile, eco, 0.0, 0.6)   # vent du nord, force 0.6
        check("anémophile ventée : pollen_recu > 0 (sans butineur)",
              mere.pollen_recu > 0.0, f"pollen={mere.pollen_recu:.2f}")
        # Nouaison réelle en fin de floraison.
        eng._tick_fruits(tile, eco, 1)               # arme a_fleuri
        mere.floraison = 0.0
        eng._tick_fruits(tile, eco, 1)               # fanaison → nouaison
        check("anémophile ventée : noue des fruits sans insecte",
              len(mere.fruits) > 0, f"{len(mere.fruits)} fruits")
        # Calme : aucun pollen anémophile → aucun fruit (sans plancher).
        tile, eco, mere, eng = _monde_anemo(0.0)
        mere.floraison = 1.0; tile.plants[1].floraison = 1.0
        eng._tick_anemophilie(tile, eco, 0.0, 0.0)
        check("anémophile au calme : aucun pollen (vent = vecteur)",
              mere.pollen_recu == 0.0)
    finally:
        AppleTree.pollination_mode = orig


def test_butineurs_cloues():
    """Le facteur d'activité butineuse décroît avec le vent local : grand vent →
    moins de pollen déposé → l'ENTOMOPHILE noue moins (§5.3, butineurs cloués)."""
    from sim.engine.butineurs import _forager_wind_factor, FORAGER_WIND_FLOOR
    f_calme = _forager_wind_factor(0.0)
    f_brise = _forager_wind_factor(0.3)
    f_tempete = _forager_wind_factor(1.5)
    check("calme : butineurs à pleine activité (facteur 1)", f_calme == 1.0)
    check("le facteur décroît avec le vent", f_calme > f_brise > f_tempete,
          f"{f_calme:.2f} > {f_brise:.2f} > {f_tempete:.2f}")
    check("plancher d'activité résiduelle respecté", f_tempete >= FORAGER_WIND_FLOOR)


def test_anemochorie_sous_le_vent():
    """Une graine ANÉMOCHORE (pissenlit) dépose son pool génétique SOUS LE VENT
    (décalé dans la direction du vent ∝ force), pas au pied ; une BAROCHORE reste
    au pied. Calme → au pied dans les deux cas (golden-safe)."""
    from sim.engine.mortalite import _plot_sous_le_vent
    from plants import Taraxacum, AppleTree
    # Direction 0 = vent du NORD → graine part vers le SUD (c décroît dans le repère).
    au_pied = _plot_sous_le_vent(5, 5, 0.0, 0.0)
    sous_vent = _plot_sous_le_vent(5, 5, 0.0, 1.0)
    check("calme : dépôt anémochore au pied (golden-safe)", au_pied == (5, 5))
    check("vent : dépôt anémochore décalé sous le vent", sous_vent != (5, 5),
          f"{au_pied} → {sous_vent}")
    check("pissenlit est anémochore", Taraxacum.seed_dispersal == "anemochore")
    check("pommier est barochore (défaut)",
          getattr(AppleTree, "seed_dispersal", "barochore") == "barochore")


def test_spores_sous_le_vent():
    """⑥ §5.4 — dispersion des spores : `_spore_load` capte l'inoculum d'un FOYER
    infecté placé AU VENT (au-delà de FUNGAL_INOC_SEUIL), pas d'un foyer sous le
    vent, et rien au calme (wind_vec nul → golden-safe)."""
    from world import Tile
    from plants import AppleTree
    from sim.effects.perturbations import _spore_load, FUNGAL_INOC_SEUIL

    tile = Tile(tile_id="S", soil_type="terre", grid_rows=6, grid_cols=6)
    cible = tile.add_plant(AppleTree, 2, 2)
    amont = tile.add_plant(AppleTree, 2, 1)   # colonne plus petite = plus au nord
    aval  = tile.add_plant(AppleTree, 2, 3)
    amont.infection_memory = 0.8              # foyer actif
    aval.infection_memory = 0.8
    # Vent du NORD (direction 0) → vecteur source = (cos0, sin0) = (+1, 0) en x.
    # x_cm croît avec la colonne (plot 50 cm) → `amont` (col 1) a x < cible (col 2)
    # → (amont − cible)·(1,0) < 0… on prend la direction qui rend `amont` au vent.
    wx, wy = (-1.0, 0.0)                       # source à l'OUEST/col décroissante
    load = _spore_load(cible, tile, (wx, wy))
    check("⑥ spore : un foyer au vent transmet de l'inoculum", load > 0.0,
          f"load={load:.2f}")
    # Inverser le vent → `aval` devient le foyer au vent, `amont` ne compte plus.
    load_rev = _spore_load(cible, tile, (1.0, 0.0))
    check("⑥ spore : inverser le vent inverse la source d'inoculum",
          load_rev > 0.0 and abs(load_rev - load) < 1e-9, f"rev={load_rev:.2f}")
    # Un foyer SOUS le seuil n'émet pas.
    amont.infection_memory = FUNGAL_INOC_SEUIL - 0.05
    aval.infection_memory = FUNGAL_INOC_SEUIL - 0.05
    check("⑥ spore : sous le seuil de foyer → aucun inoculum",
          _spore_load(cible, tile, (-1.0, 0.0)) == 0.0)
    # Calme (wind_vec nul) → court-circuit immédiat → 0 (golden-safe).
    amont.infection_memory = 0.8
    check("⑥ spore : calme (vecteur nul) → aucun transport",
          _spore_load(cible, tile, (0.0, 0.0)) == 0.0)


def test_assechement_protecteur():
    """⑥ §5.4 — la ventilation est un REMÈDE : sur de nombreux tirages déterministes,
    un sujet bien VENTÉ subit MOINS d'infections fongiques qu'un sujet confiné, à
    humidité/densité égales (assèchement protecteur, pédagogie aération)."""
    from world import Tile
    from plants import Tomato
    from fields import init_eco
    from sim.effects.perturbations import fungal_disease

    def _infections(vent_local):
        tile = Tile(tile_id="V", soil_type="terre", grid_rows=6, grid_cols=6)
        eco = init_eco("V", 6, 6, humidite=3.0, microbiome=0.1)  # humide + sol pauvre
        n = 0
        for r in range(6):
            for c in range(6):
                p = tile.add_plant(Tomato, r, c)   # Solanacée = susc. max
                p.age_weeks = 20; p.current_stage = 3
                for week in range(1, 60):
                    if fungal_disease(p, tile, eco, 7, week, vent_local, (0.0, 0.0)):
                        n += 1
                tile.plants.clear()
        return n

    confine = _infections(0.0)
    vente   = _infections(1.0)
    check("⑥ assèchement : un milieu confiné voit des infections", confine > 0,
          f"confiné={confine}")
    check("⑥ assèchement : la ventilation réduit la pression fongique",
          vente < confine, f"venté={vente} < confiné={confine}")


def test_transport_litiere():
    """⑦ §5.6 — le vent CHARRIE la litière légère du plot EXPOSÉ vers son voisin
    plus ABRITÉ sous le vent, conservation de masse, et SAUTE la passe les jours
    calmes (`wind_force < TRANSPORT_SEUIL` → coût nul, perf §7B)."""
    from fields.ecofields import init_eco
    from fields.ecofields.constants import TRANSPORT_SEUIL

    def _setup():
        # Grille 1 ligne × 3 colonnes : on impose la géométrie d'abri à la main
        # (vent FORT en c0, ABRITÉ en c1). Vent venant de l'OUEST (dir=π/2 → aval = +c).
        eco = init_eco("V", 1, 3)
        eco.vent.set(0, 0, 1.0)   # plot exposé (donneur)
        eco.vent.set(0, 1, 0.2)   # plot abrité sous le vent (receveur)
        eco.vent.set(0, 2, 0.2)
        eco.deposer_litiere(0, 0, "feuille", 1.0)   # tas de feuilles mortes exposé
        eco.deposer_litiere(0, 0, "bois", 1.0)      # bois : NE doit PAS voler (lourd)
        return eco

    wind_ouest = math.pi / 2.0   # d'où vient le vent = ouest → va vers l'est (+colonne)

    # Vent FORT : la litière légère migre du plot exposé vers le plot abrité.
    eco = _setup()
    masse_avant = eco.om_fresh_at(0, 0)
    masse_voisin_avant = eco.om_fresh_at(0, 1)
    log = eco.tick_transport(wind_ouest, 0.9)
    feuille_donneur = sum(p.masse for p in eco.litiere[0][0] if p.tissu == "feuille")
    feuille_recev = sum(p.masse for p in eco.litiere[0][1] if p.tissu == "feuille")
    bois_donneur = sum(p.masse for p in eco.litiere[0][0] if p.tissu == "bois")
    check("⑦ transport : la feuille quitte le plot exposé",
          feuille_donneur < 1.0 - 1e-9, f"reste {feuille_donneur:.3f}")
    check("⑦ transport : la feuille arrive sur le plot abrité (sous le vent)",
          feuille_recev > 1e-9, f"reçu {feuille_recev:.3f}")
    check("⑦ transport : le bois (lourd) NE vole pas",
          abs(bois_donneur - 1.0) < 1e-9, f"bois {bois_donneur:.3f}")
    # Conservation de la masse totale de litière (déplacement, pas création/perte).
    total_avant = masse_avant + masse_voisin_avant
    total_apres = eco.om_fresh_at(0, 0) + eco.om_fresh_at(0, 1)
    check("⑦ transport : masse conservée (déplacement net)",
          abs(total_avant - total_apres) < 1e-9,
          f"{total_avant:.3f} → {total_apres:.3f}")
    check("⑦ transport : marqueur diégétique 🍃 émis", any("🍃" in l for l in log))

    # Jour CALME (sous le seuil) : passe SAUTÉE, aucun mouvement (perf §7B).
    eco = _setup()
    avant = eco.om_fresh_at(0, 0)
    log = eco.tick_transport(wind_ouest, TRANSPORT_SEUIL - 0.01)
    check("⑦ calme : passe sautée (litière inchangée)",
          eco.om_fresh_at(0, 0) == avant and not log)

    # Sens INVERSE : vent d'EST (aval = −colonne) → rien ne quitte c0 (c0 est en
    # AMONT, son voisin aval c−1 n'existe pas) : pas de remontée contre le vent.
    eco = _setup()
    eco.tick_transport(3.0 * math.pi / 2.0, 0.9)   # vent d'est
    feuille_c0 = sum(p.masse for p in eco.litiere[0][0] if p.tissu == "feuille")
    check("⑦ pas de remontée contre le vent (plot amont conservé)",
          abs(feuille_c0 - 1.0) < 1e-9, f"reste {feuille_c0:.3f}")

    # Déterminisme : deux exécutions identiques (zéro RNG).
    e1 = _setup(); e1.tick_transport(wind_ouest, 0.9)
    e2 = _setup(); e2.tick_transport(wind_ouest, 0.9)
    check("⑦ transport déterministe",
          [p.masse for p in e1.litiere[0][1]] == [p.masse for p in e2.litiere[0][1]])


def test_voix_transport():
    """⑦ voix — le marqueur 🍃 du tick est CONSIGNÉ au ledger (hors tick) et le carnet
    en tire une note de concept « décomposition » (descriptif/interprétatif)."""
    from sim import journal, carnet, maitrise
    from sim.evenements import evenements

    log = ["[T0]", "    🍃 Le vent charrie la litière vers l'abri (+0.40 sous le vent)"]
    evs = evenements(log)
    check("⑦ voix : 🍃 parsé en transport_litiere",
          len(evs) == 1 and evs[0].kind == "transport_litiere" and evs[0].espece is None)

    gs = {}
    journal.consigner(gs, "j", log, semaine=5)
    notes = carnet.carnet_lire(gs, "j")
    check("⑦ voix : une note de carnet est produite", len(notes) == 1, f"{notes}")
    check("⑦ voix : concept = décomposition (descriptif par défaut)",
          notes and notes[0]["concept"] == "décomposition"
          and notes[0]["registre"] == "descriptif")
    # Au seuil de maîtrise « décomposition » → bascule interprétative (révélation).
    st = maitrise.ensure_player_maitrise(gs, "j")
    st["objets"]["décomposition"] = {"palier": carnet.SEUIL_CARNET, "preuves": 0}
    notes_i = carnet.carnet_lire(gs, "j")
    check("⑦ voix : note bascule en interprétatif au seuil",
          notes_i and notes_i[0]["registre"] == "interprétatif",
          notes_i[0]["texte"] if notes_i else "")


def main():
    print("=== test_vent (① masse d'air + ③ abri + ⑤ pollin./dispersion + ⑥ maladies + ⑦ transport/voix) ===")
    test_determinisme()
    test_bornes()
    test_saisonnalite()
    test_evenement_venteux()
    test_cable_evapotranspiration()
    test_abri_spatial()
    test_anemophilie_noue_sans_butineur()
    test_butineurs_cloues()
    test_anemochorie_sous_le_vent()
    test_spores_sous_le_vent()
    test_assechement_protecteur()
    test_transport_litiere()
    test_voix_transport()
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n[test_vent] {passed}/{total} OK")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
