# Conception — Arc Pollinisation & Cycle de vie (SYMBIOSE)

> **Document de conception. Aucun code moteur écrit tant qu'il n'est pas figé.**
> Spec de référence pour le futur sprint d'implémentation (MOTEUR → re-fige le
> golden), découpé en sous-sprints. Kickoff :
> `sprints/sprint_pollinisation_cycle_vie/00_conception_kickoff.md`.
>
> Origine : idée Nico (vue·rattrapage 02, gravée 2026-06-16). S'appuie sur
> l'horloge `daylength(wiy)` (sprint saisonnalité vie macro, 2026-06-16). Mémoires
> liées : [[design_pollinisation_cycle_vie]], [[regle_interconnexion_acteurs]].
>
> **État de rédaction** : **CONCEPTION COMPLÈTE & FIGÉE (2026-06-16)** — §A–§E
> tranchés par Nico, synthèse moteur + découpe d'impl en §F. Prêt pour
> l'implémentation (sprint MOTEUR découpé ①→④, re-fige le golden).

---

## 0. Constat & périmètre

L'arc relie **floraison → pollinisation → fruit → graine** et boucle un cycle de
vie inter-guildes (**chenille → papillon**). Audit de l'existant (kickoff §2) :

**Déjà fait (à NE PAS reconstruire)** :
- **Brassage génétique pollinisé** (`sim/reproduction.py`) : `find_father` +
  `child_genes` (biparental/autoféc./introgression) + `pollinator_reach` **modulé
  par la densité locale du champ `pollinisateur`** (D31.2). Modes `wind/insect/self`.
- **Fruits traçables** (`engine/decompo.py:_tick_fruits`) : nouaison annuelle,
  maturation, chute, `manger` ciblé (absorbe D19).
- **Champ `pollinisateur`** saisonnier (`fields/population.py`), ressource =
  proxy `_flower_grid` (stade ≥ 2).

**Le vrai gap (périmètre de l'arc)** :
- **A** Floraison RÉELLE + phénologie (aujourd'hui : proxy de rendu + semaine fixe).
- **B** Nouaison CONDITIONNÉE à la pollinisation (aujourd'hui : inconditionnelle).
- **C** Rétroaction floraison ↔ Vigueur du champ pollinisateur.
- **D** Chenille → papillon (transfert `ravageur` → `pollinisateur`).
- **E** (option) Raffinement du brassage (pollen multi-pères).

Garde-fous : **philo #2** (flux → contrainte → réponse émergente, jamais de
malus direct sur la plante), **#3** (déterministe), **#6** (apprentissage diffus,
pas de chiffres HUD), **interconnexion** (tout coexiste). Re-figeage golden MOTEUR
attendu surtout sur **D** — maîtrisé et annoncé.

---

## A. Floraison réelle & phénologie — FIGÉ (2026-06-16)

**Décisions Nico** : état = **scalaire `floraison ∈ [0,1]`** ; déclencheur =
**photopériode + chaleur cumulée** ; **une fenêtre par espèce** (surtout estivale,
défauts par famille/strate).

### A.1 État moteur
- Nouveau champ `floraison: float = 0.0` sur `PlantInstance` (intensité de
  floraison courante). **Pas** d'organes-fleurs en moteur : le rendu les régénère
  procéduralement (contrat `organs` inchangé). `floraison` est l'**assiette** qui :
  - alimente la ressource du champ pollinisateur (remplace le proxy `_flower_grid`
    stade ≥ 2 — voir §C) ;
  - porte l'intégrale de pollinisation reçue (voir §B).

### A.2 Double porte de déclenchement (deux signaux complémentaires)
La floraison s'ouvre quand **les DEUX** conditions sont vraies — calque du couple
`phenology`/`warmth` des guildes :

1. **Chaleur cumulée (forçage thermique, GDD)** — *« la plante est prête »* :
   accumulateur **par plante** `gdd_accum`, incrémenté chaque tick de
   `max(0, T_semaine − T_BASE_FLORAISON)` (`T_BASE_FLORAISON` ≈ 6 °C, réutilise
   l'esprit de `T_COLD_ZERO`). **Remis à 0 au passage d'année** (reset annuel,
   déterministe). Porte franchie quand `gdd_accum ≥ gdd_floraison(espèce)`.
2. **Photopériode** — *« c'est la saison »* : `daylength(wiy)` dans la fenêtre
   `[bloom_daylen_min, bloom_daylen_max]` de l'espèce (réutilise `daylength`).
   La quasi-totalité du catalogue = fenêtre estivale (jours longs). Stratégie
   jours-courts (automne) laissée extensible (un seul couple de seuils à régler).

### A.3 Dynamique de l'intensité
- Les deux portes ouvertes → `floraison` **monte** vers 1 (relaxation douce) ;
  une porte retombe (jour trop court / fin de chaleur / fanaison) → `floraison`
  **redescend** vers 0. Knobs de montée/descente = calibrage post-test.
- Gate de **maturité** : une plante trop jeune ne fleurit pas (réutilise
  `maturity_years` pour les fruitiers ; pour les annuelles, un stade minimal). Les
  espèces non reproductrices peuvent garder `floraison` à 0 (neutre).

### A.4 Paramètres par espèce (placeholders, calibrage post-test)
- `gdd_floraison: float` — seuil de degrés-jours (défaut par famille/strate).
- `bloom_daylen_min/max: float` — fenêtre photopériodique (h de jour).
- Réutilise `T_BASE_FLORAISON`, `daylength`, `maturity_years` existants.

### A.5 Golden
À évaluer à l'implémentation. La floraison n'agit (B/C) qu'ensuite ; en soi
l'ajout d'un scalaire neutre + accumulateur **peut rester golden-neutre** s'il
n'est lu par rien tant que B/C ne sont pas branchés (à confirmer au tronçon ①).

---

## B. Nouaison conditionnée à la pollinisation — FIGÉ (2026-06-16)

**Décisions Nico** : gate **continu** ; nouaison en **fin de floraison, par
plante** (remplace `FRUIT_NOUAISON_WEEK`) ; **`self`/`wind` nouent toujours**,
**entomophiles SANS plancher** (0 pollinisateur → 0 fruit, extinction locale
possible — assumée).

### B.1 Dose de pollinisation
- Accumulateur **par plante** `pollen_recu: float = 0.0`, incrémenté chaque tick
  PENDANT la floraison : `pollen_recu += densité_pollinisateur_locale × floraison`
  (intégrale flux × assiette florale, philo #2). Lit le champ `pollinisateur`
  (D31.2) au plot-foyer. Déterministe (champ déterministe).
- Remis à 0 à la nouaison (cohorte annuelle suivante repart de zéro).

### B.2 Nouaison en fin de floraison (par plante)
- **Remplace le rendez-vous global `FRUIT_NOUAISON_WEEK`** : chaque plante noue
  quand **sa** `floraison` retombe sous un seuil (fleurs fanées), après avoir
  intégré sa dose. Toujours déterministe (`floraison` dérive de `daylength`+`gdd`).
- Gate complet de mise à fruit : `fruitier` ET `age_years ≥ maturity_years` ET
  a fleuri cette année.
- **Fraction nouée (continue)** : `frac = g(pollen_recu)` ∈ [0,1] (rampe douce,
  saturante — knob calibrage). Nombre de fruits = `round(frac × |organ_sites|)`,
  borné `MAX_ORGANS`. `frac` faible → quelques fruits ; `frac` ≈ 0 → aucun.
- **Par mode** : `self`/`wind` court-circuitent la dose → `frac = 1` (nouaison
  pleine, sans insectes). `insect` → `frac = g(pollen_recu)` **sans plancher**
  (aucun pollinisateur ⇒ 0 fruit ⇒ pression écologique : l'espèce peut décliner
  localement, ce qui valorise les volets C/D).

### B.3 Conséquences & interconnexion
- La survie reproductive des fruitiers entomophiles dépend désormais de la
  **chaîne pollinisateur** : floraison (A) → champ pollinisateur (saisonnalité +
  C) ← chenille→papillon (D). Boucle vivante, philo #6.
- `_tick_fruits` (decompo.py) : la nouaison annuelle inconditionnelle devient
  conditionnelle (lit `pollen_recu`, mode, et le déclencheur passe au seuil de
  fin de floraison par plante). Maturation/chute inchangées.

### B.4 Golden
Re-figeage à évaluer. La seule `fruitier` précoce du smoke est la **tomate**
(`maturity_years=0`) qui **meurt w2-3** (froid de démarrage, [[tomate_mort_precoce]])
AVANT toute floraison/nouaison estivale → **probablement golden-neutre** pour B
(à confirmer au tronçon ②). Le pommier (`maturity_years=5`) ne fructifie pas sur
2 ans.

## C. Rétroaction floraison ↔ Vigueur du champ pollinisateur — FIGÉ (2026-06-16)

**Décisions Nico** : ressource du champ = **floraison réelle pondérée mellifère** ;
**pas de Vigueur joueur** (récompense écosystémique).

### C.1 Reconnexion de la ressource
- `_flower_grid` (proxy stade ≥ 2) **remplacé** : la ressource du champ
  `pollinisateur` devient `Σ_plantes_du_plot (floraison × attractivite_pollinisateur)`,
  normalisée (réutilise `FLOWER_REF`). Le butinage qui fait prospérer la guilde
  devient *vrai* (philo #2 : flux floral → capacité de charge → densité émergente).
- Nouveau trait espèce **`attractivite_pollinisateur ∈ [0,1]`** (le nectar) :
  fort pour les mellifères (Phacélie, Clover, Yarrow…), faible pour les fleurs
  peu nectarifères. Défaut par famille. → **stratégie joueur** : semer des
  mellifères soutient la pollinisation de ses fruitiers (interconnexion).

### C.2 Pas de Vigueur joueur
Le joueur agit sur le **milieu** (philo #1), il n'est pas l'insecte. La récompense
de cultiver des mellifères reste **indirecte/écosystémique** : plus de
pollinisateurs → plus de nouaison (B) → plus de récolte et de graines. Aucun
crédit de Vigueur joueur direct.

### C.3 Golden
La reconnexion de la ressource du champ pollinisateur **re-figera** (le champ lit
désormais `floraison` au lieu de stade ≥ 2 ; et le pollinisateur, lu par
`pollinator_reach`, influe sur la repro). Re-figeage MAÎTRISÉ attendu, à isoler
au tronçon ③. (Note : se cumule au re-figeage du volet D.)

## D. Chenille → papillon (cycle de vie inter-guildes) — FIGÉ (2026-06-16)

**Décisions Nico** : **champ `chenille` dédié + maturité** (pas une 5ᵉ guilde
trophique — la chenille est un *stade de cycle de vie*) ; chenilles issues de la
**ponte des papillons** (cycle bouclé) ; **famine → mortalité** (pas de
métamorphose sans nourriture).

### D.1 Deux nouveaux champs (légers, `EcoFields`)
- `chenille` — densité [0,1] de larves de lépidoptères (≠ ravageur généraliste).
- `chenille_nourrie` — maturité moyenne cumulée [0,1] de la cohorte.
- **Pas un `PopulationField`/`TrophicSpec`** (pas les 4 fonctions trophiques) :
  c'est un cycle de vie, traité à part dans le tick (évite la 5ᵉ guilde, cohérent
  avec la décision décompo ④).

### D.2 Cycle (dans le tick, après les guildes)
1. **Ponte** (fenêtre de ponte, printemps→début été ancrée sur `daylength`) :
   `chenille += PONTE_RATE · pollinisateur_local · feuillage_local`, bornée. Les
   papillons (densité `pollinisateur`) pondent **là où il y a du feuillage** →
   **boucle** pollinisateur → chenille.
2. **Herbivorie** : la chenille **s'ajoute** à la pression d'herbivorie —
   `HERBIVORY_GAIN` (D31.2, `sim/effects/perturbations.py`) lit désormais
   `ravageur + chenille`. Les chenilles mangent vraiment les feuilles.
3. **Maturation par la nourriture** : `chenille_nourrie += MATUR_RATE ·
   nourriture_consommée` (∝ min(chenille, feuillage local)). Pas de feuille →
   ne mûrit pas.
4. **Famine** : sans feuillage, `chenille` **décline** (mortalité) en plus de ne
   pas mûrir → régulation boom-bust (trop de chenilles épuisent leur ressource
   et s'effondrent). Réaliste, auto-limitant.
5. **Métamorphose** : `chenille_nourrie ≥ METAM_SEUIL` → `pollinisateur +=
   chenille · (1 − METAM_PERTE)` (perte = prédation/parasitisme/échec), puis
   `chenille = 0`, `chenille_nourrie = 0`. **Boucle** chenille → pollinisateur.

### D.3 Effet émergent recherché
Pic de chenilles au printemps (herbivorie forte) → métamorphose → **bouffée de
pollinisateurs en été**, pile pour la floraison/nouaison (B). Les ravageurs du
printemps deviennent les pollinisateurs de l'été ; répit d'herbivorie en prime.
Cycle complet, interconnexion maximale (philo #6).

### D.4 Paramètres (placeholders, calibrage post-test)
`PONTE_RATE`, fenêtre de ponte (seuils `daylength`), `MATUR_RATE`, `METAM_SEUIL`,
`METAM_PERTE`, taux de mortalité de famine. Tous à régler jeu en main.

### D.5 Golden
**Re-figeage MOTEUR MAÎTRISÉ attendu** (annoncé) : `HERBIVORY_GAIN` lit
maintenant `ravageur + chenille` → la pression d'herbivorie change → santé des
plantes → golden. Se cumule avec C. À isoler au tronçon ④. Invariant : à
`chenille = 0` partout (aucun pollinisateur pour pondre, ou hors fenêtre), la
pression d'herbivorie est **strictement inchangée** vs aujourd'hui → dérive
attribuable au seul cycle chenille.

## E. Brassage multi-pères (option) — FIGÉ : NON RETENU (2026-06-16)

**Décision Nico** : garder l'existant. `pollinator_reach` (rayon du père ∝
densité pollinisateur, D31.2) + `child_genes` biparental couvrent déjà le
« mélange des pollens » : plus de pollinisateurs → père plus lointain → plus de
brassage ; peu/pas → autofécondation. **Pas de tronçon E.** Raffinement
multi-pères (diversité du lot ∝ butinage) laissé en backlog lointain si le
calibrage le réclame.

---

## F. Synthèse moteur & découpe d'implémentation

### F.1 Nouveaux éléments moteur
| Élément | Où | Rôle |
|---|---|---|
| `floraison: float` | `PlantInstance` | intensité de floraison (assiette) |
| `gdd_accum: float` | `PlantInstance` | degrés-jours cumulés (reset annuel) |
| `pollen_recu: float` | `PlantInstance` | dose de pollinisation intégrée (reset à la nouaison) |
| `gdd_floraison` | famille/espèce | seuil thermique de floraison |
| `bloom_daylen_min/max` | famille/espèce | fenêtre photopériodique de floraison |
| `attractivite_pollinisateur ∈[0,1]` | famille/espèce | nectar (pondère la ressource pollinisateur) |
| champs `chenille`, `chenille_nourrie` | `EcoFields` | cycle de vie larvaire (densité + maturité) |
| `T_BASE_FLORAISON`, `PONTE_RATE`, `MATUR_RATE`, `METAM_SEUIL`, `METAM_PERTE`… | constantes | calibrage post-test |

### F.2 Points de greffe
- `fields/population.py` : ressource `pollinisateur` ← `floraison × attractivite`
  (remplace `_flower_grid`).
- `sim/effects/perturbations.py` : `HERBIVORY_GAIN` lit `ravageur + chenille`.
- `sim/engine/decompo.py:_tick_fruits` : nouaison conditionnelle (lit `pollen_recu`,
  mode) déclenchée en **fin de floraison par plante** (remplace `FRUIT_NOUAISON_WEEK`).
- nouveau pas de tick : montée/descente de `floraison` (GDD + `daylength`) +
  cycle `chenille` (ponte/herbivorie/maturation/famine/métamorphose).

### F.3 Découpe en sous-sprints (chacun préserve ou re-fige le golden de façon isolée)
1. **① Floraison réelle + phénologie** (A) : `floraison`, `gdd_accum`, fenêtre par
   espèce. Rien ne lit encore `floraison` → **golden visé NEUTRE** (tronçon sûr).
2. **② Nouaison pollinisée** (B) : `pollen_recu`, nouaison fin-de-floraison,
   modes, gate continu. **Golden probablement neutre** (tomate meurt w2-3 avant
   nouaison estivale ; pommier pas de fruit < 5 ans). À confirmer.
3. **③ Reconnexion ressource pollinisateur** (C) : `floraison × attractivite`
   remplace `_flower_grid`. **Golden re-figé MAÎTRISÉ.**
4. **④ Cycle chenille → papillon** (D) : 2 champs + ponte/herbivorie/maturation/
   famine/métamorphose ; `HERBIVORY_GAIN` lit `ravageur + chenille`. **Golden
   re-figé MAÎTRISÉ** (invariant : `chenille=0` ⇒ herbivorie inchangée).

Ordre conseillé ①→②→③→④ (les golden-neutres d'abord, puis les re-figeages isolés).
Pas de ⑤ (E non retenu). La **vue Godot** (sprites papillons/chenilles, fleurs
réelles, fruits gated) suit, hors de ce sprint moteur (la vue échantillonne déjà
les champs).

### F.4 Invariants transverses
Déterminisme (`seed`/`_hash_noise`/`daylength`, jamais de RNG vivant) ; philo #2
(flux→contrainte→émergence, jamais de malus direct) ; interconnexion (fleurs ↔
pollinisateurs ↔ fruits ↔ graines ↔ chenilles) ; re-figeages golden annoncés et
isolés par tronçon.
