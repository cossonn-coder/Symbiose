# CONCEPTION — Humectation foliaire & les deux guildes cryptogamiques

**Statut** : **FIGÉE** le 2026-07-26 (skill `/conception`, arbitrages Nico QA/QB/QC).
**Origine** : amorce D38 « rosée nocturne & hygrométrie de l'air ».
**Rangement** : `vegetal/sante` — le sujet est une correction de la **pression
fongique**, pas un champ climatique (cf. §1.4).
**Sprint** : `sprints/vegetal/sante/sprint_humectation_foliaire/` — 6 tronçons.

---

## 1. Ce que cette conception corrige (et pourquoi elle n'est pas D38)

### 1.1 D38(a) « rosée » est CLOSE de fait

Vérifié au code, pas à la dette. `fields/ecofields/rosee.py` livre déjà tout ce que
la ligne D38 demandait :

- point de rosée calculé — `t_rosee = t_air − ECART_ROSEE_SEC(6.0) + GAIN_HUM_ROSEE(5.0)·hum_norm` ;
- **apport écrit dans `humidite`** (`rosee.py:84`, `eco.humidite.add(r, c, cond + gel)`) —
  c'était le point que l'amorce soupçonnait manquant : il ne manque pas ;
- continuum liquide / gelée blanche + fonte différée (`eco.givre`) ;
- `rosee_last` consommé par **trois** sites : faune abreuvée
  (`fields/population/resources.py:413`), captation foliaire
  (`sim/engine/croissance.py:284`), pont (`tools/simserver/serialize.py:441`).

Reliquats hors de ce sprint : rendu C# gouttes/givre (**D24**, absorbé ici au ⑥) et
dégât foliaire du givre (`GIVRE_SEVERITY_REF` réservée, bloqué par `_mediated_damage`
qui ne cible que le stade « semis » — reste en dette).

### 1.2 D38(b) « freine l'évaporation » est ABANDONNÉ — double comptage

L'amorce affirme que le VPD est « le troisième facteur, et le seul manquant ».
C'est inexact. `tick_hydrology` (`hydrologie.py:85-125`) porte déjà **trois** pilotes
d'évaporation :

| Terme | Constante | Sens |
|---|---|---|
| température | `EVAP_TEMP_COEF·max(0, T_sol − 11°C)` | chaud → assèche |
| rayonnement | `EVAP_RAD_COEF·(1 − nébulosité)` = 0.0042 | ciel clair → assèche |
| vent | `EVAP_WIND_COEF·vent[r,c]` = 0.0035 | vent → assèche |

Le VPD (déficit de pression de vapeur) n'est pas un quatrième terme : c'est le
**produit croisé des deux premiers** (pression saturante ∝ exp(T), déficit ∝ sécheresse
de l'air ≈ ciel clair). L'ajouter reviendrait à recalibrer `EVAP_RAD_COEF` sous un autre
nom — en payant un **re-figeage golden LARGE** sur la formule exacte qui a déjà tué un
pommier par asphyxie 57 ans trop tôt (**D39**), avec cascade sur `drought_memory`, la
sénescence et `test_senescence`.

**Décision : `tick_hydrology` n'est PAS touché par ce sprint.** Réduire le périmètre
plutôt que casser un équilibre durement calibré.

### 1.3 Pas de grandeur « hygrométrie » — l'objet de jeu est l'humectation

L'amorce propose trois formes (scalaire global / `GridField` plein / hybride) pour une
grandeur « hygrométrie de l'air ». **Aucune des trois n'est retenue.** L'HR de l'air est
un intermédiaire de calcul, pas un objet de jeu ; l'amorce le dit elle-même en §1.2 puis
l'oublie. Ce que le joueur observe et sur quoi il agit, c'est **l'eau posée sur les
feuilles**. Aucun `GridField` persistant neuf n'est créé.

### 1.4 Le vrai trou : un proxy faux, déjà en production, qui enseigne l'inverse du bon geste

`sim/effects/perturbations.py:216` (la fonction s'appelle `fungal_disease`) :

```python
hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)   # ← humidité du SOL
p = eco.disease_probability(r, c, base_rate=FUNGAL_BASE, family=plant.plant_class.family)
p *= hum_norm * (0.4 + density) * susc
```

**L'humidité du SOL sert de proxy à l'humectation du FEUILLAGE.** Et `arroser`
(`sim/actions/gestes.py:188`) n'écrit que `eco.humidite`, sans distinction pied/feuillage.
D'où la chaîne actuelle :

> `arroser` → `humidite` ↑ → `hum_norm` ↑ → **maladie fongique ↑**

Le joueur qui sauve une plante de la sécheresse **la rend malade**, par un chemin
biologiquement faux : arroser au pied ne mouille pas le feuillage et n'ouvre pas la
porte au mildiou. Le modèle enseigne aujourd'hui **l'inverse** de la règle permacole
(« arrose au pied, jamais sur les feuilles ») → **violation dormante de philo #6**.

**Second site du même défaut** : `infection_memory` (`croissance.py:316-317`) utilise le
même `min(1.0, hum/3.0)`, et alimente par plasticité le gène `resistance_pathogene`.
Les deux sites sont corrigés (tronçon ②).

### 1.5 Deux corrections d'inventaire

- `disease_probability` (`fields/ecofields/sol.py:118-144`) ne porte **aucun** terme de
  vent — l'amorce le supposait. Il ne porte que microbiome + inoculum familial. Le vent
  agit en aval, dans `fungal_disease` (`FUNGAL_VENT_DRY`, `_spore_load`).
- **H5 est un fait accompli, pas une question ouverte.** `fields/abri.py` baisse
  `eco.vent[r,c]` sous un brise-vent → le facteur `1 − FUNGAL_VENT_DRY·vent_local`
  remonte → maladie ↑. Le brise-vent favorise **déjà** la maladie depuis le sprint
  VENT ⑥, sans que ç'ait été décidé. Arbitrage Nico (QC) : **assumer et rendre lisible**.

---

## 2. Le modèle retenu

### 2.1 `wetness_memory` — l'état intermédiaire (par PLANTE)

Nouvelle mémoire physiologique sur `PlantInstance`, exactement sur le patron des six
existantes (`shade_memory`, `drought_memory`, `asphyxie_memory`, `cold_memory`,
`infection_memory`, `wind_memory`, `root_herbivory_memory`) :

```python
wetness_memory: float = 0.0   # durée d'humectation foliaire intégrée [0-1]
```

**Granularité PLANTE** (et non plot — Q5 de l'amorce) : c'est le *feuillage* qui est
mouillé, et la hauteur/densité de canopée conditionnent son séchage.
**Interdit d'emblée** : jamais par segment/organe (D29) — on ne rouvre pas un poste de
coût par plante × segments.

**Constante de temps — plus RAPIDE que les autres mémoires.** Les mémoires existantes
lerpent à 0.05 (~20 semaines : stress chronique). L'humectation se mesure en *heures* ;
à l'échelle du tick (1 semaine) le signal pertinent est « combien de nuits mouillées
cette semaine ». On veut néanmoins de l'inertie pour que « trois nuits douces et sans
vent » émerge comme critère de **durée** (règle de Mills / périodes de Smith) :

```python
WETNESS_MEMORY_LERP = 0.35      # montée/descente en ~3 semaines
```

**Décroissance garantie et borne haute** (philo #4, run éternel) : le lerp symétrique
vers un signal borné [0,1] garantit la fuite ; `max(0, min(1, …))` après chaque mise à
jour, comme toutes les autres mémoires. Aucune intégrale sans fuite.

### 2.2 Le signal d'humectation du tick — pur, dérivé, zéro RNG

Calculé dans `_update_physiology` (`sim/engine/croissance.py`), où **tout est déjà
chargé** — aucune lecture neuve, aucune passe de champ supplémentaire :

```
mouillage =   ROSEE_WET_GAIN    · min(1, capte / ROSEE_SURFACE_REF)     # rosée sur la canopée
            + PLUIE_WET_GAIN    · min(1, pluie_event / PLUIE_WET_REF)   # pluie de la semaine
            + ASPERSION_WET_GAIN· min(1, aspersion / DOSE_ARROSAGE)     # geste au feuillage

sechage   = (1 − VENT_WET_DRY · min(1, vent_effectif))
          × (1 − RAD_WET_DRY  · (1 − nebulosite))

humectation_sig = max(0, min(1, mouillage · sechage))
```

**Réutilisations, aucun recalcul** (règle « ne jamais recalculer dans un tick ») :

- `capte` — la rosée moyenne sur l'empreinte foliaire est **déjà calculée**
  (`croissance.py:286-288`) pour la captation foliaire. ⚠️ Elle est aujourd'hui sous le
  garde `if drought_stress > 0.0` : le tronçon ① la **remonte hors du garde** (le calcul
  de `relief`, lui, reste sous le garde → `drought_stress` inchangé → golden neutre).
- `vent_local` — déjà chargé (`croissance.py:271`).
- `nebulosite` — disponible dans la boucle (`boucle.py:95`, `nebul`) mais **pas encore
  passée** à `_update_physiology` (`boucle.py:381`) : le ① ajoute l'argument.
- `pluie_event` — déjà calculé par la boucle pour `tick_hydrology`.

### 2.3 L'aération émergente — le levier de milieu (philo #1)

Le vent ne pénètre pas un couvert dense. C'est ce qui transforme la géométrie du jardin
en levier :

```
vent_effectif = vent_local · (1 − COUVERT_WET_SHELTER · densite_locale)
```

où `densite_locale` combine la densité de canopée propre de la plante
(`plant_class.foliage_density`) et la densité de voisinage — `_local_density` **existe
déjà** (`perturbations.py:95`).

Conséquences émergentes, toutes des gestes de **milieu**, jamais d'action sur le vivant :

| Geste joueur | Chaîne | Effet |
|---|---|---|
| espacer / éclaircir | densité ↓ → vent_effectif ↑ → séchage ↑ | mildiou ↓ |
| tailler | canopée ↓ → idem | mildiou ↓ |
| arroser **au pied** | n'écrit plus `aspersion` | mildiou inchangé ✅ |
| arroser **au feuillage** | `aspersion` ↑ → mouillage ↑ | mildiou ↑, **oïdium ↓** |
| brise-vent | vent ↓ → séchage ↓ | mildiou ↑ (assumé, QC) |
| pailler | ne touche pas le feuillage | neutre sur l'humectation |

Aucun bonus/malus direct : l'eau se dépose, puis sèche. Flux → contrainte → réponse
(philo #2).

### 2.4 Les deux guildes cryptogamiques

**Attribut retenu — additif, pas exclusif** : plutôt qu'un enum de guilde qui forcerait à
reclasser les 27 espèces, on ajoute un **second scalaire** à côté de l'existant, sur
`PlantBase` (`plants/base/familles.py:91`) :

```python
fungal_susceptibility: float = 0.5    # EXISTANT — guilde « à eau libre »
oidium_susceptibility: float = 0.0    # NEUF — guilde « air humide, feuillage sec »
```

Pourquoi additif : **(i) rétrocompatible** — défaut 0.0 ⇒ aucun effet ⇒ golden neutre
pour ce chemin ; **(ii) biologiquement juste** — une espèce peut être sensible aux deux
(le pommier a tavelure *et* oïdium), ce qu'un enum interdirait ; **(iii)** aucune
réindexation d'`InoculumField` (l'amorce s'interrogeait : la réponse est non — il reste
indexé par famille, l'inoculum ne distingue pas la guilde).

**Le porteur d'oïdium existe déjà** : la **courgette** (`Zucchini`, `Cucurbitaceae`,
`plants/species/potageres.py:94`) est le cas d'école. Grandes feuilles molles,
`foliage_density = 0.60`, port étalé, fin d'été chaud — c'est exactement le profil.
Elle hérite directement de `PlantBase` (pas de classe famille `Cucurbitaceae`), donc son
`fungal_susceptibility` est au défaut 0.5. On lui pose `oidium_susceptibility = 0.9`.
**Aucune espèce nouvelle n'est ajoutée** — donc aucune dette de 5 voix neuves (la règle
« toute plante ajoutée = ses 5 voix » ne se déclenche pas ; la courgette a déjà les
siennes).

Second porteur léger, pour que la guilde ne soit pas mono-espèce : le **pommier**
(`oidium_susceptibility = 0.3`) — hors smoke golden, dérive neutre.

**La réponse oïdium** — l'inverse exact du mildiou :

```python
oidium_sig = (1 − wetness_memory) · chaleur_norm
p_oidium   = disease_probability(r, c, OIDIUM_BASE, family)
           · oidium_susc / expressed_gene("resistance_pathogene")
           · oidium_sig · (0.4 + density)
```

`chaleur_norm = min(1, max(0, (T_air − OIDIUM_T_REF) / OIDIUM_T_SPAN))`.

C'est la phénologie réelle sans exiger la moindre HR : **printemps mouillé → mildiou ;
fin d'été chaude et sèche → oïdium**. Et le dilemme fonctionne dans les deux sens —
aérer fait baisser `wetness_memory` donc **monter** l'oïdium ; asperger fait l'inverse.
Pas d'optimum unique (philo #1 : l'usure de la solution facile ; philo #6).

Le gène `resistance_pathogene` (D22b) médie les **deux** guildes — aucun gène neuf.

**Canal de bruit** : `_hash_noise(seed, week * 47, r, c)`. Inventaire vérifié au grep —
utilisés : `week·`{0,2,3,5,7,11,13,17,19,23,29,31,37,41,53,59} ; `week·43` réservé D41
(non consommé) ; **47, 61, 67 libres**. `fungal_disease` tire sur `week·13`.

### 2.5 `arroser` — le mode qui rend le geste juste

`arroser(game_state, player, eco, r, c, urgence=False, feuillage=False)` :

- `feuillage=False` (**défaut**) : comportement actuel **strictement inchangé** — écrit
  `eco.humidite` seul. Tous les appelants existants (pont, tests) restent bit-identiques.
- `feuillage=True` : écrit `eco.humidite` **et** `eco.aspersion_last` (carte transiente,
  remise à plat chaque tick comme `rosee_last`). Coût Vigueur **identique** — le choix
  est écologique, pas économique : on ne pénalise pas le mauvais geste par le prix, on le
  laisse produire sa conséquence (philo #6, apprentissage diffus).

---

## 3. Passe philosophie #1-#7

| # | Verdict |
|---|---|
| **#1** milieu | ✅ Tous les leviers sont des gestes de milieu : espacer, tailler, arroser au pied, ouvrir un brise-vent. Aucune action directe sur le vivant. |
| **#2** flux → contrainte | ✅ La chaîne est complète : eau déposée → `wetness_memory` → pression → réponse. Le garde-fou tient : le signal dépend de la **géométrie** (densité, abri, exposition), pas d'un modificateur d'espèce. |
| **#3** déterminisme | ✅ Tout pur et dérivé. Un seul canal neuf (`week·47`), vérifié libre. Aucun RNG vivant. |
| **#4** run éternel | ✅ Lerp symétrique vers un signal borné + clamp [0,1] : décroissance garantie, borne haute. Aucune intégrale sans fuite. |
| **#5** pas de chiffres | ✅ Feuillage luisant (humectation), taches différenciées mildiou/oïdium (**D33**), gouttes/givre (**D24**). ⚠️ **Piège d'ambiguïté traité** : sol humide et air/feuillage humide doivent avoir deux vocabulaires visuels francs — le sol s'assombrit, le feuillage perle et luit (croise D45c). |
| **#6** sagesse écologique | ✅ **C'est le cœur du sprint** : on corrige un modèle qui enseignait l'inverse du bon geste, et le dilemme mildiou/oïdium interdit la solution unique. |
| **#7** hétérogénéité | ✅ Restituée par la géométrie du jardin (couvert, abri, exposition) sans champ de bruit ni `GridField` neuf. |

**Règle « tout coexiste »** : la conception branche `rosee_last` (météo) × `eco.vent`
(abri) × `foliage_density` (végétal) × `disease_probability` (sol/microbiome/inoculum) ×
`resistance_pathogene` (génétique) × le geste joueur. Six acteurs déjà présents, aucun
nouveau champ.

---

## 4. Coût perf

**Négligeable, borné O(N plantes).** `wetness_memory` est une float mise à jour dans la
boucle `_update_physiology` **déjà existante**, à partir de valeurs **déjà chargées**
(`capte`, `vent_local`, `nebulosite`, `pluie_event`). `oidium_disease` est un second
tirage par plante, du même ordre que `fungal_disease`.

- Aucune passe de champ neuve · aucun `GridField` persistant neuf · **aucun O(N²)**.
- `eco.aspersion_last` : un `GridField` **transient** (remis à plat par tick, patron
  `rosee_last`) — coût mémoire d'une carte, coût CPU d'un `set` par geste.
- Budget attendu : **≪ +10 %** de tick. Le seul risque était l'humectation par
  segment/organe : **explicitement interdite** (§2.1).

---

## 5. Voix narratives

Aucune espèce nouvelle ⇒ **la règle des 5 voix ne se déclenche pas**. La prêle et la
vigne proposées par l'amorce sont **écartées de ce sprint** (la courgette suffit à
incarner l'oïdium) — la prêle reste une bonne candidate pour **D26**.

- **Encyclopédie** — concept transversal 3 niveaux « humectation du feuillage » :
  N1 *l'eau se pose sur les feuilles au petit matin* → N2 *rosée, séchage par le vent et
  le soleil, aération du couvert* → N3 *les deux guildes et le dilemme aérer/asperger*.
  Prolonge le concept « météo » et les pages P21/P22 existantes, ne repart pas de zéro.
- **Carnet** — causes neuves `humectation`, `mildiou`, `oidium` dans `CONCEPT_DE`
  (`sim/carnet.py:53`). Bascule interprétative au palier 3 :
  *« les taches sont venues après trois nuits sans vent — l'air ne séchait plus entre
  les feuilles »*.
- **Sémiologie** — signe `humectation` dans le registre (`sim/semiologie.py:207`),
  priorité **basse** (c'est un état, pas une souffrance — patron `acclimatation`).
- **Pages secrètes** — une page sur la rosée (« le pain du matin », les toiles perlées à
  l'aube, la rosée de mai). Optionnelle mais peu coûteuse.
- **Magazine** — rien de spécifique (aucune espèce neuve).
- **Signalétique de l'abri ambivalent** (QC) : le carnet interprétatif doit pouvoir
  **nommer** le confinement, pour que le joueur comprenne son brise-vent au lieu de le
  subir.

---

## 6. Découpage en 6 tronçons

| # | Objet | Golden |
|---|---|---|
| ① | `wetness_memory` posée + alimentée, **lue par personne** (inerte) | **NEUTRE** |
| ② | Bascule du proxy : `fungal_disease` + `infection_memory` lisent l'humectation | **RE-FIGÉ ANNONCÉ** |
| ③ | `arroser(feuillage=…)` + `eco.aspersion_last` + pont | **NEUTRE** |
| ④ | Guilde oïdium : `oidium_susceptibility` + `oidium_disease` + courgette/pommier | **NEUTRE** (à prouver) |
| ⑤ | Voix : encyclopédie, carnet, sémiologie, page secrète | **NEUTRE** |
| ⑥ | **Vue Godot** : pont, feuillage luisant, taches différenciées (D33), gouttes/givre (D24), banc F5 | **INTACT** |

**Un seul re-figeage, au ②**, et il est inévitable : corriger un proxy faux change le
comportement par construction. Il doit être **localisé et expliqué** — la pression
fongique cesse de suivre l'humidité du sol pour suivre l'eau réellement posée sur le
feuillage. Tous les autres tronçons sont neutres par construction (défauts inertes),
le ④ devant le **prouver** par isolation, pas le supposer.

Le ⑥ vue Godot est le dernier tronçon (**règle permanente** Nico 2026-07-03 : jamais de
rendu différé en dette).

---

## 7. Rattachement à la dette

| Réf | Effet de ce sprint |
|---|---|
| **D38** | **RÉÉCRITE** : (a) close de fait, (b) évaporation abandonnée (double comptage), (b) maladie devient ce sprint |
| **D24** | reliquat gouttes/givre **absorbé** au ⑥ |
| **D33** | sémiologie foliaire — **partiellement soldée** au ⑥ (taches mildiou vs oïdium) |
| **D22b** | `resistance_pathogene` médie les deux guildes — **aucun gène neuf** |
| **D27** | susceptibilité familiale — étendue d'un second scalaire additif |
| **D10** ✅ | `disease_probability(family)` reste le point de greffe unique ; `InoculumField` **non** réindexé |
| **D39** ✅ | alerte respectée : `tick_hydrology` **non touché** |
| **D41** 🟡 | patron mémoire→santé copié ; canal `week·43` **laissé** à D41, on prend `week·47` |
| **D45c / D46** 🟡 | piège de confusion sol/air traité au ⑥ (deux vocabulaires visuels francs) |
| **D26** 🟢 | prêle reste candidate, **hors** de ce sprint |
| **D40** 🟢 | plus de conflit de séquencement : ce sprint ne touche pas l'équilibre hydrique |
| Givre foliaire | reste en dette (`GIVRE_SEVERITY_REF`, bloqué par `_mediated_damage`) |
