## 2026-07-11 — Sprint PALETTE DE GESTES PERSONNALISABLE (①→⑤) — SPRINT TERMINÉ

**Décision :** le joueur compose lui-même son jeu d'outils « façon palette de
peinture » — une sélection choisie de gestes puisée dans un catalogue de base +
des gestes débloqués, avec des **macros** (séquences rejouées sur la cible
cliquée). Remplace l'accès historique « touches 1..9 + Tab » devenu ingérable.

Sprint GROS découpé en 5 tronçons autosuffisants (perf-first, vue en dernier),
**golden NEUTRE/INTACT partout** (référence
`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`), pont
0.5.22 → **0.5.26**, `dotnet build` vert.

- **① Déblocage Python** — `game_state["gestes_debloques"][player]` + table
  data-driven `GESTE_UNLOCK` (grammaire D12 : `maitrise`/`action`/`et`/
  `evenement`, chaîne sécateur→couper→tailler→bouturer) + hook
  `evaluer_deblocages` + expo snapshot ; geste BRUT neuf `couper` (ancêtre de
  `tailler`, désormais GATED). Golden NEUTRE, pont 0.5.23.
- **② Bouture** — geste `bouturer` 2 temps (mère bouturable → plot), clone
  génétique exact (réutilise `sim/clonal.py`), flag `bouturable` sur 8 espèces,
  bouffée `stress_memory` sur la mère, marqueur `bouture_spontanee` (D12) + 5
  voix. Golden NEUTRE, pont 0.5.24.
- **③ Greffe** — geste `greffer` 2 temps (greffon → porte-greffe), gate
  `species_compatible` (même famille), modèle aérien(greffon)/racinaire(porte-
  greffe) D8, flag `greffable` sur 4 ligneuses fruitières + 5 voix (outil neuf
  `greffoir`). Déterministe, zéro RNG (#3). Golden NEUTRE, pont 0.5.25.
- **④ Palette UI (C#)** — colonne verticale gauche (D11), une icône MUETTE
  procédurale par geste (`GesteIcon` ~16 pictogrammes/familles, philo #5), lit
  `player.gestes_debloques` (verrouillés grisés+inertes), flash vert au
  déblocage (voie savoir, philo #6) ; câble tous les gestes + bouturer/greffer.
  Pur vue (Option B), golden intact, `dotnet build` vert.
- **⑤ Macros + persistance layout + banc F5** — Python : `sim/actions/palette.py`
  (`FAMILLE_CIBLE`/`macro_coherente` : une macro = gestes de MÊME famille de
  cible, un clic les nourrit tous ; `definir_palette` valide PUIS écrit
  transactionnellement, refus en bloc si mixte), commande pont NEUVE `palette`
  (`PaletteCmdMixin`), bloc `player.palette` = `{slots, macros}` persisté par
  avatar (D10), banc `palette_gestes` + hook NEUF `BANC_POST_INIT` (force
  maîtrise → bouturer/greffer ouverts). C# : `WorldView.Macros.cs` (touche **K**
  enregistre une séquence → persistée via `SimBridge.Palette`, touche **J** arme,
  clic capture le point → `DrainMacro` rejoue chaque sous-geste au rythme du pipe,
  **chacun paie sa Vigueur**, philo #1 ; pas de pinceau balayé, D5). Golden
  intact, pont 0.5.26, `dotnet build` vert.

**Tests :** `test_deblocage` 24/24, `test_bouture` 27/27, `test_greffe` 31/31,
`test_palette` 22/22, suite pont **269/269** (sections 19/20/21 câblées),
`test_encyclopedie` 68/68, golden `452b5256…` inchangé.

**Reste F5 Nico :** recette par tronçon dans
`sprints/sprint_palette_gestes/00_etat.md` §Avancement (colonne cliquable,
filtrage par déblocage, gestes 2 temps bouture/greffe, K/J macros, calibrages
espèces/coûts/BASE). Sélecteur multi-macro à ajouter si souhaité (proto = slot
n°1). D1/D5/D10/D11/D12 tranchés et livrés.
