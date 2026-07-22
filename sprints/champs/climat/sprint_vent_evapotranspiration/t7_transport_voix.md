# Tronçon ⑦ — Transport litière/neige & voix (clôture sprint)

> Kickoff autonome. Design : `docs/champs/climat/conception_vent_evapotranspiration.md` **§5.6** + **§5**.
> Passe spatiale **conditionnelle** (perf amortie). Re-figeage golden probable.
> **Dernier tronçon → clôture du sprint.**

## But
1. **Transport litière & neige** (§5.6) : le vent transporte `om_fresh` de surface +
   la neige et les **dépose en zone abritée** (sous le vent, §4) → hétérogénéité du
   sol (coin abrité = matière + manteau neigeux isolant). Transfert net d'une
   fraction des plots ventés vers les plots abrités voisins **dans la direction** du
   vent. Couple décompo/structure.
   - **Perf (§7B levier 5)** : passe spatiale **SAUTÉE les jours calmes** (exécutée
     seulement si la force dépasse un seuil). Mesurer ms/tick (jour calme vs venté).
2. **Signes diégétiques & voix** : signes du vent (réutiliser/étendre « le vent
   tourne » déjà présent pour Tempête) ; entrées de voix narratives (ledger
   `sim/journal.py`, hors tick) pour les phénomènes neufs introduits par le sprint
   (vent qui tourne, endurcissement, brise-vent, nuages amenés/chassés…). Voir
   `docs/narration/voix/conception_voix_narratives.md`.

## Critères de succès
- Test transport : sous vent fort, `om_fresh`/neige migrent vers l'abri dans la
  bonne direction ; jour calme = passe sautée (pas de transfert).
- Golden re-figé (annoncé). Suites : `test_sim_server`, suites décompo/structure.
- Perf : passe conditionnelle effective (coût nul les jours calmes).

## Clôture du SPRINT (tout le D37)
- Solder **D37** + confirmer **D32** (⓪) + **D39** (②, mort sénescente) dans `DETTE.md`.
- MAJ `journal.md` (index) + entrée `journal/NN_vent_evapotranspiration.md`.
- MAJ `00_etat.md` (⑦ ✅, sprint CLOS) + `BACKLOG.md`.
- **Supprimer `HANDOFF.md`** (obsolète).
- Vérifier le golden final consigné + tous les hash documentés.
- « Arbres en drapeau » reste en **dette** (hors périmètre, §9).
