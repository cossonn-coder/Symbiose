"""
SYMBIOSE — bancs/modele_spatial.py
Banc d'observation du MODÈLE SPATIAL (sprint du même nom, tronçon ③, F5).

Instrument pour VOIR de ses yeux les deux acquis du sprint, sur une seule tuile,
SANS aucune mécanique nouvelle (golden NEUTRE) :
  ① AIR DE FAMILLE CLONAL (tronçon ②, `form_seed` héritable) — un framboisier
     mature (drageon, silhouette de BUISSON à bois lisible) laissé émettre des
     ramets sur la saison (`sim.clonal.emettre_ramets` au tick). Chaque ramet
     COPIE le `form_seed` de la mère et REJOUE la séquence de débourrement depuis
     le début → sa k-ième branche tire le même angle que la k-ième de la mère :
     les jeunes drageons ont le PORT de la mère, en plus petit (juvéniles, PAS de
     head-start — philo #2). C'est le « air de famille » à comparer à l'œil.
  ② PAS DE SUPERPOSITION (tronçon ①, placement sous-plot) — 3 plantes posées sur
     le MÊME plot-foyer mais à des positions sous-plot DISTINCTES (x_cm/y_cm
     écrits explicitement, quelques cm d'écart). Avant le sprint elles étaient
     recentrées au centre du plot → superposition exacte ; ici elles se
     CHEVAUCHENT sans se confondre. Le pont sérialise déjà x_cm/y_cm par plante
     (`serialize.py`) → le rendu les place distinctement (`WorldToScreen`).

Pure COMPOSITION de l'état moteur (plantes du catalogue + champs éco) — AUCUNE
mécanique nouvelle, AUCUN changement `data/code/` moteur → golden NEUTRE (cette
fabrique n'est JAMAIS montée pour smoke/full, cf. `cmd_init`). Framboisier /
trèfle / fraisier sont déjà au catalogue et à l'encyclopédie (règle catalogue/
voix respectée).

Banc ISOLÉ (succession spontanée coupée : on regarde CES plantes, pas des
pionnières) + PAILLÉ (anti-gel des frileuses au démarrage), patron `luxuriance`.

Vérifications automatiques (`python3 -m bancs.modele_spatial`) : voir `verifier()`
en bas — assert form_seed hérité + positions sous-plot distinctes.
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE
from .base import build_banc_tile, monde, vieillir

Raspberry  = PLANT_CATALOGUE["framboisier"]   # drageon, buisson à bois lisible
Clover     = PLANT_CATALOGUE["trefle"]        # stolon, couvre-sol
Strawberry = PLANT_CATALOGUE["fraisier"]      # stolon, rosette

# ① La MÈRE clonale, pré-vieillie d'un an pour porter déjà du bois de buisson
# (silhouette lisible) ET être mature → elle émet des drageons dès l'observation.
MERE_CLONALE = (Raspberry, 4, 4)

# ② Le TRIO au MÊME plot-foyer (plot (2,2), donc x_cm/y_cm dans [100,150[×[100,150[)
# à des positions sous-plot DISTINCTES : trois trèfles à ~12 cm d'écart. Même plot
# = même chimie (plot-foyer stable), positions continues distinctes = pas de
# superposition visuelle. (Espèce identique → seule la POSITION les distingue à
# l'œil, ce qu'on veut démontrer.)
TRIO_PLOT = (2, 2)
TRIO_POS_CM = [(112.0, 112.0), (124.0, 130.0), (138.0, 118.0)]


def modele_spatial():
    """Banc « modèle spatial » (③, observation F5) : sur UNE tuile, un framboisier
    mature qui essaime des drageons À L'AIR DE FAMILLE (même port que la mère, en
    plus jeune) + un trio de trèfles au MÊME plot posés à des positions sous-plot
    distinctes (plus de superposition). Pas d'oracle à seuil : instrument
    d'observation, calibrage à l'œil par Nico. Isolé (pas de succession) + paillé."""
    tile, eco = build_banc_tile("MODELE_SPATIAL", "terre", 8, 8,
                                humidite=1.6, fertilite=1.3, microbiome=0.7)
    eco.lumiere.fill(1.0)   # plein soleil (le drageon héliophile a besoin de lumière au sol)

    # ① Mère clonale pré-vieillie → mature, bois lisible, drageonne sur la saison.
    cls, r, c = MERE_CLONALE
    vieillir(tile.add_plant(cls, r, c), 1.0)

    # ② Trio au même plot, positions sous-plot explicites (plus de recentrage).
    for x_cm, y_cm in TRIO_POS_CM:
        p = tile.add_plant(Clover, *TRIO_PLOT)
        p.x_cm, p.y_cm = x_cm, y_cm

    # Banc ISOLÉ + anti-gel (patron `luxuriance`) : succession spontanée COUPÉE
    # (sinon des pionnières lèvent de la SeedBank-sol et brouillent l'observation) ;
    # paillage SATURÉ (protège les frileuses des gelées tardives de démarrage).
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for stake in tile.stakes:
        while stake.add("paillage"):
            pass

    return monde([tile], {tile.tile_id: eco})


# ---------------------------------------------------------------------------
# Vérifications automatiques (kickoff ③ §B). Le banc n'est PAS branché sur le
# smoke (golden INTACT) : ce runner monte le monde du banc, déroule quelques
# saisons dans un Engine local (déterministe, comme test_golden) pour laisser le
# clonal émettre, puis vérifie les deux invariants du sprint.
# ---------------------------------------------------------------------------

def verifier(n_years: int = 2) -> None:
    """Monte le banc, tourne `n_years` dans un Engine local, et ASSERTE :
      • deux ramets d'une même mère ont le MÊME `form_seed` (air de famille ②) ;
      • deux plantes du même plot ont des `(x_cm,y_cm)` DISTINCTS (placement ①).
    Déterministe (seed fixe de l'Engine). Lève AssertionError si un invariant casse.
    """
    from world import House
    from sim.engine import Engine

    tiles, ecos, house, _banque = modele_spatial()
    tile = tiles[0]

    # ② Placement sous-plot : vérifié SUR LE MONDE FRAÎCHEMENT POSÉ (l'invariant
    # est celui de la POSE — après plusieurs saisons, mort/clonal changent la
    # composition et brouilleraient le décompte). Le trio de trèfles partage le
    # plot-foyer TRIO_PLOT mais a des positions continues DISTINCTES (aucun doublon
    # (x,y)) : avant le sprint elles étaient recentrées → superposées.
    trio = [p for p in tile.plants
            if p.plant_class is Clover and p.position == TRIO_PLOT]
    assert len(trio) == len(TRIO_POS_CM), \
        f"trio attendu ({len(TRIO_POS_CM)} trèfles @ {TRIO_PLOT}), obtenu {len(trio)}"
    positions = [(p.x_cm, p.y_cm) for p in trio]
    assert len(set(positions)) == len(positions), \
        f"positions sous-plot NON distinctes (superposition) : {positions}"

    # ① Air de famille : on déroule quelques saisons dans un Engine local
    # (déterministe, comme test_golden) pour laisser le clonal émettre des ramets.
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "house": house,
    }
    engine = Engine(game_state)
    for _ in range(n_years):
        for _ in range(52):
            engine.tick_semaine()
            game_state["log"].clear()

    # Les ramets de framboisier (mêmes gènes que la mère) ont
    # COPIÉ son form_seed. On regroupe les framboisiers par form_seed : au moins
    # une lignée doit compter la mère + >=1 ramet, tous au MÊME form_seed.
    raspberries = [p for p in tile.plants if p.plant_class is Raspberry]
    assert len(raspberries) >= 2, \
        f"aucun ramet émis en {n_years} ans ({len(raspberries)} framboisier(s)) — " \
        "vérifier plein soleil / maturité / cadence clonale"
    from collections import Counter
    par_forme = Counter(p.form_seed for p in raspberries)
    lignee_partagee = [fs for fs, n in par_forme.items() if n >= 2]
    assert lignee_partagee, \
        f"aucune lignée clonale ne partage un form_seed : {dict(par_forme)}"

    print(f"[modele_spatial] OK — {len(trio)} trèfles distincts @ {TRIO_PLOT} "
          f"positions={positions} ; {len(raspberries)} framboisiers, "
          f"form_seed partagé sur {len(lignee_partagee)} lignée(s) clonale(s).")


if __name__ == "__main__":
    verifier()
