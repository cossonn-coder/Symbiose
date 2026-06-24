# Tronçon ② — Branchement `expressed_gene` chez les consommateurs

> Sprint « plasticité ». Conception : `docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md`
> (§2.1, §2.2, §5). **Lire la conception + relire le journal `00_etat.md` du ①.**
> **Re-figeage golden MAÎTRISÉ et annoncé** (l'acclimatation devient active).

## Objectif
Faire LIRE `expressed_gene(g)` (au lieu de `gene(g)`) par tous les sites qui
consomment un gène **adaptogène**. À partir d'ici, une plante endurcie résiste
mieux : la boucle d'acclimatation (stress → expression↑ → dégât↓) s'active.

## Périmètre — remplacer `plant.gene("…")` par `plant.expressed_gene("…")` aux sites :
**Dégâts (consommateurs n°1)**
- `drought_stress_damage` — `perturbations.py:171` (`tolerance_secheresse`).
- `shade_stress_damage` — `perturbations.py:210` (`tolerance_ombre`).
- `damping_off` — `perturbations.py:110` (`resistance_pathogene`).
- `fungal_disease` — `perturbations.py:132` (`resistance_pathogene`).
- **gel** — `_mediated_damage(gene_name="rusticite_froid")` appelé depuis
  `boucle.py:119`. Faire lire `expressed_gene` (vérifier la signature de
  `_mediated_damage` dans `engine/mortalite.py` — adapter pour qu'il résolve
  l'expression, pas le génotype brut).
- **asphyxie** — dégât d'asphyxie `engine/mortalite.py:69` : médier par
  `expressed_gene("tolerance_asphyxie")` (aujourd'hui NON médié par le génotype —
  c'est le premier usage du nouveau gène).

**Gates de croissance (consommateurs n°2)**
- `ok_hum` — `engine/croissance.py:76` (`tolerance_secheresse`).
- tolérance ombre effective — `engine/croissance.py:211` ET
  `sim/growth/phases.py:160` (`tolerance_ombre`).

> NE PAS toucher les lectures de `gene("vigueur")` / `gene("hauteur")` (non
> adaptogènes). Laisser `gene()` tel quel pour eux.

## Vérifs
- `python3 -m tests.test_golden` → **le hash VA changer**. Capturer le NOUVEAU
  hash, vérifier que la dérive est *plausible* (le monde golden subit-il de
  l'ombre/sécheresse/gel/asphyxie ? sinon la dérive doit être faible/nulle).
  **Annoncer** la dérive dans `00_etat.md` (localisée, expliquée — règle #3).
- Test d'unité : à expression neutre (1.0), comportement identique au génotype
  brut (non-régression) ; à expression haute, dégât/gate mesurablement plus doux.
- `dotnet build` vert (aucun schéma de pont changé ici).

## Sortie
MAJ `00_etat.md` (statut ② clos, ANCIEN→NOUVEAU hash + justification de la dérive,
journal). Commit. `/clear` avant `03_cout.md`.
