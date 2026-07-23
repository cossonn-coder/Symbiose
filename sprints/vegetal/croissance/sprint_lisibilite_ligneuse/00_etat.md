# Sprint — Lisibilité de l'architecture ligneuse (le vieux pommier)

> **Carnet de bord VIVANT** (skill `/conception`, §0bis). Phase A en cours —
> RIEN n'est figé. Ce fichier persiste ce qui a déjà été établi/tranché, pour
> reprise à froid sans intervention de Nico.

- **Type/thème** : `vegetal/croissance` (même famille que D29/D21, docs
  `docs/vegetal/croissance/`).
- **Origine** : F5 Nico 2026-07-23 — un vieux pommier a un « tronc comme un
  baobab », des « branches emmêlées comme des ronces », un « diamètre uniforme
  (ronces diamètre baobab) ». Problème de **lisibilité de forme**, pas de bio.

## Phase courante
Phase A (challenge) — diagnostic établi, arbitrage du MODÈLE en attente de Nico.

## Diagnostic — CAUSE RACINE établie (lecture code, revérifiée)
Le défaut est **dans le moteur** (`data/code`, source de vérité), pas dans la vue.

- `Segment` (`plants/base/stades.py:44`) porte déjà `thickness_cm`.
- `sim/growth/phases.py:67` : à chaque tick, **tout segment non-apex** fait
  `s.thickness_cm += THICKEN_RATE` — **constant (0.03 cm/tick), uniforme, non
  borné, indépendant de l'ordre de branche**.
- Pommier (`plants/perennials.py`) : `wood_persistence = 4000` sem. → un segment
  vit ~77 ans. À 0.03/tick : épaisseur → **~120 cm** ⇒ **« baobab »**. Et comme
  l'incrément est le MÊME pour tous, une brindille vieille atteint la même
  épaisseur que le tronc ⇒ **« ronces diamètre baobab »** (aucun amincissement).
- La **topologie encode déjà l'ordre de branche** (`_depths`, `_children`,
  `_subtree`, comptage de terminaux possible) — elle n'est simplement **pas lue**
  par l'épaississement. La hiérarchie (flèche/buisson) existe déjà via l'auxine
  (`apical_dominance_base=2.0` pour le pommier). → l'« emmêlement » est d'abord un
  défaut de **contraste d'épaisseur**, pas un manque de mécanique de ramification.

## Couplages de `thickness_cm` (cartographiés)
- **Écologie : AUCUN** (ni lumière, ni compétition, ni biomasse). Pure grandeur
  morphologique/rendu ⇒ changer le modèle ne ripple PAS dans l'écosystème.
- **Rendu C#** : (a) **largeur de trait** `thickness × PxPerCmX × 2.2`
  (`PlantRenderer.cs:452/505`) ; (b) **placement des feuilles** `Thickness ≤
  LeafMaxThickCm(1.5)` (`PlantRenderer.Organs.cs:201`, fin = feuillu). La
  **couleur du bois est AGE-based** (`LignifyFullWeeks`), PAS thickness → SAFE.
- **Maquettes Python** (`tools/maquette/*`, `tools/render_structure`) : largeur
  ∝ thickness + `LEAF_MAX_THICK_CM` (organes.py:73).
- **Golden** : `thickness_cm` est sérialisé (9 champs bois) ⇒ **tout changement de
  modèle RE-FIGE le golden** (dérive localisée au champ épaisseur des ligneux,
  à annoncer). Le smoke a un pommier < 5 ans.

## Modèle proposé (RECO, à valider par Nico)
Remplacer l'accumulation uniforme par **amincissement dérivé de la topologie
(pipe model) + épaississement secondaire borné (âge)** :

`thickness_i = THICKNESS_INIT + girth_max_espèce × sat(age_i) × taper_i`
- `sat(age) = 1 − exp(−age/TAU)` : croissance secondaire **saturante** ⇒ tronc
  vénérable MAIS **borné** (tue le baobab).
- `taper_i` = fonction croissante du **nb de terminaux portés en aval** (pipe
  model de Shinozaki/Léonard : section ∝ ce qui est supporté) ⇒ tronc épais,
  brindilles fines, charpentières intermédiaires (tue la « ronce »). Exposant
  `p` = levier de calibrage (0.5 = physique / 1 = hiérarchie forte).
- Calcul **1 passe O(n) post-ordre par tick** (n ≤ max_segments=70), remplace
  l'incrément existant → perf ≈ neutre. Déterministe, zéro RNG (philo #3).
- `girth_max_espèce` : 1 param par espèce (pommier gros, herbacée ≈ actuel).

Philo : #2 ✓ (dérive de l'état, aucun bonus/malus plaqué) · #3 ✓ · #5 ✓ (la
forme porte l'âge/l'espèce) · #7 ✓.

## Arbitrages TRANCHÉS (Nico 2026-07-23)
1. **Terme d'âge saturant : OUI** — pipe model + croissance secondaire saturante
   (tronc vénérable mais borné).
2. **`girth_max` PAR ESPÈCE** (pas de levier global) — cohérent #7 + perennials.py.
3. **Découpage = 2 tronçons** : ① moteur (pipe model + taper + girth_max espèces +
   golden re-figé + tests taper monotone) → ② vue Godot (recalibrer largeur ×2.2
   + seuil feuilles LeafMaxThickCm + banc F5 vieux pommier, golden intact).

## Calibrage (défauts à poser dans le kickoff ①, placeholders → F5)
- `TAU` (saturation d'âge), `TAPER_EXP p` (0.5 physique / 1 hiérarchie forte),
  `girth_max_cm` par espèce ligneuse (pommier/cerisier/figuier/noyer/chêne/aulne).
- Herbacées : `girth_max` faible par défaut sur PlantBase pour rester proche de
  l'actuel (limiter l'ampleur du re-figeage aux ligneux visibles).

## Périmètre (arbitré Nico 2026-07-23) — CIBLÉ
Effet visible sur le **pommier seul** (seul arbre `procedural_growth=True`). Les 9
autres arbres n'ont pas de topologie de segments (rendus par silhouette de
couronne) → `girth_max_cm` posé pour eux (prêt) mais SANS effet tant qu'ils ne
sont pas migrés. Migration des 9 arbres en procédural = **sprint distinct, dette**.

## Carte des tronçons (FIGÉE, prête `/sprint-auto`)
- **① `01_moteur_taper.md`** — `taper_thickness` pure (pipe model : n_terminaux
  par sous-arbre) + croissance secondaire saturante `sat(âge)` ; leviers module
  `GIRTH_TAU`/`TAPER_EXP` ; `girth_max_cm` sur `PlantBase` + 10 ligneux ; retrait
  de l'accumulation `+= THICKEN_RATE` (constante conservée, commentée obsolète) ;
  recalibrage `LEAF_MAX_THICK_CM` maquette ; tests taper monotone + tronc borné +
  déterminisme. **Golden RE-FIGÉ maîtrisé annoncé** (champ `thickness_cm` des
  procédurales, sans couplage écolo → autres suites intactes).
- **② `02_vue_godot.md`** — recalibrer largeur de trait (`×2.2`) + seuil feuilles
  `LeafMaxThickCm` C# contre la nouvelle échelle ; banc F5 « vieux pommier » ;
  complément encyclopédie optionnel. **Golden INTACT** (pur-vue).

## Artefacts figés
- Doc : `docs/vegetal/croissance/conception_lisibilite_ligneuse.md`
- Kickoffs : `01_moteur_taper.md`, `02_vue_godot.md`

## §REPRISE
Conception FIGÉE, sprint prêt pour `/sprint-auto sprint_lisibilite_ligneuse`.
Prochain : tronçon ① (moteur), golden re-figé maîtrisé attendu. Rien à concevoir
de plus. Reste F5 Nico après ②.
