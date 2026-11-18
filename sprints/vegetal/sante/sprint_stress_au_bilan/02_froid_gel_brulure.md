# ② Froid, gel, brûlure : ce que le froid et le chaud détruisent (golden RE-FIGÉ annoncé)

Lire : `CLAUDE.md`, `00_etat.md` (ce sprint + sprint A), conception §4-§5,
`docs/vegetal/genetique/conception_niche_thermique.md` (plage D139).

## Biologie
- **Froid sans gel** (tropicales sous `lim_froid`) : lésions des membranes des
  feuilles → feuilles perdues ; la plante vit si ses bourgeons et réserves tiennent.
- **Gel** sous `lim_gel` : la sève gèle dans les tissus → les **feuilles** gèlent
  d'abord ; à un froid plus profond (marge à définir sous `lim_gel`), bourgeons et
  collet gèlent → **destruction** (mort). Chez les ligneux, le gel-dégel répété
  ajoute de l'**embolie** (cf. ①).
- **Brûlure** (`t_feuille > lim_chaud`) : feuilles échaudées → feuillage perdu.

## Existant
`sim/engine/reponse_thermique.py` : `_tick_nuit_froide` (froid sans gel / gel,
`ReduceHealth` ∝ écart × `FROID_LESION_K`) et `_tick_brulure` (∝ excès ×
`BRULURE_K`) ; `sim/engine/mortalite.py` `_mediated_damage` (gel/grêle médiés) ;
`T_CONGELATION_SEVE` (`plants/base/instance.py`) ; `posture_thermique.py` (signes).

## À faire
1. Froid sans gel et brûlure : retrait de **feuillage** proportionnel à l'écart
   (remplace le passage par l'adaptateur `erode`), conserver `cause` pour la
   sémiologie.
2. Gel : feuillage gelé ∝ écart sous `lim_gel` ; sous `lim_gel − MARGE_BOURGEONS`
   → destruction (cause `gel`). Ligneux : gel-dégel → `embolie` (①).
3. Grêle (`_mediated_damage`, `sim/engine/aleas.py`) : feuilles hachées → perte de
   feuillage (pas de mort directe sauf plantule).
4. Tests : `test_niche_thermique` adapté ; une tomate sous un gel léger perd ses
   feuilles mais pas ses bourgeons ; sous un gel profond meurt ; un chêne endurci
   ne perd rien à −10 °C.

## Golden
RE-FIGÉ annoncé, dérive prouvée par neutralisation des seuls chemins thermiques.
