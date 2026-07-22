# ③ Gène `phenologie_florale` — désynchroniser la floraison (S2)

> Kickoff autosuffisant. Lire AVANT : `CLAUDE.md`, `00_etat.md`,
> `docs/meta/calibrage/conception_bugs_emergence.md` (volet S2).
> Source de vérité = Python `data/code/`. Lancement depuis `data/code/`.
> **Précédent à répliquer À L'IDENTIQUE : le gène `germination_thermique`**
> (sprint germination thermique tronçon ④, journal 88) — même patron, mêmes
> garde-fous. Le lire d'abord dans le code.

## Objectif
Introduire une variation individuelle du déclenchement floral pour que les
plantes fleurissent à des dates ÉTALÉES (et non toutes la même semaine), avec
sélection darwinienne émergente. Effet écologique : nectar soutenu → dynamique
des pollinisateurs saine (`registry._make_nectar_grid` → `apiculture`).

## Cause à corriger (rappel)
`sim/engine/floraison.py` : double porte GDD + photopériode, seuils constants de
classe identiques pour tous les individus → franchissement synchrone. Aucune
variance individuelle.

## Fichiers à toucher
- `plants/genetics.py` — ajouter `"phenologie_florale"` EN QUEUE de `GENE_NAMES`
  (garde-fou des canaux de hash : en queue, comme `germination_thermique`, pour
  ne pas décaler les canaux des gènes existants). Vérifier `neutral_genes()` /
  `default_factory` : le nouveau gène naît neutre à 1.0.
- `sim/engine/floraison.py` — appliquer le décalage GDD par individu.
- Constante de calibrage `FLORA_GENE_SHIFT` (analogue `GERM_GENE_SHIFT=3.5`).

## Modèle
Dans `_tick_floraison`, remplacer la porte chaleur par un seuil effectif décalé
par le gène propre de la plante :

```
gene = plant.gene("phenologie_florale")           # 1.0 = neutre
gdd_eff = cls.gdd_floraison − FLORA_GENE_SHIFT · (gene − 1.0)
porte_chaleur = plant.gdd_accum >= gdd_eff
```

(gène > 1 → seuil abaissé → fleurit plus tôt ; < 1 → plus tard.) Le gène est déjà
échantillonné du pool banque-sol AVEC variance à la germination férale
(`SeedBank.sample_genes`, succession.py) et hérité par `child_genes`
(reproduction.py) — donc l'étalement + la sélection émergent SANS code dédié, dès
que la clé existe dans `GENE_NAMES`. Vérifier qu'aucun point ne référence les
gènes par index positionnel de façon fragile (l'ajout est en queue → sûr).

## Golden attendu
**RE-FIGÉ MAÎTRISÉ.** Preuve à reproduire (patron ④ thermique) : à
`FLORA_GENE_SHIFT = 0`, la sim doit être STRICTEMENT identique au démarrage (le
gène neutre 1.0 ne décale rien ; seule une clé s'ajoute au vecteur sérialisé). Si
le golden sérialise le vecteur de gènes, il dérive du seul ajout de clé → re-figer
et consigner le nouveau hash + raison. Ensuite passer `FLORA_GENE_SHIFT` à sa
valeur de calibrage (l'étalement émerge plus tard, golden inchangé au démarrage).
Consigner le hash final dans le test + `00_etat.md`.

## À NE PAS faire
- Ne PAS insérer le gène ailleurs qu'en QUEUE de `GENE_NAMES` (casserait les
  canaux de hash → golden explose de façon non maîtrisée).
- Pas de bonus/malus direct : le gène ne fait que décaler une PORTE (flux
  thermique → réponse), philo #2.
- Ne pas toucher la porte photopériode ni la maturité (elles sont correctes).

## Clôture
`00_etat.md` (§REPRISE + hash golden), commit.
