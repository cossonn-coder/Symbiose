# 2026-11-06 — Conception CHRONIQUE DES ESPÈCES (D127, outillage des runs longs) — FIGÉE

**Déclencheur** : rapport C du run `verger_mur` de 192 ans (PC, turbo). Nico :
« il faut s'outiller pour ». On ne savait ni quand les fruitiers avaient disparu,
ni de quoi.

**Trouvé au code** :
- bilan annuel borné à 60 ans (`MAX_ANNEES`) et réduit au top 3 → « plus que des
  noyers dès l'an 132 » est probablement le bord de la fenêtre ;
- `sim/evenements.py` range toute mort `✗` en « conflit » avec `espece=None`, alors
  que la mort par conflit n'existe plus : le carnet écrit « a cédé la place à plus
  vigoureux », sans nom, pour une plante mangée. Le test vérifiait un format que
  le moteur n'émet plus ;
- hypothèse non mesurée : dans `verger_mur` (levées coupées, arbres plantés à 15
  ans), les fruitiers meurent de vieillesse vers l'an 30-65 ; mais 2 → 5 noyers
  prouve une autre voie de recrutement.

**Arbitrages Nico** : chronique sur la VM ET au rapport C (même code) ; correction
du carnet dans le même sprint ; toutes les espèces végétales (faune → D119).

**Sprint** : `sprints/perf/run_eternel/sprint_chronique_especes/`, 4 tronçons,
golden `a10b7225…` intact partout, pont 0.6.10 au ②. Conception :
`docs/perf/run_eternel/conception_chronique_especes.md`.
