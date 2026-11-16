# CONCEPTION — Niche thermique : la plage vivable décide (D139, sprint ② sur 3)

> Figée le 2026-11-16 (`/conception` D139). Bâtie sur
> [`conception_genetique_infinitesimale.md`](conception_genetique_infinitesimale.md)
> (registre des caractères, unités en °C). Sprint :
> `sprints/vegetal/genetique/sprint_niche_thermique/`.

## 1. Le constat : un basilic vert en plein hiver

F5 de Nico, le 2026-11-16. Quatre causes, vérifiées au code :

1. **Mort calendaire trop tardive.** `boucle.py`, étape 16 : `_winter_transition` se
   déclenche quand `week_in_year − 40 ≥ 9`, donc aux semaines 49 à 52. Depuis le calendrier
   unique (l'année démarre à l'équinoxe), cela tombe **entre mi-février et mi-mars**. Le
   docstring parle encore de « semaines 48-52 ».
2. **Le gel ne frappe que le stade `semis`** (`mortalite.py`, `_mediated_damage`, filtre
   `p.stage.name != "semis"`). Un basilic adulte ne craint pas le gel.
3. **Aucun dégât de froid sans gel.** Sous `temp_min_growth` (5 °C par défaut), la plante
   stagne. Rien de plus.
4. **Un climat qui gèle trop peu.** `t_min_nuit_at` est la nuit **type** de la semaine :
   54 semaines avec une nuit sous 0 °C en 8 ans [seed 42, sol nu, sans vent], soit ≈ 7 par
   an. Caen compte ≈ 35-40 jours de gel par an [ordre de grandeur, non revérifié]. Côté chaud,
   T_air hebdo plafonne à 24,9 °C [8 ans, seed 42], alors que la Normandie a vu 40 °C cet été
   (Nico).

## 2. Décisions (Nico, 2026-11-16)

- **T1 — Le moteur ne tue pas, la plante meurt** quand ses conditions de mort sont atteintes
  (vieillesse, froid, chaud, maladie). La mort calendaire des annuelles
  (`winter_strategy="die"`) **disparaît**. Les annuelles rustiques (mâche, seigle, blé,
  bourse-à-pasteur) passent l'hiver. Une annuelle s'éteint d'elle-même après ses graines
  (sénescence de fin de cycle, propriété de la plante). Il n'y a **pas** de filet de vieillesse
  arbitraire.
- **T2 — Températures extrêmes** : la **nuit la plus froide** et le **jour le plus chaud** de
  la semaine. La température de la **feuille** dépend du soleil et de la soif.
- **T3 — Plage vivable portée par l'espèce, décalée par les gènes, en °C.** Trois caractères :
  `rusticite_froid` (refondu en °C), `limite_froid`, `limite_chaud`.
- **T4 — Signes visibles par paliers de température**, en une gamme continue froid → confort
  → chaud, sans chiffre (philo #5).
- **T5 — Le gel touche tous les stades**, et le froid sans gel abîme les plantes tropicales.

## 3. Températures extrêmes (tronçon ①)

**Nuit la plus froide.** Elle s'ajoute à `t_min_nuit_at` (`fields/ecofields/thermique.py`),
ou la remplace : un terme d'**écart à la nuit type**, déterministe, plus grand par semaine
claire. Le paillage, la neige, le voile et le vent la modulent déjà par les termes existants.
**Cible de calibrage** : ≈ 12-15 semaines par an avec au moins une nuit sous 0 °C sur sol nu
[cible, ordre de grandeur Caen], minimum de l'ordre de −10 °C en hiver rude. Mesurer avant
et après (script de mesure sous le dossier du sprint).

**Jour le plus chaud.** Nouvel helper pur, miroir de `t_min_nuit_at` :

    t_max_jour = T_air + AMPLITUDE_DIURNE·(1 − nébulosité) + écart au jour type

**Cible** : une semaine de canicule atteint 33-40 °C en plein soleil [cible, Normandie 2019
et été 2026].

**Température de la feuille** (par plante) :

    T_feuille = t_max_jour + ECHAUFF_FEUILLE · lumière_reçue · soif

`soif` ∈ [0, 1] mesure la fermeture des stomates. Elle se lit sur un proxy existant
(`drought_memory` ou humidité ressentie D111 ④, à choisir après lecture). Une plante bien
arrosée transpire et reste proche de l'air ; une plante assoiffée en plein soleil peut monter
de +10 à +15 °C (`ECHAUFF_FEUILLE ≈ 12 °C`). Une plante à l'ombre ne chauffe pas.

Ces helpers sont **purs** et calculés une fois par plante et par semaine. Pas de nouveau
champ de grille.

## 4. La plage vivable

### 4.1 Niche d'espèce (couche 1, données)

Cinq attributs de classe dans `PlantBase` (`plants/base/familles.py`), surchargés par
espèce :

| Attribut | Sens |
|---|---|
| `t_froid_lesion` | sous ce seuil (nuit la plus froide), dégât de froid sans gel ; `None` = espèce non sensible |
| `t_gel_tendre` | limite de gel d'un tissu **non endurci** |
| `endurcissement_max` | °C gagnés à endurcissement complet (froid doux vécu, `cold_memory`) ; dormance comprise |
| `t_chaud_stress` | T_feuille au-delà de laquelle la plante cesse de croître et le pollen devient stérile |
| `t_brulure` | T_feuille au-delà de laquelle le tissu meurt (échaudage) |

`temp_min_growth` (stagnation) reste tel quel : c'est un seuil de **croissance**, pas de dégât.

### 4.2 Caractères génétiques (couche 2, registre du sprint ①)

| Caractère | Unité | Neutre | σ_A | Effet |
|---|---|---|---|---|
| `rusticite_froid` (refondu) | °C | 0 | 1,5 | abaisse `t_gel_tendre` |
| `limite_froid` (neuf, en queue) | °C | 0 | 1,0 | abaisse `t_froid_lesion` |
| `limite_chaud` (neuf, en queue) | °C | 0 | 1,5 | relève `t_chaud_stress` et `t_brulure` |

### 4.3 Plasticité (couche 3)

- **Endurcissement au froid** : l'expression liée à `cold_memory` existe déjà. Elle devient
  **additive en °C** : `endurci = endurcissement_max × (expression − 1)/(EXPR_MAX − 1)`.
- **Acclimatation à la chaleur** : nouvelle mémoire `heat_memory` (T_feuille au-dessus de
  `t_chaud_stress − 5`), même dynamique d'hystérèse que les autres. Elle relève les seuils
  chauds de 3 °C au plus. C'est réel (protéines de choc thermique).

Pour un caractère en °C, le phénotype vaut **génotype + plasticité** : `expressed_gene`
multiplicatif ne s'applique plus à ces caractères.

### 4.4 Limites effectives d'une plante

    lim_gel   = t_gel_tendre   − rusticite_froid − endurci
    lim_froid = t_froid_lesion − limite_froid
    lim_chaud = t_chaud_stress + limite_chaud + acclim_chaud
    lim_brul  = t_brulure      + limite_chaud + acclim_chaud

### 4.5 Compromis

Chaque °C de tolérance **au-delà du neutre** (somme des trois caractères génétiques, pas la
plasticité qui a déjà son coût) réduit la vigueur effective de `K_THERMO = 0,02` par °C, sur
le même chemin que `cout_defense`. Réel : sucres et protéines de protection coûtent de la
croissance.

## 5. La réponse de la plante (tronçon ③)

Une fois par plante et par semaine, tous stades confondus :

| Condition | Réponse | Cause (sémiologie) |
|---|---|---|
| nuit < `lim_froid` (espèces sensibles) | dégât **cumulatif** ∝ (lim_froid − nuit), via `erode` | `froid` |
| nuit < `lim_gel` | dégât ∝ (lim_gel − nuit)/`FROST_SEVERITY_REF`, médié par le couvert local (chemin `_mediated_damage` sans le filtre `semis`) | `gel` |
| T_feuille > `lim_chaud` | pas de croissance cette semaine + **pollen stérile** (nouaison bloquée cette semaine) | posture chaude |
| T_feuille > `lim_brul` | dégât ∝ excès, via `erode` | `brulure` |

**Ligneux.** Leur `endurcissement_max` est grand (dormance) : un pommier endurci tient
−30 °C en janvier, mais ses jeunes feuilles gèlent à −3 °C en avril. La perte de rameaux
reste en **D131**.

**Fin de la mort calendaire.** `_winter_transition` ne tue plus les `die`.
- **Sénescence de fin de cycle** des annuelles : elle démarre après la fin de leur floraison
  (horloge par plante `bloom_week` + `bloom_duration`) plus la maturation des graines
  (`fruit_semaines_maturation` de l'espèce ou un défaut). C'est un déclin interne, décrément
  direct comme la sénescence d'âge.
- **Bisannuelles** : même mécanisme, si leur floraison de l'an 2 passe par `bloom_week`.
  Sinon, garder la règle actuelle et le consigner.
- **Dormance** et **ralentissement des persistantes** : leur déclenchement suit l'entrée en
  hiver réelle (`SEMAINE_HIVER`) ou un seuil de `cold_memory`, plus la semaine 49.

**Dépôt de graines.** La graine qu'une annuelle déposait à sa mort calendaire
(`seed_bank.add`) doit continuer d'exister par la voie de reproduction normale. **Vérifier**
que les annuelles fructifient et dispersent déjà sans ce dépôt de mort ; sinon, déplacer le
dépôt à la mort par sénescence de fin de cycle.

## 6. Signes par paliers (tronçon ④)

Une **gamme continue**, lue sur les seuils mêmes du moteur (invariant DRY de
`sim/semiologie.py` : le signe ne ment jamais).

| Zone | Paliers (du plus doux au plus dur) |
|---|---|
| Froid | feuilles qui **pendent** (lim_froid + 3 °C) → teinte **violacée** (froid prolongé, `cold_memory` haute) → taches **translucides détrempées** (dégât de froid) → **noircissement** (gel) → **effondrement** (vitalité basse après gel) |
| Confort | feuilles **étalées, bien ouvertes** |
| Chaud | feuilles qui **se replient** de profil au soleil (lim_chaud − 3 °C) → **flétrissement de midi** (chaud + soif) → **bords jaunis** (> lim_chaud) → **brûlure** (> lim_brul) |

Le pont exporte une **posture thermique** ∈ [−1, 1] par plante, plus les marques
événementielles `froid`, `gel`, `brulure`. Le carnet consigne les premières observations
(« le basilic a noirci cette nuit »). L'encyclopédie (niveau 2) dit la frilosité en mots.

## 7. Niches de départ des espèces

Valeurs en °C [valeurs de départ, ordres de grandeur horticoles, non revérifiées espèce par
espèce, calibrage F5]. `—` = pas de dégât de froid sans gel. Gel endurci = `t_gel_tendre −
endurcissement_max`.

| Espèce | froid_lésion | gel tendre | endurc. max | chaud stress | brûlure |
|---|---|---|---|---|---|
| Basilic | 10 | −1 | 0 | 35 | 45 |
| Tomate | 10 | −1 | 0 | 32 | 45 |
| Poivron | 10 | −1 | 0 | 33 | 45 |
| Courgette | 10 | −1 | 0 | 35 | 46 |
| Haricot | 8 | −1 | 0 | 32 | 45 |
| Tournesol | 5 | −3 | 1 | 36 | 48 |
| Chanvre | — | −3 | 1 | 35 | 47 |
| Bourrache | — | −4 | 3 | 32 | 45 |
| Phacélie | — | −6 | 2 | 32 | 45 |
| Moutarde | — | −6 | 4 | 30 | 44 |
| Bourse-à-pasteur | — | −10 | 8 | 30 | 44 |
| Mâche | — | −10 | 10 | 25 | 42 |
| Seigle | — | −8 | 17 | 30 | 44 |
| Blé | — | −8 | 12 | 32 | 44 |
| Carotte | — | −5 | 5 | 30 | 44 |
| Ail | — | −8 | 10 | 30 | 44 |
| Trèfle | — | −8 | 10 | 30 | 44 |
| Minette | — | −8 | 10 | 32 | 45 |
| Consoude | — | −8 | 20 | 32 | 45 |
| Dactyle | — | −8 | 15 | 32 | 45 |
| Fétuque rouge | — | −8 | 15 | 30 | 44 |
| Pâturin annuel | — | −8 | 12 | 30 | 44 |
| Plantain lancéolé | — | −8 | 15 | 33 | 46 |
| Menthe | — | −5 | 15 | 32 | 45 |
| Molène | — | −8 | 15 | 35 | 48 |
| Armoise | — | −8 | 20 | 35 | 48 |
| Ortie | — | −6 | 20 | 30 | 44 |
| Pissenlit | — | −8 | 20 | 32 | 46 |
| Achillée millefeuille | — | −8 | 20 | 35 | 48 |
| Violette odorante | — | −8 | 15 | 28 | 42 |
| Fraisier | — | −6 | 12 | 30 | 44 |
| Rossolis | — | −6 | 15 | 30 | 42 |
| Sphaigne | — | −5 | 15 | 28 | 40 |
| Lavande | — | −6 | 10 | 38 | 50 |
| Thym | — | −8 | 10 | 40 | 52 |
| Lierre | — | −8 | 10 | 35 | 46 |
| Jasmin | — | −5 | 8 | 35 | 47 |
| Bambou traçant | — | −8 | 12 | 38 | 48 |
| Framboisier | — | −8 | 25 | 32 | 45 |
| Myrtille | — | −5 | 25 | 28 | 42 |
| Figuier | — | −3 | 12 | 40 | 50 |
| Pommier | — | −3 | 30 | 35 | 47 |
| Cerisier | — | −3 | 27 | 35 | 47 |
| Noyer | — | −2 | 25 | 38 | 48 |
| Chêne | — | −3 | 30 | 38 | 48 |
| Hêtre | — | −3 | 30 | 33 | 45 |
| Charme | — | −3 | 30 | 35 | 46 |
| Noisetier | — | −4 | 30 | 35 | 46 |
| Bouleau | — | −4 | 40 | 32 | 44 |
| Aulne | — | −4 | 35 | 32 | 44 |
| Saule | — | −4 | 40 | 33 | 45 |
| Sapin | — | −6 | 25 | 30 | 44 |

Une espèce ajoutée plus tard au catalogue reçoit sa ligne. Les défauts de `PlantBase` valent
ceux d'une herbacée tempérée (—, −6, 10, 32, 45).

**Effets attendus en Normandie** :
- le **basilic** souffre dès septembre-octobre (nuits < 10 °C), noircit aux premières gelées
  et meurt avant décembre ; le paillage et le voile retardent sa mort ;
- la **mâche** et le **seigle** passent l'hiver ;
- le **pommier** perd ses fleurs à une gelée tardive ;
- en canicule, une **violette** ou un **fraisier** assoiffés en plein soleil grillent,
  alors que les mêmes plantes, paillées et arrosées, tiennent.

## 8. Golden et perf

| Tronçon | Golden |
|---|---|
| ① températures extrêmes | **RE-FIGÉ** annoncé : le gel existant lit la nuit la plus froide |
| ② niche + caractères | **RE-FIGÉ** annoncé : clés de gènes neuves dans le digest + refonte de `rusticite_froid` |
| ③ réponse + fin de la mort calendaire | **RE-FIGÉ** annoncé, dérive large attendue : les annuelles changent de date de mort |
| ④ signes | **INTACT** (lecture pure) |
| ⑤ vue | **INTACT** |

Perf : O(1) par plante et par semaine (deux helpers purs, quatre comparaisons). Budget
≤ +2 % de tick par tronçon, **mesuré** au ① et au ③.

## 9. Hors périmètre

- D131 : perte de rameaux des ligneux au gel.
- D107 : fréquence des canicules (le sprint rend la canicule **mordante**, pas plus
  fréquente).
- D138 (e) : le gel marque le sol.
- Changement climatique, autres lieux (au BACKLOG).
