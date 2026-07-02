# CONCEPTION — Hydrologie de relief & marécages

> **Statut : FIGÉE le 2026-07-03** (skill `/conception`, 6 arbitrages tranchés avec
> Nico). Prête pour `/sprint-auto`. Source de vérité de la conception ; les kickoffs
> `sprints/sprint_hydrologie_marecage/0N_*.md` en dérivent.
>
> Sujet (F5 post-D57) : l'eau s'écoule des plots hauts vers les bas ; un plot saturé
> forme une **flaque** ; une flaque persistante devient un **marécage**, avec sa
> guilde d'espèces (aulne, plante carnivore, sphaigne) et sa faune de mare.

## §0 — Résumé exécutif

On ajoute la **dimension hydraulique latérale** qui manquait : jusqu'ici chaque
plot gérait son eau **verticalement et isolément** (`tick_hydrology` : pluie →
rétention → drainage par sol). Désormais l'eau **circule** entre plots selon un
**micro-relief topographique** (`altitude`), s'**accumule en surface** (`eau_surface`
= flaque) dans les cuvettes, et une flaque durable fait basculer le plot en
**marécage** (état persistant `marais_memory`, milieu anaérobie acide → tourbe).
Ce nouveau milieu ouvre une **niche** habitée par une guilde interconnectée :
**sphaigne** (ingénieur : acidifie + retient l'eau + tourbe), **aulne** (fixe
l'azote), **plante carnivore** (mange la **faune de mare**, s'affranchissant de la
faim d'azote). Le joueur peut **creuser** (cuvette) ou **drainer**.

**Invariants respectés** : déterminisme total (zéro RNG vivant, hash spatial,
double-buffer pour le ruissellement) ; flux → contrainte → réponse émergente
(jamais de bonus direct sur plante, philo #1/#2) ; hétérogénéité persistante
(#7) ; run éternel/mémoire du sol (#4) ; indices visuels (#5).

## §1 — Champ `altitude` (micro-relief topographique)

**Décision D1.** L'eau ruisselle sur un **champ `altitude` NEUF**, distinct de
`epaisseur_sol` (D57). Raison : `epaisseur_sol` = épaisseur d'**humus**, pas
l'altitude du terrain ; faire ruisseler sur l'humus créerait une boucle instable
(humus↑ → relief↑ → l'eau fuit → sol s'assèche → humus↓). La topographie est une
donnée **du terrain**, indépendante.

- `altitude : GridField` (cm au-dessus d'une référence arbitraire), **initialisé
  déterministe** au patron D56 : `_init_heterogene`-like sur un **canal de hash
  décorrélé** de l'humus — `seed_tuile = stable_str_hash(tile_id + "_alt")`,
  `alt = ALT_BASE + ALT_AMPLITUDE·(2·_hash_noise(seed_tuile,0,r,c) − 1)`.
  Amplitude modérée (micro-relief de jardin : ~0 à ~40 cm de dénivelé), bornée ≥ 0.
- **FIXE** : le tick ne le modifie jamais. Seuls les **gestes joueur** (`creuser`/
  `drainer`, §6) le changent → event-driven hors tick → **golden neutre** pour
  altitude seule (① ne fait que POSER le champ ; personne ne le lit encore).
- **Surface hydraulique** d'un plot = `altitude + epaisseur_sol` (l'humus surélève
  en second ordre). C'est la grandeur qui pilote le sens d'écoulement (§2) et que
  la vue extrude (§7, base du relief D57 déjà en place).
- Exposé au registre `get_field` (overlay debug F6) + au snapshot (§7).

## §2 — `eau_surface` + ruissellement latéral

**Décision D2.** Une **lame d'eau de surface** `eau_surface` (NEUF), distincte de
`humidite` (eau des pores, ce que boivent les racines). C'est elle qui **ruisselle**
et fait la **flaque**. Découplage physiquement juste : les pores saturent (≤ cap),
le surplus reste en surface.

**Génération (dans `tick_hydrology`)** : après infiltration/rétention, si
`humidite` dépasserait sa **capacité** `HUM_CAP` (= le plafond 3 actuel, ou un
seuil dédié), l'excédent `h − HUM_CAP` part en `eau_surface` et `h = HUM_CAP`.
Aujourd'hui le GridField écrête silencieusement à `max_val` : on **capture**
l'excédent au lieu de le jeter.

**Ruissellement (`tick_ruissellement`, NOUVEAU, appelé juste après
`tick_hydrology`)** :
- Pour chaque plot, comparer sa surface hydraulique `S = altitude + epaisseur` à
  celle de ses **4 voisins** (von Neumann). Distribuer une fraction de
  `eau_surface` vers les voisins **plus bas**, **∝ la pente** (multiple-flow-
  direction : réparti entre tous les voisins descendants proportionnellement au
  dénivelé). Coût O(plots × 4) — trivial.
- **DÉTERMINISME** : lire `eau_surface` sur un **double buffer** (snapshot en début
  de tick, écrire dans un buffer neuf) → le résultat NE dépend PAS de l'ordre de
  balayage (sinon biais directionnel = RNG déguisé). **Conservation de masse** :
  l'eau distribuée sort d'un plot et entre dans les voisins, somme conservée
  (hors infiltration/évaporation).
- **Infiltration** : une part de `eau_surface` redescend dans `humidite` si le sol
  peut encore boire (`humidite < HUM_CAP`), taux ∝ structure/drainage du sol (un
  sol grumeleux réabsorbe la flaque, un sol battu/argileux la garde en surface).
- **Évaporation de surface** : `eau_surface` perd une fraction (lame libre → évapore
  plus vite que le sol ; couplée au même moteur évaporation que l'hydro).
- Aux **bords du monde** : l'eau qui ruisselle au-delà du dernier plot est **perdue**
  (exutoire implicite — pas de tuile voisine simulée, cf. option B des chemins).

**Flaque** = `eau_surface > SEUIL_FLAQUE` (visible §7). **Golden RE-FIGÉ LARGE
ANNONCÉ** : l'eau bouge enfin entre plots → le bilan hydrique de chaque plot change
(surtout les cuvettes se gorgent, les bosses s'assèchent). Dérive attendue,
localisée à la topographie, expliquée. **Non-régression D39** (asphyxie du pommier)
et **D57** à re-vérifier : le nouveau bilan ne doit pas re-casser `test_senescence`
(le monkeypatch `_meteo_labo` reste ; si une cuvette gorge le pommier, ajuster
l'altitude du banc de test, pas le modèle). Tests : conservation de masse d'eau,
anti-emballement 500 ans, écoulement bien orienté (une cuvette accumule).

## §3 — Marécage (`marais_memory` + hystérèse)

**Décision D4.** Le marécage est un **état persistant émergent**, pas un type de
sol scripté. Miroir de `asphyxie_memory`/`drought_memory` déjà en place.

- `marais_memory : GridField` (∈ [0,1], `max_val=1`) intègre lentement la présence
  de flaque : `marais_memory += (cible − marais_memory)·MARAIS_LERP` où `cible = 1`
  si `eau_surface > SEUIL_FLAQUE` sinon `0`. Intégration LENTE (une flaque doit
  **durer** des semaines pour faire un marais).
- **Hystérèse** : le plot est « marais » quand `marais_memory > MARAIS_ON` ; il en
  sort quand `marais_memory < MARAIS_OFF` (`MARAIS_OFF < MARAIS_ON`) → pas de
  clignotement, persistance (philo #4 : le sol garde mémoire de son passé humide).
- **Effets du marais** (tous branchés sur des mécaniques existantes → interconnexion,
  peu de code neuf) :
  - **Décompo anaérobie** : `speed` de `tick_decomposition` ↓ ∝ `marais_memory`
    (`×(1 − MARAIS_DECOMP_MALUS·marais)`). La MO ne se minéralise plus → elle
    **s'accumule** = **tourbe** → `epaisseur_sol` monte **émergemment** (via
    `_cible_epaisseur`, aucun code neuf). Couple **D40** (speed sensible au milieu).
  - **Acidification** : `tick_ph` pousse le pH vers `PH_TOURBE` (~4.0) ∝
    `marais_memory` (terme additif borné). Un marais est acide.
  - **Recul du mycélium** aérobie saprophyte (anaérobie) : terme ∝ marais qui
    freine `mycelium` (interconnexion champignon, optionnel/léger).
  - **Niche** : `marais_memory` haut + humide + acide = signature de germination des
    espèces marécageuses (§5), lue par `niche_index`.
- Exposé au snapshot (§7). Signe sémiologique/diégétique possible (`marais`).
- **Golden** : le **smoke reste SANS cuvette profonde** → aucun marais ne s'y forme
  → ③ **golden NEUTRE**. Observation via un **banc `tourbiere`** dédié (cuvette
  gorgée forcée) + oracle Python. Si un plot du smoke bascule, re-figeage MAÎTRISÉ
  annoncé (à éviter en calibrant l'altitude du smoke).

## §4 — Faune de mare (guilde aquatique)

**Décision D5.** Nouvelle faune DÉDIÉE, data-driven (`TrophicSpec`), sur le patron
du registre existant (`fields/population/registry.py`).

- **`moustique`** (category `ravageur` ou `aquatique` — au choix d'impl., neutre) :
  `resource_fn` = `eau_surface`/`marais_memory` (prolifère sur l'eau stagnante) ;
  `habitat_fn` = flaque ; `predators = ("libellule",)` + **puits carnivore** (§5).
  Fenêtre photopériode estivale (chaleur). Larves aquatiques → adultes volants.
- **`libellule`** (category `auxiliaire`) : `resource_fn` = `_espece_grid("moustique")`
  (prédateur), `habitat_fn` = flaque/marais + végétation haute (perchoir). Sommet de
  chaîne aquatique. Fenêtre estivale.
- Mini-chaîne : eau → moustique → libellule (+ carnivore §5). **Interconnexion**
  avec l'existant : la flaque nourrit le moustique, le moustique nourrit la
  libellule et la carnivore.
- **Golden** : nouvelles espèces absentes du smoke (pas de flaque) → densité nulle
  → re-figeage population NEUTRE (ou maîtrisé si l'ajout décale l'ordre de tick —
  annoncer). **5 voix** de chaque espèce (§9).

## §5 — Espèces végétales de la guilde (aulne · sphaigne · carnivore)

**Décision D3.** Trois espèces, chacune un **flux** (jamais un bonus direct). Toutes
avec **niche marécageuse** (germent où `marais_memory`/humidité hauts + pH acide),
et leurs **5 voix** (§9). Règle projet « toute plante = ses 5 voix ».

### §5.1 Aulne (`Alder`, famille **Betulaceae** NEUVE, pérenne ligneux)
- `PerennialWoody` (patron `plants/perennials.py`), strate haute, caduc.
- **Fixe l'azote** : actinorhizien (symbiose *Frankia*), réutilise le mécanisme
  `nitrogen_fixer` (archétype Medicago) → **enrichit le N du sol** sous lui. Un
  fixateur ARBORÉ (premier du catalogue) → enrichit durablement le marécage.
- `tolerance_asphyxie` **élevé** (gène existant) → survit les pieds dans l'eau là
  où pommier/noyer meurent (D39). Niche = berge humide.
- Anémophile (chatons) → attractivité pollinisateur ~0 (déjà géré par familles
  anémophiles du registre).

### §5.2 Sphaigne (`Sphagnum`, mousse, strate basse — INGÉNIEUR d'écosystème)
- Nouvelle forme : **mousse** (tapis, pas de vraies racines, pas de bois). Modèle
  minimal (pas de morphogénèse segments : couvre-sol). Famille Sphagnaceae ou
  catégorie « bryophyte ».
- **Ingénieur** (3 flux) : (a) **acidifie** le pH local vers l'acide (terme dans
  `tick_ph` sous une sphaigne vivante — ATTENTION double-comptage avec l'acidif.
  du marais §3 : la sphaigne ACCENTUE, borné ensemble) ; (b) **rétention d'eau
  énorme** (bump de `soil_memory`/rétention sous le tapis → garde le sol gorgé) ;
  (c) **nécromasse quasi-indécomposable** → litière `mousse`/tourbe à `decay` très
  bas → **tourbe** (épaisseur↑). La sphaigne **crée** le marais autant qu'elle
  l'habite. Niche = humide + acide.

### §5.3 Plante carnivore (`Drosera` — rossolis, herbacée, strate basse)
- **PUITS sur la faune de mare** : le premier **végétal-prédateur**. Chaque
  `Drosera` vivante retire une fraction de la densité `moustique` sur ses
  `foliar_plots` (couplage plante→champ faune, NOUVEAU — cf. kickoff ⑥). Le flux
  **insectes → azote fonctionnel** l'affranchit de la **faim d'azote** : elle
  prospère sur tourbe acide **pauvre en N** là où les autres crèvent.
- Modèle : pas un bonus arbitraire — la carnivore n'a pas de pénalité de carence N
  (son N vient des proies), et son emprise sur `moustique` est un vrai prélèvement
  (la faune baisse localement, observable). Niche = marais acide pauvre.
- Petite fleur (entomophile faible) — mais son intérêt est le piège, pas le nectar.

## §6 — Gestes joueur `creuser` / `drainer`

**Décision D6.** Deux gestes sur le MILIEU (philo #1), coûteux en Vigueur,
event-driven (hors tick → **golden neutre**). Dans `sim/actions.py` + pont.
- **`creuser`** (une mare) : abaisse `altitude` du plot ciblé d'un cran
  (`CREUSER_DELTA` cm) → cuvette → l'eau s'y accumule (via §2). Coût élevé
  (terrassement), perturbe le sol (↓ microbiome, comme `becher`). Borné ≥ 0.
- **`drainer`** : évacue `eau_surface` du plot (vide la flaque) **et** abaisse
  `marais_memory` (assèchement forcé) — creuser une rigole. Coût modéré-élevé.
- Maîtrise : objets `("terrassement", "bêche")` (cf. `cout_action`), techniques
  déclarables. Découverte à la 1ʳᵉ utilisation (D60).

## §7 — Vue Godot (pur-vue, F5)

- **Relief** : la base du losange (déjà extrudée par l'épaisseur, D57) intègre
  `altitude` → `surface = altitude + epaisseur` (le terrain a des creux/bosses même
  sans humus). Réglage exagération commun.
- **Flaque** : `eau_surface > SEUIL_FLAQUE` → lame d'eau translucide bleutée
  réfléchissante au-dessus du plot (∝ profondeur).
- **Marécage** : `marais_memory` haut → sol sombre saturé, teinte tourbeuse ;
  tapis de **sphaigne** (couvre-sol vert-glauque), **aulnes** en berge.
- **Faune de mare** : moustiques (nuée fine au-dessus des flaques), libellules
  (vol stationnaire) via `MacroLife`/sprites échantillonnés.
- **Gestes** : curseurs `creuser`/`drainer` (palette D55 future) ; feedback du
  changement d'altitude/flaque.
- Snapshot : blocs `altitude`, `eau_surface`, `marais` par tuile (grilles denses,
  patron `epaisseur`/`t_sol`). Bumps pont au fil des tronçons.

## §8 — Découpage & politique golden

| # | Tronçon | Golden |
|---|---------|--------|
| ① | Champ `altitude` déterministe + expo snapshot | **NEUTRE** (lu par personne) |
| ② | `eau_surface` + `tick_ruissellement` (double-buffer) + expo | **RE-FIGÉ LARGE annoncé** |
| ③ | Marécage `marais_memory` + hystérèse + effets décompo/pH + banc `tourbiere` | NEUTRE hors banc |
| ④ | Faune de mare (moustique + libellule) + 5 voix | pop NEUTRE / maîtrisé annoncé |
| ⑤ | Aulne (Betulaceae) + Sphaigne (ingénieur) : moteur + niches + 5 voix | NEUTRE hors smoke |
| ⑥ | Carnivore + couplage PUITS→`moustique` + 5 voix | NEUTRE hors smoke |
| ⑦ | Gestes `creuser` / `drainer` (actions + pont) | **NEUTRE** (event-driven) |
| ⑧ | Vue Godot (relief+altitude, flaque, marais, sphaigne/aulne/faune, gestes) | pur-vue, F5 |

**Perf** : ruissellement O(plots×4) trivial ; budget ≤ +10 % tick/tronçon. Le
double-buffer du ② est le seul point à surveiller (une allocation grille/tuile/tick,
négligeable). Aucun recalcul géométrique lourd type LightField.

**Ordre imposé** : ④ (faune moustique) AVANT ⑥ (carnivore-puits qui la lit). ②
avant ③ (marais lit `eau_surface`). ① avant ② (ruissellement lit `altitude`).

## §9 — Voix narratives (corpus par espèce)

Chaque espèce ajoutée (aulne, sphaigne, carnivore, + faune moustique/libellule)
reçoit ses **5 voix** (cf. `CONCEPTION_VOIX_NARRATIVES.md`) :
1. **Encyclopédie** : fiche 3 niveaux (basique → bio → effets écosystémiques).
2. **Carnet** : concepts/causes illustrés (`CONCEPT_DE` — ex. `asphyxie`→eau,
   `marais`, fixation d'azote, carnivorie).
3. **Pages secrètes** : lore si l'espèce en porte (tourbière = fort potentiel
   poétique/paysan : « la terre qui garde ses morts », rossolis des sorcières).
4. **Magazine** : rattachement famille (Betulaceae/Sphagnaceae/Droseraceae) + offre.
5. **Événements** : marqueurs de cycle consignés au ledger (formation de marais,
   1ʳᵉ capture carnivore, arrivée libellule).

Les corpus détaillés sont écrits **dans les tronçons ④/⑤/⑥** (l'espèce arrive avec
ses voix), golden neutre (voix hors tick).
