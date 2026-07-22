# CONCEPTION — Santé continue & constitution de résilience

> Figé le 2026-07-13 (`/conception`). Remplace les PV plats `health: int 0–3`
> (uniformes toutes espèces) par une **vitalité continue [0,1]** différenciée par
> espèce, via une **constitution `resilience_base` data-driven par espèce** (PAS
> un gène). Complète la couche de tolérances de niche (grêle, déficit racinaire)
> et replie le fix du **canal chronique campagnol** (herbivorie racinaire → perte
> d'uptake, couplage mycorhize, annélation létale conservée).
> Dette : **D75**. Sprint : `sprints/vegetal/sante/sprint_sante_resilience/`.

## 0. Motivation

Le modèle actuel `health: int = 3` (3 sain / 2 affaibli / 1 malade / 0 mort) est
**plat et uniforme** : toutes les espèces encaissent et récupèrent à la même
vitesse, par paliers entiers. Deux défauts :

1. **Granularité entière** — le moteur lui-même (`mortalite.py:356`) déplore que
   « le gène départage surtout aux seuils » : une plante rustique encaisse 0 là
   où une fragile perd 1, rien entre les deux.
2. **Aucune constitution d'espèce** — un audit (§2) montre que la « coriacité »
   d'espèce n'existe aujourd'hui que pour 2 voies (ombre `shade_tolerance_base`,
   fongique `fungal_susceptibility`). Pour sécheresse/froid/asphyxie/vent/grêle/
   campagnol/mortalité, **aucune espèce n'est plus robuste qu'une autre**.

## 1. Vitalité continue `[0,1]`

- `PlantInstance.vitalite: float = 1.0` (renomme `health`). 1.0 = sain neuf,
  0.0 = mort.
- Property **`etat`** : discrétise `vitalite` en {sain / affaibli / malade / mort}
  pour tous les lecteurs discrets et la sémiologie (préserve la sémantique 0-3).
  Seuils (miroir `k/3`) : sain `> 2.5/3 ≈ 0.833`, affaibli `(1.5/3, 2.5/3]`,
  malade `(0, 1.5/3]`, mort `≤ 0`.
- `is_alive = vitalite > 0`.
- **Correspondance d'échelle** : ancien `h ∈ {0,1,2,3}` ↔ `vitalite = h/3`.
  `VITALITE_STEP = 1/3` convertit les décréments/gains entiers `±1` → `±1/3` : à
  constitution neutre et sans dégât médié fractionnaire, la vitalité **suit
  exactement** `health/3` d'antan. La dérive golden vient de deux sources isolées :
  (a) les dégâts médiés (gel/grêle/vent) perdent leur **plancher entier**
  (`int(effective/DAMAGE_STEP)` → continu) ; (b) la constitution d'espèce (②).

## 2. Deux couches distinctes — niche vs constitution (audit + décision Nico)

**Audit des gènes existants** : les 6 tolérances agissent chacune sur la
**susceptibilité d'UN stresseur précis** (à la source du dégât) —
`tolerance_secheresse`, `tolerance_ombre`, `tolerance_asphyxie`, `rusticite_froid`,
`resistance_pathogene`, `port_trapu`. Elles encodent la **niche** (une plante du
désert tolère la sécheresse mais pas l'ombre). **Non redondantes entre elles.**

Un gène `resilience` **générique** ferait doublon : il diviserait toute érosion,
donc doublerait chaque tolérance sur son propre stresseur. **Écarté.** À la place,
deux couches à des **niveaux différents du pipeline** :

### Couche 1 — Tolérance de NICHE (par stresseur) : « ce stresseur passe-t-il ? »

Filtre de **susceptibilité À LA SOURCE** du dégât (`suscept = 1/tolérance`).
- **Gènes individuels** (plastiques, existants) : les 6 ci-dessus. Inchangés.
- **Bases d'espèce** existantes : `shade_tolerance_base` (par strate),
  `fungal_susceptibility` (0.2 aromatique → 0.6 adventice).
- **Niches MANQUANTES à compléter** (base d'espèce data-driven, **SANS nouveau
  gène** — décision Nico, zéro croissance de `GENE_NAMES`) :
  - **grêle** → `hail_resistance_base(espèce)` : aujourd'hui le dégât de grêle
    (`_mediated_damage`, `gene_name=None`) n'est médié par RIEN. On branche une
    susceptibilité d'espèce (feuilles petites/coriaces résistent ; grandes feuilles
    tendres se déchirent). Divisor à la source, comme `resistance_pathogene`.
  - **déficit racinaire** (campagnol) → `root_loss_tolerance_base(espèce)` : module
    la conversion `root_herbivory_memory → perte d'uptake` (③). Racines profondes /
    dépendance mycorhizienne encaissent mieux la perte de racines superficielles.

### Couche 2 — CONSTITUTION `resilience_base` (générique, par espèce, SANS gène)

« Quand un coup PASSE, à quel point je plie vs je casse ? » — tampon de
**magnitude générique EN AVAL**, à `erode()`. **Orthogonale à la niche** : un
cactus tolère la sécheresse (niche haute) mais a une constitution faible (tissu
succulent qui décline vite une fois blessé) ; un arbre a des tolérances moyennes
mais une constitution haute (le bois encaisse). Points **différents du pipeline**
(susceptibilité à la source vs magnitude en aval) → **aucun double-compte**.

- Attribut de classe `resilience_base: float` (CSR fast-fragile / slow-tough).
- **Table COMPLÈTE** : une valeur explicite pour **chaque espèce du catalogue**
  (exigence Nico « constitution complète »), pas de défaut silencieux 1.0.
  Bande de DÉPART (calibrage post-test) :

  | profil CSR | espèces (indicatif) | base |
  |---|---|---|
  | coriaces stress-tolérantes (S) | sedum/orpin, ligneuses établies, pionnières rustiques, ortie/consoude | **1.25** |
  | intermédiaires | vivaces herbacées, aromatiques, compagnes | **1.0** |
  | fragiles ruderales/rapides (R) | tomate & Solanaceae, annuelles tendres, semis exigeants | **0.8** |

### 2.1 Récupération — inchangée (`vigueur`)

`vigueur` = « volonté de vivre / récupérer / se reproduire » (décision Nico). La
convalescence (`mortalite.py`) garde `heal = Q × HEAL_RATE × gene("vigueur") ×
cout_defense`. Érosion (constitution) et récupération (vigueur) agissent sur des
**côtés opposés** → pas de double-compte.

### 2.2 Primitive d'érosion unique `plant.erode()` (décision Nico)

Pour que la constitution atteigne **toutes** les voies d'insulte — y compris les
**décréments directs** (« attention aux décréments directs, certaines plantes plus
résilientes à l'asphyxie ») — on centralise l'érosion :

    def erode(self, amount: float) -> None:
        self.vitalite = max(0.0, self.vitalite - amount / self.plant_class.resilience_base)

**Passent par `erode()`** (insultes EXTERNES, bufferisées par la constitution) :
- toutes les `ReduceHealth` (résolution — herbivorie, fongique, sécheresse, ombre,
  gel, grêle, vent, mortalité de fond, fonte des semis…) ;
- **asphyxie** (`mortalite.py` — APRÈS sa médiation amont par `tolerance_asphyxie`
  sur la *pression* ; la constitution module la *magnitude*) ;
- `PropagateDisease`.

**Ne passent PAS par `erode()`** (décréments directs assumés) :
- **sénescence** (`mortalite.py` — horloge interne de fin de vie ; on ne « résiste »
  pas à son propre vieillissement) → `vitalite -= VITALITE_STEP` brut ;
- **gestes joueur** (écraser/déraciner/`regress`/greffe → `vitalite = 0`) et
  **annélation létale** (§3) → mécanique brute, la constitution n'y peut rien.

`erode()` est introduite au **tronçon ①** avec `resilience_base` implicite = 1.0
(le champ n'existe pas encore → `getattr(..., 1.0)`, no-op) ; le **tronçon ②**
pose la table complète → la différenciation s'active.

## 3. Fix du canal chronique campagnol (replié ici)

**État actuel** (`perturbations.py:root_herbivory`, sommet trophique ①) : le
campagnol produit un `ReduceHealth −1` **plat**, en concurrence avec les autres
voies dans `_cap_chronique` (une plante broutée *et* ombragée ne perd qu'1 point —
le campagnol est « avalé » par le cap). Érosion générique, pas le vrai mécanisme.

**Cible (philo #2 : flux → contrainte → réponse émergente)** :

1. **`root_herbivory_memory`** (nouvel état d'instance, lerp lent ∝ densité
   `herbivore_vertebre` locale) : intègre la pression de broutage racinaire.
2. **Perte d'uptake** : `root_herbivory_memory` réduit l'**uptake effectif** —
   se branche dans `_apply_uptake` (`croissance.py`), à côté de `shade_memory`/
   `drought_memory` déjà passés à `plant_uptake`. Moins d'eau/azote → la plante
   souffre par les **voies existantes** (`drought_stress_damage`, faim d'azote) au
   lieu d'un `ReduceHealth` plat. Le campagnol **affame** au lieu d'éroder en direct.
3. **Niche `root_loss_tolerance_base(espèce)`** (couche 1, §2) : module la
   conversion mémoire → perte d'uptake. Racines profondes / dépendance mycorhizienne
   → tolèrent mieux.
4. **Couplage mycorhize** (interconnexion « tout coexiste ») : une plante branchée
   au réseau mycélien (champ `mycelium`, rôle mycorhize — wood-wide-web, boost P)
   **compense** partiellement la perte racinaire → la perte d'uptake est rabotée
   ∝ la densité mycélienne sous l'empreinte. Le réseau nourrit la plante amputée.
5. **Annélation létale CONSERVÉE** : le jeune ligneux (écorce annelable, dens ≥
   `ROOT_HERBIVORY_LETHAL`) meurt toujours — collet rongé = sève coupée
   (sectionnement mécanique) → **bypass `erode()`** (`vitalite = 0` direct), certain.

**Golden NEUTRE** : au smoke, densité `herbivore_vertebre` = 0 →
`root_herbivory_memory` reste 0 → uptake inchangé → invariant.

## 4. Découpage en tronçons

| # | Tronçon | Golden |
|---|---|---|
| **①** | **Socle vitalité continue** : renomme `health→vitalite [0,1]`, property `etat`, `VITALITE_STEP`, primitive `erode()` (base implicite 1.0), migration de TOUS les lecteurs (`/3.0`) et écrivains (ReduceHealth, sénescence/asphyxie/heal, gestes, cap chronique, médiés sans plancher entier), `_PLANT_ATTRS` golden | **RE-FIGÉ #1 annoncé** |
| **②** | **Constitution + niche grêle** : `resilience_base` COMPLET par espèce (active `erode()`), `hail_resistance_base` branché au dégât de grêle | **RE-FIGÉ #2 annoncé** (différenciation espèces du smoke) |
| **③** | **Canal campagnol → uptake + mycorhize** : `root_herbivory_memory`, perte d'uptake, `root_loss_tolerance_base`, compensation mycélienne, fin du `ReduceHealth` plat, annélation létale bypass conservée | **NEUTRE** (campagnol = 0 au smoke) |
| **④** | **Vue Godot** (règle permanente) : le pont expose `vitalite`/`etat` (`serialize.py`), le `PlantRenderer` C# passe du palier 0-3 à un **dégradé continu** de vitalité | **INTACT** |

Deux re-figeages **maîtrisés et annoncés** (①, ②), chacun une dérive localisée et
prouvable (neutraliser la nouveauté retombe sur le hash antérieur) ; ③ neutre ;
④ intact.

## 5. Coût perf

- Vitalité continue : neutre (float remplace int). `GENE_NAMES` **inchangé**
  (aucun gène) → zéro impact sur le canal de hash génétique.
- `resilience_base` : lecture d'attribut de classe O(1)/érosion → négligeable.
- `hail_resistance_base` : lecture O(1) au seul dégât de grêle.
- `root_herbivory_memory` : +1 lerp O(N)/tick ; compensation mycorhize = lecture
  champ `mycelium` sur l'empreinte (déjà parcourue pour l'uptake) → marginal.
- Budget ≤ +10 %/tronçon **largement** respecté.

## 6. Philo de design

- **#1/#2** (flux → contrainte → réponse) : la constitution ne donne aucun
  bonus/malus direct — elle module l'**amplitude** d'une érosion déjà médiée par
  un flux. Le campagnol passe d'un verdict de santé à une **famine émergente**.
- **#3** (déterminisme) : aucun RNG neuf ; mémoires = lerps, érosion = division.
  `GENE_NAMES` intact (pas d'ajout → aucun décalage de canal positionnel).
- **#5** (indices visuels, pas de chiffres) : la vitalité continue reste cachée ;
  seuls les **4 états** et la **sémiologie** (flétrissure, teinte) la trahissent.
- **#6** (usure pas punition) : le cap chronique continu (`−VITALITE_STEP/tick`)
  garde « une plante saine tient plusieurs ticks » ; la constitution adoucit encore.
- **#7** (hétérogénéité) : constitution d'espèce × tolérances de niche
  individuelles/plastiques × vigueur → deux pieds n'encaissent jamais pareil.
