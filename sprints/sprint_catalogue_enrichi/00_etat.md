# SPRINT CATALOGUE ENRICHI — état partagé

> Lancement Python depuis `data/code/`. Filet C# : `dotnet build Symbiose.csproj`.

## Objectif

**Étoffer le catalogue de plantes ET d'animaux pour souligner leur inclusion et
leur place dans les features déjà développées** (thermique/microclimat,
pollinisation & cycle de vie, décomposition/compost, vigueur/maîtrise, écrasement,
compétition intra-plot, succession). Le cast actuel exerce inégalement ces
mécaniques ; on l'enrichit pour les mettre en valeur — et côté FAUNE on passe de
guildes abstraites à des **espèces NOMMÉES** rattachées aux guildes.

## Décisions de cadrage (2026-06-18, avec Nico)

- **Doc-conception D'ABORD** (tronçon ①, golden intact) : un doc de référence à
  étudier (matrice espèce × feature + sélection raisonnée), PUIS implémentation
  en sous-sprints écrits une fois le doc figé.
- **Périmètre = plantes ET animaux** (gros sprint → découpé).
- **Animaux = espèces NOMMÉES rattachées aux guildes existantes** (coccinelle,
  carabe, merle, hérisson, ver…), sur le patron data-driven du registre des
  pollinisateurs (`PollinatorSpec` dans `fields/population.py`). PAS de refonte
  moteur, PAS de 5ᵉ guilde sauf décision contraire du doc.

## État de l'existant (audit de départ, à approfondir dans le doc)

- **Plantes — 17** (`plants/catalogue.py`) : 8 cultivées (tomate, poivron,
  haricot, trèfle, tournesol, basilic, achillée, phacélie) + 4 adventices/succession
  (bourse-à-pasteur, minette, pâturin, pissenlit) + 5 pérennes ligneuses (figuier,
  pommier, cerisier, noyer, chêne).
- **Animaux — guildes abstraites** (`fields/population.py`) : 4 guildes trophiques
  (ravageur, auxiliaire, pollinisateur, vers_de_terre) + 3 types pollinisateurs
  NOMMÉS data-driven (abeille, syrphe, papillon) + 2 ponts larvaires
  (chenille→papillon, syrphe_larve→syrphe).
- **Familles botaniques** : `plants/base/familles.py` (Solanaceae, Fabaceae,
  Asteraceae, Lamiaceae + ligneuses). Attractivité florale par famille :
  `_ATTRACT_*` dans `population.py`.

## Tronçons

| # | Tronçon | Golden | Statut |
|---|---------|--------|--------|
| ① | Doc-conception `CONCEPTION_CATALOGUE_ENRICHI.md` (audit + matrices + sélection + partage doc/code) | INTACT (0 code) | ✅ |
| ② | Plantes lot 1 — familles connues (thym, lavande, bourrache, consoude, moutarde) | NEUTRE (hash intact) | ✅ |
| ③ | Plantes lot 2 — familles + cycles neufs (carotte, ortie, courgette, mâche, ail) + `_ATTRACT_*` + **vérif `biennial`/`evergreen`** | re-figé maîtrisé + corrections moteur ? | ⬜ |
| ④ | Faune nommée — **parfums** (puceron, coccinelle, carabe, merle, hérisson, lombric…) : sprite + encyclopédie | NEUTRE | ⬜ |
| ⑤ | Faune nommée — **nouveaux pollinisateurs** (bourdon, osmie) : registre data-driven | re-figé maîtrisé (pollen/nouaison) | ⬜ |
| ⑥ | Vue Godot / sprites / encyclopédie | NEUTRE | ⬜ |

## §REPRISE

**① CLOS** le 2026-06-18 — doc figé `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`
(golden `5fddfe54…` intact, doc seul). Découpage ②→⑥ arrêté ci-dessus (détail
§7 du doc). **Alerte moteur** : `life_cycle="biennial"` et
`winter_strategy="evergreen"` sont codés mais **jamais exercés** → ③ devra les
vérifier (trou possible).

**② CLOS** le 2026-06-18 — +5 plantes : thym/lavande (`aromatiques.py`, nouveau
fichier, Lamiacées evergreen) + bourrache/consoude/moutarde (`compagnes.py`,
217 LDC). Câblées `species/__init__.py`, `plants/__init__.py`, `catalogue.py`
(PLANT_CATALOGUE seul ; WEED_/PERENNIAL_ intacts). Golden **NEUTRE** (hash
`5fddfe54…` inchangé — espèces non plantées par le smoke). Chemin
`winter_strategy="evergreen"` désormais EXERCÉ : nouveau `tests/test_evergreen.py`
(thym vivant + feuillé après hiver ; 5 espèces germent). `biennial` reste à
vérifier en ③ (carotte/ail).

**Prochain au choix Nico** : ③ (familles + cycles neufs : carotte, ortie,
courgette, mâche, ail + vérif `biennial`) ou ④ (faune en parfums, golden-neutre).
Kickoff `0N_*.md` à écrire au lancement (pas d'enchaînement auto).
