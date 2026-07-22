# CONCEPTION — LOD des émetteurs d'ombre (D67)

> Conception figée le 2026-07-08 (`/conception D67`). Dette **D67**, suite de
> **D66②** (spatial hash bit-identique) et **D32** (scatter sol bit-identique).
> Sprint : `sprints/perf/lod/sprint_perf_lod_ombre/` (3 tronçons). Source de vérité =
> `data/code/fields/light.py`. Golden de départ : `33c0ea6f…` (D69),
> `population_hash` `1aa4997d…`.

## 1. Problème

Le `LightField.compute` (`fields/light.py`) pèse ~½ du tick à l'an 6 (table
`tools/profile_monde.py`). Deux boucles géométriques balaient **tous** les
obstacles d'ombre `infos` (plantes vivantes + squelettes debout) :

- **lumière reçue par plante** (l.262-289) — via `ObstacleIndex` ;
- **lumière-sol par plot** (scatter, l.302-351).

D66② a coupé « combien d'obstacles je **visite** par échantillon » (élagage
spatial **bit-identique**). Il reste « combien d'obstacles **existent** ». Or N
est dominé par des **semis** (Clover×85, PoaAnnua×65…) dont l'ombre individuelle
est négligeable : un semis de 3 cm × 5 cm × densité 0,2 n'assombrit quasi rien,
mais il coûte du bucketing (index), du tri de candidats et une passe de scatter.

## 2. Idée — LOD asymétrique émetteur/récepteur

Sous un seuil de **pouvoir ombrageant**, une plante **REÇOIT** toujours la
lumière (sa croissance, son self-thinning restent pilotés) mais **n'ÉMET plus
d'ombre** (retirée des deux boucles). C'est une **approximation de modèle**, donc
**PAS bit-identique** → re-figeage golden maîtrisé (§6).

- **Métrique** (D1) : `pouvoir = current_height × canopy_radius_at ×
  foliage_density_at`. Les trois grandeurs sont **déjà** calculées dans `infos`
  (aucun état neuf, déterministe). Nulle pour un caduc défeuillé (densité 0 → non
  émetteur, cohérent avec le fait qu'un tapis nu n'ombre pas — cf. `couverture.py`).
  Dynamique énorme entre semis (~5 unités) et tournesol mûr (~4800) → un seuil
  absolu sépare proprement.
- **Seuil** : constante globale unique `SHADING_POWER_MIN` dans `light.py`.
- **Découplage** (D2) : `compute` construit `receivers` = toutes les plantes
  vivantes (réception inchangée) et `emitters` = sous-ensemble dont `pouvoir ≥
  SHADING_POWER_MIN`. L'`ObstacleIndex` et le scatter sol itèrent `emitters` ; la
  boucle reçue itère `receivers`. Les squelettes debout (`SILHOUETTE_SECHE`)
  suivent la même règle de seuil.
- **Structures fixes** : la maison est **hors `infos`** (chemin séparé
  `_point_in_swept_rect`) → **toujours émettrice**, jamais LOD. Bacs/piles/abris
  n'ombrent pas. « Structures fixes toujours émettrices » est donc vrai gratuitement.

### Invariant seuil=0 (D3) — le filet
`SHADING_POWER_MIN = 0.0` ⇒ aucune plante coupée ⇒ `emitters == receivers` dans
**l'ordre exact** de `infos` ⇒ produit multiplicatif d'opacités bit-identique ⇒
**golden intact**. C'est le mode « LOD dormant ». Verrou = test dédié. Le tronçon
① livre le mécanisme dormant (défaut 0.0, golden intact) ; le tronçon ② l'active.

## 3. Fidélité — pourquoi le risque est faible, et comment on le prouve

Dissymétrie des lecteurs de lumière (vérifiée dans le code) :

- **Lumière REÇUE** (`light_received`) : croissance, convalescence, **self-thinning
  vis B** (`shade_stress_damage`). Un émetteur sous-seuil ne peut ombrer qu'un
  récepteur **aussi petit ou plus petit** (l'auto-ombrage `qh <= ph` exclut déjà
  les plus hauts). Les férales sont **SCIAPHILES** (`perturbations.py:246`) → la
  vis B mord peu sur elles ; le plateau N vient surtout de la **vis A**
  (couverture→germination, `couverture.py`), **indépendante du LightField**.
- **Lumière-SOL** (`lumiere.at_plot`) : germination (`succession`), clonal
  (`clonal`), mortalité, uptake, thermique. Surface plus large → couper des
  émetteurs sous-seuil **éclaircit un peu le sol** → **plus de germination** → **N
  et coût/tick montent un peu**. Ce contre-effet peut manger une part du gain :
  **le banc mesure le ms/tick NET au nouvel équilibre**, jamais à N figé.

### Bras fidélité (D6) — `tools/diag_lod_ombre.py`
Compare **LOD off** (`SHADING_POWER_MIN = 0.0`) vs **LOD on** (seuil calibré),
**même seed**, `config="full"`, an 0→6. Cinq critères :

1. **Trajectoire N** — N(semaine) superposées : onset + plateau dans la bande D5.
2. **Dérive `light_received`** — écart moyen/max par plante avec/sans (quantifie
   directement l'approximation du modèle d'ombre).
3. **Self-thinning vis B** — nombre/rythme des morts « carence lumineuse » : la
   vis B ne doit pas s'effondrer.
4. **Gain ms/tick** — bras perf (réutilise `profile_monde`) à l'an 6.
5. **Coût perf de la germination surnuméraire** — ms/tick mesuré à **chaque
   équilibre PROPRE** (net) + comptage germination/saison : le gain reporté est
   honnête, net de l'inflation de N que le LOD provoque.

### Tolérance (D5)
Bande **souple ~±15 %** autour de ~613/an6 (D69). On mesure, on consigne, on ne
rouvre PAS le calibrage D69 (`GERM_PRESSION_FERALE`) sauf **dépassement franc**.

## 4. Coût perf attendu

Gain sur les deux boucles (~½ tick à l'an 6). N dominé par des émetteurs
sous-seuil → couper leur ombre réduit fortement le volume d'obstacles :
- boucle reçue : index plus petit → moins de candidats à collecter/trier ;
- scatter sol : moins d'itérations de la boucle externe `for q in emitters`.

Chiffre net à établir au tronçon ② (banc perf+fidélité). Budget : gain franc
attendu, borné par le contre-effet germination (mesuré, critère 5).

## 5. Ce que ce sprint NE fait PAS

- Pas de portage C# de la simulation (Option B : Godot est une vue).
- Pas de réouverture du calibrage férale D69 (sauf dépassement franc mesuré).
- Pas de nouvel état par plante ni de RNG (métrique = géométrie déjà présente,
  déterministe, philo #3).
- Pas de LOD sur la maison (toujours émettrice).

## 6. Golden

- **Tronçon ①** : `SHADING_POWER_MIN = 0.0` par défaut → **golden INTACT**
  (`33c0ea6f…`). Test invariant D3 (seuil 0 ≡ comportement actuel).
- **Tronçon ②** : activation du seuil calibré → **golden RE-FIGÉ maîtrisé et
  annoncé** (dérive localisée : les plots/plantes dont l'ombre sous-seuil
  disparaît) + digest `population_hash` re-figé (même cause). Nouveaux hash
  consignés dans `00_etat.md`, DETTE et journal.
- **Tronçon ③** : vue Godot + snapshot read-only → **golden INTACT**.

## 7. Découpage (3 tronçons, perf-first, vue en dernier)

| # | Objectif | Golden |
|---|----------|--------|
| ① | Bras fidélité `diag_lod_ombre.py` + découplage receivers/emitters gaté par `SHADING_POWER_MIN` (défaut 0.0, dormant) + test invariant seuil=0 | INTACT |
| ② | Calibrage du seuil sur le banc perf+fidélité, activation par défaut, consignation gain net + dérive | RE-FIGÉ maîtrisé |
| ③ | Vue Godot : overlay F4 reflète le gain + toggle debug émetteurs/récepteurs (snapshot `emitteur`, bump protocole mineur) | INTACT |
