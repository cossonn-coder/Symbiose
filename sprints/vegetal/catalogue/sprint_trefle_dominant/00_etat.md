# Sprint TRÈFLE DOMINANT (D126) — état partagé

**Conception** : `docs/vegetal/catalogue/conception_trefle_dominant.md` (figée le 2026-11-02).
**Où on en est** : ① fait, non commité. Golden `ac48b170…` → `c23f70d9…`. Prochain : ②.

## Décisions clés (Nico, 2026-11-02)

- Un tapis qui bouge, sans plafond : le cycle azote-graminées fait reculer le trèfle.
- 4 espèces spontanées en plus : dactyle, fétuque rouge, plantain lancéolé (neuves) ; ortie (existante).
- Vue : trèfle et espèces neuves ; le reste attend D118.
- Trèfle à quatre feuilles rare ; le récolter donne un bonus au joueur.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_cycle_azote.md` — fixation freinée, renouvellement des stolons | re-figé `c23f70d9…` | **fait** |
| ② | `02_flore_spontanee.md` — 3 espèces neuves + ortie, 5 voix, mesure de l'effet | re-figé annoncé si des levées du smoke changent | à faire |
| ③ | `03_quatre_feuilles.md` — fonction pure, récolte, bonus, pont | intact | à faire |
| ④ | `04_vue_prairie.md` — tapis, quatre feuilles, formes, protocole F5 | intact | à faire |

## ① : ce qui a été fait

- `sim/effects/resolution.py` : clé optionnelle `sature_a` sur `inject_field`, flux plein à 0, nul à la valeur donnée. Sans la clé, flux constant.
- `sature_a` = 1,5 sur `Fabaceae.family_effects` (trèfle, haricot) et sur les deux effets de `MedicagoLupulina`, qui redéfinit les siens sans hériter de `Fabaceae`. L'aulne (Frankia) n'est pas une Fabaceae : inchangé.
- `Clover.longevity_years = 2` (défaut 5). Un fondateur meurt à 1,60 an en climat de laboratoire [n=1 graine, VM], par la sénescence existante.
- Rondelle `add_rondelle fertilite` de `Clover` : laissée telle quelle. Aucune lecture de cette rondelle trouvée au grep dans `sim/`, `fields/`, `world/` : elle ne semble pas apporter d'azote.
- Effet, détail dans `mesures/apres_cycle.md` : trèfle an 5 537 → 289, part 64,4 % → 46,0 % [automate actif, seed 42, n=1 graine, VM].

**Golden re-figé** `ac48b170…` → `c23f70d9…`. Raison : le smoke porte du trèfle et du haricot. Preuve de cause : les deux changements neutralisés à l'exécution, le hash retombe sur `ac48b170…`.

**`population_hash` re-figé aussi**, non prévu par le kickoff : `6007f2cd…` → `898ef008…`. Même preuve de cause (`6007f2cd…` une fois les changements neutralisés). Le journal montre déjà des re-figeages conjoints avec le golden (sprint floraison, 2026-07-18).

## Écarts à connaître pour la suite

1. **La référence du kickoff n'avait pas d'automate.** 729 / 434 / 274 viennent de `tick_semaine()` direct ; l'automate joue dans `cmd_step_week`. Le tableau §1 de la conception a la même limite. Pour ② et les suivants, mesurer avec `mesures/mesure_prairie.py` ; le vrai « avant » an 5 est 834 plantes, trèfle 537 sur 345 plots [n=1 graine, VM].
2. **Sans graminées, le trèfle ne fait que baisser** de l'an 3 à l'an 5. Critères §5 non tenus à ce stade : part 46,0 %, plots neufs 28 %, 16 espèces [n=1 graine, VM].
3. **4 tuiles sur 8 sans aucun trèfle** en 5 ans (N, O, SO, SE) [n=1 graine, VM], cause non isolée.
4. Le trèfle porte désormais le signe de sénescence dès ~1,4 an (`sim/semiologie.py`, miroir de la mortalité) : à regarder au F5.
5. `plants/species/cultivees.py` : 366 lignes de code pur, bande 🟡 (une seule responsabilité). ② ajoutera des espèces : ne pas l'y faire gonfler.

## Ce qui reste

②, ③, ④. Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 5 ans de jeu. Déjà rouges avant ce sprint : `test_succession`, `test_edaphique`, `test_parasite` (`IndexError` dans `deposer_litiere`).

## §REPRISE

① fait, à commiter (`mesures/` compris, pas le `__pycache__` de `sprint_optim_vie_macro`). Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ». Lancer : `/sprint-auto sprint_trefle_dominant`.
