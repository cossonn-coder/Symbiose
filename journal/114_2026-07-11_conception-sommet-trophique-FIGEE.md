# 2026-07-11 — Conception SOMMET TROPHIQUE (T1+T7) — FIGÉE (`/conception`)

## Demande de Nico
Combler le **sommet trophique** de l'écosystème : super-prédateur (T1) + herbivore
vertébré (T7), les deux trous couplés du référentiel D61
(`docs/conception/CONCEPTION_COMPLETUDE_ECOSYSTEME.md` §3). Première `/conception`
d'ajout d'espèces nourrie par ce référentiel.

## Diagnostic (code de vérité `data/code/`)
La faune est déjà data-driven (`TrophicSpec` + `PopulationField`). Un puits top-down
= lister un nom dans `predators=(...)` (résolu au tick, `vie_macro.py`) ; à densité 0
→ golden neutre. Ordre de tick « proies avant prédateurs » = boom-bust émergent. La
**boucle ouverte la plus grave** (D61) : merle/hérisson/coccinelle/carabe n'ont AUCUN
puits (régulés seulement bottom-up). Herbivorie plante = `herbivory_pressure` lit
`category_density("ravageur")`. Le pont sérialise DÉJÀ la faune par espèce
(`serialize.py:238`) → nouveaux champs auto-exposés, ③ = C# seul.

## Arbitrages Nico (Q1-Q3, tous = reco)
- **Q1 — 2 super-prédateurs** : `rapace` (aérien, proies campagnol+merle) +
  `couleuvre` (terrestre, proies campagnol+limace). Data-driven, air+sol, campagnol
  doublement prédaté (réaliste). Belette écartée (doublon rongeur).
- **Q2 — hérisson laissé** peu régulé : quasi-apex du jardin, très peu prédaté en
  réalité ; pas de blaireau/grand-duc juste pour cocher la boucle. Frein = habitat +
  fenêtre. Auxiliaires insectes idem hors périmètre.
- **Q3 — dégât campagnol = canal racinaire DÉDIÉ** : catégorie NEUVE
  `herbivore_vertebre` + perturbation `root_herbivory` (lit sa propre catégorie) +
  signe `rongeur_racinaire` (flétrissure au collet, distinct du criblage foliaire).
  Pas rattaché à `ravageur` (éviterait le conflat feuillage/racine, faux signe).

## Design figé
- **T7 `campagnol`** (proie) : cat. `herbivore_vertebre`, resource = biomasse racinaire
  (`p.root_plots` × préférence bulbes/racines/écorce), habitat galeries (sol non remué
  + mulch), `predators=("rapace","couleuvre")`, salt `0x2AF001`, fenêtre large.
- **T1 `rapace`/`couleuvre`** : cat. `super_predateur`, resource = densité proies
  (`_espece_grid` sommés), `predators=()` (sommet), salts `0x2B0001`/`0x2B1001`.
- **Câblage puits** : campagnol←rapace+couleuvre, merle←rapace, limace←+couleuvre.
- 5 voix au standard des 15 espèces faune (encyclo `faune_encyclo.py` + invariant
  symétrie du sous-graphe trophique ; carnet concepts ; événements ledger ; pages
  optionnelles ; magazine n/a faune).

## Découpage (3 tronçons, perf-first)
- **① campagnol + dégât racinaire** — golden **re-figé maîtrisé #1** (herbivorie
  édaphique). `01_campagnol_degat_racinaire.md`.
- **② rapace + couleuvre + câblage puits** — golden **re-figé maîtrisé #2** (top-down
  boom-bust), tickés en dernier. `02_super_predateurs.md`.
- **③ vue Godot** — sprites C# par espèce (pont déjà par espèce, Python intact) +
  mapping signe `rongeur_racinaire`. Golden **intact**. `03_vue_godot.md`.

Coût perf : 3 `PopulationField`, resources prédateurs = grilles déjà calculées (cheap),
campagnol = 1 balayage plantes mémoïsable. ≤ +10 %/tronçon.

## Livrables
`docs/conception/CONCEPTION_SOMMET_TROPHIQUE.md` + `sprints/sprint_sommet_trophique/`
(00_etat + kickoffs 01-03) + DETTE.md (D61). Prêt pour
`/sprint-auto sprint_sommet_trophique`. À l'implémentation : repasser T1/T7 ⚠️→✅ dans
le référentiel D61 + `/audit-projet ecosysteme`.
