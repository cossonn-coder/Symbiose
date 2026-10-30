# Conception — Météo / Climat + signes diégétiques (SYMBIOSE)

> **Document de conception. Aucun code écrit.** Spec de référence pour le
> futur sprint d'implémentation météo (qui sera découpé en sous-sprints et
> devra préserver / re-figer `tests/test_golden.py`).
>
> Issu du **Sprint conception météo** (2026-06-03). Couvre la dette **D16**
> (forecast) et la catégorie **Z2** (signes diégétiques). Climat de référence :
> Normandie ~49°N, océanique tempéré.

---

## 0. Le constat de départ (et le pivot qui structure tout)

Le système météo **actuel** (`sim/engine.py`, fonction `tick_semaine`) tire
l'aléa de saison avec :

```python
meteo = random.choice(ALEAS_METEO)
```

`random.choice` est un **RNG live** : il consomme l'état global de `random`.
Le golden ne reste déterministe que parce que `main.py` et les tests appellent
`random.seed(42)` avant de tourner — béquille fragile qui **viole la philo #3**
(déterminisme = seed global + hash spatial, jamais de RNG vivant). Tout le reste
du moteur (perturbation, sénescence, reproduction) a déjà migré vers
`_hash_noise(seed, week, r, c)` ; la météo est le dernier îlot non conforme.

**Pivot de cette conception : remplacer le tirage par une fonction pure
`weather_at(seed, week)` à base de `_hash_noise`.** Ce seul changement débloque
gratuitement le forecast (D16), les signes (Z2) et la prévisibilité au
transcendant — parce qu'une fonction pure du temps est *évaluable en avance sans
faire avancer la simulation*.

> **Principe directeur, valable partout dans ce doc :** la météo est
> **intégralement déterministe**. La maîtrise ne change pas *ce qui arrive*,
> seulement *combien le joueur sait le lire*. L'imprévisibilité ressentie est
> **informationnelle** (UX), jamais simulatoire.

---

## 1. Modèle climatique déterministe

Trois échelles de temps superposées, toutes dérivées du seed global — aucune
n'utilise `random`.

### 1.1 Climat normal saisonnier (lisse, 100 % prévisible)
La « toile de fond » : des **normales** fonction de `week_in_year` (1–52), pas
des événements. Deux sinusoïdes calées sur la Normandie :

- **Température normale** : minimum semaine `W_T_MIN` = 45 (≈ fin janvier),
  maximum ~semaine 19 (≈ fin juillet). Convention **équinoxe** : wiy 1 ≈ 20 mars
  (D122, source unique `data/code/calendrier.py`, table mois → semaine dans
  [`conception_calendrier_unique.md`](conception_calendrier_unique.md) §4 ; avant
  D122 le minimum était en wiy 4, calendrier au 1ᵉʳ janvier).
  `temp_norm(w) = T_moy − T_amp · cos(2π·(w − W_T_MIN)/52)` — p.ex. `T_moy ≈ 11 °C`,
  `T_amp ≈ 7 °C` (océanique = faible amplitude, hivers doux, étés frais).
- **Pluviométrie normale** : océanique → pluie toute l'année, **maximum
  automne/hiver**, minimum fin de printemps. Sinusoïde décalée, jamais nulle.

Aucune surprise : c'est le rythme des saisons, déjà à demi présent via
`BASE_RAIN` et les 4 saisons de `engine.py`. On le rend explicite et continu.

### 1.2 Dérive interannuelle (lente, multi-années)
On **réutilise `climate_stress(year_fraction, phase)`** déjà dans
`fields/noise.py` (oscillation ±`CLIMATE_AMPLITUDE`=0.080, `phase` dérivée du
seed). Elle module légèrement la toile de fond : certaines années plus
sèches/fraîches, sur plusieurs ans. C'est ce qui donne à un terrain « son
caractère » (philo #7) sans aucun stockage.

### 1.3 Événements météo hebdomadaires (le « bruit » discret)
Une fonction pure tire l'événement de chaque semaine :

```
occ  = _hash_noise(seed, week, K_OCC,  0)   # un événement, oui/non
pick = _hash_noise(seed, week, K_PICK, 0)   # lequel, pondéré par la saison
mag  = hash_gauss (seed, week, K_MAG,  0)   # intensité (loi normale)
```

`K_OCC / K_PICK / K_MAG` = coordonnées-sentinelles réservées (hors de la grille
des plots, comme un canal dédié) → décorrélées des tirages de sol. **Catalogue**
et **saisonnalité** :

| Événement | Saisons probables | Nature | Impact dominant |
|---|---|---|---|
| **Beau temps / Calme** | toutes (cas par défaut) | ponctuel | aucun |
| **Gelée tardive** | printemps (sem. 14–19) | ponctuel, bref | tissu tendre exposé |
| **Canicule** | été (sem. 22–32) | ponctuel, 1–2 sem. | température↑, humidité↓ |
| **Sécheresse** | été–début automne | **état multi-semaines** | pluie suspendue → humidité↓ lente |
| **Tempête / vent fort** | automne, hiver, équinoxes | ponctuel | perturbation spatiale, verse les hautes plantes |
| **Grêle** | fin printemps / orages d'été | ponctuel, **localisé** | patch de feuillage abîmé |
| **Pluie prolongée** | automne, hiver | état multi-semaines | humidité↑ forte → risque fongique |
| **Redoux** | hiver | ponctuel | température↑ → réveil prématuré de dormance |

Distinction de modélisation : **événement ponctuel** (choc d'une semaine : gel,
grêle, tempête) vs **état climatique** (tendance de plusieurs semaines :
sécheresse, pluie prolongée). Un état n'est pas re-tiré chaque semaine ; il se
*déduit* de la fonction pure sur une fenêtre (p.ex. « sécheresse » = `rain_norm`
bas **et** dérive interannuelle sèche **et** pas de pluie tirée depuis N
semaines — tout calculable sans état stocké).

---

## 2. Couplage aux champs écologiques (flux → contrainte → réponse émergente)

Règle absolue (philo #1/#2) : **la météo agit sur le MILIEU, jamais en
bonus/malus direct sur la plante.** Chaque événement = un (ou des) delta(s) de
champ via `apply_weather`, plus éventuellement une **durée**. La réponse
biologique *émerge* des mécanismes déjà en place (`drought_memory`,
`disease_probability`, seuils de croissance `ok_hum/ok_light`, conflits,
nécromasse).

### 2.1 Température — décision : **champ ambiant (Option B)**
Le moteur n'a aujourd'hui **pas de champ température** : la croissance ne se gate
que sur humidité + lumière (`_avancer_stades`). Or la météo est d'abord une
affaire de température. **Décision actée (Sprint conception météo, 2026-06-03) :
ajouter un `GridField temperature` ambiant**, piloté comme `lumiere` /
`disturbance` (déjà le patron du moteur) :

- la météo **écrit** dans `temperature` (deltas transitoires) ;
- `_avancer_stades` lit un nouveau gate `ok_temp = temp >= seuil_espèce` →
  `can_grow = ok_hum and ok_light and ok_temp` ;
- l'évaporation (`tick_hydrology`) se couple à la température (chaud → évapore
  plus) ;
- gel / redoux / canicule deviennent des **deltas de température propres** →
  réponse émergente, plus de voie « malus direct ».

> **Coût assumé :** ajouter `ok_temp` modifie le gate de croissance → le golden
> devra être **régénéré une fois puis re-figé** dans le sprint d'implémentation.
>
> **Alternative écartée (Option A — température implicite, sans champ stocké) :**
> plus légère (ne touche pas le gate), mais gel et redoux deviennent acrobatiques
> à modéliser proprement (rien où écrire « il fait −2 °C cette semaine »). Notée
> ici pour mémoire au cas où l'implémentation révélerait un coût golden trop lourd.

### 2.2 Table de couplage (événement → champ → réponse émergente)

| Événement | Agit sur le milieu | Réponse biologique émergente |
|---|---|---|
| **Canicule** | `temperature`↑ (transitoire) ; évaporation↑ → `humidite`↓ | `drought_memory` monte (physiologie existante) → croissance stagne |
| **Sécheresse** | `BASE_RAIN` suspendu plusieurs sem. → `humidite`↓ lente | stress hydrique cumulé ; semis fragiles meurent → nécromasse |
| **Gelée tardive** | `temperature`↓ < 0 (transitoire), **tamponnée par le paillage** | dégât tissulaire **médié par gène de rusticité × protection** (voir 2.3) |
| **Tempête / vent** | `disturbance`↑ (spatial) ; paillage dispersé (rondelle −) ; `humidite`↓ légère | hautes plantes versées ∝ hauteur (gène) si non tuteurées ; perturbation rouvre des niches |
| **Grêle** | `disturbance`↑ **localisé** (patch via hash spatial) | feuillage exposé abîmé là où non couvert ; localité = hétérogénéité |
| **Pluie prolongée** | `humidite`↑ forte, durable | `disease_probability` / fonte (`DAMPOFF`) montent (déjà branchés) → maladie émergente |
| **Redoux** | `temperature`↑ (hiver) | dormance rompue prématurément → vulnérabilité si gel revient (émergent) |

### 2.3 Le cas délicat : gel, grêle, verse — n'est-ce pas un malus direct ?
Aujourd'hui « Gelée tardive » fait un `ReduceHealth` direct sur les semis
(mode `health` dans `appliquer_alea`) — à la limite de la philo #2. La
**réécriture conforme** : le gel pose une contrainte *de milieu* (température
basse transitoire) ; le dégât subi par un individu **dépend de son état et de
son génotype** :

```
dégât = sévérité_gel × (1 − rusticité_gène) × (1 − protection_paillage_local)
```

Toujours « flux → contrainte → réponse », pas un malus plat : deux plantes côte
à côte réagissent différemment selon leur gène de rusticité et le paillage du
joueur. Idem **verse** (∝ gène hauteur × absence de tuteur) et **grêle**
(∝ exposition × absence de voile). Le **gène de rusticité au froid** est à
ajouter au vecteur génétique (`plants/genetics.py`, extensible par design) —
petit chantier couplé à l'implémentation.

---

## 3. Forecast (D16) — le cadeau de la fonction pure

Puisque `weather_at(seed, week)` est **pure et sans état**, prévoir = **l'évaluer
en avance**. Aucun « tirage décalé » à stocker, aucun RNG à espionner :

```python
def forecast(seed, week, horizon=2):
    return [weather_at(seed, week + k) for k in range(1, horizon + 1)]
```

- **Cohérence garantie par construction** : la semaine venue, l'engine calcule
  *la même fonction* → ce qui était prévu *est* ce qui arrive. Impossible que
  prévision et réalité divergent (contrairement à un tirage stocké qu'on
  pourrait oublier de rejouer).
- **Reproductible / déterministe** : même seed → même climat à 500 ans,
  rejouable (utile pour partager une « école de départ » entre amis via la seed
  d'origine persistée).
- **Structure de donnée** : un petit `@dataclass WeatherEvent(kind, intensity,
  duration_weeks, scope)`. Pas de table mutable.

> **Reformulation de D16 :** l'énoncé original (« décaler le tirage en forecast
> 1-2 semaines en avance ») supposait un tirage à état. Avec la fonction pure, le
> forecast **tombe gratuitement** — c'est une simplification, pas un système à
> construire. D16 est donc « conçu, simplifié par la déterminisation ».

Les **signes** (§4) lisent `forecast(seed, week+1..2)`. L'oiseau fuit parce
qu'une tempête est dans le *futur déterministe*, pas parce qu'un dé est tombé.

---

## 4. Signes diégétiques (Z2)

Un signe = un **indice perceptif** rendu dans le monde, 1–2 semaines *avant*
l'événement annoncé. Aucune icône calendrier (philo #5).

### 4.1 Table signe → événement

| Événement à venir | Signes diégétiques |
|---|---|
| **Gelée tardive** | ciel clair et étoilé au crépuscule · brume rasante au petit matin · **anneau (halo) autour de la lune** |
| **Canicule / sécheresse** | ciel blanc laiteux · insectes au ras du sol · **sol qui craquelle** · feuilles qui se recroquevillent |
| **Tempête / vent** | oiseaux qui se taisent puis s'agitent / volent bas · le vent tourne · ciel qui vire au plomb |
| **Grêle** | nuages d'enclume sombres · chute brutale de la lumière · calme lourd « avant l'orage » |
| **Pluie prolongée** | ciel bas et gris constant · escargots et limaces qui sortent · hirondelles qui rasent le sol |
| **Redoux** | fonte, gouttes · oiseaux qui se remettent à chanter |

Plusieurs signes par événement → redondance perceptive ; certains signes sont
**ambigus** entre deux événements proches — voulu : ça crée l'incertitude
d'interprétation des débuts.

### 4.2 Fiabilité croissante — *sans toucher au signal*
Le signe est **toujours montré** quand l'événement est dans l'horizon (signal
parfait). Ce qui change avec la maîtrise, c'est **l'interprétation** :

- **Sous le seuil de maîtrise** : le joueur *voit* l'anneau lunaire, mais le
  carnet ne le **nomme pas**. À lui de corréler « anneau → souvent gel » par la
  méthode scientifique (observer → hypothèse → test → conclusion). Les signes
  ambigus restent indiscernables. → **fiabilité perçue faible**, alors que le
  signal est parfait.
- **Au seuil de maîtrise** : carnet + encyclopédie **basculent en
  interprétatif** sur la météo → le signe est annoté avec son sens et un horizon
  (« anneau lunaire → gel probable sous 1–2 nuits »). → **fiabilité élevée**.

### 4.3 La part ~20 % imprévisible
Un masque déterministe décide si un événement **émet un signe** :

```
signé = _hash_noise(seed, week, K_SIGN, 0) > 0.20   # ~80 % signés
```

→ ~20 % des événements arrivent **sans préavis** (ou avec un signe trompeur)
tant qu'on n'est pas transcendant. **Au transcendant**, le palier lève le masque
côté UI : même les 20 % deviennent lisibles → *tout devient prévisible*. Crucial :
**l'événement lui-même ne change pas** — seule la *visibilité de son signe*
dépend de la maîtrise. Le déterminisme simulatoire est intact (philo #3) ;
l'imprévisibilité est purement UX.

---

## 5. Palier de maîtrise « météo / climat » (concept transversal, 5 paliers)

| Palier | Ce qui se débloque |
|---|---|
| **Découverte** | signes visibles mais **non nommés** ; carnet purement descriptif (« ciel laiteux observé ») |
| **Investissement** | le carnet **regroupe les co-occurrences** récurrentes (« plusieurs fois : anneau lunaire puis gel ») — proto-corrélations, encore des hypothèses |
| **Maîtrise** *(seuil clé)* | carnet + encyclopédie **interprétatifs** : signe → sens + horizon explicites. La météo devient lisible. |
| **Expertise** | horizon fiable à 2 semaines · indices d'**intensité** (« forte gelée ») et de **localité** (patch de grêle) → préparation mieux ciblée |
| **Transcendant** | les **~20 % sans signe** deviennent lisibles → *tout est prévisible*. Récompense rare qui cristallise la non-action. |

**Progression (méthode scientifique)** : la maîtrise avance en *vivant et en
interprétant correctement* des cycles météo — p.ex. un compteur d'« événements
de chaque classe traversés avec préparation pertinente », ou de corrélations
signe→événement confirmées dans le carnet. Principe seulement (chiffres =
calibrage post-test).

---

## 6. Articulation Vigueur — préparation (figé) vs réaction (temps réel)

Levier pédagogique central (philo #1 : l'usure de la solution facile) —
**anticiper coûte peu, réagir dans l'urgence coûte cher.** Boucle complète :
*lire les signes → préparer à bas coût en planification → éviter le sauvetage
réactif coûteux.*

### 6.1 Préparation (temps figé, Vigueur modérée) — structures persistantes
Posées *avant* la saison / avant l'événement prévu. Toutes **agissent par le
milieu** (rondelles ou modificateurs locaux qui amortissent les deltas de
`apply_weather`) :

- **Paillage profond** → tamponne la température du sol (gel) + retient
  l'humidité (sécheresse) + résiste à la dispersion par le vent.
- **Voiles d'hivernage / cloches** → protègent une zone du gel et de la grêle.
- **Brise-vent** (haie, claie) → réduit la `disturbance` locale du vent,
  persistant.
- **Ombrière** → atténue la canicule sur une zone.
- **Buttes / drainage** → gèrent la pluie prolongée (excès d'humidité,
  asphyxie).
- **Réserve d'eau / arrosage anticipé** → tampon avant sécheresse.

### 6.2 Réaction (temps réel, saison, Vigueur élevée — urgence)
Gestes ponctuels quand l'événement frappe (ou n'était pas prévu — les 20 %) :

- Arrosage ciblé d'une plante en détresse (canicule).
- Secouer une branche givrée / couvrir à la main en catastrophe (gel surprise).
- Tuteurer / redresser une plante couchée par le vent.
- Couvrir précipitamment avant la grêle.
- Récolter en urgence les fruits mûrs avant la tempête.

Le **coût élevé** de la réaction est la « perturbation » de la philo #1 : agir
directement sur le vivant dans l'urgence épuise la Vigueur. La récompense de la
maîtrise = passer du registre réactif (cher) au registre préparatoire (sobre).
Chiffres de Vigueur = calibrage post-test (cf. D11, non encore implémenté).

---

## 7. Petits chantiers induits (pour le sprint d'implémentation, pas ce sprint)

1. Remplacer `random.choice(ALEAS_*)` par `weather_at(seed, week)` pure → **et
   retirer la béquille `random.seed(42)`** (le golden devra être régénéré une
   fois, puis re-figé).
2. Ajouter le champ `temperature` (`GridField`) + un gate `ok_temp` dans
   `_avancer_stades` ; coupler l'évaporation à la température.
3. Ajouter un **gène de rusticité au froid** au vecteur génétique (extensible
   par design).
4. Réécrire `appliquer_alea` pour router gel / grêle / verse via
   milieu × gène × protection (fin de la voie `health` directe).
5. Implémenter `weather_at`, `forecast`, le `WeatherEvent`, le masque de signe.
6. Le tout **doit préserver / re-figer `tests/test_golden.py`** (sprint découpé
   en sous-sprints autosuffisants, cf. workflow CLAUDE.md).
</content>
</invoke>
