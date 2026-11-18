# ⑤ Ouverture du monde `full` + critères d'acceptation (golden INTACT)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/sante/conception_plante_vivante.md` §7-§8,
`sim/monde_complet.py`.

## Objectif
Vérifier — et corriger si besoin — que l'ouverture du monde `full` en semaine 10
donne une mortalité **partielle**, et réparer l'âge affiché par la chronique.

## À faire
1. `ouvrir_monde_complet` : les plantes posées et pré-crues ont réserves et
   feuillage pleins (défaut). Si la pré-croissance appelle des chemins qui
   consomment les réserves, le vérifier et l'expliquer.
2. Chronique (D140 g1) : `tools/simserver/chronique.py` (~l. 130, 183) affiche
   `p.age_weeks`, qui compte les semaines **dans le stade courant**
   (`advance_stage` le remet à 0). Afficher l'âge vrai depuis `age_years`
   (semaines si < 1 an, années sinon). Adapter `tests/` de la chronique.
3. Banc d'acceptation `tests/test_ouverture_vivante.py` (monde `full`, seed 42,
   s10 → s30, via `SimServer` comme `tests/simserver/base.py`) :
   - **0 arbre posé mort** ;
   - **≤ 25 % des herbacées posées mortes** hors fin de cycle (cause chronique
     ≠ `fin de cycle`) ;
   - **≤ 4 rejets par arbre mort** au total.
   Si un critère échoue : diagnostiquer (cause, espèce, facteur limitant du bilan)
   et ajuster les **paramètres d'espèce** (`plants/physiologie.py`) ou `K_HERB` —
   jamais une règle spéciale pour l'ouverture (mémoire Nico « pas de béquille »).
   Consigner les chiffres dans `00_etat.md`.
4. Perf : tick monde `full` s10-s30 avant sprint (commit de départ du sprint, cf.
   `00_etat.md`) vs maintenant, 3 paires alternées, charge via `uptime` ; consigner.

## Golden
**INTACT** (le smoke n'ouvre pas le monde `full`). Si un ajustement de paramètre
d'espèce le fait bouger : re-figer de façon annoncée, dérive prouvée localisée.

## Ne PAS faire
- Pré-rouler la faune à l'ouverture (mesuré : aggrave).
- Lancer `test_epaisseur_500ans`.
