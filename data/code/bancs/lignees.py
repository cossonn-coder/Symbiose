"""
SYMBIOSE — bancs/lignees.py
Banc d'essai LIGNÉES (sprint génétique infinitésimale ④, D139, observation F5).

Ce que Nico doit VOIR sur une seule tuile, trois rangées :
  ① TOMATES (autogames, autofécondation ≈ 95 %) issues de six générations de
     ressemis — la lignée est fixée (F ≈ 0,98) : les pieds se ressemblent comme des
     frères, même hauteur, floraison groupée ;
  ② COURGETTES (allogames) issues des mêmes six générations — la lignée reste
     mêlée (F ≈ 0) : hauteurs et floraisons dispersées ;
  ③ BASILICS tirés de la BANQUE-SOL (pool fondateur, comme une levée férale) :
     la diversité « sauvage » de départ, ni sélectionnée ni consanguine.
Le survol G (debug) s'ouvre au montage (WorldView.Genes.cs) : pointer un pied montre
sa lignée et ses caractères dans leur unité.

📖 Les générations sont PRÉ-CALCULÉES ici, hors simulation : un couple de fondateurs
(`founder_genes`), puis à chaque génération huit frères nés par `heredite` (la vraie
loi du moteur, ②), dont les deux premiers deviennent les parents suivants — le
patron du banc `mesures/banc_reponse_selection.py` (b). Rien n'est forcé à la main :
F et la dispersion sortent de la loi d'hérédité. Pure COMPOSITION d'un état →
golden NEUTRE (une fabrique de banc n'est jamais montée pour smoke/full).
"""
from __future__ import annotations

from plants import PlantInstance, Tomato, Zucchini, Basil
from fields import founder_genes
from sim.reproduction import heredite
from .base import build_banc_tile, monde, banque_de, sans_herbivorie

ROWS, COLS = 8, 8
GENERATIONS = 6          # 6 ressemis : F tomate ≈ 0,98 (mesuré au ③)
FRERES = 8               # frères par génération (= une rangée)
SEED = 0x11A7EE5         # seed LOCAL du banc : seule sa constance compte (philo #3)
POOL_DENSITE = 0.05      # pool basilic ≫ SPECIES_POOL_MIN_DENSITY (0,005) → tirage réel
ORIGINE_CM = 1450.0      # coin de tuile (monde 20 m, maison au centre 6-14 m)

# Rangées : tomates en haut, courgettes au milieu (une sur deux, elles s'étalent),
# basilics en bas. Les rangées vides entre elles laissent lire chaque groupe.
RANG_TOMATE, RANG_COURGETTE, RANG_BASILIC = 1, 4, 6


def _lignee(cls) -> list[tuple[dict, float]]:
    """(gènes, F) des FRERES de la dernière génération d'une lignée ressemée."""
    mere = PlantInstance(plant_class=cls, position=(0, 0))
    mere.genes = founder_genes(cls, SEED, 1, 0, 0, 25.0, 25.0)
    pere = PlantInstance(plant_class=cls, position=(0, 1))
    pere.genes = founder_genes(cls, SEED, 1, 0, 1, 75.0, 25.0)
    for gen in range(1, GENERATIONS + 1):
        freres = []
        for k in range(FRERES):
            p = PlantInstance(plant_class=cls, position=(0, 0))
            p.genes, p.F = heredite(mere, pere, SEED, 100 * gen + k)
            freres.append(p)
        mere, pere = freres[0], freres[1]
    return [(p.genes, p.F) for p in freres]


def _semer(tile, cls, r, c, genes, F):
    p = tile.add_plant(cls, r, c)
    if p is not None:
        p.genes, p.F = dict(genes), F


def lignees():
    """Banc « lignées » (④) : tomates fixées, courgettes mêlées, basilics du pool."""
    # Tuile posée DEVANT la maison (côté sud-est du monde) : derrière elle, le toit de
    # 6 m la masquerait à l'écran.
    tile, eco = build_banc_tile("LIGNEES", "terre", ROWS, COLS, ORIGINE_CM, ORIGINE_CM,
                                humidite=1.4, fertilite=1.3, microbiome=0.5)
    # Instrument d'observation : sans ce garde, l'herbivorie tue les 24 pieds en
    # 5-6 semaines (mesuré : tout meurt S15-S17, avant la fin du warmup F5) — patron
    # de `houppiers`/`biotique`, cf. D127.
    sans_herbivorie(eco)
    for c, (genes, F) in enumerate(_lignee(Tomato)):
        _semer(tile, Tomato, RANG_TOMATE, c, genes, F)
    for k, (genes, F) in enumerate(_lignee(Zucchini)):
        # Quinconce sur deux rangs : 8 courgettes sans qu'elles se recouvrent toutes.
        _semer(tile, Zucchini, RANG_COURGETTE + k % 2, (k // 2) * 2 + k % 2, genes, F)
    banque_sol = eco.seed_bank
    for c in range(COLS):
        banque_sol.seed_founder_pool(RANG_BASILIC, c, Basil, None, POOL_DENSITE)
        _semer(tile, Basil, RANG_BASILIC, c,
               banque_sol.sample_genes(RANG_BASILIC, c, Basil, SEED, 1),
               banque_sol.sample_F(RANG_BASILIC, c, Basil))
    # Graines en poche pour ressemer soi-même au F5 (tomate, courgette, basilic).
    return monde([tile], {tile.tile_id: eco},
                 banque=banque_de("tomate", "courgette", "basilic", par_espece=3))
