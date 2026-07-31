# Tronçon ② — Readers de rythme périphériques + bascule herbivorie

## Objectif
Migrer les modulateurs de rythme restants (mémoire du sol, ressource lombric,
détox allélopathique) vers `MICROBE_RHYTHM_REF`, et réparer le comparateur à
seuil de la bascule létale d'herbivorie (aujourd'hui cassé : le sol est
« toujours mort »).

## Pré-requis
Le tronçon ① est fait : `MICROBE_RHYTHM_REF = 0.6` existe dans `constants.py`, la
décompo est déjà migrée. Lire `docs/meta/calibrage/conception_rythmes_mo.md`
§3.A et §3.C.

## Fichiers à toucher
### Catégorie A (migration simple vers RHYTHM_REF)
1. `data/code/fields/ecofields/sol.py` — **`tick_soil_memory` (ligne ~81)** :
   `micro = self.microbiome.at_plot(r, c) / 3.0`
   → `micro = min(1.0, self.microbiome.at_plot(r, c) / MICROBE_RHYTHM_REF)`.
   **Cap à AJOUTER** (pas présent aujourd'hui — même piège `max_val=3.0` qu'①).
   `micro` pèse 40 % de la `target` de mémoire du sol.
2. `data/code/fields/population/resources.py` — **ligne ~316** (ressource
   lombric) : `micro = min(1.0, eco.microbiome.at_plot(r, c) / 3.0)`
   → `... / MICROBE_RHYTHM_REF)`. **Cap déjà présent**, ne rien ajouter.
3. `data/code/fields/ecofields/allelopathie.py` — **ligne ~43** (détox) :
   `detox = ALLELO_DECAY_MICROBE * min(1.0, eco.microbiome.at_plot(r, c) / 3.0)`
   → `... / MICROBE_RHYTHM_REF)`. **Cap déjà présent**.
   Vérifier l'import de `MICROBE_RHYTHM_REF` dans chacun de ces modules (ils
   importent déjà d'autres constantes — ajouter au besoin).

### Catégorie C (migration + re-dérivation du seuil)
4. `data/code/sim/effects/perturbations.py` — **ligne ~438** :
   `micro_norm = min(1.0, eco.microbiome.at_plot(r, c) / 3.0) if eco else 0.3`
   → `... / MICROBE_RHYTHM_REF) ...`.
   Puis **re-dériver `HERBIVORY_LETHAL_MICRO`** (constante, chercher sa
   définition — `perturbations.py:377`, actuellement `0.20`). Intention : sur
   l'échelle `/0.6`, un sol d'équilibre SAIN (microbiome ~0,05 → micro_norm
   ~0,083) NE doit PAS déclencher la bascule « sol mort » ; seul un sol
   réellement dégradé/stérile (microbiome proche de 0, post-bêchage) le doit.
   → Abaisser le seuil (ordre de grandeur ~0,05, à confirmer). **Méthode** :
   instrumenter vite (`python3 -c` ou lecture du banc) la distribution de
   micro_norm sur sol sain vs sol bêché, et poser le seuil sous le sain, au-
   dessus du stérile. **Nombre mesuré, pas deviné.** Ajuster le `if eco else 0.3`
   par défaut si nécessaire pour rester cohérent avec la nouvelle échelle.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher `croissance.py:245` (ancre B) ni `om_stable / 5.0`.
- Ne PAS re-toucher la décompo (faite en ①).
- Ne PAS lancer `test_epaisseur_500ans`.

## Golden
**RE-FIGE prévu.** `soil_memory` alimente la succession/seedbank → la
composition finale bouge. La bascule herbivorie re-fige si le smoke l'exerce
(pression ravageur > seuil sur une plante). Procédure identique à ① : lancer,
vérifier que la dérive est cohérente (pas de crash/NaN), `--capture`, consigner
le hash. **Si le golden ressort inattenduement NEUTRE** (aucun de ces chemins
n'est exercé par le smoke) : NE PAS re-capturer à l'aveugle — le consigner tel
quel dans `00_etat.md` (golden inchangé = les champs ne sont pas dans le digest,
c'est un fait à noter, pas un échec).

## Fin de tronçon
Maj `00_etat.md` (hash, seuil herbivorie retenu + sa justification mesurée) + commit.
