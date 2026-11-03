# Sprint TRÈFLE DOMINANT (D126) — état partagé

**Conception** : `docs/vegetal/catalogue/conception_trefle_dominant.md` (figée le 2026-11-02).
**Où on en est** : ② fait, non commité. Golden `c23f70d9…` → `a10b7225…`. Deux critères §5 ratés (voir ②). Prochain : ③.

## Décisions clés (Nico, 2026-11-02)

- Un tapis qui bouge, sans plafond : le cycle azote-graminées fait reculer le trèfle.
- 4 espèces spontanées en plus : dactyle, fétuque rouge, plantain lancéolé (neuves) ; ortie (existante).
- Vue : trèfle et espèces neuves ; le reste attend D118.
- Trèfle à quatre feuilles rare ; le récolter donne un bonus au joueur.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_cycle_azote.md` — fixation freinée, renouvellement des stolons | re-figé `c23f70d9…` | **fait** |
| ② | `02_flore_spontanee.md` — 3 espèces neuves + ortie, 5 voix, mesure de l'effet | re-figé `a10b7225…` | **fait, 2 critères ratés** |
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

## ② : ce qui a été fait

- `plants/species/prairie.py` (neuf) : `Dactyle`, `FetuqueRouge`, `PlantainLanceole` (famille neuve Plantaginaceae). `adventices.py` et `cultivees.py` non touchés.
- `plants/catalogue.py` : `FLORE_SPONTANEE`, `AZOTE_RICHE` = 0,45, `ESPECES_SPONTANEES`. `WEED_CATALOGUE`, `SEED_ARCHETYPES` et la banque ne changent pas. `CLOVER` reste hors levée.
- `sim/succession.py` : `choisir_espece`, pure, hash sur le canal `week × 61`. Les portes pH, température et allélopathie restent celles de la tête d'archétype.
- `tools/jardinier_auto/objectifs.py` : lisait `WEED_CATALOGUE` pour « peut lever seule », passe à `ESPECES_SPONTANEES`. Point non prévu par le kickoff.
- Voix : 3 fiches, concept `succession` N3 (le cycle), causes de levée `sol_riche` / `sol_maigre` → concept carnet `azote`, page P48 (plantain), magazine par le catalogue.
- `tests/test_flore_spontanee.py` ; `test_encyclopedie` passe à 51 fiches. `mesure_prairie.py` relève aussi le temps par an et l'ombre du dactyle.
- Détail et variantes : `mesures/apres_flore.md`.

**Golden re-figé** `c23f70d9…` → `a10b7225…`, **population** `898ef008…` → `0556d1c1…`. Raison : des levées du smoke changent d'espèce (7 dactyles, 3 plantains, 1 fétuque). Preuve de cause : `choisir_espece` neutralisée à l'exécution (tête d'archétype), les deux hash retombent sur `c23f70d9…` et `898ef008…`.

**Critères §5 après ②** [n=1 graine, VM] : part 44,6 %, **raté** ; plots neufs 29 %, **raté** (perdus 45 %) ; 20 espèces, tenu ; les 4 présentes, tenu ; N 0,17 à 0,80, tenu ; tick an 2 sous +10 %, tenu. Cause : l'ombre marche (41 plots à dactyle sur 41 sous la porte, an 5), mais ~40 dactyles face à ~300 trèfles. Les vivaces à archétype ne réalimentent pas leur banque (`mortalite.py`), et la levée férale reste rare. Le retour du trèfle n'est pas observé. **Arbitrage de Nico attendu**, pistes dans `apres_flore.md`.

## Écarts à connaître pour la suite

1. **La référence du kickoff n'avait pas d'automate.** 729 / 434 / 274 viennent de `tick_semaine()` direct ; l'automate joue dans `cmd_step_week`. Le tableau §1 de la conception a la même limite. Pour ② et les suivants, mesurer avec `mesures/mesure_prairie.py` ; le vrai « avant » an 5 est 834 plantes, trèfle 537 sur 345 plots [n=1 graine, VM].
2. **Le trèfle ne fait que baisser** de l'an 3 à l'an 5, avec ou sans graminées. Après ① : part 46,0 %, plots neufs 28 %, 16 espèces [n=1 graine, VM]. Après ② : voir ci-dessus.
3. **4 tuiles sur 8 sans aucun trèfle** en 5 ans (N, O, SO, SE) [n=1 graine, VM], cause non isolée.
4. Le trèfle porte désormais le signe de sénescence dès ~1,4 an (`sim/semiologie.py`, miroir de la mortalité) : à regarder au F5.
5. `plants/species/cultivees.py` : 366 lignes de code pur, bande 🟡 (une seule responsabilité). Ne pas l'y faire gonfler.
6. Vue (④) : les 3 neuves n'ont pas encore de forme ni d'entrée C# ; dactyle, fétuque et plantain sont déjà dans les snapshots du pont.

## Ce qui reste

③, ④, et l'arbitrage sur les 2 critères ratés de ②. Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 5 ans de jeu. Déjà rouges avant ce sprint : `test_succession`, `test_edaphique`, `test_parasite` (`IndexError` dans `deposer_litiere`).

## §REPRISE

② fait, à commiter (`mesures/` compris, pas le `__pycache__` de `sprint_optim_vie_macro`). Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ». Lancer : `/sprint-auto sprint_trefle_dominant`.
