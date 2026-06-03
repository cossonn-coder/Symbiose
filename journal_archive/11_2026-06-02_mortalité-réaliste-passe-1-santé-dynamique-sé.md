<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-06-02 — Mortalité réaliste passe 1 : santé dynamique + sénescence (Python)

### Contexte

Implémentation du **cœur** du sprint sénescence (D27), découpé en deux passes
sur décision de Nico. **Passe 1 = M1–M3** : santé dynamique, sénescence par âge,
mort bisannuelle. Passe 2 (à venir) = fonte des semis, maladies fongiques,
ravageurs létaux, renouvellement (M7) + nécromasse ∝ hauteur.

### Réalisé

- **`models.py`** : `longevity_years`/`maturity_years` sur `PlantBase` +
  classmethod `longevity()` (override sinon défaut par cycle : annuel ∞,
  bisannuel 2, vivace 5). Longévités explicites minette/pâturin 3, pissenlit 8.
- **`perennials.py`** : `longevity()` (override par arbre, repli `age_curve[-1]
  × 1,5`) ; longévités cerisier 60 / pommier 70 / figuier 80 / noyer 200 /
  chêne 500, maturités 5/5/5/15/25.
- **`fields.py`** : `SENESCENCE_ONSET=0.70`, `SEN_RATE=0.04`, `HEAL_RATE=0.06`,
  `HEAL_SEN_CUTOFF=0.50`.
- **`effects.py`** : plancher `max(1, …)` de `background_mortality` **levé**
  (la mort à 0 ne touche en pratique que les sujets déjà à `health=1`) ;
  nécromasse déposée pour les morts de fond avant nettoyage.
- **`engine.py`** : `_tick_senescence_health` (sénescence ∝ âge au-delà de
  l'onset → déclin santé ; guérison en bon milieu `Q = lumière·humidité·(1−
  perturbation)`, coupée à `sen ≥ 0.5`) ; mort bisannuelle en transition
  hivernale (`age_years ≥ 2`). Tout déterministe (`_hash_noise`, flux `week·3`
  déclin / `week·5` guérison décorrélés).
- **`main.py`** : pommier en coin `(0,7)` pour observer la sénescence.

### Effet de bord corrigé

Les aléas saisonniers « semis » (gelée tardive, limaces, chenilles) ciblaient
`current_stage == 0` — donc le **stade perpétuel des arbres** (« arbre », index
0), frappé comme un semis fragile à chaque saison (pommier isolé mort à l'an 2).
Recadré sur le stade **nommé** `"semis"` : zéro régression (tous les semis
herbacés portent ce nom), arbres exclus.

### Validation

- Pommier isolé : santé oscille 1↔3 en jeunesse (**plus de zombie**), remonte à
  3/3 vers l'an 7, puis décroche après l'onset (an 49) → **mort par sénescence
  à l'an ~60** (L=70). ✔ critères 1 & 2.
- Run `main.py` **500 ans, exit 0, aucune extinction** (23 plantes vivantes).
  `%vivace` oscille 48–81 % (mosaïque), cohérent avec la cible ~65 %. ✔ critère 6.

### Reste (passe 2)

M4 fonte des semis, M5 maladies fongiques, M6 ravageurs létaux, M7 renouvellement
(ressemis vivaces + semis arbres), nécromasse ∝ `current_height`. D27 reste 🟡
jusqu'à la passe 2 + portage C# (→ D24/D27).

---
