# ② Moteur — nouaison calibrée (D86 secondaire)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` +
> `docs/conception/CONCEPTION_FLORAISON_FRUCTIFICATION.md` §3. Prérequis : ①
> (floraison replacée au bon moment) est FAIT. Lance depuis `data/code/`.

## Objectif
Maintenant que la floraison se place correctement et dure franchement (①), rendre
la **nouaison** significative pour un fruitier bien pollinisé — corriger « une
seule pomme sur le pommier » (D86 secondaire) **sans casser** l'invariant « 0
pollinisateur → 0 fruit » (philo #2, pression écologique).

## Contexte code (déjà en place)
- `sim/engine/decompo.py::_tick_fruits` : une fruitière mûre s'arme quand
  `floraison ≥ SEUIL_FLEURI (0.5)` (`a_fleuri=True`) et NOUE quand `floraison <
  SEUIL_NOUAISON (0.2)`. Fraction nouée : `self` → 1.0 ; `insect`/`wind` →
  `frac_nouaison(pollen_recu) = pollen_recu / (pollen_recu + POLLEN_DEMI)`
  (`POLLEN_DEMI = 2.0`), **sans plancher**. Pose `round(frac × |organ_sites|)`
  fruits verts, remet `pollen_recu` à 0.
- `sim/engine/butineurs.py::_apply_deposits` (~ligne 102) : chaque dépôt de
  butineur incrémente `plant.pollen_recu` (constance florale mécanique).
- Espèces `fruitier=True` : Tomato (`self`? vérifie), Zucchini/Courgette
  (`insect`), Strawberry, Raspberry, AppleTree (`insect`).

## Démarche (perf-first, mesure AVANT tuning)
1. **Banc de mesure** (`data/code/bancs/`, script neuf, hors golden) : sème un
   pommier mûr (âge ≥ 5) dans un monde avec une population pollinisatrice normale,
   simule une année, **journalise** la `floraison` hebdo et le `pollen_recu`
   accumulé au moment de la nouaison, et la `frac` obtenue. Objectif : savoir si
   le problème est (a) trop peu de pollen déposé, (b) `POLLEN_DEMI` trop haut, (c)
   trop peu de butineurs.
2. **Tuner** le minimum nécessaire pour qu'une **floraison bien visitée** noue une
   fraction significative (cible indicative **frac ≥ 0.5** à bonne densité
   pollinisatrice), en préférant le levier le plus simple :
   - baisser `POLLEN_DEMI` (demi-saturation) si `pollen_recu` typique est faible ;
   - et/ou ajuster le débit de dépôt des butineurs si la dose est structurellement
     trop basse.
   Documente le choix + le chiffre dans le commentaire (pédagogie CLAUDE.md).
3. **Invariant préservé** : `pollen_recu = 0` → `frac = 0` → **0 fruit**. Ne mets
   jamais de plancher. Une espèce `self` reste à frac=1 (autogame).

## Tests
- `tests/test_fruits.py` couvre déjà : `insect` sans pollen → 0 fruit ; dose forte
  → nouaison ≈ pleine ; `self` → pleine. Garde-les VERTS ; si tu changes
  `POLLEN_DEMI`, ajuste les valeurs de dose des cas de test en conséquence (garde
  la sémantique : faible→peu, fort→plein, zéro→zéro).
- **NE LANCE JAMAIS** `test_epaisseur_500ans`.

## Golden
- `_tick_fruits` est NEUTRE tant qu'aucune fruitière mûre ne noue dans le smoke
  (2 tuiles × 4 ans). Si ① a déjà re-figé pour cette raison, ② peut re-toucher le
  hash **uniquement si** le calibrage change la quantité de fruits nouée dans le
  smoke (dérive cohérente, annoncée). Sinon **golden intact**. Lance
  `python3 -m tests.test_golden`, applique la même procédure qu'au ① (dérive
  floraison/nouaison seule tolérée, consignée).

## Ce qu'il NE faut PAS faire
- Pas de refonte de l'arc pollinisation (champs, guildes, butineurs) — **calibrage
  seul**.
- Pas de plancher de nouaison.
- Ne touche pas au modèle de floraison du ① (figé).

## En finissant
Mets à jour `00_etat.md` (② fait : levier retenu + chiffre, golden). Commit
(fichiers nommés, `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`). Puis
tronçon ③.
