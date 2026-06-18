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
| ① | Doc-conception `CONCEPTION_CATALOGUE_ENRICHI.md` (audit + matrices + sélection + partage doc/code) | INTACT (0 code) | ⬜ |
| ②+ | Implémentation par lots (plantes, puis animaux nommés) — **kickoffs écrits APRÈS figeage du doc ①** | à définir | ⬜ |

## §REPRISE

**Rien de fait.** Prochain : tronçon ① — lire `01_doc_conception.md` (kickoff
autosuffisant) et produire `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`.
Le découpage des tronçons d'implémentation ②+ sera arrêté à la fin du doc (sa
dernière section = « partage doc/code » qui propose les lots).
