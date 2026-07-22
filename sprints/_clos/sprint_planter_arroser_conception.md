# Kickoff de CONCEPTION — gestes `planter` & `arroser` (+ modèle « eau » : asphyxie & drainage du sol)

> **Kickoff autosuffisant** (démarrage à froid après `/clear`). Objectif : faire
> passer ces **deux gestes de base** de l'**intention** (déjà écrite,
> `docs/joueur/vigueur/conception_vigueur.md` §3.2) à une **conception FIGÉE** (décisions Q-par-Q
> tranchées par Nico), prête pour un kickoff d'implémentation séparé.
>
> **CE SPRINT NE PRODUIT PAS DE CODE.** Conception seule. Livrable unique :
> `data/code/CONCEPTION_PLANTER_ARROSER.md` (modèle proposé + décisions figées +
> découpage impl.), sur le modèle de `docs/joueur/gestes/conception_ecrasement.md`.
>
> Règles projet : **moteur Python = source de vérité** (« moteur d'abord, pont
> ensuite ») ; **pédagogie explicite** sur chaque choix ; **max 3 questions à la
> fois** en session ; ne rien créer d'autre sans « OK ». Ampleur conception :
> **petit/moyen** (les ancrages existent déjà).

## 0. Cadrage tranché par Nico (2026-06-12) — à intégrer dans la conception figée

Trois décisions prises après lecture du kickoff ; elles **élargissent le scope** et
**ouvrent 3 sous-questions** (à trancher en session).

- **Q1 → GERMINATION DIFFÉRÉE.** `planter` ne spawn PAS un semis : il **dépose une
  graine dans la banque-sol** (`SeedBank-sol`), qui **germe via la succession
  ordinaire** quand la niche le permet (timing réaliste, leçon du « bon moment » ;
  réutilise `succession.py` → zéro chemin de germination neuf).
- **Q4 → EMPILEMENT AUTORISÉ.** Planter ne refuse jamais un plot occupé. La
  **compétition intra-plot** (sprint backlog) est faite **juste après** ce sprint et
  gérera la cohabitation/éclaircissage.
- **Q11 → ON PUNIT L'EXCÈS, par paliers.** Le **sur-arrosage** devient une vraie
  « fausse bonne idée » : excès d'humidité → **asphyxie** (uptake ↓ puis santé ↓ si
  ça dure, §0 C.iii ; **nouvelle cause de stagnation « noyé »**). **`drainer` N'EST
  PAS un geste joueur** (Q8, Nico) : c'est une **propriété du SOL** — la
  **composition/texture** (`soil_type` : argile / terre / sable) module la vitesse
  d'évacuation. Argile retient → asphyxie facile ; sable draine → sèche vite. **Le
  remède du joueur au sur-arrosage = connaître son sol** (et ne pas trop arroser),
  pas un bouton. Supersede la ligne « Drainer » de `CONCEPTION_VIGUEUR §3.2`.

**Conséquence scope :** **gestes** = **`planter` + `arroser`** (les 2 du backlog,
event-driven, golden intact). **Modèle « eau » côté TICK** = **asphyxie** (excès →
uptake/santé) **+ drainage par `soil_type`** (le `DRAINAGE`/la rétention de
`tick_hydrology` deviennent fonction du sol). ⚠️ Ce modèle « eau » est une mécanique
de TICK → **il RE-FIGE le golden `16a1b937…`** → **re-figeage MAÎTRISÉ et annoncé**
requis (règle CLAUDE.md : dérive localisée, expliquée). Les 2 gestes restent hors tick.

**Sous-questions — TRANCHÉES par Nico (2026-06-12) :**

- **A — Génétique de la graine plantée → (ii) GRAINE EN ATTENTE.** PAS de dilution
  dans la banque-sol agrégée : `planter` crée un **dépôt distinct identifié** qui
  germe **tel quel** avec **ses gènes propres** (préserve la sélection D17/D22 — semer
  une belle graine récoltée a un sens). Nouvelle petite structure « graine en
  attente » par plot, à concevoir (germe via la succession, gènes non moyennés).
- **B — Tag « replanté » en différé → OUI.** Le tag cultivé/féral
  (`marquer_replante`, détection maîtrise §9.4) se pose **sur le dépôt** et **se
  transmet à la plante** quand elle germe.
- **C (asphyxie) — Où poser la pénalité → (iii) PAR PALIERS.** L'excès d'humidité pèse
  d'abord sur l'**uptake** (la plante boit mal → croissance ↓, doux/réversible),
  **puis sur la santé** (`health` ↓) **si ça dure** — symétrique de la gradation
  sécheresse existante. Reste à CALIBRER (proposé chiffré en session) : le **seuil
  d'excès** sur [0,3] (à partir d'où on « noie »), la **durée** avant bascule
  uptake→santé, l'**ampleur** de chaque palier.
- **Note (empilement × différée).** La succession ne germe que sur **plot libre**
  (`occupied_roots`) ; « autoriser l'empilement » (Q4) se réalise donc pleinement
  **quand le sprint compétition intra-plot arrive** (juste après). En attendant, une
  graine déposée sur un plot occupé **patiente** (germe quand le plot se libère).

**Décisions de détail (Nico, 2026-06-12) — figées :**
- **Q2** source = **banque-joueur uniquement** (prend une `Seed` + ses gènes, refus
  si lot vide). **Q3 / Q8** cible = **plot cliqué** (+ diffusion naturelle pour l'eau).
- **Q5** tag « replanté » posé **à la création du dépôt** (cf. B). **Q6** semis = **plein
  air uniquement** v1 (serre / semis intérieur = sprint futur). **Q7** bouture/division
  = **sprint dédié** (hors scope).
- **Q9** dose d'arrosage **cumulative** (s'empile → peut mener à l'asphyxie), apport
  unitaire à calibrer (proposé +0,5, calé sur la pluie d'aléa). **Q10** `arroser` existe
  en **planification (prévention)** ET **saison (× URGENCE)**.
- **Coûts** : `planter` **FAIBLE** (planif.) ; `arroser` **MODÉRÉ** (× URGENCE en saison).

**Reste OUVERT (à clarifier avant rédaction de la conception figée) :**
- **Q12 — « c'est sur la plante » (Nico) vs philo #2.** L'effet de l'arrosage se
  matérialise **sur la plante** (croissance/santé). Deux lectures à départager :
  *(a)* l'arrosage écrit le **champ `humidite`** (event-driven, golden intact) et la
  plante **répond au tick** (la sécheresse se lève ; l'excès → asphyxie) = effet
  **visible sur la plante mais médié par le champ**, philo #2 respectée (le principe
  « non négociable » de `CONCEPTION_VIGUEUR §3.2`) ; *(b)* l'arrosage **écrit
  directement** un attribut de la plante (effet immédiat) = **entorse assumée** à
  philo #2 + le geste devient tick-affecting. *Reco : (a)* — l'asphyxie (C.iii) agit
  déjà « sur la plante » via le champ lu au tick, donc (a) donne « c'est sur la
  plante » SANS casser philo #2.

## 1. Pourquoi ces deux gestes, pourquoi maintenant

`planter` et `arroser` sont les **derniers gestes de base absents du moteur**.
La page d'accueil (CLAUDE.md) liste cliquer · **planter** · observer · méditer ·
manger ; tous existent sauf planter. Le backlog les a gravés ensemble (gravé
2026-06-11, t4 intégration) : exclus du pont tant que Python ne les porte pas.

Tous deux sont du **canal vertueux** (philo #1 : le joueur agit principalement
sur le **MILIEU**) — un bon contrepoint aux gestes sur le vivant (`écraser`,
`tailler`, `deraciner`) qu'on vient de finir. Les concevoir maintenant complète
la palette d'interaction de base avant le packaging.

## 2. L'intention est DÉJÀ écrite (source de vérité du « quoi »)

`docs/joueur/vigueur/conception_vigueur.md` §3.2 (« Actions sur le milieu — le canal vertueux ») :

| Action | Phase | Champ / effet | Coût | Réponse émergente |
|---|---|---|---|---|
| **Semer / planter** | planif. | introduit une graine (banque-joueur) à `x_cm,y_cm` | `FAIBLE` | germination → succession ordinaire |
| **Arroser** | saison | `humidite` locale ↑ | `MODÉRÉ × URGENCE` | sort de la stagnation sécheresse (`ok_hum`) |

§3.1 ajoute : « arroser en **prévention** ≠ arroser en **catastrophe** » — une même
action peut vivre dans les **deux phases** à des coûts différents. **Principe non
négociable (philo #2)** : l'action ne touche **jamais** la plante directement,
elle modifie un **champ** ; la plante répond par **émergence**.

→ Le « quoi » est posé. Ce sprint tranche le **« comment »** exact (les Q ci-dessous).

## 3. État du code vérifié (ancrages — 2026-06-12)

- **Banque-joueur** : `sim/seeds.py` → `PlayerSeedBank` (lots par espèce,
  `take(species)` FIFO, `Seed{species, genes}`, sérialisable JSON). Vit dans
  `game_state["player_seed_bank"]` (lu `engine.py:693`) ; le **pont récolte →
  graine est déjà câblé** (une plante mûre récoltée dépose une `Seed` gènes
  inclus). C'est la source naturelle de `planter`.
- **Créer une plante** : `world/tile.py:145 add_plant(cls, r, c)` → `PlantInstance`
  au stade *semis*. Ne vérifie **que les bornes** (`is_valid_plot`), **PAS
  l'occupation**. Position interne **continue** (`x_cm/y_cm`, centre du plot-foyer
  si non fournie).
- **Germination spontanée** (le « → succession ordinaire » de l'intention) :
  `sim/succession.py` crée un semis **immédiatement** quand `niche_index`
  (lumière / densité racinaire / perturbation / sol) le permet, sur plot **libre**,
  gènes échantillonnés de la **banque-sol**. C'est le chemin de référence à imiter
  ou à court-circuiter (Q1).
- **Banque-sol** : `fields/seedbank.py` `SeedBank` (par espèce × plot, génétique
  moyenne/variance) — le pendant **latent** ; `add_species(...)` existe. Reste au
  terrain au déménagement (≠ banque-joueur qui suit l'avatar).
- **Humidité** : champ `eco.humidite`, **échelle [0, 3]** (normalisée `/3.0`
  partout). Tick `ecofields.py:tick_hydrology` = évaporation (× , couplée
  température) + pluie de fond + rétention (`soil_memory`) + drainage (×). →
  **tout apport manuel DÉCROÎT** sur les ticks suivants : l'arrosage est
  **transitoire** par construction = l'usure de la solution facile (philo #1).
  Diffusion spatiale `HUMIDITY_INERTIA`. Les aléas « Pluies/Canicule » écrivent
  déjà ce champ (`+0.5 / −0.4`) — calibre de référence pour la dose d'arrosage.
- **Stagnation hydrique** : `maitrise_detection.py` reconnaît `stagne (sec …)` →
  concept de maîtrise « eau ». **L'asphyxie / l'excès d'eau n'est PAS modélisé**
  (causes = `sec` / `ombre` / `froid` seulement) → enjeu du sur-arrosage (Q11).
- **Maîtrise** : `maitrise_detection.py:163` a un **hook explicite** pour le futur
  `planter` (`marquer_replante`) — distinguer le **cultivé** (replanté) du
  **féral** pour la détection §9.4. Coûts : tables `COUTS` / `OBJETS_TOUCHES` dans
  `sim/actions.py` (il faudra **2 entrées neuves**).
- **Pont** : `tools/sim_server.py` route par **verbe + forme du `target`** (cf.
  `ecraser`/`tailler`). Le snapshot devra **exposer la banque-joueur** (pour que
  la vue propose les graines plantables). Protocole à bumper.

## 4. Où ça atterrit dans la philosophie (pédagogie)

- **`planter`** = geste **fondateur**, pas un bonus direct (philo #2 respectée) :
  il **introduit une propagule**, la suite **émerge** (le semis lutte ou prospère
  selon lumière/sol/saison). Planter au mauvais endroit → le semis dépérit = la
  **méthode scientifique** (action → conséquence → hypothèse). Le geste porte la
  **génétique** sélectionnée (lien D17/D22 : on sème ce qu'on a récolté).
- **`arroser`** = écriture sur le **champ humidité**, canon philo #2. **Transitoire**
  (évaporation/drainage) → ré-arroser coûte = la solution facile s'use. **Sur-arroser**
  doit pouvoir être une **fausse bonne idée** (pédagogie #6) — d'où Q11.

## 5. Questions de conception à TRANCHER (le cœur du sprint)

> Chaque Q : **enjeu → options → reco** (penchant pédagogiquement justifié, **NON
> figé** — Nico tranche, comme Q1-Q6 de l'écrasement). À traiter par paquets de ≤ 3.

### `planter`
- **Q1 — [TRANCHÉE → §0 : DIFFÉRÉE]** Germination immédiate ou différée ? Spawn d'un **semis garanti**
  (`add_plant`, contrôle clair du geste) **OU** dépôt d'une **graine dans la
  banque-sol** qui germe quand la niche le permet (= « succession ordinaire » de
  l'intention, réaliste, enseigne le **timing**). *Reco : immédiate (semis)* — le
  geste a un effet lisible, et la **lutte post-semis** fait déjà la leçon ; la
  banque-sol différée reste le canal de la succession spontanée. À débattre (c'est
  la décision la plus structurante).
- **Q2 — Source = banque-joueur uniquement ?** Consomme une `Seed` (gènes inclus),
  **refus si lot vide**. Un mode « graine générique du catalogue » (hors banque)
  existe-t-il ? *Reco : strictement banque-joueur* (sinon la banque perd son sens) ;
  l'amorçage passe par le réglage « graines de démarrage » déjà prévu (Options).
- **Q3 — Cible = plot cliqué.** Le joueur clique un point → plot-foyer (comme les
  autres gestes), `x_cm/y_cm` déduits. Confirmer (vs saisie d'un point continu).
- **Q4 — [TRANCHÉE → §0 : EMPILEMENT AUTORISÉ]** Plot déjà occupé ? **Refuser** proprement pour l'instant, **OU**
  **autoriser** l'empilement (la **compétition intra-plot** est un sprint backlog
  dédié qui s'en chargera). *Reco : à trancher* — refuser est plus simple et sûr
  v1 ; autoriser anticipe la compétition.
- **Q5 — Tag maîtrise.** `planter` marque la plante **« replanté »**
  (`marquer_replante`) à la création → la détection distingue cultivé/féral
  (§9.4). Confirmer.
- **Q6 — Semis intérieur (maison) = hors scope v1 ?** La fonction maison « Semis
  intérieur » (démarrage protégé + repiquage) est un sprint futur. *Reco : plein
  air uniquement v1*, mention seulement.
- **Q7 — Coût & phase.** `FAIBLE`, **planification** (intention §3.2). La
  **multiplication végétative** (bouture/division, clone) est une **ligne voisine**
  de §3.2 → **HORS scope** (sprint dédié). Confirmer.

### `arroser` + modèle « eau » (asphyxie & drainage du sol — §0 Q11)
- **Q8 — [TRANCHÉE → §0 : PLOT CLIQUÉ ; `drainer` ≠ geste, c'est le sol]** Cible
  arroser = **plot cliqué** + diffusion naturelle (`HUMIDITY_INERTIA`) = l'arrosoir.
  Le **drainage** n'est pas un geste : il dépend du **`soil_type`** (modèle eau, tick).
- **Q9 — Dose.** Apport **fixe** calé sur la pluie d'aléa (`+0.5`) ou paramétrable ?
  **Cumulatif**, **plafonné** à l'échelle [0, 3]. *Reco : add fixe calibré,
  cumulatif borné.*
- **Q10 — Phases.** **Saison** (réaction, `× URGENCE` déjà codé) **et/ou**
  **planification** (prévention, coût simple) — §3.1 oppose les deux. *Reco : les
  deux*, l'urgence est le multiplicateur existant.
- **Q11 — [TRANCHÉE → §0 : ON PUNIT L'EXCÈS, PAR PALIERS + `drainer` dans le scope]**
  Le sur-arrosage est une **fausse bonne idée** : excès → **asphyxie**, pénalité **par
  paliers** (uptake d'abord, santé si ça dure, §0 C.iii), **cause de stagnation
  « noyé »**. Reste à CALIBRER : **seuil** d'excès sur [0,3], **durée** avant bascule
  uptake→santé, **ampleur** des paliers ; **branchement dans le tick** (re-figeage
  golden, §0) ; geste **`drainer`** (humidité ↓, planif./saison).
- **Q12 — [À CLARIFIER → §0 : « c'est sur la plante » vs philo #2]** L'effet se
  matérialise sur la plante ; reste à départager *médié par le champ* (a, reco) vs
  *écriture directe* (b, entorse philo #2). Voir §0 « Reste OUVERT ».

## 6. Garanties (par construction)

- **Golden** : les **2 gestes** (`planter`, `arroser`) sont **event-driven hors tick**
  → golden INTACT (le golden ne les appelle jamais). **EXCEPTION (§0 Q11)** : le
  **modèle « eau » (asphyxie + drainage par `soil_type`)** vit DANS le tick (pénalité
  uptake/santé, évacuation par le sol) → **re-figeage MAÎTRISÉ et annoncé** du golden
  `16a1b937…` (dérive localisée, expliquée). À isoler clairement de la partie gestes.
- **Déterminisme** : aucun RNG dans le geste (si Q1 = différée, on réutilise le
  hash de germination existant).
- **Maîtrise / Vigueur** : 2 entrées neuves dans `COUTS`/`OBJETS_TOUCHES`,
  atténuation neutre tant qu'aucune maîtrise (golden Vigueur intact).

## 7. Découpage pressenti de l'IMPL (à confirmer dans le kickoff d'impl, PAS ici)

Moyen→gros (le scope a grandi avec §0). Probable : (1) `planter` (graine **en
attente** par plot, gènes propres + tag « replanté » différé + coût ; germination via
succession, **golden intact**), (2) `arroser` (champ humidité ↑ + phases + dose
cumulative, **golden intact**), (3) **modèle « eau »** dans le tick = **asphyxie**
(seuil d'excès + paliers uptake→santé + stagnation « noyé ») **+ drainage par
`soil_type`** (**golden RE-FIGÉ maîtrisé** — tronçon ISOLÉ, le plus risqué), (4) pont
`sim_server` + banque-joueur au snapshot, (5) tests + golden. Le **rendu Godot** des
gestes (choisir une graine, viser, voir le sol s'humidifier) = volet vue ultérieur.
**NB** : la **compétition intra-plot** est le sprint qui suit (Q4 / Note §0).

## 8. Livrable & reprise

- **Livrable de CE sprint** : `data/code/CONCEPTION_PLANTER_ARROSER.md` —
  §1 intention (reprise §3.2), §2 modèle proposé (les 2 gestes mappés sur le code
  ci-dessus), §3 **décisions FIGÉES** (Q1-Q12 tranchées par Nico), §4 découpage
  impl. Puis un kickoff d'implémentation autosuffisant (modèle
  `sprint_ecrasement_plantes.md`).
- **Reprise à froid** : « lis `sprints/sprint_planter_arroser_conception.md` »
  (+ `docs/joueur/vigueur/conception_vigueur.md` §3.2 pour l'intention, `docs/joueur/gestes/conception_ecrasement.md`
  comme gabarit de structure de la conception figée).
