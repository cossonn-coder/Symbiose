# CONCEPTION — Caractères vivants : 20 gènes qui relient la plante au jardin (D139, sprint ③ sur 3)

> Figée le 2026-11-16 (`/conception` D139). Bâtie sur
> [`conception_genetique_infinitesimale.md`](conception_genetique_infinitesimale.md)
> (registre, unités, brassage) et
> [`conception_niche_thermique.md`](conception_niche_thermique.md).
> Sprint : `sprints/vegetal/genetique/sprint_caracteres_vivants/`.

## 1. Principe

Demande de Nico (2026-11-16) : des gènes de fleurs, de fruits, de pollen, de comestibilité
et de son inverse, et des gènes qui répondent aux gestes et aux événements. Deux règles
encadrent la liste :

- **Un gène n'entre que si une mécanique existante le lit** : sinon il est inerte. Chaque
  lecteur ci-dessous a été vérifié au code le 2026-11-16.
- **Chaque gène a un prix** : sans compromis, la sélection pousse tout au maximum et la
  diversité meurt (`etude_genetique_realiste.md` §2.6).

Tous les gènes sont ajoutés **en queue** de la liste (canaux de hash). Ils sont déclarés
dans le registre du sprint ①, avec leur unité, leur neutre et leur σ_A.

## 2. Les 20 caractères

### 2.1 Fleurs (tronçon ①)

| Caractère | Unité, neutre, σ_A | Effet | Prix | Lecteur vérifié |
|---|---|---|---|---|
| `taille_fleur` | facteur, 1, 0,15 | attrait des fleurs ; fleurs dessinées plus grandes | croissance | `poids_floral` (`fields/population/registry.py:384`), lu par le champ ET par les agents butineurs |
| `nectar` | facteur, 1, 0,15 | multiplie le `nectar` d'espèce → nourriture des butineurs, miel | croissance (sucre) | `poids_floral` (ressource), ruche |
| `pollen` | facteur, 1, 0,15 | pollen offert (`pollen_vibre`) et dose anémophile | graines | `poids_floral` (voie `pollen_vibre`), `sim/engine/anemophilie.py` |
| `couleur_fleur` | position sur l'axe de couleur de l'espèce, 0, 0,15 | préférence de chaque butineur ; teinte visible des pétales | aucun en soi | `poids_floral` (facteur de préférence par type) |
| `guide_nectar` | facteur de contraste, 1, 0,15 | piste d'atterrissage : visites plus efficaces | croissance (faible) | `poids_floral` (efficacité) et constance florale des butineurs |
| `parfum` | facteur, 1, 0,15 | attire de plus loin les butineurs ; repousse une part des ravageurs | croissance (carbone) | `poids_floral` ; `herbivory_pressure` (`sim/effects/perturbations.py`) |

**Couleur, inspirée du réel (Nico, 2026-11-16).** Une fleur ne choisit pas une couleur au
hasard : elle **guide** son pollinisateur vers le nectar.
- **Axe de couleur par espèce** (données) : la bourrache va du bleu au rose, la phacélie du
  lavande au blanc, le tournesol du jaune à l'orange, la tomate reste jaune. Le gène
  `couleur_fleur` déplace la plante sur l'axe de son espèce. La vue dessine la teinte
  correspondante, en **dégradé visible** d'une plante à l'autre.
- **Préférence par type de butineur** (registre de faune, donnée) : l'abeille préfère le
  bleu, le violet et le jaune (elle voit l'ultraviolet, pas le rouge) ; le bourdon le bleu et
  le violet ; le papillon le rose, le rouge et l'orange ; le syrphe le jaune et le blanc. Le
  facteur de préférence entre dans `poids_floral` : une bourrache qui dérive vers le bleu
  attire plus d'abeilles.
- **Guides à nectar** : des lignes ou un œil central contrasté mènent l'insecte au nectar,
  comme une piste d'atterrissage. Une partie n'est visible qu'en ultraviolet, donc par
  l'abeille et pas par nous. Effet réel : l'insecte trouve le nectar plus vite, visite plus
  de fleurs par heure et reste fidèle à l'espèce. Dans le moteur, `guide_nectar` augmente
  le rendement d'une visite. La vue dessine les lignes ou l'œil. L'encyclopédie, au palier
  de maîtrise de la pollinisation, révèle « ce que voit l'abeille ».

### 2.2 Fruits et comestibilité (tronçon ②)

| Caractère | Unité, neutre, σ_A | Effet | Prix | Lecteur vérifié |
|---|---|---|---|---|
| `taille_fruit` | facteur, 1, 0,15 | masse d'un fruit × gène | **nombre** de fruits ÷ gène (compromis taille ↔ nombre) | `sim/engine/decompo.py` (≈ l. 92-106, `fruit_masse`, `fruits_par_site`), `sim/zoochorie.py`, geste `manger` |
| `appetence_fruit` | goût ∈ [−1, 1], neutre d'espèce, 0,10 | > 0 savoureux, nourrit mieux ; < 0 amer ou toxique | savoureux = plus mangé par les mulots et le joueur | `manger` (`sim/actions/gestes.py:58`, mode fruit ciblé) ; zoochorie |
| `appetence_feuille` | goût ∈ [−1, 1], neutre d'espèce, 0,10 | idem pour le feuillage | savoureux = plus brouté | `manger` (mode générique) ; `herbivory_pressure` |

**Toxicité, organe par organe (Nico, Q8).** Certaines plantes sont avantagées par la
toxicité, d'autres ont besoin d'être mangées pour se disperser. D'où deux caractères.
- **Manger un organe de goût < −0,3** fait **perdre** de la Vigueur au joueur, en proportion
  (dette D31, gains négatifs). On goûte, on apprend ; le carnet le note.
- La pression des ravageurs est multipliée par `(1 + appetence_feuille)`, avec un plancher.
- **Les oiseaux tolèrent les baies toxiques pour nous** (lierre, réel). La zoochorie
  lit la taille et la chair du fruit, pas sa toxicité pour l'homme.

Neutres d'espèce [valeurs de départ ; défaut feuille 0, fruit +0,3] :

| Espèce | feuille | fruit | Espèce | feuille | fruit |
|---|---|---|---|---|---|
| Tomate | −0,6 | +0,7 | Basilic | +0,6 | — |
| Poivron | −0,4 | +0,6 | Mâche | +0,7 | — |
| Courgette | −0,2 | +0,5 | Menthe | +0,4 | — |
| Lierre | −0,8 | −0,8 | Thym | +0,3 | — |
| Armoise | −0,5 | — | Pissenlit | +0,4 | — |
| Consoude | −0,3 | — | Ortie | +0,3 | — |
| Noyer | −0,4 | +0,6 | Bourrache | +0,2 | — |
| Fraisier | 0 | +0,8 | Framboisier | 0 | +0,8 |
| Myrtille | 0 | +0,8 | Figuier | −0,2 | +0,8 |
| Cerisier | −0,3 | +0,7 | Pommier | 0 | +0,6 |

### 2.3 Feuille et gestes (tronçon ③)

| Caractère | Unité, neutre, σ_A | Effet | Prix | Lecteur vérifié |
|---|---|---|---|---|
| `coriacite_feuille` | facteur, 1, 0,15 | résiste à la grêle et aux herbivores ; litière plus lente à décomposer | croissance | grêle (chemin `species_base="hail_resistance_base"` de `_mediated_damage`) ; `herbivory_pressure` ; décomposition de la litière (taux par `litter_tissue`) |
| `repousse` | facteur, 1, 0,15 | repart plus vite après taille, pincement, récolte, broutage | floraison (réserves) | `sim/actions/taille_herbacee.py`, `tailler`/`pincer` (`gestes.py`), convalescence après herbivorie |
| `aptitude_bouture` | probabilité de reprise, neutre d'espèce, 0,10 | la bouture prend plus souvent | presque aucun | `sim/actions/bouture.py` (`peut_bouturer`, `bouturer`) |
| `dormance_graine` | facteur, 1, 0,15 | la graine dure plus longtemps dans la banque | levée plus lente, étalée | vieillissement de la banque (`fields/seedbank.py`, `tick_species_aging`) et germination (`sim/succession.py`) |
| `dominance_apicale` | facteur, 1, 0,15 | module `apical_dominance_base` : tige haute ou buisson | haute = moins de fleurs latérales ; buisson = vite ombragé | croissance des segments (auxine, `sim/growth/`) ; `pincer` lève déjà la dominance |

### 2.4 Sol et expansion (tronçon ④)

| Caractère | Unité, neutre, σ_A | Effet | Prix | Lecteur vérifié |
|---|---|---|---|---|
| `vigueur_clonale` | facteur, 1, 0,15 | rejets plus fréquents et plus loin (stolons, rhizomes, drageons) | moins de graines | `sim/clonal.py` (`clonal_interval`, `clonal_radius_cm`) |
| `portee_graine` | facteur, 1, 0,15 | les graines portées par le vent volent plus loin | graines plus légères : semis plus fragiles | anémochorie (`ANEMOCHORIE_PORTEE_PLOTS`, `sim/engine/mortalite.py` ≈ l. 42) |
| `fixation_azote` | facteur, 1, 0,15 | apport d'azote des légumineuses | croissance (sucre) ; la fixation baisse en sol déjà riche | effet de famille des légumineuses (`plants/base/familles.py` ≈ l. 546) |
| `allelopathie` | facteur, 1, 0,15 | quantité de substances rejetées au sol | croissance (carbone) ; freine aussi ses propres semis (autotoxicité existante) | émission du champ `allelopathie` (`familles.py` ≈ l. 385) |
| `mycorhization` | facteur, 1, 0,15 | meilleur partenariat avec le réseau mycélien | cède du sucre ; inutile en sol riche | compensation mycorhizienne (`fields/ecofields/uptake.py`) |

### 2.5 Écartés (vérifiés au code le 2026-11-16)

- `tolerance_ombre`, `precocite_floraison` (`phenologie_florale`) et `resistance_maladie`
  (`resistance_pathogene`) existent déjà.
- `etiolement` est l'inverse de `port_trapu`.
- `persistance_feuillage` est un trait d'espèce (`deciduous`), et l'abscission suit déjà le
  gène tempo.
- `tuberisation` (aucun organe souterrain), `profondeur_racinaire` (sol sans profondeur) et
  `epines` (aucun grand herbivore brouteur) seraient inertes : à rouvrir quand ces mécaniques
  existeront.
- Le **changement de couleur après pollinisation** (signal honnête du marronnier) est noté
  au BACKLOG.

## 3. Le coût génétique

Une fonction unique `cout_genetique()` sur l'instance, à côté de `cout_defense`. Pour
chaque caractère coûteux, on compte l'excès au-dessus du neutre en σ_A :

    cout_genetique = max(PLANCHER, 1 − Σ_g K_g · max(0, (a_g − neutre_g) / σ_A,g))

`K_g` ≈ 0,03 par σ (valeurs de départ), avec `PLANCHER = DEFENSE_PLANCHER`. La fonction
multiplie la vigueur effective sur le même chemin que `cout_defense`. Les compromis
**structurels** (taille ↔ nombre de fruits, clonalité ↔ graines, repousse ↔ floraison,
portée ↔ fragilité, dormance ↔ levée) s'appliquent là où le caractère est lu, pas dans
`cout_genetique`.

Le coût thermique (`K_THERMO`) du sprint ② y est **rapatrié** s'il a été posé ailleurs.

## 4. Ce qui se voit (tronçons ⑤ et ⑥)

Chaque caractère a un signe sans chiffre, exporté par le pont puis dessiné :

| Caractère | Signe |
|---|---|
| `taille_fleur`, `couleur_fleur`, `guide_nectar` | taille, teinte et motif des pétales |
| `parfum` | particules légères au survol |
| `nectar`, `pollen` | rien sur la plante : on les voit à la fréquentation des butineurs |
| `taille_fruit` | taille et nombre des fruits |
| `appetence_*` | rien à l'œil : on les apprend en mangeant, et le carnet les note |
| `coriacite_feuille` | feuille plus mate et plus sombre |
| `dominance_apicale` | port en flèche ou en buisson |
| `vigueur_clonale` | rejets visibles |
| `fixation_azote`, `mycorhization` | rien en surface ; on les voit par les voisines plus vertes et les carpophores |

Le survol de debug (touche G) liste tous les caractères dans leur unité.

## 5. Golden et perf

| Tronçon | Golden |
|---|---|
| ①-④ (mécanique) | **RE-FIGÉ** annoncé à chaque fois : clés neuves dans le digest + valeurs fondatrices tirées avec σ_A + lecteurs branchés |
| ⑤ signes et pont, ⑥ vue | **INTACT** |

Perf : O(1) par lecture (une multiplication de plus là où le moteur lit déjà la donnée
d'espèce). `poids_floral` est appelé par plante et par type de butineur : la préférence de
couleur s'y calcule en O(1), sans boucle supplémentaire. Budget ≤ +2 % de tick par tronçon,
mesuré au ①.
