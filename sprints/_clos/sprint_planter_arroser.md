# Sprint — `planter` & `arroser` (+ modèle « eau » : drainage du sol & asphyxie)

> **Kickoff autosuffisant** (démarrage à froid). Implémente les **deux derniers
> gestes de base** (`planter`, `arroser`) + le **modèle « eau »** au tick
> (drainage par `soil_type`, asphyxie par paliers). La conception est **FIGÉE** :
> la source de vérité des décisions est
> **`data/code/CONCEPTION_PLANTER_ARROSER.md`** (§3 décisions Q1–Q12, §4
> calibrage, §6 découpage). Ce fichier porte le **plan d'implémentation testable**.
>
> Règles projet : **moteur Python = source de vérité** ; **pédagogie explicite** ;
> **conserver tout code/test** ; pur **Python** (le volet Godot des gestes viendra
> plus tard). Ampleur : **moyen→gros** → **3 sessions avec `/clear`** (balises
> ci-dessous). Si tu préfères un dossier découpé `00_etat.md` + `0N_*.md`,
> dis-le ; sinon ce fichier unique pilote les 3 sessions.

## Ce qu'on construit, en une phrase
`planter` **dépose une graine** (banque-joueur, gènes propres) qui **germe au bon
moment** via la succession ; `arroser` **mouille le champ humidité** (la plante
se débrouille au tick, Q12 a) ; **trop arroser noie** (asphyxie par paliers) et
le **sol** (`soil_type`) décide de la vitesse de drainage — **pas un bouton**.

## État de départ (vérifié au kickoff, 2026-06-13)

- **Les 2 gestes n'existent pas encore** dans le moteur (derniers gestes de base
  absents — page d'accueil CLAUDE.md). Backlog t4 : exclus du pont tant que
  Python ne les porte pas.
- **Banque-joueur** : `sim/seeds.py:PlayerSeedBank` — lots par espèce,
  `take(species)` FIFO rend `Seed{species, genes}`, sérialisable JSON. Vit dans
  `game_state["player_seed_bank"]` (lu `engine.py:693`). **Source de `planter`**.
- **Banque-sol agrégée** : `fields/seedbank.py:SeedBank` (par espèce×plot,
  génétique **moyenne/variance**) — c'est le canal de la **succession
  spontanée**, gènes **échantillonnés** (`sample_genes`). On **n'y dépose pas**
  la graine plantée (elle diluerait les gènes) → nouvelle structure **distincte**.
- **Germination spontanée** : `sim/succession.py:39 succession()` +
  `:123 spring_flush()`. Boucle : plot occupé → skip ; sinon `niche_index` →
  `germination_candidates` → `tile.add_plant(plant_class, r, c)` →
  `sample_genes(r, c, …)` écrit `new_plant.genes`. **C'est là** qu'on lèvera en
  priorité les **grains en attente** (avec leurs gènes **propres**, sans
  `sample_genes`).
- **Créer une plante** : `world/tile.py:145 add_plant(cls, r, c)` → `PlantInstance`
  stade semis ; vérifie **les bornes** (`is_valid_plot`), **pas l'occupation**
  (empilement possible, Q4). Position interne continue (`x_cm/y_cm`).
- **Humidité** : `eco.humidite`, échelle **[0, 3]**. `ecofields.py:211
  tick_hydrology` = évaporation (× temp) + `BASE_RAIN=0.015` + rétention
  (`soil_memory × SOIL_RETENTION`) + **`h *= DRAINAGE` (0.993 CONSTANT)**.
  Diffusion `HUMIDITY_INERTIA=0.55`. Aléas Pluies/Canicule écrivent déjà
  `+0.5 / −0.4` → calibre de référence pour la dose.
- **Croissance / stagnation** : `engine.py:195`
  `ok_hum = hum >= 0.15/tolerance_secheresse` → stagnation **« sec »**
  (`:210`). **Pas de versant haut** aujourd'hui → enjeu de l'asphyxie.
- **Santé / stress** : `engine.py:302`
  `drought_stress = max(0, 1 - hum/0.5) if hum < 0.5` → `drought_memory`
  (lerp 0.05, `:303`). **Symétrie** exacte à construire pour l'excès.
- **Maîtrise** : `maitrise_detection.py:163` a un **hook** `marquer_replante`
  (cultivé vs féral, §9.4). Coûts : `actions.py:82 COUTS` /
  `:100 OBJETS_TOUCHES` (`FAIBLE=5`, `MODERE=15`, `URGENCE_MULT=1.5`).
- **Pont** : `tools/sim_server.py`, `ENGINE_VERSION = "0.3.2"`. `_do_action`
  route par verbe ; `_plant_at(tile, x_cm, y_cm)` résout une plante. Le snapshot
  a déjà un bloc `player` (0.2.0) — il faudra **exposer la banque-joueur**.
- **Golden** : 2 tuiles — **T0 `terre` (hum 1.5)**, **T1 `argile` (hum 2.0)**
  (`tests/test_golden.py:62-69`). Empreinte courante `16a1b937…` (smoke test).

## Modèle figé (résumé — détail dans CONCEPTION_PLANTER_ARROSER.md §2-4)

```
# planter (event-driven, golden INTACT)
seed = player_seed_bank.take(species)            # refus si lot vide (Q2)
grains_en_attente[(r,c)].append(GrainEnAttente(  # gènes PROPRES, non moyennés (A)
    species, genes=seed.genes, cultive=True))    # tag replanté différé (B)
# → la succession lève le grain sur plot LIBRE + niche OK, gènes tels quels (Q1)

# arroser (event-driven, golden INTACT)
eco.humidite[r,c] = min(3.0, hum + DOSE_ARROSAGE) # cumulatif, cap 3 (Q9)
                                                  # 2 phases (Q10), MODÉRÉ × urgence

# modèle eau (TICK — golden RE-FIGÉ T1 uniquement)
h *= DRAINAGE_PAR_SOL[tile.soil_type]             # terre=0.993 inchangé (Q8,Q11)
ok_hum = (hum >= 0.15/tol) and (hum <= HUM_NOYE)  # stagnation « noyé » par le haut
if hum > HUM_EXCES: uptake ↓ ∝ excès             # palier 1 (doux, réversible)
asphyxie_memory += (excès_stress - asphyxie_memory)*0.05
if asphyxie_memory soutenu: health ↓             # palier 2 (si ça dure)
```

Chiffres de départ (à valider, CONCEPTION §4) : `DOSE_ARROSAGE=+0.5`,
`HUM_EXCES=2.3`, `HUM_NOYE=2.6`, `DRAINAGE_PAR_SOL = {terre 0.993, argile 0.997,
sable 0.985, roche 0.975}`. **Modulation espèce** (`tolerance_exces_eau`) :
**commencer sans** (simplicité), ajouter si le test montre que tout se noie pareil.

---

## SESSION A — `planter` (golden INTACT)  ⟶  `/clear` à la fin

1. **`GrainEnAttente`** dans `fields/seedbank.py` (à côté de `SeedBank`,
   **sans la modifier**) : dataclass `{species, genes: dict, cultive=True,
   semaine_depot}`. Stockage **par plot** : nouvel attribut
   `grains_en_attente: dict[(r,c), list]` (où le porter — `EcoFields` ou `Tile` —
   à trancher : **reco `Tile`**, c'est le porteur des plantes ; la banque-sol,
   elle, est sur `eco`. Choisis et note-le). → **vérif** : golden inchangé
   (structure neuve, vide au repos, lue nulle part au tick).
2. **Dépôt** : `planter(game_state, player, tile, eco, species, r, c)` dans
   `sim/actions.py` : `seed = player_seed_bank.take(species)` (refus + message si
   lot vide) ; crée le `GrainEnAttente` (gènes de la `Seed`, `cultive=True`) ;
   coût **`FAIBLE`** via `cout_action(…, "planter", _objets_action("planter"))`
   (+ entrées neuves dans `COUTS`/`OBJETS_TOUCHES`). Phase planification (pas
   d'`URGENCE`). → **vérif** : test dépôt + refus lot vide + coût débité.
3. **Levée différée** dans `sim/succession.py` (`succession()` ET
   `spring_flush()`) : **avant** le balayage adventices, pour chaque plot
   **libre** avec niche favorable portant un `GrainEnAttente`, lever **le plus
   ancien** : `tile.add_plant(class, r, c)` puis écrire **ses gènes propres**
   (`new_plant.genes = grain.genes`, **pas** `sample_genes`) + **transmettre le
   tag** (`marquer_replante` si `grain.cultive`). Retirer le grain levé.
   Déterministe (réutilise le hash de niche existant). → **vérif** : un grain
   posé sur plot libre lève avec **ses** gènes + tag ; posé sur plot occupé
   **patiente** ; lève quand le plot se libère.
4. **Golden** : `python3 -m tests.test_golden` doit rester **`16a1b937…`**
   (planter event-driven, structure neuve vide → la succession ne trouve aucun
   grain → comportement inchangé).

**Critères Session A** : [x] dépôt + refus lot vide + coût ; [x] levée gènes
propres + tag transmis ; [x] empilement → patiente → lève au dégagement ;
[x] **golden `16a1b937…` intact**.

> ✅ **Session A CLOSE (2026-06-13).** `GrainEnAttente` (`fields/seedbank.py`,
> gènes propres + `cultive`/`player`/`semaine_depot`), `Tile.grains_en_attente`,
> `planter` (`sim/actions.py`, coût `FAIBLE` binaire, refus lot vide en amont),
> levée différée (`succession.py` helper `_lever_grains_en_attente`, canal de hash
> distinct, `marquer_replante` en import local). `test_planter` 18/18, golden
> `16a1b937…` intact, vigueur 135/135, croissance 67/67. Détail : `journal.md`.

→ `journal`/`00_etat` court, **commit**, **`/clear`**.

---

## SESSION B — `arroser` + modèle « eau » (golden RE-FIGÉ T1)  ⟶  `/clear`

5. **`arroser`** (event-driven, golden intact) dans `sim/actions.py` :
   `arroser(game_state, player, eco, r, c, urgence=False)` → `eco.humidite` au
   plot `+= DOSE_ARROSAGE`, **cap 3.0**, cumulatif (la diffusion `tick_hydrology`
   mouille autour). Coût **`MODERE`** ; **`× URGENCE_MULT` si `urgence`** (phase
   saison). → **vérif** : champ monte, plafonne à 3, **redescend** au tick
   suivant (évaporation/drainage) ; coût simple en planif, × urgence en saison.
6. **Drainage par sol** (TICK) dans `fields/ecofields.py:tick_hydrology` :
   remplacer `DRAINAGE` constant par `DRAINAGE_PAR_SOL[soil_type]` (**terre =
   0.993 inchangé**). ⚠️ `tick_hydrology` doit **connaître le `soil_type`** :
   le passer en argument (depuis l'`engine`, qui a la `Tile`) ou poser
   `eco.soil_type` à l'init. → **vérif** : T0 (terre) **bit-identique** ;
   argile/sable drainent comme attendu (test ciblé hors golden).
7. **Asphyxie par paliers** (TICK) :
   - `engine.py:195` : `ok_hum` faux **aussi par le haut** (`hum > HUM_NOYE`) →
     stagnation **« noyé »** (nouveau message, miroir de « sec » `:210`).
   - **Uptake ↓** ∝ excès au-dessus de `HUM_EXCES` (palier 1, doux) — là où
     l'uptake est calculé (`_apply_uptake` / `plant_uptake`).
   - **`asphyxie_memory`** sur `PlantInstance` (`plants/base.py`, défaut 0.0,
     miroir de `drought_memory`) : intégration lerp 0.05 d'un `exces_stress`
     quand `hum > HUM_EXCES` ; **santé ↓** quand soutenu (palier 2), via le
     chemin santé existant (`_tick_senescence_health` / là où `drought` pèse).
   → **vérif** : sous le seuil = rien ; au-dessus = croissance ↓ puis, si ça
   dure ~3-4 sem, santé ↓ ; un assèchement lève l'asphyxie (réversible).
8. **Golden RE-FIGÉ — MAÎTRISÉ** : `python3 -m tests.test_golden` **va bouger**.
   Exigence : **dérive LOCALISÉE sur T1 (argile)** — **T0 (terre) doit rester
   bit-identique**. Inspecter le diff tuile par tuile ; **si T0 bouge → BUG**
   (un couplage a fui : le modèle eau touche autre chose que prévu). Re-figer
   l'empreinte **seulement** après avoir vérifié et **expliqué** la dérive T1
   (drainage argile 0.997 + bord d'asphyxie). Noter la nouvelle empreinte +
   l'explication dans le commit (règle CLAUDE.md : re-figeage maîtrisé et annoncé).

**Critères Session B** : [x] arroser monte/plafonne/redescend + coûts ;
[x] drainage par sol ; [x] asphyxie 2 paliers réversible + stagnation « noyé » ;
[x] **golden re-figé — diff expliqué** (⚠️ T0 a bougé aussi, voir ci-dessous).

> ✅ **Session B CLOSE (2026-06-13).** `arroser` (`sim/actions.py`, `+DOSE_ARROSAGE
> =0.5`, cap 3.0, coût `MODERE` × urgence), drainage par sol (`DRAINAGE_PAR_SOL`,
> `tick_hydrology(soil_type)`, terre=0.993 fallback), asphyxie 2 paliers
> (palier 1 uptake ∝ excès courant réversible dans `plant_uptake` ; `asphyxie_memory`
> miroir de `drought_memory` → palier 2 santé via flux `week·7` dans
> `_tick_senescence_health`), stagnation « noyé » (`ok_hum` borné par le haut à
> `HUM_NOYE`). `test_eau` 20/20, toute la suite verte (`test_senescence` fixture
> réajustée : argile gorgée → terre médiane, sinon le pommier mourait asphyxié).
>
> **⚠️ Re-figeage : T0 A BOUGÉ AUSSI** (golden `16a1b937…` → `7ee907d3…`). La
> prémisse §5 de la conception (« terre n'atteint jamais HUM_EXCES, T0 inerte »)
> était **fausse** : `soil_memory`+rétention font monter terre à **2.636** en
> automne (sem. 46) → asphyxie légitime sur les DEUX sols (terre ~10 %/an des
> semaines >2.3, argile ~43 %). Dérive T0 = palier-1 uptake réduit + sa cascade
> (vérifié : 100 % attribuable au modèle eau, aucune fuite hors-périmètre, rien
> en semaine 1). **Décision Nico (option A, 2026-06-13)** : asphyxie = phénomène
> global, on assume la dérive T0+T1, calibration figée conservée. Détail :
> `journal.md`.

→ **commit avec l'explication du re-figeage**, **`/clear`** puis Session C (pont).

---

## SESSION C — Pont + suite complète  ⟶  clôture

9. **Pont** `tools/sim_server.py` :
   - Router `verb == "planter"` (target : `tile` + `x_cm/y_cm` + `params.species`)
     → `planter(...)`. Router `verb == "arroser"` (target : `tile` + `x_cm/y_cm`,
     `params.phase`/`urgence`) → `arroser(...)`. Messages clairs (« graine
     déposée — germera au bon moment » / « arrosé : +X » / « lot vide »).
   - **Exposer la banque-joueur** au snapshot (lots plantables) pour que la vue
     propose les graines — étendre le bloc `player` existant.
   - **Bump `ENGINE_VERSION` 0.3.2 → 0.3.3** + ligne d'historique (commandes
     `planter`/`arroser`, banque-joueur au snapshot).
   → **vérif** : `tests/test_sim_server.py` — planter par position dépose ;
   arroser monte le champ ; **déterminisme byte-à-byte** conservé.
10. **Suite complète** : `test_golden` (re-figé T1, attendu), `test_vigueur`
    (coûts planter/arroser), `test_croissance` (non-régression — l'asphyxie
    touche le chemin croissance), `test_sim_server`. **`main.py` tourne**.

**Critères Session C** : [x] pont route planter/arroser ; [x] banque-joueur au
snapshot ; [x] protocole 0.3.3 ; [x] déterminisme pont ; [x] toute la suite
verte (golden = empreinte Session B `7ee907d3…`, INCHANGÉ — le pont ne touche pas
le moteur).

> ✅ **Session C CLOSE (2026-06-13) — SPRINT CLOS.** Routing `planter`/`arroser`
> dans `_do_action` (cible position → plot-foyer via helper `_plot_at`, miroir de
> `PlantInstance.plot_foyer`). `planter` : `params.species` validé contre
> `PLANT_CATALOGUE`, refus « lot vide » en amont (sans coût), façade `A.planter`,
> coût `FAIBLE`. `arroser` : `params.urgence`/`phase=="saison"` → `× URGENCE_MULT`,
> message humidité avant→après. Banque-joueur attachée à `cmd_init` (remplie à la
> récolte) + exposée au snapshot `player.seeds`. `ENGINE_VERSION` 0.3.2 → **0.3.3**.
> `test_sim_server` **113/113** (section 12 neuve, 2 runs byte-identiques) ; golden
> `7ee907d3…` intact, `test_vigueur` 135/135, `test_croissance` 67/67, `test_planter`
> 18/18, `test_eau` 20/20 ; `main.py` exit 0. Détail : `journal.md`.

## Pièges identifiés (à ne pas réapprendre à chaud)

- **NE PAS déposer la graine plantée dans la banque-sol agrégée** : ses gènes
  seraient moyennés → la sélection D17/D22 perd son sens. `GrainEnAttente` est
  une structure **distincte**, gènes **propres**, levée **sans** `sample_genes`.
- **T0 (terre) est le garde-fou de revue** du re-figeage : terre garde 0.993 et
  T0 n'atteint jamais `HUM_EXCES` (hum ≤ 1.5) → **T0 doit rester bit-identique**.
  Si elle bouge, le modèle eau a fui hors de son périmètre — **c'est un bug, pas
  un re-figeage**. Ne re-fige JAMAIS un golden dont T0 a bougé.
- **`asphyxie_memory` est le miroir EXACT de `drought_memory`** : même lerp
  (0.05), même bornage [0,1], chemin santé symétrique. Ne pas inventer un autre
  mécanisme — copier la gradation sécheresse par symétrie haute.
- **`ok_hum` à deux bornes** : aujourd'hui une seule (`>= seuil_sec`). Ajouter la
  borne haute (`<= HUM_NOYE`) sans casser la basse ni la modulation
  `tolerance_secheresse`.
- **`tick_hydrology` ne connaît pas le sol aujourd'hui** : il faut lui passer le
  `soil_type` (la `Tile` le porte, `:65`) — décider du canal (argument vs
  `eco.soil_type` posé à l'init) et le faire **proprement**, pas en global.
- **Déterminisme byte-à-byte du pont** : `test_sim_server` compare deux runs.
  Planter/arroser doivent être des fonctions **pures** de l'état (aucun RNG ;
  la levée différée réutilise le hash de niche déterministe).
- **Empilement (Q4) = patiente, pas refus** : `planter` n'échoue jamais sur plot
  occupé ; c'est la **succession** (plot libre) qui temporise la levée. Ne pas
  ajouter de vérification d'occupation dans `planter`.

## Après ce sprint
- Mettre à jour `journal.md` (clôture planter/arroser + modèle eau, **nouvelle
  empreinte golden T1 expliquée**), `BACKLOG.md` (retirer planter/arroser), la
  mémoire projet. Marquer le re-figeage golden dans `00_etat`/journal.
- **Sprint suivant cadré** : **compétition intra-plot** (réalise pleinement Q4 —
  cohabitation/éclaircissage quand plusieurs plantes partagent un plot).
- Le **rendu Godot** des gestes (choisir une graine, viser, voir le sol
  s'humidifier, indices visuels d'asphyxie) = **volet vue ultérieur** — le pont
  est prêt (protocole 0.3.3, banque-joueur au snapshot).
- Backlog connexe (CONCEPTION non couvertes ici) : semis intérieur maison (Q6),
  bouture/division (Q7), gène `tolerance_exces_eau` si le calibrage le réclame.
