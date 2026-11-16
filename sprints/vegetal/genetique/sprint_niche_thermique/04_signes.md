# ④ Signes par paliers — posture thermique et marques

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_niche_thermique.md` §6, et l'en-tête de
> `data/code/sim/semiologie.py` (invariant DRY : un signe lit le seuil même du dégât).
> Golden attendu : **INTACT** (lecture pure, au snapshot).

## Objectif
Une gamme continue de signes, du froid au chaud, que la vue pourra dessiner et que le carnet
pourra dire, sans chiffre.

## À faire
1. **Détecteur `posture_thermique`** dans `sim/semiologie.py` (ou un module voisin si la taille
   l'exige ; 80 LDC aujourd'hui) : ∈ [−1, 1], lu sur `lim_froid`/`lim_gel`/`lim_chaud`/
   `lim_brul` (méthodes du ②) et sur la nuit et la T_feuille de la semaine. Paliers :
   froid = pendent (lim_froid + 3 °C), violacé (`cold_memory` haute), translucide (dégât de
   froid), noirci (gel), effondré ; confort = étalé ; chaud = replié (lim_chaud − 3 °C),
   flétri à midi (chaud + soif), bords jaunis, brûlé. Rampes avec la forme existante
   (`clamp01`). Si le snapshot n'a pas accès aux températures de la semaine, les mémoriser
   sur la plante au tick **sans** les mettre dans le digest (même principe que
   `symptom_marks`), et le justifier.
2. **Marques événementielles** `froid` et `brulure` (`gel` existe) dans le registre des
   symptômes et dans l'agrégateur `leaf_symptoms`.
3. **Pont** : exporter `posture_thermique` et les marques (`tools/simserver/serialize.py`,
   patron des signes existants), incrémenter `ENGINE_VERSION`. Comparer le snapshot JSON
   avant/après (le golden ne voit pas le pont).
4. **Voix** : le carnet consigne la première observation de chaque palier par espèce
   (« le basilic a noirci cette nuit », « les feuilles du fraisier se replient au soleil »),
   descriptif sous le palier de maîtrise du concept (météo/climat), interprétatif au-dessus.
   Légende des signes (`sim/signes_corpus.py`) : entrées pour les nouveaux paliers.

## Tests
- Test ciblé : posture < 0 pour un basilic une nuit à 7 °C, ≈ 0 à 20 °C, > 0 pour une plante
  assoiffée au soleil en canicule ; le signe s'allume au seuil même du dégât (DRY).
- `tests/test_signes_legende.py` vert ; golden identique.

## Ne PAS faire
- Écrire dans un champ lu par le tick (golden INTACT).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ④ FAIT. Commit.
