## 2026-06-04 — Sprint impl. D31.2 : câblage écologique de la vie macroscopique (Python)

**Périmètre.** Brancher les 4 champs de population (calculés mais lus par rien en
D31.1) dans la simulation : *ce qu'on voit devient ce qui agit* (boucle vu↔agi,
`CONCEPTION_VIE_MACRO.md` §1). **Re-figeage golden assumé et unique**, comme le
sprint météo.

**Livré (4 câblages, lecture de la densité locale du champ — plus aucun proxy
reconstruit) :**
- **Herbivorie ← `ravageur`** (`sim/effects.py:herbivory_pressure`). La pression
  sur la santé dérive désormais de `eco.populations["ravageur"].at_plot(r,c)` ·
  `HERBIVORY_GAIN` (0.20) — c'est le **ravageur visible** qui mord, plus la
  reconstruction `biomass_local × HERBIVORY_BASE`.
- **Prédation ← `auxiliaire`.** Le terme `predator` reconstruit de proxies
  (biodiversité + rondelles + stabilité) **disparaît du calcul** (commenté
  « SUPPLANTÉ D31.2 — conservé pour mémoire », non supprimé). **Décision
  anti-double-comptage :** le champ ravageur intègre **déjà** la régulation par
  l'auxiliaire (sa survie est rabotée par la densité auxiliaire au tick) → lire le
  ravageur, c'est lire une pression **déjà régulée**. L'auxiliaire est donc lu
  **directement** seulement pour la **bascule létale** (`aux < 0.20 ∧ micro < 0.20`
  → dégâts doublés), pas comme second multiplicateur continu (qui double-compterait).
- **`pollinator_reach` ← `pollinisateur`** (`sim/reproduction.py`). Le rayon de
  croisement insecte est modulé par la **densité locale du champ pollinisateur**
  (saturation `POLLINATOR_SAT` = 0.40), plus par les rondelles. **Changement
  d'interface** : `pollinator_reach(mother, tile, eco)` et
  `find_father(mother, plants, tile, eco, seed, week)` (eco threadé depuis
  `engine._reproduction`). Les rondelles `pollinisateur`/`auxiliaire` restent
  **terme-source d'habitat du champ** (via `_pollinisateur_habitat_grid` /
  `_stability_grid`) → favoriser les auxiliaires nourrit toujours le brassage,
  **via le champ, pas en double**. Ancienne modulation rondelles commentée.
- **Aération/structure ← `vers_de_terre` — point ouvert tranché SOBRE.** D30
  (système structure/compaction) **n'est pas implémentée** ; je n'invente pas D30
  ici. **Couplage léger et borné** retenu (option (b) du kickoff) : la
  bioturbation des vers **accélère « un poil » la décomposition locale**
  (`tick_decomposition` : `speed += WORM_DECOMP_BONUS·worms`, 0.25 max). C'est le
  **seul** service rendu par le champ ver à la sim pour l'instant ; le système
  complet aération/infiltration/brassage des horizons **reste différé à D30**.
  Choisi plutôt que « laisser non câblé » pour **refermer vu↔agi sur les 4
  guildes** ; un retour à l'option (a) serait une ligne. *(À l'arbitrage de Nico.)*

**Ordre de tick (cohérence).** Décomposition (642), herbivorie (709) et
reproduction (698, automne) lisent toutes les populations de la semaine
**précédente** (mises à jour en 718) → décalage uniforme d'une semaine, déterministe,
**aucun nouveau RNG**.

**Validation comportementale.** `test_auxiliaires` (stress chronique monoculture,
2 tuiles jumelles) : le contraste **persiste** par le nouveau chemin — dégâts
cumulés AUX **2469** < TÉMOIN **2877** sur 30 ans, écart monotone à long terme. La
boucle « habitat → auxiliaires → champ ravageur reflue → moins de dégâts »
fonctionne. Magnitudes bien plus élevées qu'avant (l'ancien proxy donnait ~26 :
le ravageur visible mord franchement) — c'est le re-figeage attendu. `main.py`
tourne (500+ ans, sans crash, scores cohérents) ; `test_genetique` adapté (faux
`eco` exposant le champ pollinisateur) **20/20**.

**Garde-fous tenus :** code supplanté **commenté, jamais effacé** ; règle de
couches respectée ; déterminisme préservé (canaux `_hash_noise` inchangés) ;
**un seul re-figeage**, les deux hash bougent une fois (la boucle écologique se
referme : herbivorie modifie le feuillage → ressource du ravageur → densités).

### Hash golden (journal de re-figeage)
`ee79dd66…` → **`c950f06c…`** (golden engine re-figé : la santé dépend désormais
des champs). Golden de champ `population_hash.txt` : `2e6c3075…` → **`b005d9ba…`**
(la boucle écologique refermée change le feuillage, donc les densités).

---
