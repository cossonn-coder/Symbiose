# Tronçon ③ — Coût croissance/défense

> Sprint « plasticité ». Conception : `docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md`
> (§2.4, §3-P6, §5). **Lire la conception + relire le journal `00_etat.md` des ①②.**
> **Re-figeage golden MAÎTRISÉ et annoncé** (le compromis modifie la croissance).

## Objectif
Faire payer la défense : la **sur-expression** (expression > 1) re-route la vigueur
au lieu de s'ajouter. Une plante qui blinde sa tolérance croît moins et fait moins
de graines → arbitrage émergent, pas de buff gratuit (philo #2).

## Périmètre
- `sim/vigueur_plante.py:91` — formule actuelle
  `vigueur = sante × maturite × qi_local × gene("vigueur")`.
- Ajouter un facteur **coût de défense** :
  ```
  surexpression = Σ_g max(0, expression[g] − 1)     # budget défense mobilisé
  cout_defense  = max(PLANCHER, 1 − DEFENSE_COST × surexpression)
  vigueur      *= cout_defense
  ```
  - `expression[g]` ne ronge QUE par sa part > 1 (désexprimer n'est jamais pénalisé).
  - Borné par un `PLANCHER` (> 0) pour ne jamais annuler la vigueur.
  - `DEFENSE_COST` = knob (calibrage P6) ; démarrer modéré pour que survivre reste
    gagnant sous stress mais payant sous abondance (éviter l'anti-sélection, P6).

## Garde-fou conceptuel (P6)
Vérifier qualitativement qu'on n'a pas créé d'anti-sélection : une plante acclimatée
sous stress doit globalement mieux s'en sortir qu'une non-acclimatée (le gain de
survie > coût de croissance). Si l'inverse émerge, baisser `DEFENSE_COST` /
`EXPR_GAIN` (itératif assumé — ne pas chercher le réglage parfait ici, juste un
comportement sain).

## Vérifs
- `python3 -m tests.test_golden` → **hash change**. Annoncer la dérive (la vigueur
  baisse là où des plantes se sont acclimatées). Capturer le nouveau hash.
- Test d'unité : expression neutre → `cout_defense = 1` (non-régression vigueur) ;
  sur-expression → vigueur strictement réduite, jamais sous `PLANCHER`.
- `dotnet build` vert.

## Sortie
MAJ `00_etat.md` (statut ③ clos, hash, justification dérive, journal). Commit.
`/clear` avant `04_priming.md`.
