# 2026-07-23 — Conception LISIBILITÉ DE L'ARCHITECTURE LIGNEUSE (D90) — FIGÉE

`/conception` sur repo. Retour F5 de Nico : un vieux pommier a un « tronc comme un
baobab », des « branches emmêlées comme des ronces », un « diamètre uniforme
(ronces diamètre baobab) » → on ne lit pas l'arbre. Problème de **lisibilité de
forme**, pas de bio.

## Cause racine établie (lecture moteur, revérifiée)
Le défaut est **dans le moteur** (`data/code`, source de vérité), pas la vue.
`sim/growth/phases.py` (`_elongate_emit`) épaissit **tout segment non-apex** de
`THICKEN_RATE` (0.03 cm/tick) — **constant, uniforme, NON borné, indépendant de
l'ordre de branche**. Combiné au pommier (`wood_persistence=4000` sem.) :
- tronc → ~120 cm ⟹ **baobab** ;
- même incrément pour brindille et tronc ⟹ une vieille brindille aussi grosse que
  le tronc ⟹ **« ronces diamètre baobab »** (aucun amincissement) ;
- sans contraste d'épaisseur, l'œil ne hiérarchise plus ⟹ **« emmêlement »**.

Deux faits qui cadrent la solution : la **topologie encode déjà l'ordre de
branche** (`_depths`/`_children`/`_subtree`, comptage de terminaux possible), non
lu par l'épaississement ; et `thickness_cm` n'a **AUCUN couplage écologique**
(pure grandeur morphologique de rendu — changer son modèle ne ripple pas dans
l'écosystème).

## Modèle figé — pipe model + croissance secondaire saturante
`thickness_i = INIT + girth_max_espèce · sat(âge_i) · taper_i`
- **`taper_i` = pipe model** (Léonard/Shinozaki : section ∝ ce qui est porté) =
  `(n_terminaux_i / n_terminaux_racine)^TAPER_EXP` ⟹ tronc épais → charpentières →
  brindilles fines (tue la « ronce »).
- **`sat(âge)=1−exp(−âge/GIRTH_TAU)`** = croissance secondaire (cambium)
  **saturante** ⟹ tronc vénérable mais **borné** (tue le « baobab »).
- **`girth_max_cm` par espèce** (nouveau levier sur `PlantBase`, surchargé par les
  ligneux).
- 1 passe **O(n) post-ordre/tick** (n ≤ max_segments) **remplaçant** l'accumulation
  → perf neutre, zéro RNG (philo #3). Philo #2 ✓ (dérive de l'état), #5 ✓ (la forme
  porte l'âge/l'espèce), #7 ✓.

## Arbitrages Nico
- **Terme d'âge saturant : OUI** (vénérable > pipe model pur).
- **`girth_max` PAR ESPÈCE** (pas de levier global).
- **Découpage = 2 tronçons.**
- **Périmètre CIBLÉ** : effet visible sur le **pommier seul** (unique arbre
  `procedural_growth=True`) ; les 9 autres arbres (aulne/hêtre/bouleau/cerisier/
  figuier/sapin/charme/chêne/noyer) sont rendus par silhouette de couronne, **sans
  segments** → `girth_max_cm` posé pour eux (prêt) mais sans effet. Leur migration
  en procédural = **D91** (gros chantier distinct).

## Couplages rendu (tronçon ②)
`thickness_cm` pilote la **largeur de trait** (`×2.2`, `PlantRenderer.cs`) et le
**placement des feuilles** (`LeafMaxThickCm`, `Organs.cs`) → à recalibrer contre la
nouvelle échelle. La **couleur du bois est age-based** (`LignifyFullWeeks`) →
épargnée.

## Découpage — 2 tronçons
- **① moteur** : `taper_thickness` pure + `sat(âge)` + `girth_max_cm` + retrait de
  l'accumulation (`THICKEN_RATE` conservé, commenté obsolète) + recalibrage maquette
  + tests taper monotone/tronc borné/déterminisme. **Golden RE-FIGÉ maîtrisé
  annoncé** (champ `thickness_cm` des procédurales, autres suites intactes).
- **② vue Godot** : recalibre largeur + seuil feuilles C#, banc F5 « vieux
  pommier », complément encyclopédie optionnel. **Golden INTACT** (pur-vue).

Doc `docs/vegetal/croissance/conception_lisibilite_ligneuse.md` + sprint
`sprints/vegetal/croissance/sprint_lisibilite_ligneuse/` (00_etat + 01_moteur_taper
· 02_vue_godot). DETTE **D90 → 🟢** (conçu, prêt) + **D91** ouverte (migration des 9
arbres). Prêt pour `/sprint-auto sprint_lisibilite_ligneuse`.
