# Conception — Rythmes et flux de la matière organique du sol (D77 + D40 → débloque D41)

> Sprint `meta/calibrage/sprint_rythmes_mo`. Suite directe du sprint
> CALIBRATION RÉALISTE (`conception_calibration_realiste.md`) : ce document
> traite le **D-cal** que son §6 avait explicitement différé — la calibration des
> **modulateurs de RYTHME** du microbiome/MO. Il absorbe D77 et D40 (voir
> découverte §1), et prépare le déblocage de D41 (§5).

---

## 1. Découverte cardinale — D40 est déjà codé, mais inerte, et D40 ≡ D77

Le catalogue de dette pose **D40** (rendre la décompo sensible à la température
Q10 et à l'humidité) et **D77** (recalibrer les modulateurs de rythme qui
divisent le microbiome par 3.0) comme deux chantiers distincts. **Le code montre
que c'est un seul.**

La sensibilité Q10 réclamée par D40 **existe déjà** : la fonction pure
`thermique.py::microbe_clim_factor(t_sol, hum_norm)` — cloche gaussienne de
température (optimum `MICROBE_T_OPT = 20 °C`, demi-largeur `MICROBE_T_TOL = 12`)
multipliée par une cloche d'humidité (montée linéaire jusqu'à `MICROBE_HUM_OPT`,
léger repli d'anoxie à saturation) — a été câblée dans `tick_decomposition`
(`matiere_organique.py:148`) par le sprint **météo→champs ④**.

**Mais elle est mécaniquement morte.** Le facteur climatique multiplie le terme
biologique `micro = microbiome / 3.0`, et le microbiome opère (banc 20 ans) en
**moyenne ~0,01–0,26** — il relaxe bas (équilibre ~0,05, plot riche ~0,3–0,5,
pics transitoires ~2,3). Divisé par 3.0, `micro` plafonne autour de **0,08**.
Résultat mesuré (`speed = 0.5 + micro·f_clim·0.5`, pH neutre, humidité optimale) :

| microbiome (plot riche) | hiver (5 °C) | été (20 °C) | swing saisonnier |
|---|---|---|---|
| 0,50 — **denom 3.0 actuel** | 0,517 | 0,583 | **+13 %** |
| 0,50 — **denom 0.6 proposé** | 0,587 | 0,917 | **+56 %** |

`f_clim` varie pourtant **×5** (0,21 à 5 °C → 1,0 à 20 °C), mais il module un
terme plafonné à ~0,08 : le socle abiotique 0,5 mange tout. Les deux promesses
— « la décompo gèle l'hiver, s'emballe l'été » (D40) et « le sol vivant
décompose jusqu'à 2× plus vite » (le commentaire du code lui-même) — sont
**non tenues**.

**Conséquence de conception : on ne calibre pas D40 séparément. C'est le
rescaling D77 qui l'allume.** Le seul levier est le dénominateur.

## 2. Le mismatch d'échelle — rappel du diagnostic CALIBRATION RÉALISTE

Le sprint précédent a établi (son §2.1) que le littéral `microbiome / 3.0` porte
**deux sémantiques confondues** :

- **Référence de SATURATION** (dynamique du champ) — `croissance.py:245`, le
  feedback exsudats `× (1 − micro_norm)`, qui **fixe l'équilibre** vers lequel le
  microbiome converge. La changer déplacerait la trajectoire du champ lui-même.
- **Référence d'EFFET/RYTHME** (lecture du champ) — « combien de microbiome =
  plein effet ». C'est **elle** qui est mal calée (3.0 vs plage réelle ~0,5).

CALIBRATION RÉALISTE a réaligné les **readers d'EFFET destinés à la VUE et à
l'uptake/maladie** (`uptake`, `sol.py:140` maladie, `sol.py:157` vitalité, qi)
sur une constante dédiée `MICROBE_EFFECT_REF = 0.6`, et a laissé — délibérément,
§6 — les **modulateurs de RYTHME** sur `/3.0`. Ce sont eux, ici.

Une nuance déjà tranchée et RECONDUITE : `om_stable / 5.0` est **correct** (le
banc 50 ans le voit monter 0,15 → 2,66, accumulateur centennal ; jeune sol lit
bas = philo #7). **On n'y touche pas.**

## 3. Design — recalibration ciblée, trois catégories

On introduit une constante **neuve** `MICROBE_RHYTHM_REF = 0.6`, distincte de
`MICROBE_EFFECT_REF` (même valeur au départ). Rationale : découpler le réglage de
la **dynamique MO** du réglage de la **lisibilité de la vue** — re-tuner l'un ne
reshapera jamais l'autre en douce (la thèse « séparer saturation et effet » du
doc précédent, appliquée un cran plus profond).

Les 7 sites `microbiome / 3.0` se répartissent en trois catégories :

### A — readers de rythme « sol vivant » → migrent vers `MICROBE_RHYTHM_REF`
| Site | Rôle | Cap `min(1.0,·)` |
|---|---|---|
| `matiere_organique.py:96` `decomp_speed` | fragmentation squelettes | **à AJOUTER** |
| `matiere_organique.py:133` `tick_decomposition` | décompo principale (**site D40**) | **à AJOUTER** |
| `sol.py:81` `tick_soil_memory` | mémoire rapide bio (poids 40 %) | **à AJOUTER** |
| `fields/population/resources.py:316` | ressource lombric | déjà présent |
| `fields/ecofields/allelopathie.py:43` | détox microbienne | déjà présent |

> ⚠ **Piège vérifié** : le champ microbiome a `max_val = 3.0` (`grids.py`). À
> `/3.0` le quotient reste ≤ 1 (cap superflu) ; à `/0.6` un pic de plot atteint
> **5,0** → sans `min(1.0,·)` la décompo divergerait (masses négatives /
> oscillation). Le cap devient **obligatoire** aux trois sites qui ne l'ont pas.

### B — ancre de SATURATION → INCHANGÉE
`croissance.py:245`, feedback exsudats `(1 − micro_norm)`. Reste `/3.0`. La
toucher déplacerait l'équilibre du champ (confirmé Nico). C'est ce qui **borne**
la dérive du microbiome lui-même dans le golden re-figé.

### C — comparateur à seuil → rescalé ET seuil re-dérivé
`perturbations.py:438`, bascule létale herbivorie : `micro_norm =
min(1, microbiome/3.0)` comparé à `HERBIVORY_LETHAL_MICRO = 0.20`. Aujourd'hui
micro_norm ~0,017 < 0,20 → « sol mort » **toujours vrai** → dégâts d'herbivorie
**toujours doublés** (calibration cassée). Après migration vers `0.6`,
re-dériver `HERBIVORY_LETHAL_MICRO` pour que **seul un sol réellement dégradé/
stérile** (microbiome proche de 0, post-bêchage) déclenche le doublement — le sol
d'équilibre sain (~0,05) ne doit PAS être « mort ». Valeur exacte fixée au banc
au tronçon d'implémentation (intention prescrite, nombre mesuré).

## 4. Perf & golden

- **Perf : neutre.** Pur changement de dénominateur sur des lectures existantes —
  zéro boucle, zéro champ neuf. Le cap `min(1.0,·)` est un test scalaire.
- **Golden : re-figeage LARGE, assumé et annoncé.** La décompo pilote la cascade
  fresh → active → stable → minéralisation N/P/K → humus → vitalité : tout l'aval
  se déplace. L'ancre B préservée limite la dérive directe du champ microbiome,
  mais le monde re-fige largement. Un seul re-fige par tronçon, attribué.

## 5. Ce que ça débloque — D41 (mesuré, pas gravé ici)

D41 (mort par carence édaphique chronique) était bloquée : l'uptake vide N/P/K
plus vite que la minéralisation ne renouvelle → `qi_local ~0,014` même sur jardin
sain → favorabilité de base trop basse pour une voie « chronique saine » (un
signal qui doit être ≈ favorable en conditions normales, comme
`drought_memory ≈ 0`). En relevant la vitesse de minéralisation sur sol vivant,
la **ligne de base NPK/favorabilité d'un jardin sain remonte**.

**Décision (Nico) : ce sprint DÉBLOQUE + MESURE, il n'implémente pas D41.** On
ne peut pas concevoir la courbe de mort contre un sol qui n'a pas encore été
recalibré. Le tronçon ③ mesure la nouvelle distribution de **favorabilité =
Liebig(min NPK) × fenêtre pH, calculée DIRECTEMENT** (pas le `qi_local` épuisé)
sur jardin sain, et documente si la précondition de D41 est atteinte. Si oui,
D41 part en `/conception` de suivi, conçue contre le sol **mesuré**, avec sa
recette déjà prête (`starvation_memory`, `soil_starvation_damage` miroir de
`shade_stress_damage`, signe sémio `famine`).

## 6. Découpage en tronçons (3)

1. **① Décompo cœur** — `matiere_organique.py:96` + `:133` migrent vers
   `MICROBE_RHYTHM_REF` (constante neuve) + cap `min(1.0,·)`. C'est le site D40 :
   la décompo devient saisonnière et sensible au sol vivant. **Golden re-fige
   LARGE** (cascade MO → NPK → humus → vitalité). Vérif : le swing saisonnier de
   décompo est mesurable (mémo dans `00_etat.md`).
2. **② Readers périphériques + herbivorie** — `sol.py:81` (+cap),
   `resources.py:316`, `allelopathie.py:43` migrent vers `MICROBE_RHYTHM_REF` ;
   `perturbations.py:438` migre + `HERBIVORY_LETHAL_MICRO` re-dérivé au banc.
   Ancre B (`croissance.py:245`) et `om_stable/5.0` **NON touchés**. **Golden
   re-fige** (soil_memory → succession ; herbivorie si exercée).
3. **③ Banc de mesure + vérif vue F5** — étend `tools/banc_calibration.py` (ou
   sonde dédiée) pour mesurer, sur jardin sain post-recalibration : distribution
   microbiome → décompo saisonnière → NPK → **favorabilité D41 directe**. Vérifie
   au **F5 Godot** que les heatmaps F6 (om/npk/microbiome) et l'accumulation
   saisonnière de litière reflètent la nouvelle dynamique (D40 enfin visible :
   litière qui s'accumule l'hiver, se recycle l'été). **Golden INTACT** (mesure
   + observation, aucun champ/rendu neuf attendu ; si une heatmap manque, la
   câbler côté `FieldOverlay`). Livre le verdict de précondition D41.

## 7. Ce qu'il ne faut PAS faire

- Ne PAS toucher `croissance.py:245` (ancre de saturation B) ni `om_stable / 5.0`
  (4 sites : `matiere_organique:223`, `hydrologie:144`, `sol:85`, `sol:160`).
- Ne PAS oublier le cap `min(1.0,·)` aux trois sites A qui ne l'ont pas (piège
  `max_val = 3.0`).
- Ne PAS implémenter D41 (mort édaphique) dans ce sprint — seulement mesurer sa
  précondition.
- Ne PAS lancer `test_epaisseur_500ans` (interdit). La stabilité long-horizon se
  vérifie au banc 20 ans du ③, pas à 500.
- Ne PAS forcer un re-figeage non prévu : si un tronçon laisse le golden
  inattenduement NEUTRE, s'arrêter et le signaler (ne pas re-capturer à l'aveugle).
