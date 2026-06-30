# Tronçon ⑤ — Flush émergent : suppression de `spring_flush`

> Kickoff **autosuffisant** (lis CLAUDE.md + 00_etat.md + ce fichier).
> Conception : `CONCEPTION_GERMINATION_THERMIQUE.md` §0 + §1.1. Lancement depuis
> `data/code/`. Golden : **RE-FIGÉ maîtrisé** (annoncé).

## Objectif
Supprimer l'**artefact calendaire** `spring_flush` (×2.5 selon `week`). Avec la
porte thermique typée (②③) + le gène (④), la vague de printemps **émerge** déjà du
réchauffement du sol. Le flush calendaire fait maintenant **double emploi** et
viole la philo (#2/#3). On le retire → la levée devient **100 % émergente**.

## À faire
1. **`sim/engine/boucle.py:175`** — supprimer l'appel
   `slog = spring_flush(self.game_state, tile, eco, week)` et le traitement de son
   retour `slog` (vérifier ce que `slog` alimente — log/notifications — et nettoyer
   proprement sans casser le reste de la boucle).
2. **`sim/succession.py:236`** — supprimer la fonction `spring_flush` entière.
3. **`sim/__init__.py:18`** — retirer `spring_flush` de l'import/export
   `from sim.succession import choisir_archetype, succession, spring_flush`.
4. **Chercher tout autre usage** : `grep -rn spring_flush data/code/` doit revenir
   **vide** après coup (tests, bancs, tools inclus). Nettoyer les orphelins que
   CETTE suppression crée (imports, refs), sans toucher au code pré-existant non lié.

## Golden
**RE-FIGÉ maîtrisé.** Retirer le ×2.5 printanier change le volume/timing des levées
du smoke test (moins de levées massées en début de printemps, plus étalées selon
T_sol). C'est l'effet recherché. Lancer le golden, constater, **re-figer** le hash,
**annoncer** au commit + cocher ⑤. **Vérification de sens** : il doit RESTER une
vague de printemps **émergente** (les levées se concentrent quand T_sol franchit
les fenêtres) — si plus aucune levée saisonnière n'apparaît, la porte thermique
②③ est trop sévère, à réajuster (signaler à Nico).

## Ce qu'il NE faut PAS faire
- Ne PAS remplacer `spring_flush` par un autre proxy calendaire : l'émergence doit
  porter seule.
- Ne pas laisser d'import mort de `spring_flush`.
- Ne pas toucher aux autres chemins de germination (déjà branchés ②③④).
