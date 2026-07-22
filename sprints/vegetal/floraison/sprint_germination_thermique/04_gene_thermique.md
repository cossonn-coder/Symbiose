# Tronçon ④ — Gène `germination_thermique` (variabilité + sélection darwinienne)

> Kickoff **autosuffisant** (lis CLAUDE.md + 00_etat.md + ce fichier).
> Conception : `docs/vegetal/floraison/conception_germination_thermique.md` §2. Lancement depuis
> `data/code/`. Golden : **RE-FIGÉ maîtrisé** (annoncé).

## Objectif
Donner une **variabilité intra-espèce** à la fenêtre de levée via un gène hérité,
pour que la **sélection darwinienne ÉMERGE** : sur un plot froid, les lignées
« lève-tôt » dominent le pool-sol au fil des saisons — sans aucun code de
sélection.

## À faire
1. **`plants/genetics.py:43`** — ajouter `"germination_thermique"` **EN QUEUE** de
   `GENE_NAMES` (préserve les canaux de hash existants, cf. commentaire l.36/42).
   `clamp_gene` (l.103) le borne déjà à `[0.40, 1.60]` ; `neutral_genes` (l.109)
   le démarre à 1.0. **Héritage automatique** : `child_genes`
   (`reproduction.py:121`, boucle `for i, g in enumerate(GENE_NAMES)`) le calcule
   seul — NE PAS écrire de code d'héritage.
2. **Constante `GERM_GENE_SHIFT`** (~3-4 °C, calibrage ⑥) — couche `fields`/`sim`,
   à côté de `T_GERM_FLOOR` (③). Décalage d'optimum par unité de gène.
3. **Formule du décalage** (les deux points portés) :
   ```python
   t_opt_eff = plant_class.t_germ_opt - GERM_GENE_SHIFT * (gene - 1.0)
   ```
   (gène > 1.0 → optimum abaissé → lève plus au froid.)
   - **Grain propre** (`succession.py` `_lever_grains_en_attente`, l.40) :
     `gene = grain.genes.get("germination_thermique", 1.0)`. Remplacer le
     `t_germ_opt` brut de la cloche ② par `t_opt_eff`.
   - **Pool féral** (`succession.py` `succession`, l.133) : pour chaque archétype,
     `gene = eco.seed_bank.species[r][c][cls]["genes"]["germination_thermique"].mean`
     (`GeneStat.mean`, `seedbank.py:57`, **défaut 1.0** si la clé/le stat est
     absent — gérer le cas proprement). Injecter `t_opt_eff` dans le dict
     `arch_temp` construit au ②.
4. **Vérifier** que le gène voyage avec la graine (déjà le cas via le vecteur de
   gènes) et que le réensemencement écrit bien la valeur dans `GeneStat` du
   pool-sol (déjà en place — ne pas réimplémenter, juste vérifier le chemin).

## Golden
**RE-FIGÉ maîtrisé.** Le défaut neutre du gène est 1.0 → `t_opt_eff == t_germ_opt`
au démarrage, MAIS le smoke test fait tourner plusieurs années → la dérive du pool
peut décaler des levées. Lancer le golden, constater, **re-figer** le hash,
**annoncer** au commit + cocher ④. Si dérive énorme : vérifier que le défaut 1.0
est bien appliqué partout (pas de `KeyError` silencieux donnant un gène aberrant).

## Ce qu'il NE faut PAS faire
- Ne PAS écrire de code de sélection : elle émerge de reproduction + héritage +
  réensemencement déjà en place.
- Ne PAS insérer le gène ailleurs qu'en **queue** de `GENE_NAMES` (casse le hash).
- Ne pas toucher `spring_flush` (⑤).
