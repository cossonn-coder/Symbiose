## 2026-06-03 — Sprint gènes du vecteur : vigueur + résistance pathogène + tolérance sécheresse (Python)

Extension du vecteur de gènes héréditaire (D22) de **2 → 5 gènes**, chacun branché
sur une mécanique existante selon le patron `rusticite_froid` (susceptibilité =
`1/gène`, aucun bonus/malus direct — philo #2/#7). Découpage acté avec Nico : les
**coûts en Vigueur joueur** (couche transversale D11) restent une conception
séparée à venir — ce sprint ne touche que les traits héréditaires des plantes.

**Décision (3 questions) :** (1) **découper** — gènes maintenant, Vigueur joueur
ensuite ; (2) définir **`vigueur`** tout de suite comme multiplicateur de fitness
**PROVISOIRE** (à recâbler sur la Vigueur D11) ; (3) ajouter une **vraie voie
sécheresse → santé** (pas seulement la stagnation de croissance).

### Ce qui est fait
- `plants/genetics.py` : `GENE_NAMES` = (`hauteur`, `rusticite_froid`, **`vigueur`**,
  **`resistance_pathogene`**, **`tolerance_secheresse`**). Héritage biparental et
  banque-sol suivent **automatiquement** (canaux de hash décorrélés par index → les
  deux gènes existants restent bit-pour-bit identiques en isolation).
- **`vigueur`** (fitness générale) — `engine` : accélère l'avancement de stade
  (`needed = duration_weeks / gène`) et la convalescence (`heal × gène`).
- **`resistance_pathogene`** — `effects` : `susc /= gène` dans `fungal_disease` ET
  la fonte des semis (`damping_off`) → sélection émergente des lignées résistantes.
- **`tolerance_secheresse`** — abaisse le seuil d'humidité de stagnation
  (`ok_hum = 0.15 / gène`, `engine`) ET **nouvelle** voie `drought_stress_damage`
  (`effects`, canal week·37) : une sécheresse sévère **prolongée**
  (`drought_memory > 0.6`) abîme le tissu, médiée par le gène. Vraie pression de
  sélection sans nouveau champ.

### Vérifs
- **Golden re-figé** `63bfdac4…` → `ee79dd66…` (comportement intentionnellement
  modifié — ce n'est pas un refactor ; re-vérif PASS sur le nouveau hash).
- **Stabilité 200 ans × 3 sols** : effectifs ~2–16 plantes/tuile, **aucun
  effondrement ni emballement** ; dérives génétiques douces et bidirectionnelles
  (0.93–1.06) → la couche mord sans runaway.
- `test_genetique` **20/20**, `test_auxiliaires` OK.

### Hors périmètre (gated)
- **Vigueur joueur + coûts d'action** (manger, récolte, déracinage) — **D11**,
  conception séparée. `HARVEST_VIGUEUR_COST` reste 0 ; le gène `vigueur` y sera
  recâblé.
- **Calibrage fin de la pression de sélection** (intensités, balance pionnières /
  cultivées) — même observation qu'au sprint météo 03, sprint ultérieur.
- **Portage C#** — **D24**.

### Hash golden (journal de re-figeage)
`63bfdac4…` (météo 04) → `ee79dd66…` (gènes du vecteur).

---
