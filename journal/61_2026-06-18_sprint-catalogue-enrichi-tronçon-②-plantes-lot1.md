# 2026-06-18 — Sprint CATALOGUE ENRICHI · tronçon ② : plantes lot 1 (familles connues) — golden NEUTRE — ② CLOS

## Contexte

Tronçon ② du sprint catalogue enrichi (kickoff `sprints/sprint_catalogue_enrichi/02_plantes_lot1.md`,
doc de référence figé `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`). On
ajoute **5 espèces** dans des familles **déjà cataloguées** → attractivité florale
héritée gratis, aucun mécanisme moteur nouveau, **donnée pure**.

## Ce qui est fait

**+5 plantes** (clés `PLANT_CATALOGUE`) :

| Espèce | Latin | Famille | Cycle | Hiver | Niche |
|---|---|---|---|---|---|
| Thym | *Thymus* | Lamiaceae | perennial | **evergreen** | mellifère abeille, couvre-sol persistant |
| Lavande | *Lavandula* | Lamiaceae | perennial | **evergreen** | mellifère abeille/papillon, structurante |
| Bourrache | *Borago* | Boraginaceae | annual | die | mellifère abeille majeure, comestible |
| Consoude | *Symphytum* | Boraginaceae | perennial | dormant | accumulatrice (pivot, +fertilité local), biomasse |
| Moutarde | *Sinapis* | Brassicaceae | annual | die | engrais vert (+om_fresh local), mellifère syrphe |

- **Nouveau fichier** `plants/species/aromatiques.py` (Lamiacées persistantes,
  concept distinct des compagnes) : `Thyme`, `Lavender`. 68 LDC pur.
- **Étendu** `plants/species/compagnes.py` (docstring mis à jour) : `Borage`,
  `Comfrey`, `Mustard`. 217 LDC pur (< 350). Moutarde `archetype=None`
  explicite → pas de télescopage avec `WEED_CATALOGUE`/succession.
- Câblage : `species/__init__.py`, `plants/__init__.py`, `catalogue.py`
  (PLANT_CATALOGUE seul ; `WEED_CATALOGUE`/`PERENNIAL_CATALOGUE` intacts).
- Attractivité florale **héritée gratis** : les 3 familles sont déjà dans les
  tables `_ATTRACT_*` de `population.py` ; chaque espèce pose la rondelle
  `pollinisateur` à la floraison → la `resource_fn` nectar les lit sans rien
  toucher dans `population.py`.

## Chemin `evergreen` désormais EXERCÉ (trou comblé)

`winter_strategy="evergreen"` (mortalite.py:245 — survie + léger stress, ni mort
ni dormance) existait mais **aucune espèce ne l'exerçait**. Thym et lavande sont
les premiers porteurs. Nouveau **`tests/test_evergreen.py`** :
- `test_thym_survit_hiver` : thym planté, ≥1 hiver traversé (60 semaines) →
  `is_alive` ET `foliage_density_at(saison="hiver") > 0` (evergreen = non caduc).
- `test_catalogue_germination` : les 5 espèces sont au catalogue, germent et
  dépassent le stade semis.

`biennial` (carotte/ail) reste à vérifier en ③.

## Golden

**NEUTRE** — hash `5fddfe54…` inchangé. Le smoke (2 tuiles × 4 ans) n'instancie
aucune des 5 nouvelles espèces ; ajouter des classes + entrées de catalogue non
plantées ne touche pas la trajectoire. Suites annexes OK (population, attraction,
compétition, génétique).

## Reste / prochain (choix Nico, pas d'enchaînement auto)

③ (plantes lot 2 : carotte, ortie, courgette, mâche, ail + vérif `biennial`) ou
④ (faune nommée « parfums », golden-neutre).
