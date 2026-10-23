# Conception — FLUIDITÉ DU JARDIN EN AN 2 (D114 recadrée)

> Figée le 2026-10-23 (`/conception D114`, accord Nico : cible + périmètre).
> Sprint : `sprints/perf/fluidite/sprint_fluidite_an2/`. **Golden jamais re-figé** :
> référence `fecccded8cd146368623372919f4bdc6c61fb8bb997c75fdc59806f08dc3898b`.

## 1. Pourquoi D114 est recadrée

D114 disait : « tick an 2 1 417 → 1 884 ms (+33 %) après D111 ① ». Re-mesure à HEAD
`5c69ac6` (VM, graine 1521550718, monde `full`, `SimServer.cmd_step_week`) :

| cas | tick an 0 / 1 / 2 | automate an 2 | snapshot an 2 | plantes an 2 |
|---|---|---|---|---|
| sans automate | 591 / 921 / 1 074 ms [n=1 run] | — | 183 ms [n=1 run] | 654 |
| automate ON (curatif, LIBRE) | 564 / 853 / 1 022 ms [n=1 run] | 24 ms [n=1 run] | 172 ms [n=1 run] | 613 |

- Le 1 884 ms venait d'**un run sous charge** ; au ⑦ du sprint sol, le tick an 2 était déjà
  1 042-1 082 ms [n=2 runs], un run à 1 422 ms écarté (charge VM 3,6-5,1). Le critère
  littéral de D114 (≤ 1 417 ms à population ≥ 675) est **déjà tenu**.
- **L'automate est innocent côté Python** : 24 ms/tick, population plus basse (il désherbe),
  roulement +6/−3 plantes/sem contre +5/−3 [n=1 run]. Le ralentissement ressenti au F5
  vient d'ailleurs — **Nico : « c'est peut-être un autre ralentissement, il faut mesurer »**.
- Au rythme nominal (60 s/sem), un tick de ~1,4 s sur le PC de Nico [estimation ×1,3 vs VM,
  mesure du 2026-07-09] est invisible (step asynchrone, `Task.Run`).

**Le goulot ressenti est la VUE.** Banc Godot VM (`tools/perf_vm.sh -E 30 -A 1 -W 90`,
llvmpipe — FPS non portables, proportions oui) [n=1 run, 30 s] :
- demandé 1 s/semaine → **obtenu 2,73 s/semaine** ;
- retard : **semaine en application 13,9 s sur 30**, step en vol 2,9 s ;
- pipe 1 139 ms dont tick 874 ms ; parse JSON 150-297 ms (thread du pool) ; réponse 1,5 Mo ;
- **cuisson hors budget** : budget 4 ms/image, pics 60-74 ms/image (le budget n'est testé
  qu'APRÈS la 1ʳᵉ plante : une seule cuisson lourde le crève) ;
- étalement : application ~1 ms/plante sur le thread principal [mesure VM 2026-10-15], tranche
  de 6 ms/image → ~650 plantes ≈ 110 images ≈ 3,6 s à 30 FPS : **à lui seul incompatible avec
  1 s/semaine**.

## 2. Ce que les mesures excluent (et pourquoi)

- **Envoyer seulement les plantes changées** : 589/590 plantes ont une géométrie qui bouge de
  > 1 cm par semaine [n=1 semaine, s85] (vraie croissance, nouveaux segments). Un delta par
  plante ne gagnerait rien. Écarté.
- **Brider la population** : interdit (D114, Nico).
- **Re-figer le golden** : rien dans ce sprint ne touche la dynamique. Toute optimisation
  moteur est **bit-identique** ; si elle bouge le hash, on l'abandonne.

## 3. Cible (Nico, 2026-10-23)

Sur le **PC de Nico** (i5-4200H, HD 4600), **an 2**, cadence de test **1 s/semaine** :
**≤ 1,5 s/semaine effectives** et **aucune image > 100 ms**, **automate branché ou non**.
Nominal 60 s/semaine inchangé. Validation **par mesure** (banc E converti), F5 = ressenti seul.

Budget intermédiaire VM (proxy, llvmpipe) : semaine effective ≤ 1,5 s au banc E `-A 1 -W 90`,
p99 image ≤ 100 ms hors rendu GPU logiciel (postes CPU + étalement + cuisson).

## 4. Décisions

1. **Mesurer avant d'optimiser** (①) : un banc unique, répété (n ≥ 3 runs, charge VM
   contrôlée), headless ET Godot, automate ON/OFF **et onglet Automate ouvert/fermé** — pour
   trouver « l'autre ralentissement » au lieu de le supposer.
2. **Moteur bit-identique** (②) : postes plats du profil an 2 (cProfile s88, 584 pl.) —
   `tick_populations` 17 %, `apply_disturbances` 11 %, `tick_light` 10 %, `grow_plant` 8 %,
   `_apply_uptake` 7 %, `tick_soil_memory` 6 % ; `is_alive` ~200 k appels/tick,
   `grids.at_plot` ~210 k. Cible −20 % sur le tick an 2 [VM], golden INCHANGÉ.
3. **Pont allégé** (③) : `auxin` par segment (inutilisé par la vue — vérifié `grep` C#) retiré
   **du snapshot seulement** (`structure_to_dict()` reste intact : save/tests l'utilisent) ;
   flottants arrondis à la précision perceptible ; coût `_snapshot` et taille ciblés à −40 %.
   Perception pure → golden intact ; version de pont incrémentée.
4. **Vue** (④) : (a) la lecture des plantes du snapshot (`PlantStructure.FromSnapshot` & co.)
   passe sur le **thread du pool**, à côté du parse JSON — le thread principal n'applique que
   des structures prêtes ; (b) la cuisson respecte son budget (diagnostiquer la cuisson unique
   de 60-74 ms) ; (c) traiter le ralentissement « automate » identifié au ①.
5. **Bilan** (⑤) : banc VM final, protocole de mesure PC pour Nico, clôture D114.

## 5. Coût / risques

- ① et ⑤ : instruments seulement. ② : risque de dérive golden → garde bit-identique stricte.
- ③ : risque de casser un lecteur du snapshot (tests `tests/simserver/*`, outils `mesures/`,
  C#) → inventaire au `grep` avant de retirer une clé.
- ④ : risque de thread (un `GDict` partagé entre pool et thread principal) → la pré-digestion
  ne touche **que** le snapshot fraîchement parsé, jamais un nœud de scène.
