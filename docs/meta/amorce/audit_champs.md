# Audit des champs — Symbiose

**Statut : AUDIT — état des lieux, non figé.** Destiné à alimenter `/conception` et la priorisation DETTE/BACKLOG.
**Date :** 2026-07-17
**Périmètre :** tous les champs du paquet `data/code/fields/` (top-level + `ecofields/` + `population/`), lus dans le code réel.
**Méthode :** lecture des 35 modules `fields/*` + orchestration `sim/engine/boucle.py` ; run headless 10 ans (monde smoke 2 tuiles 6×8, seed 42) ; 6 ablations mesurées (5 ans) pour chiffrer l'effet réel de chaque champ moteur.

> ⚠️ Deux points d'honnêteté d'entrée de jeu :
> 1. Les chiffres « effet sur 10 ans » viennent du **monde smoke** (2 tuiles), pas du jardin complet 1600 plots (trop lourd pour le bac à sable ici). Ils valent en **relatif** (quel champ pèse le plus), pas en absolu.
> 2. `vitalite_average` sort **bas** dans ce monde dense (canopée fermée) ; je m'en sers comme **signal comparatif** entre scénarios, pas comme note de santé.

---

## 0. Origine & intention

Tu veux « un audit de tous les champs implémentés pour connaître l'impact et l'importance de chacun dans la mécanique globale et la biologie simulée ». Après cadrage, tu as précisé la grille par champ : **rôle & I/O**, **importance mécanique**, **interconnexions**, **fidélité bio + respect philo #1-#7**, **coût en performances**, **effet réel dans le jeu sur 10 ans**. Périmètre : tout `data/code/fields/`, y compris abri, alarme, apiculture, faune, foragers, lifecycle, light/light_index, noise, seedbank, allélopathie, autotoxicité.

Constat de départ : le code a largement dépassé les docs de knowledge. L'ancien `fields.py` plat est éclaté en un paquet ; `EcoFields` porte aujourd'hui **~40 champs** (contre la poignée décrite dans `architecture.md`). Cet audit repart donc du code.

---

## 1. Le pipeline du tick — la clé de lecture de l'« importance »

L'importance d'un champ se lit d'abord dans **l'ordre du tick hebdomadaire** (`boucle.py:tick_semaine`) : qui écrit avant qui, qui lit quoi. Ordre réel observé :

1. **Météo** (pure, seed+week) → pose `temperature` (T_air), nébulosité, événement pluie/neige, direction/force du vent.
2. **Neige** (`tick_snow`) → 2b **Lumière** (`tick_light`) → **Abri/vent** (`tick_abri` → `vent`) → **Thermique** (`tick_thermique` → `temperature_sol`) → 2c **Rosée** (`tick_rosee` → `humidite`/`givre`/`rosee_last`) → 2d **Couverture** (`tick_couverture` → `couverture_sol`).
3. **Hydrologie** (`tick_hydrology` : évaporation → pluie → rétention → drainage, écrit `humidite`/`drainage_last`/`eau_surface`) → **Ruissellement** (`tick_ruissellement`) → **Marais** (`tick_marais`).
4. **Décomposition** (`tick_decomposition` : cascade litière→active→stable→minéralisation N/P/K) → structures compost → **pH** → **structure_sol** → **mycélium** → **allélopathie**.
5. **Diffusion** spatiale (humidité, N, P, K, microbiome).
6. **Avancement des stades** (conditionné lumière + humidité).
7. **Effets weekly** des plantes (flux écologiques, exsudats).
8. **Uptake racinaire** (`plant_uptake` : eau + N/P/K, loi de Liebig, modulé microbiome/structure/pH/asphyxie).
9. Mémoire physiologique → 10. Floraison → 11. Récolte (`add_necromass`) → 12. Conflits.
13. **Perturbations** (`tick_disturbance`) → **Populations** (`tick_populations`) → **Épaisseur** (`tick_epaisseur`) → **Ponts de cycle de vie** (`tick_lifecycle_bridges`).
14. **Banque de graines** (`tick_seed_bank`) → 15. **Succession** → **Transport éolien** (`tick_transport`) → **Paillage** (`tick_paillage`).
16. **Transition hivernale** (sem. 48-52) → 17. **Soil memory** (fin de saison) → **Autotoxicité** (fin de saison).

Lecture immédiate : les champs **lus à l'étape 8 (uptake) et 6 (stades)** sont les goulets d'étranglement de la biologie — c'est là que le sol devient plante. Ce sont `humidite`, `n/p/k`, `microbiome`, `structure_sol`, `lumiere`. Tout le reste les **alimente** (amont) ou les **observe** (aval, vue).

---

## 2. Table de synthèse — classement par impact

Statut : **ACTIF** (lu par la biologie aujourd'hui) · **PARTIEL** (lu par un sous-système seulement) · **DORMANT** (posé/tické mais lu par personne au tronçon courant) · **VUE** (lu uniquement par le snapshot Godot / encyclopédie).
Tier d'impact : **S** structurant · **A** fort · **B** modulateur · **C** marginal/différé.

| Champ | Module | Statut | Tier | Rôle en une ligne | Coût perf |
|---|---|---|---|---|---|
| `lumiere` (LightField) | light.py | ACTIF | **S** | Éclairement astronomique par capsule ; porte croissance + thermique + couverture | **Le plus cher (~53 % CPU)** |
| `humidite` | hydrologie.py | ACTIF | **S** | Eau des pores ; uptake, évaporation, germination, rosée, mycélium | O(plots) diffusion |
| `n` / `p` / `k` | nutriments.py | ACTIF | **S** | Nutriments Liebig (minimum) ; **limiteur dominant** de la croissance | O(plots) ×3 diffusion |
| litière (`litiere`) + `om_active` + `om_stable` | matiere_organique.py | ACTIF | **S** | Cycle MO : décompo cascade → N/P/K, humus, rétention, épaisseur | O(plots), scatter racines |
| `microbiome` | sol.py / uptake.py | ACTIF | **A** | Bonus d'uptake, vitesse de décompo, détox, vitalité | O(plots) diffusion (inertie 0.92) |
| `temperature` (T_air) + `temperature_sol` | thermique.py | ACTIF | **A** | Microclimat de surface ; évaporation, fenêtres bio, gel | O(plots) |
| `structure_sol` | structure.py | ACTIF | **A** | Compaction ∈[0,1] ; infiltration, asphyxie, pénétration racinaire | O(plots) lent |
| `soil_memory` (+ `_fast` / `_deep`) | sol.py | ACTIF | **A** | Mémoire du sol double-temps ; rétention, vitalité, succession | O(plots), fin de saison |
| `disturbance` | grids.py | ACTIF | **A** | Perturbation spatiale déterministe ; herbivorie, succession, banque | O(plots) bruit |
| `seed_bank` | seedbank.py | ACTIF | **A** | Banque de graines latente (archétypes + génétique) ; moteur de succession | O(plots)+espèces |
| `populations` (dict/espèce) | population/ | ACTIF | **A** | Guildes trophiques ; `lombric`→structure, prédateurs→ravageurs, pollinisateurs→Vigueur | Borné 432 plots → ~gratuit |
| `couverture_sol` | couverture.py | ACTIF | **B** | Couverture des strates basses ; évaporation, germination férale | 1 scatter/tick |
| `paillage` (+ `paillage_nature`) | paillage.py | ACTIF | **B** | Mulch joueur anti-invasion ; germination, âge des graines, évaporation | O(plots) event-driven |
| `vent` | abri.py / transport.py | ACTIF | **B** | Force locale du vent (brise-vent émergent) ; évaporation, wind chill, transport | Cache directionnel → ~0 en régime |
| `eau_surface` + `altitude` + `marais_memory`/`_etat` | hydrologie/ruissellement/marais/marais.py | ACTIF | **B** | Eau de surface, micro-relief, mémoire de marécage ; ruissellement, décompo anaérobie, pH | Double-buffer O(plots), no-op à sec |
| `rosee_last` + `givre` | rosee.py | ACTIF | **B** | Rosée/gelée nocturne ; tampon sécheresse, habitat détritivore, fonte différée | O(plots) nocturne |
| `snow` (scalaire/tuile) | thermique.py | ACTIF | **B** | Manteau neigeux ; isolation hivernale (effet igloo) | O(1) |
| `larvae` (`chenille`, `syrphe_larve`…) | lifecycle.py | PARTIEL | **B** | Stades larvaires ; chenille→herbivorie, syrphe_larve→prédateur, métamorphose→pollinisateur | O(plots)×ponts |
| `foragers` | foragers.py | PARTIEL | **B** | Butineurs marchant fleur-en-fleur ; **déposent le pollen** → nouaison (④) | Transient, échantillonné |
| `drainage_last` | hydrologie.py | ACTIF | **B** | Eau drainée du dernier tick ; amplifie le lessivage N/P/K | O(plots) transient |
| `ph` | ph.py | **DORMANT** | **C→A** | pH maître-régulateur, dérive décennale ; **lu par personne au tronçon ①** | O(plots) lent |
| `mycelium` | mycelium.py | **DORMANT** | **C→A** | Réseau fongique ; dynamique propre mais effets §2 débranchés | O(plots) |
| `allelopathie` | allelopathie.py | **DORMANT** | **C** | Allélochimiques racinaires ; alimenté nulle part avant ⑤ émetteurs | O(plots) |
| `autotox` (+ `autotox_espece`) | autotoxicite.py | **DORMANT** | **C** | Fatigue du sol de monoculture ; aucun émetteur armé avant ⑤ | O(plots) fin de saison |
| `epaisseur_sol` | container.py / `tick_epaisseur` | **DORMANT** | **C→B** | Épaisseur de sol foisonnant ; tické mais lu par personne (effets ①b) | O(plots) |
| `alarme` | alarme.py | **VUE** | **C** | Phéromone d'alarme apienne ; pur puits lu par le snapshot Godot | O(plots) transient |
| `faune_encyclo` | faune_encyclo.py | **VUE** | **C** | Métadonnée d'encyclopédie ; jamais lue par le tick | Donnée statique |
| ruche/miel (`apiculture`) | apiculture.py | ACTIF (si ruche) | **C** | Hub abeille : capture essaim + produit miel ∝ nectar | Retour immédiat si 0 ruche |

---

## 3. Ce que la simulation dit vraiment (10 ans + ablations)

### 3.1 Trajectoire 10 ans (tuile T0 « terre », moyennes de tuile)

| An | humidité | p | microbiome | om_fresh | om_active | om_stable | soil_mem | vivantes |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.55 | 0.64 | 0.34 | 0.35 | 0.17 | 0.15 | 0.07 | 17 |
| 3 | 0.12 | 0.04 | 0.34 | 0.11 | 0.46 | 0.23 | 0.13 | 15 |
| 5 | 0.13 | 0.003 | 0.20 | 0.19 | 0.52 | 0.34 | 0.14 | 15 |
| 7 | 0.18 | 0.004 | 0.04 | 0.20 | 0.57 | 0.45 | 0.14 | 11 |
| 10 | 0.11 | 0.005 | 0.02 | 0.15 | 0.65 | 0.65 | 0.15 | 20 |

Trois phénomènes émergents nets sur la décennie :

- **L'humus se construit** : `om_stable` grimpe 0.15 → 0.65 et `om_active` 0.17 → 0.65. Le sol devient bien un *organisme* qui capitalise le carbone — c'est le cœur du modèle « sol vivant » et il fonctionne.
- **Le phosphore s'effondre** : `p` 0.64 → 0.005. En monde fermé sans amendement, **P devient le facteur limitant de Liebig**. C'est probablement LE ressort le plus déterminant de la santé à long terme (voir ablation NPK).
- **Le microbiome décroche** : 0.34 → 0.02. À creuser en `/conception` : dérive de calibration ou dynamique voulue (canopée fermée → moins de photosynthèse → moins d'exsudats → microbiome affamé) ? L'effet est fort et mérite un verdict explicite.

### 3.2 Ablations — effet réel mesuré (5 ans, somme des 2 tuiles ; baseline vitalité = 0.021)

| Scénario | vivantes | vitalité | lecture |
|---|---:|---:|---|
| **baseline** | 54 | 0.021 | référence |
| `npk` figé haut (2.0) | 56 | **0.141** (×7) | **Les nutriments sont le limiteur dominant.** Lever Liebig fait exploser la vitalité. |
| `microbiome` figé à 1.0 | 56 | 0.087 (×4) | Sol vivant = fort levier de santé (bonus uptake + poids vitalité). |
| `microbiome` figé à 0 | 53 | 0.007 (÷3) | Tuer le microbiome effondre la vitalité sans tuer tout de suite. |
| `om_stable` figé à 0 | 47 | 0.010 (÷2) | Sans humus : moins de survivants **et** vitalité divisée par deux. |
| `humidite` figé à 0.1 (sécheresse) | 48 | 0.004 (pire) | L'eau est fondatrice : `aux` (auxiliaires) tombe à **0** → tout le réseau trophique s'écroule. |

Conclusion opérationnelle : l'ordre d'importance **mesuré** pour la santé de l'écosystème est **eau ≈ nutriments (surtout P) > matière organique/humus > microbiome**, les autres champs agissant comme modulateurs ou comme amont de ceux-là.

---

## 4. Fiches — champs structurants (Tier S)

### `lumiere` — LightField (light.py + light_index.py)
**Rôle & I/O.** Éclairement par plot calculé analytiquement (ombres-capsules astronomiques, ~49°N, 4 saisons × 3 tranches diurnes + intégrale journalière). Écrit par `tick_light` (étape 2b), en lisant la géométrie des plantes + l'ombre/albédo de la maison. Lu par : avancement des stades (étape 6), photosynthèse/exsudats (effets weekly), `tick_thermique` (surchauffe solaire), `tick_couverture` indirectement.
**Importance / effet 10 ans.** Structurant : c'est le robinet d'énergie. Sur la trajectoire `lumiere_moy` reste ~0.18-0.20 (canopée fermée → forte compétition pour la lumière, cohérent). Non ablé directement (difficile à neutraliser proprement) mais il conditionne stade + photosynthèse, donc tout l'amont de l'uptake.
**Interconnexions.** Plantes (hauteur/canopée → ombre) → lumière → thermique → évaporation → humidité → uptake. Maison (ombre/albédo). Abri (réutilise la machinerie de capsule).
**Fidélité bio + philo.** Excellente : ombres réelles, plancher de lumière diffuse (0.15), auto-ombrage exclu. Philo #2 respectée (la hauteur émerge, la lumière est un champ, pas un bonus). Philo #5 : indice visuel, pas de chiffre HUD.
**Perf.** **Le poste le plus cher (~53 % du CPU d'après le code de `couverture.py`, `_point_in_capsule` ~35 % du tick d'après `abri.py`).** `light_index.py` coupe le O(N²) en n'itérant que les obstacles dont la capsule peut couvrir l'échantillon (bit-identique, D32). **C'est le premier levier perf du projet.**

### `humidite` (hydrologie.py)
**Rôle & I/O.** Eau des pores ∈[0,3]. Écrite par `tick_hydrology` (évaporation couplée T_sol/vent/ciel → pluie infiltrée ∝ structure → rétention soil_memory → drainage par type de sol), par la rosée, par la fonte du givre. Lue par uptake (eau), avancement des stades, germination, rosée, mycélium, thermique (terme latent).
**Importance / effet 10 ans.** Structurant. Ablation sécheresse (`humidite=0.1`) = pire scénario mesuré : vitalité 0.004 et **effondrement des auxiliaires à 0**. L'eau est le premier domino.
**Interconnexions.** Le hub le plus connecté du sol : T_sol (évaporation ↔ refroidissement latent), vent, structure (infiltration), couverture/paillage (moins d'évaporation), soil_memory (rétention), rosée/givre.
**Fidélité bio + philo.** Bonne : cycle évapo-pluie-rétention-drainage physique, spirale de sécheresse émergente (sol sec → chaud → plus sec). Diffusion spatiale déterministe. Philo #3 OK.
**Perf.** Diffusion O(plots) + évaporation par plot. Modéré.

### `n` / `p` / `k` (nutriments.py)
**Rôle & I/O.** Trois champs séparés depuis le sprint physico-chimie (éclatement du proxy `fertilite`, supprimé). Nourris par la minéralisation splittée (`split_miner` selon le tissu décomposé), fixation N₂ des Fabaceae (→ `n`), prélevés par l'uptake (`BESOIN` + loi du minimum), lessivés différemment (`leach_factor` : N≫K>P, modulé par la CEC). Deux lecteurs : le **min de Liebig** (croissance/Vigueur) et l'index lisse `fertilite_index` (moyenne, pour soil_memory/vitalité/succession).
**Importance / effet 10 ans.** Structurant et **limiteur dominant** : figer NPK haut multiplie la vitalité par 7. Sur 10 ans, `p` s'effondre à ~0.005 → le phosphore devient le minimum de Liebig qui plafonne tout. C'est le ressort long-terme n°1 à surveiller (et le point d'entrée d'une mécanique d'amendement/rotation).
**Interconnexions.** Décompo (source), Fabaceae (fixation N), CEC dérivée de l'humus (`om_stable`) et de la texture (rétention), `drainage_last` (lessivage), pH (à venir : lockout d'uptake).
**Fidélité bio + philo.** Très bonne : loi de Liebig (le minimum, pas la somme), mobilité différenciée N/P/K réaliste, CEC texture×humus. Philo #2/#3 respectées.
**Perf.** 3 diffusions O(plots) + minéralisation. Modéré ; c'est le prix du réalisme Liebig.

### Matière organique : litière + `om_active` + `om_stable` (matiere_organique.py, litiere.py)
**Rôle & I/O.** La litière fraîche est un **`Parcelle` typé par tissu** (feuille/herbace/bois/fruit), pas un scalaire — remplace l'ancien `om_fresh`. `tick_decomposition` fait la cascade fresh→active→stable avec trois destinations (humification, minéralisation N/P/K via `split_miner`, respiration/perte C), modulée par microbiome et température. Nécromasse et récolte entrent par la litière (`add_necromass`). Lu par : NPK (minéralisation), CEC/rétention (humus), `epaisseur_sol`, `tick_structure` (couvert anti-battance), thermique (isolation), pH (acides humiques), mycélium (substrat bois).
**Importance / effet 10 ans.** Structurant. La trajectoire montre l'humus se **construire** (om_stable ×4.3 sur 10 ans) : c'est la mémoire longue du jardin. Ablation `om_stable=0` : survivants 54→47, vitalité ÷2.
**Interconnexions.** Le carrefour du sol : lie décompo ↔ NPK ↔ CEC ↔ rétention d'eau ↔ pH ↔ structure ↔ mycélium ↔ épaisseur. Aucune création de carbone (conservation).
**Fidélité bio + philo.** Excellente : compartiments MO réels, litière typée par tissu, humification/minéralisation/respiration sommant à 1, pas de carbone ex nihilo. Philo #2 exemplaire.
**Perf.** O(plots) + scatter sur empreintes racinaires. Modéré.

---

## 5. Fiches — champs forts (Tier A), en bref

**`microbiome`** — bonus d'uptake fertilité (borné 0.40), vitesse de décompo, détox allélo, poids de vitalité. Émerge des exsudats de *toutes* les plantes (universalisé ; les Fabaceae gardent seulement la fixation N). Ablations : ×4 la vitalité à 1.0, ÷3 à 0. Mais **décroche à 0.02 sur 10 ans** dans le monde smoke → question ouverte de calibration. Interco : exsudats ← photosynthèse ← lumière ; détox allélo/autotox ; décompo. Philo OK (flux, jamais bonus direct).

**`temperature_sol`** (+ `temperature` T_air) — microclimat de surface (solaire·nébulosité − latente − isolation), inertie thermique. Lu par l'évaporation (spatialise l'assèchement soleil/ombre), la fenêtre du mycélium, le gel nocturne. Spirale de sécheresse voulue. Perf O(plots).

**`structure_sol`** — compaction ∈[0,1] ; forces continues de tick (bioturbation lombric +, racines pivots +, battance pluie sur sol nu −) ; les gestes bêcher/grelinette la mutent **directement** hors tick. Trois lecteurs : infiltration, aggravation d'asphyxie, pénétration racinaire. Interco forte avec `populations["lombric"]` et la couverture (anti-battance).

**`soil_memory` / `_fast` / `_deep`** — mémoire du sol annuelle (lerp 0.15) + décennale (lerp 0.02), composite effectif. Rétention d'eau, vitalité, seuils de succession. Monte lentement (0.07→0.15 sur 10 ans). C'est l'inertie historique du terrain (philo #7, hétérogénéité persistante).

**`disturbance`** — champ de perturbation spatiale déterministe (bruit hash, inertie 0.90). Herbivorie de fond, perturbations écologiques, enrichissement de la banque de graines (pionnières), succession. Reste ~0.5 stable. Attention (noté dans `mycelium.py`) : à ne **pas** confondre avec le travail du sol joueur.

**`seed_bank`** — banque latente par plot, deux couches : archétypes de succession (pioneer/nitrogen_fixer/grass/competitor) + couche espèce/génétique (moyenne+variance, D22). Vieillissement hebdo, enrichissement par perturbation, épuisement accéléré sous mulch. Moteur invisible de la succession et de la diversité fondatrice.

**`populations`** (dict par espèce) — guildes trophiques nommées (ravageur/auxiliaire/détritivore) + pollinisateurs par type, chacune un `PopulationField` borné 432 plots. Aujourd'hui **câblées** : `lombric`→`tick_structure`, prédateurs→ravageurs, `pollinator_density`→Vigueur macro, herbivorie. Perf quasi-gratuite (D32). Perception = sprites échantillonnés (fonction pure). Fidélité : dynamique proie→prédateur ordonnée, daylength, inertie.

---

## 6. Fiches — modulateurs (Tier B), en bref

**`couverture_sol`** — fraction couverte par les strates basses, 1 scatter/tick. Lue par l'évaporation (sol couvert = moins d'évaporation) et la germination férale (couvert dense = adventices étouffées). Socle de la luxuriance par stratification (D65).

**`paillage` (+ `paillage_nature`)** — levier permacole central anti-invasion (D69). Posé par le geste `pailler`, décroît vers `om_stable` (paille/aiguilles) ou `bois` (BRF, route faim d'azote + mycélium). Nature différenciée (paille/brf/aiguilles) : rétention d'eau, acidification (aiguilles), frein allélo. Lu par germination férale, âge des graines, évaporation. Flux, jamais bonus direct.

**`vent`** (champ d'abri) — force locale du vent = masse d'air uniforme × géométrie d'abri (brise-vent émergent, venturi). Lu par évaporation et wind chill. **Cache directionnel** → coût ≈0 en régime permanent (obstacles quasi statiques). Alimente le transport éolien.

**`eau_surface` + `altitude` + `marais_memory`/`_etat`** (hydrologie de surface) — l'eau de saturation excédentaire devient lame de surface, ruisselle sur le micro-relief (double-buffer déterministe, von Neumann), s'infiltre/s'évapore ; une flaque qui **dure** intègre `marais_memory` → décompo anaérobie (tourbe) + pH acide + niche marécageuse. `altitude` est un socle géométrique fixe décorrélé de l'humus (philo #7). No-op à sec → golden neutre. Marécage **émergent**, pas scripté (philo #2/#6).

**`rosee_last` + `givre`** — cycle thermo-hydrique nocturne sur le même thermomètre que le gel. Rosée liquide = tampon de survie en sécheresse + habitat détritivore + captation foliaire ; gelée blanche = `givre` accumulé puis **restitué à `humidite`** en fonte différée (zéro perte). Tensions voulues (nuit couverte/sol paillé/sol sec → peu de rosée), à ne pas « corriger ».

**`snow`** — scalaire par tuile (la neige tombe sur toute la tuile) ; isolation hivernale ajoutée au couvert de litière (effet igloo) dans le gel nocturne.

**`larvae`** (`chenille`/`syrphe_larve` + variantes nourries) — ponts de cycle de vie data-driven : chenille→herbivorie→papillon pollinisateur ; syrphe_larve→prédateur de pucerons→syrphe pollinisateur. Boucle d'interconnexion (philo #6). Un stade, pas une 5ᵉ guilde.

**`foragers`** — butineurs échantillonnés qui **marchent et déposent réellement le pollen** (arc pollinisation ③) → la nouaison (④) dépendra des visites. Pur & déterministe, recréé chaque tick, aucun état persistant. La couche `fields` ne touche pas les plantes : elle rend des `deposits` appliqués par l'engine.

**`drainage_last`** — utilitaire transient : l'eau drainée du dernier tick amplifie le lessivage N/P/K (les ions mobiles partent avec l'eau qui s'écoule). Actif mais discret.

---

## 7. Champs dormants & vue-only (Tier C) — la carte des trous

Ces champs sont **posés et souvent tickés, mais lus par personne** au tronçon courant (design volontaire « golden neutre » : on ajoute l'infrastructure d'abord, on branche les effets ensuite). Ce sont les **chantiers ouverts** :

- **`ph`** (physico-chimie ①) — maître-régulateur de la chimie, dérive décennale vers une cible héritée du `soil_type` puis acidifiée (litière + lessivage). **Lu par personne** ; ses lecteurs prévus (lockout d'uptake, fenêtres d'espèce, chlorose) arrivent aux tronçons ④/⑤. Potentiel Tier A une fois branché.
- **`mycelium`** (mycélium ①) — dynamique propre correcte (pousse sur bois humide, décline au sec) mais **effets §2 débranchés** (saprophyte/mycorhize/faune). Câblage = gros gisement d'interconnexions.
- **`allelopathie`** (allélopathie ①) — ne fait que décliner ; **aucune espèce n'a `allelopathie_emission > 0`** avant le tronçon ⑤. Route d'alimentation générique prête (`inject_field`).
- **`autotox` (+ `autotox_espece`)** (allélopathie ④) — fatigue du sol de monoculture, lue par la seule espèce traceée via `allelo_effectif`. Nulle tant qu'aucun émetteur n'est armé. Pépite pédagogique permaculture en attente d'émetteurs.
- **`epaisseur_sol`** (D57) — épaisseur foisonnante relaxant vers une cible bulk-density des `om_*` ; **tické mais lu par personne** (effets rétention d'eau + accès NPK au ①b, relief extrudé au ② rendu).
- **`altitude`** — socle géométrique fixe ; aucun tick ne l'écrit, il porte le ruissellement (donc indirectement actif via `eau_surface`).
- **`alarme`** (pollinisation ⑦) — **pur puits lu par le snapshot Godot** : la piqûre est temps réel côté vue, le moteur ne réinjecte rien.
- **`faune_encyclo`** — donnée pure d'encyclopédie, jamais lue par le tick.

> Remarque transversale : la discipline « golden neutre » est **saine** (chaque champ arrive inerte, prouvé bit-identique, avant d'être branché). L'audit la confirme partout. Le revers : une part notable de l'infrastructure de champs est **posée mais pas encore vivante** — c'est là que se trouve le plus grand potentiel d'interconnexion latent.

---

## 8. Respect de la philosophie #1-#7 — verdict transversal

- **#1 (agir sur le milieu)** & **#2 (flux → contrainte → réponse, jamais de bonus direct)** : respectés de façon remarquablement systématique. Chaque champ est un *milieu* ; les gestes joueur mutent des champs (structure, paillage), jamais des attributs de plante. Les effets « spéciaux » (brise-vent, marécage, ruche) sont **émergents** d'une géométrie ou d'une mémoire, pas scriptés.
- **#3 (déterminisme)** : garde-fou tenu partout — zéro RNG vivant, double-buffer sur diffusion/ruissellement/transport pour éviter tout biais d'ordre de balayage, bruit par hash. Invariant golden bit-identique vérifié à chaque ajout.
- **#5 (indices visuels, pas de HUD chiffré)** : les champs alimentent des overlays debug (F6) et le snapshot ; l'`alarme` et les `foragers` sont explicitement vue-only.
- **#7 (hétérogénéité persistante)** : `altitude` sur un canal de hash décorrélé de l'humus, `soil_memory_deep`, init hétérogène — le relief et la fertilité ne coïncident pas volontairement.

Aucune violation détectée. Les seules « frictions » sont des **dettes de câblage** (champs dormants), pas des entorses de design.

---

## 9. Questions ouvertes pour `/conception`

1. **Microbiome qui décroche (0.34→0.02 sur 10 ans)** — dynamique voulue (canopée fermée → moins d'exsudats) ou dérive de calibration ? Vu son poids (×4/÷3 sur la vitalité), c'est le premier point à trancher. Faut-il un plancher, ou est-ce le signal correct qu'un sol trop couvert s'appauvrit en vie microbienne active ?
2. **Phosphore comme limiteur terminal (p→0.005)** — en run éternel sans export ni amendement, P s'épuise et plafonne tout. Est-ce le ressort voulu qui pousse le joueur vers la rotation/l'amendement/le BRF, ou faut-il une source de P (roche broyée, mycorhize) ? C'est un choix de game design autant que bio.
3. **Priorité de câblage des champs dormants** — `ph` (lockout uptake + fenêtres d'espèce) et `mycelium` (mycorhize → bonus uptake, saprophyte → décompo) sont les deux qui débloqueraient le plus d'interconnexions. Lequel d'abord ? `ph` est déjà posé et lu par personne depuis le tronçon ①.
4. **Budget perf lumière** — LightField ~53 % du CPU. Y a-t-il une passe de conception dédiée à un LOD lumière (recalcul moins fréquent hors changement de canopée, comme le cache d'abri) ? C'est le seul champ dont le coût domine.
5. **`vitalite_average` très bas en canopée fermée** — est-ce une échelle à recalibrer, ou un indicateur qui n'a de sens qu'en relatif ? Il sert de poids et de métrique de succession, donc son échelle compte.

---

## 10. Rattachement à l'existant

- **DETTE** citée dans le code des champs : D3/D4/D9 (allélo/autotox/mulch nature), D10 (parité Python/C#), D22 (banque génétique), D24 (sol vivant → C#), D30 (structure), D31/D32 (vie macro + perf bornée), D49 (grimpantes, sprint actif), D56/D57 (épaisseur de sol), D65 (luxuriance/couverture), D69 (paillage anti-invasion).
- **Conceptions voisines** dans le knowledge : `docs/champs/eau/conception_hydrologie_marecage.md` (couvre `altitude`/`eau_surface`/`marais`), `docs/vegetal/allelopathie/conception_allelopathie.md` (couvre `allelopathie`/`autotox`), `docs/narration/voix/conception_voix_narratives.md` (les 5 voix des espèces faune), `etude_sol_vivant.md` (MO/microbiome).
- **Sprint actif (memory)** : D49 grimpantes. Cet audit n'y touche pas mais note que les grimpantes s'appuieront sur `lumiere` (ombre/hauteur émergente) et `structure`/`abri`.

---

### Annexe — reproductibilité

Les deux scripts d'audit (`run10.py` trajectoire 10 ans, `ablate.py` ablations) ont été écrits dans `data/code/outputs/` mais n'ont pas pu être supprimés (dossier monté en lecture pour la suppression). Ils sont réutilisables tels quels (`PYTHONPATH=data/code python3 run10.py 10`). À retirer manuellement si tu ne les veux pas versionnés.
