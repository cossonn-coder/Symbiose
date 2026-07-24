# 2026-07-24 — Conception MIGRATION DES 9 ARBRES EN CROISSANCE PROCÉDURALE (D91) — FIGÉE

**Type :** conception (`/conception`) · **Thème :** `vegetal/croissance` · **Statut :** FIGÉE, prête `/sprint-auto`

## Origine
Amorce rev 2 fournie par Nico (migration des 9 arbres restants — figuier, cerisier,
noyer, chêne, hêtre, bouleau, charme, sapin, aulne — de l'empreinte-couronne tabulée
`age_curve` vers la croissance procédurale en segments, comme le pommier depuis D29,
pour qu'ils se dessinent en branches et portent le taper D90). Lignée D29/D90/D26.

## Ce que la lecture du code a tranché (corrige l'amorce)
Trois faits établis au `grep`, revérifiés :

1. **Golden STRICTEMENT NEUTRE — aucun re-figeage, aucun tronçon.** `test_golden.py`
   n'instancie parmi les ligneux **que le pommier** (`AppleTree`). Les 9 arbres à
   migrer ne sont ni semés dans le scénario, ni tirés par la succession spontanée
   (`archetype=None` → hors `WEED_CATALOGUE`). L'amorce §3 hedgeait « re-figeage
   conditionnel » : la réalité est plus simple, golden-neutre de bout en bout.
2. **`port_archetype` n'est JAMAIS lu par la sim** (grep vide dans `sim/`, `fields/`)
   — étiquette descriptive. Le `fleche`↔`etale` émerge de `apical_dominance_base` +
   `auxin_release_scale`. Conséquence : un « 8ᵉ archétype pleureur » comme string ne
   fait rien → le pleureur exige un **vrai levier mécanique**.
3. **Le vrai risque n'est pas le golden, c'est la mort hydrique au F5.**
   `update_footprint` : `root_r = canopy_r = max_horiz + foliage_halfwidth`,
   `PROC_ROOT_RATIO=1.0` global. Une jeune flèche étroite → racines sur 1 plot →
   assèchement → mort ~an 3 (le pommier ne survit qu'avec `foliage_halfwidth=50`).
   → poste de calibrage n°1 par espèce, sapin & bouleau les plus exposés.

Point non vu par l'amorce : `AUXIN_RELEASE_SCALE=400 sem.` est **global** (partagé
avec le pommier/golden) → un chêne centenaire s'étale dès ~l'an 8.

## Arbitrages Nico (lot 1)
- **Q1 Pleureur = nouveau levier gravitropique** `gravitropism_gain` (défaut 0 →
  golden intact) : helper `_gravitropic_droop(dir, depth, gain)` dans `geometrie.py`,
  greffé APRÈS `_phototropic_bias` dans `_elongate_emit`, **échelonné par la
  profondeur** (tronc dressé, brindilles distales pendantes). Déterministe, prépare
  le saule (D23).
- **Q2 Ontogénie = levier par espèce** `auxin_release_scale` (défaut 400.0 = la
  constante actuelle → pommier bit-identique) : `_update_auxin` le lit en param.
  Chêne/hêtre → grand (dressé longtemps) ; bouleau/aulne → court.
- **Q3 Découpage = 4 tronçons par famille de calibrage.**

## Découpage — golden INCHANGÉ (`57c166d8…`) partout
- **① feuillus etale + levier `auxin_release_scale`** : défauts procéduraux d'arbre
  sur `PerennialWoody`, migration cerisier/charme/hêtre/noyer/chêne, calibrage
  `foliage_halfwidth` (survie) + gabarit.
- **② cas atypiques** : aulne (rôle hydro D61 intact), figuier `buissonnant`
  mono-collet (multi-tronc = option F5 différée), sapin `fleche` persistant.
- **③ bouleau + levier `gravitropism_gain`** : bouleau élancé pleureur.
- **④ vue Godot + banc F5 `foret_ports`** : rendu branches des 9 arbres (renderer
  générique), mode aiguilles du sapin, LOD, enrichissement encyclopédie optionnel.

Réserves portées explicitement (non bloquantes) : **multi-tronc figuier** = option
F5, **verticille sapin** = polish différé (#2 simplicité).

## Livrables
Doc `docs/vegetal/croissance/conception_migration_arbres.md` +
`sprints/vegetal/croissance/sprint_arbres_procedural/` (00_etat + 01→04).
DETTE **D91 → 🟢** (conçu, prêt). Prêt pour `/sprint-auto sprint_arbres_procedural`.
