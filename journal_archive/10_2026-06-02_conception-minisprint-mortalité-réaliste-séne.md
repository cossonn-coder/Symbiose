<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-06-02 — Conception mini-sprint mortalité réaliste (sénescence)

### Contexte

Question de Nico en fin de Sprint éclairement : **les plantes meurent-elles ?**
Audit du code → 4 causes (hiver des annuelles, conflit, mortalité de fond,
maladie/herbivorie) mais **aucune sénescence** : `age_years` (ajouté au sprint
éclairement) n'est lu par aucune règle de mort, et `background_mortality`
**plafonne à `health=1`** (`max(1, …)`) → les vivaces/arbres sont quasi
immortels. Preuve : au run 500 ans, trèfle/minette/pissenlit à **age=25998 sem
(~500 ans), santé bloquée à 1/3** (« zombies »). Session de **conception pure**.

### Décisions (validées par Nico)

1. **Santé = vitalité dynamique** : elle chute **et se rétablit** (convalescence
   si bon milieu). Plancher de `background_mortality` levé.
2. **Sénescence couplée à la santé** (≠ seuil dur, ≠ proba directe) : au-delà de
   70 % de la longévité, déclin de santé → mort à 0. Vulnérabilité émergente.
3. **Causes de mort naturelles élargies** (demande de Nico) : **fonte des semis**
   (damping-off, stade semis), **maladies fongiques** généralisées (au-delà du
   mildiou), **ravageurs létaux** sur plante affaiblie. Toutes via `health`.
4. **Renouvellement « comme dans la nature »** : ressemis des vivaces +
   **semis d'arbres** (mast) — aujourd'hui `reproduction_rate=0` → verger sans
   descendance. Mécanisme **provisoire** (semis local direct), à unifier par la
   SeedBank-espèce génétique (D17+D22).
5. **Mort → nécromasse ∝ taille** (`current_height`) : un chêne mort ouvre une
   grande trouée → relance la succession (mosaïque).

### Produit

- `sprints/sprint_senescence.md` (kickoff autosuffisant) ; dette **D27** ;
  backlog `CLAUDE.md` ; cette entrée. **Aucun code touché** — implémentation à
  une session future.

---
