# Tronçon ⑤ — Pollinisation & dispersion anémophiles

> Kickoff autonome. Design : `docs/champs/climat/conception_vent_evapotranspiration.md` **§5.3**.
> Effets **par-plante** (négligeable en perf). Re-figeage golden probable.
> **Rappel règle projet** : toute espèce ajoutée = ses **5 voix narratives**.

## But
1. **Anémophilie** : trait d'espèce `pollinisation: "anemophile" | "entomophile"`
   (registre data-driven, cohérent avec l'arc pollinisation conçu). Les espèces
   anémophiles (graminées, noisetier…) reçoivent `pollen_recu` ∝ `vent_local` ×
   densité de congénères **en amont** (direction du vent !) → voie de nouaison
   **parallèle** à l'entomophilie du pommier.
2. **Butineurs cloués** : grand vent → les butineurs ne volent plus → la
   pollinisation **entomophile** chute (`eco.foragers` modulé par `vent_local`).
   Tension réaliste : jour venteux = mauvais pour l'abeille, bon pour la graminée.
3. **Anémochorie** : dispersion des graines (samares, aigrettes) **sous le vent** →
   dépôt en `seed_bank` à distance et **dans la direction** du vent (rayon/direction
   ∝ force) → oriente/élargit la succession.

## Si ajout d'espèce(s) anémophile(s) au catalogue
Le catalogue grandit avec les idées (règle projet) : si l'effet est mieux incarné
par une espèce absente (noisetier, graminée nommée…), l'**ajouter** — et alors lui
donner ses **5 voix** (encyclopédie 3 niveaux, carnet via `CONCEPT_DE`, page secrète
si lore, magazine famille, événements de cycle de vie). Voir
`docs/narration/voix/conception_voix_narratives.md`.

## Critères de succès
- `test_fruits`/`test_pollinisation` étendu : une anémophile noue sous vent sans
  butineur ; une entomophile noue moins par grand vent ; anémochorie dépose sous le
  vent.
- Golden re-figé (annoncé). Suites : `test_fruits`, `test_biennial`, `test_sim_server`.
- Voix complètes pour toute espèce ajoutée (sinon fiche muette = à éviter).

## Clôture
MAJ `00_etat.md` (⑤ ✅). Commit. `/clear`. Lancer `t6_maladies_fongiques.md`.
