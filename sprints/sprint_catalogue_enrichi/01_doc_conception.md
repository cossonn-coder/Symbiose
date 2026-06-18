# Tronçon ① — DOC-CONCEPTION « catalogue enrichi » (audit + matrices + sélection)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Kickoff **autosuffisant** (relançable à froid).
> **DOC SEUL — golden INTACT par construction** : zéro fichier `data/code/` ou C#
> touché. Le seul livrable est `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`.

## Objectif

Produire le **doc de référence à étudier** qui prépare l'enrichissement du
catalogue. Pas de code : on AUDITE l'existant, on révèle les trous, on SÉLECTIONNE
les espèces à ajouter (plantes + animaux nommés) et on MONTRE leur place dans les
features développées. La sortie de ce doc = la matière que Nico étudie, puis le
découpage des tronçons d'implémentation ②+.

Rappel de cadrage (00_etat.md) : **doc d'abord**, **plantes ET animaux**, **animaux
= espèces nommées rattachées aux guildes existantes** (patron `PollinatorSpec`).

## Sujet bio/éco — produire un doc à étudier, PAS des questions à trancher

Nico est ingénieur embarqué (Python/simu expert), PAS botaniste/écologue. Les choix
d'espèces et de traits relèvent de connaissances hors de son expertise : le doc doit
**proposer et justifier** (allure naturaliste, comme l'encyclopédie ingame), avec
assez de pédagogie pour qu'il valide ou réoriente — surtout pas une liste de
questions « quelle espèce préfères-tu ? ». Les seuls arbitrages qu'on lui laisse
sont de DESIGN (ampleur des lots, priorités), pas de biologie.

## À LIRE avant d'écrire (sources de vérité)

Moteur (`data/code/`) :
- `plants/catalogue.py` — les 3 catalogues (cultivées, adventices `WEED_CATALOGUE`
  pour la succession, pérennes).
- `plants/species/cultivees.py`, `compagnes.py`, `adventices.py` — les classes
  d'espèces : champs `family`/`genus`/`name`/`rarity`/`keywords`/`life_cycle`/
  `winter_strategy`/`foliage_density`/`resistance_ecrasement`/`stimulation_ecrasement`/
  `fruitier`/`procedural_growth`/`growth_stages` (+ effects `floraison`/`recolte`/
  `permanent`/`companion_bonus`).
- `plants/perennials.py` — pérennes ligneuses (`maturity_years`, port arboré).
- `plants/base/familles.py` — les familles botaniques et ce qu'elles portent.
- `plants/base/effets.py`, `empreintes.py`, `stades.py`, `instance.py` — registre
  d'effets, empreintes canopée/racines, `GrowthStage`, `PlantInstance` (dont
  `floraison`, `foliar_plots`, `health`).
- `fields/population.py` — **CLÉ pour les animaux** : `TrophicSpec` (guilde
  data-driven), `PollinatorSpec` + `build_pollinator_registry` (le PATRON pour des
  espèces nommées), les 4 guildes (`build_population_specs`), attractivité florale
  par famille (`_ATTRACT_*`), signal fruit (`signal_fn`).
- `fields/lifecycle.py` (`LifeCycleBridge`), `fields/foragers.py` (`ForagerParams`),
  `fields/apiculture.py` (ruche/miel).

Conception des features (`docs/conception/`) — pour savoir QUELS leviers chaque
espèce peut actionner :
- `CONCEPTION_THERMIQUE_MICROCLIMAT.md` (gel/neige/ombre/`winter_strategy`),
- `CONCEPTION_POLLINISATION_CYCLE_VIE.md` (floraison, attractivité, ponts larvaires),
- `CONCEPTION_DECOMPOSITION_COMPOST.md` (fruitiers, litière, attraction animale),
- `CONCEPTION_ECRASEMENT.md`, `CONCEPTION_COMPETITION_INTRAPLOT.md`,
  `CONCEPTION_VIGUEUR.md`, `CONCEPTION_MAITRISE.md`, `CONCEPTION_VIE_MACRO.md`,
  `CONCEPTION_SAISONNALITE_VIE_MACRO.md`.

> Conseil token : un agent Explore peut faire l'inventaire des champs d'espèces et
> des accroches feature en parallèle ; garder la SYNTHÈSE pour soi (le doc).

## Plan du doc à produire (`CONCEPTION_CATALOGUE_ENRICHI.md`)

1. **Intention & cadrage** — pourquoi enrichir (souligner l'inclusion des espèces
   dans les features), périmètre, rappel des décisions du 00_etat.md.
2. **Audit de l'existant** — table des 17 plantes (famille, cycle, stratégie
   d'hiver, fruitier, mots-clés) + table des guildes/pollinisateurs avec leurs
   ressources/habitats/ponts. Lister les CHAMPS de donnée qui relient une espèce à
   chaque feature (vocabulaire de raccordement déjà en place).
3. **Matrice espèce × feature (EXISTANT)** — lignes = espèces actuelles, colonnes =
   thermique / pollinisation / décompo / vigueur-maîtrise / écrasement / compétition
   / succession. Cellule = comment l'espèce y participe (ou « — »). **Révéler les
   trous** : features sous-exercées, familles/niches/stratégies manquantes (ex :
   gélives vs rustiques pour le gel ; diversité de mellifères ; types de litière ;
   bisannuelles ; couvre-sols d'hiver ; faune non nommée).
4. **Plantes à AJOUTER** — sélection raisonnée PAR NICHE (chaque candidate justifiée
   par la/les feature(s) qu'elle exerce). Pour chacune : nom FR/genre, famille,
   `life_cycle`, `winter_strategy`, `foliage_density` indicatif, `keywords`,
   `fruitier`, place dans la succession si adventice, et l'attractivité induite par
   sa famille (les `_ATTRACT_*` existent déjà → une famille déjà cataloguée hérite
   gratis). Viser un nombre RAISONNABLE (proposer un ordre de grandeur, pas 50).
5. **Animaux NOMMÉS à AJOUTER** — catalogue rattaché aux 4 guildes + types
   pollinisateurs, sur le patron `PollinatorSpec`/`TrophicSpec`. Pour chacun : nom
   FR, guilde de rattachement, ressource/habitat (réutiliser les `*_grid`
   existantes ou en proposer), pont larvaire éventuel (`LifeCycleBridge`), saison
   d'activité (fenêtre photopériodique `daylen_*`). Préciser le MODÈLE retenu : une
   espèce nommée = un « parfum » d'une guilde (variante de sprite + entrée
   encyclopédie) OU un champ dédié — peser le coût moteur et TRANCHER dans le doc
   (option par défaut : variantes nommées d'une même guilde, le moins invasif).
6. **Matrice nouvelle espèce × feature** — le cœur du « souligner leur place » :
   montrer que chaque ajout exerce au moins une feature, et que chaque feature
   gagne en richesse.
7. **Partage DOC vs CODE & découpage ②+** — ce qui se règle par DONNÉE PURE (ajout
   de classes d'espèces / d'entrées de registre, golden potentiellement re-figé mais
   maîtrisé) vs ce qui demande un MÉCANISME nouveau (à éviter ou isoler). Proposer
   les lots d'implémentation (ex : ② plantes lot 1, ③ plantes lot 2, ④ animaux
   nommés, ⑤ vue Godot/sprites/encyclopédie) avec, pour chacun, l'impact golden
   attendu. NE PAS écrire ces kickoffs ici — juste les esquisser.
8. **Lien version physique** (si pertinent) — le catalogue nourrit aussi les cartes
   MTG / l'encyclopédie ; noter les implications sans s'y étendre.

## Garde-fous

- **DOC SEUL.** Aucune ligne dans `data/code/` ni en C#. Si l'écriture du doc
  donne envie de coder → s'arrêter, c'est le signe qu'un tronçon ② commence.
- **Pas d'invention de mécanique** : on raccorde aux features EXISTANTES via les
  champs de donnée déjà là. Toute mécanique nouvelle pressentie va en §7 (à peser),
  pas dans la sélection.
- **Interconnexion des acteurs** (règle Nico) : chaque espèce ajoutée doit être
  reliée aux autres (plante↔pollinisateur↔ravageur↔auxiliaire↔sol↔structures) — le
  doc le montre explicitement, c'est le but même du sprint.
- Respecter la philo de design (flux > action directe, déterminisme, indices
  visuels, run éternel).

## Validation

- `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md` existe et couvre les 8 sections.
- Les deux matrices sont remplies ; les trous de l'existant sont nommés ; chaque
  ajout est justifié par une feature.
- `git status` : SEUL le doc (et les `.md` de sprint) a changé → golden INTACT.
- `python3 -m tests.test_golden` (depuis `data/code/`) PASSE inchangé (sanity).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (① ✅ + le découpage ②+ arrêté en §7 du doc).
- **Mettre à jour `journal.md`** (entrée : conception catalogue enrichi figée).
- Commit : `docs(catalogue) : conception catalogue enrichi (plantes + animaux nommés) — FIGÉE`.
- Proposer à Nico le lancement du premier tronçon d'implémentation (②), PAS
  d'enchaînement automatique.
