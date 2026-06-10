# SYMBIOSE

**Sandbox écologique évolutif** en permaculture — jardin éternel à un seul
run. Version vidéo (Godot 4 / C#) et version physique (tuiles 3D imprimées
+ cartes MTG) développées en parallèle. Public : amis et famille de Nico,
ingénieur électronique embarqué à Grenoble.

> Avant : « roguelike écologique ». Redéfini le 2026-05-29 — voir
> Sprint conception dans `journal.md`. Ne plus utiliser le vocabulaire
> roguelike (run, shop inter-run, extinction terminale, héritage entre
> runs).

## Source de vérité

Le moteur Python dans `data/code/`, **réorganisé en paquets** (Sprint refactor
structurel, 2026-06-03), est la **source de vérité écologique** du jeu :

- `constants.py` — échelle (`PLOT_CM`)
- `plants/` — `genetics.py` (gènes, `clamp_gene`, `species_compatible`),
  `base.py` (`GrowthStage`/`PlantInstance`/`ConflictNotification`/`PlantBase`
  + 5 familles + empreintes + registre d'effets), `species.py`,
  `perennials.py`, `catalogue.py`
- `world/` — `tile.py` (`Tile`, `StakeSlot`, `RONDELLE_TYPES`), `building.py`
  (`House` paramétrable, ombre + albédo espalier)
- `fields/` — `noise.py` (fondation déterministe), `grids.py`, `light.py`,
  `seedbank.py`, `ecofields.py`, `population.py` (vie macro, 4 guildes)
- `sim/` — `effects.py`, `seeds.py`, `reproduction.py`, `succession.py`,
  `engine.py`, `weather.py` (météo pure `weather_at`), `growth.py`
  (morphogénèse segments + auxine + phototropisme), `vigueur.py` /
  `vigueur_plante.py` / `vigueur_macro.py`, `actions.py` (gestes joueur +
  `cout_action`), `maitrise.py` / `maitrise_detection.py`
- `main.py` (démo 8 tuiles + maison, banc d'essai — n'est plus le golden) ;
  `tools/` (`render_structure.py` maquettes SVG, `export_structure.py` pont
  JSON → Godot) ; `tests/` (`test_golden.py` = smoke test déterministe
  2 tuiles × 4 ans + 11 suites ciblées : génétique, croissance, maîtrise,
  vigueur, population, ombre maison, phototropisme, sénescence, signes…)

Règle de couches : `plants ← fields ← sim ← engine ← main` (les couches basses
n'importent jamais les hautes). Imports absolus ; lancement depuis `data/code/`
(`python3 main.py`, `python3 -m tests.test_golden`).

- Toute mécanique Godot doit avoir un équivalent Python ou être propagée
  vers Python avant intégration.
- Quand Python et C# divergent (cf D10 dans `DETTE.md`), prioriser
  l'alignement vers Python sauf décision explicite contraire de Nico.
- `main.py` tourne — il a simulé 500+ ans sans crash. C'est la référence
  comportementale. **Tout changement du moteur doit préserver le golden output**
  (`tests/test_golden.py` — déterminisme, règle de design #3). Depuis le Sprint
  maison (2026-06-07) le golden est un **smoke test** (2 tuiles × 4 ans) ; tout
  re-figeage doit être **maîtrisé et annoncé** (dérive localisée, expliquée).

## Stack technique

- Godot 4.6 .NET, C# .NET 8.0
- Namespace `Symbiose` sur tous les fichiers de gameplay
- **GDScript INTERDIT** — tout en C#
- Pixel art : filtre `Nearest` partout (réglé dans `project.godot`)
- Résolution 1920×1080
- Zoom par paliers entiers ×4 / ×8 / ×16 / ×32 — jamais de fraction
- **Boucle hybride** : phase planification en temps figé ↔ phase saison
  de 15 minutes en temps réel (1 semaine = 60 secondes)

## Philosophie de design — NE JAMAIS DÉRIVER

1. Le joueur agit **principalement** sur le MILIEU. L'action directe sur
   les êtres vivants reste possible (écraser un nuisible, déraciner une
   plante) mais coûteuse en Vigueur et perturbatrice — la permaculture
   s'enseigne par l'usure de la solution facile.
2. Jamais bonus/malus direct **sur les plantes** — toujours flux →
   contrainte écologique → réponse biologique émergente.
3. Simulation déterministe (seed global, hash de bruit spatial).
4. **Run éternel** — un jardin unique et persistant, le sol porte la
   mémoire et grandit avec le joueur.
5. Indices biologiques visuels + encyclopédie et carnet auto comme
   dispositifs informationnels. Pas de chiffres ni de barres en HUD
   primaire (sauf mode debug).
6. La sagesse écologique prime — pas de tutoriel imposé. L'apprentissage
   est diffus : action → conséquence → consultation → hypothèse.
7. Hétérogénéité persistante — deux joueurs n'ont jamais le même terrain.

Pour le détail historique, voir `journal.md` + `journal_archive/` (les anciens
`models.py`/`fields.py` ont été éclatés en paquets au refactor du 2026-06-03).

## Mécaniques centrales (Sprint conception + Sprint conception bis, 2026-05-29)

### Vigueur unifiée (Qi + Mana)
Chaque être vivant possède sa **Vigueur** (≡ Mana, énergie propre).
Les **champs écologiques existants** (`microbiome`, `soil_memory`, `om_*`,
`fertilite`) modélisent le **Qi territorial**. La Vigueur se puise dans
le territoire et y retourne à la mort.

**Modèle de Vigueur joueur** (base, à ajuster post-test) :
- Montant initial 100, +10/semaine simulée, full au passage de saison
- Sources extra : récolte plantes mûres, méditation au foyer, **consommer
  une feuille / fleur / fruit (action « manger »)** — Vigueur retrouvée
  proportionnelle à la maturité de l'organe consommé
- **Vigueur max augmente avec les paliers de maîtrise**
- **La vitesse de régen passive augmente aussi avec la maîtrise** : plus
  on comprend l'écologie, plus vite on se ressource au jardin

### Maîtrise et paliers
5 paliers par famille botanique et par concept écologique transversal :
**découverte → investissement → maîtrise → expertise → transcendant**.
La maîtrise débloque : extension de terrain (tuile thématique), accès au
magazine, basculement du carnet en mode interprétatif, augmentation de
la Vigueur max joueur.

**Transcendant = non-action existentielle** : l'écosystème devient
auto-suffisant, le joueur n'a plus besoin d'agir. Les perturbations
entretiennent l'engagement à très long terme.

### Apprentissage par méthode scientifique
Observer → formuler → tester → conclure. Trial & error, prise de risque,
diversification d'idées sont récompensés. Aucune action n'est punitive en
soi — c'est l'écosystème qui répond.

### Trois voix narratives diégétiques
- **Encyclopédie** : wiki ingame qui se complète aux découvertes (voir
  une espèce = entrée basique ; cycle complet = description bio ; cycles
  répétés avec succès = effets écosystémiques). Voix « naturaliste qui
  observe ».
- **Carnet auto** : enregistrement automatique des événements,
  consultable, indexé. **Descriptif au début**, **interprétatif au seuil
  de maîtrise** sur le concept concerné. Voix interne à la première
  personne. Préserve la méthode scientifique pendant l'apprentissage,
  révèle les causes une fois la compréhension intériorisée.
- **Pages secrètes** : connaissances perdues, éparses, ésotériques —
  trouvées par hasard, gagnées après une belle réalisation, découvertes
  en fouillant. Voix multiples : extraits poétiques, savoirs paysans,
  herbiers anciens, citations type Fukuoka / Sackville-West / sorcières
  médicinales. Consultation pressentie : coffret au grenier de la maison.

**Pas de narrateur externe omniscient, pas de PNJ, pas de quête imposée.**
Histoire émergente via les événements rares (bouture, oiseau, vent).

### Acquisition d'espèces (4 canaux)
1. Succession spontanée (`niche_index` dans le moteur Python)
2. Événements rares (bouture, oiseau, vent)
3. Exploration de friche périphérique (abstraite au début)
4. **Magazine de botanique** — déblocage par Vigueur joueur + maîtrise

### Auxiliaires
**Visibles dès le début, non identifiables sans maîtrise.** Modèle
technique : champ ambiant `GridField` pour la dynamique + sprites
apparents pour la perception. Tu vois l'insecte avant de connaître son
nom — posture du naturaliste débutant.

### Maison normande — hub vivant (5 fonctions)
Atelier · Semis intérieur · Magazine de botanique · Carnet · **Foyer**
(point de récupération de Vigueur).

### Démarrage du jardin (3 écoles au choix)
Friche pionnière · Sol modeste · Jardin abandonné.

### Extension du terrain
**Par maîtrise écologique** uniquement. Maîtriser une famille fait
apparaître une tuile thématique (verger, mare, prairie aromatique…).
Pas d'achat, pas de conquête : la connaissance ouvre l'espace.

### UX du volume cognitif
1600 plots (monde 20×20 m) × 15 min temps réel = trois mitigations actives simultanément :
**pause libre + notifications hiérarchisées + zoom contextuel**.

### Gestion des aléas météo
Préavis météo par **signes diégétiques** (oiseaux, ciel, anneau lunaire,
brume, sol qui craquelle) — pas d'icône calendrier. L'interprétation
explicite débloque au palier de maîtrise du concept « météo / climat ».
Action joueur en **deux temps** :
- **Préparation** (planification, temps figé) : paillage profond, voiles
  d'hivernage, brise-vent, structures persistantes — Vigueur modérée
- **Réaction** (saison, temps réel) : arrosage ciblé, sauver une plante
  précise, secouer une branche givrée — Vigueur élevée (urgence)

**~20 %** d'événements météo restent **imprévisibles** tant qu'on n'est
pas au palier transcendant en météo. **Au transcendant : tout devient
prévisible** — récompense rare qui cristallise la philo non-action.

### Profils, avatars, déménagement
- **Profils multiples** sur la même installation. Un profil = un **avatar
  joueur** (nom, encyclopédie, paliers, banque de graines, Vigueur max
  courante) + un ou plusieurs **terrains**.
- **Déménagement** : un avatar peut migrer d'un terrain à un autre. Il
  emporte son savoir, ses paliers, ses graines, sa Vigueur max. Le
  terrain reste lui-même (sol, climat, friche). Le savoir voyage, le
  territoire non.
- **Encyclopédie et paliers strictement par avatar** — pas de méta-savoir
  inter-avatars. Nouvel avatar = repart de zéro.
- **Pas de multijoueur synchrone** (incompatible pause libre / temps lent).
  Asynchrone + co-saison hot-seat 2 joueurs = backlog v2.0+.

### Cycle de sauvegarde
- **Auto-save uniquement au passage de saison.** Pas d'auto-save
  intra-saison. Perdre une saison en cas de crash est accepté.
- **JSON lisible**, pas binaire — debug + curiosité future du joueur.
- **Un seul save par profil.** Pas de save-scumming.
- **Pas de migration de save < v1.0** — champ `engine_version` dans le
  save, casse explicite sinon.
- **Seed d'origine du terrain persistée** dans le profil : permet de
  re-générer le même point de départ (debug, partage école avec un ami).

### Conditions de panne sèche
- **Pas de game over.** La succession spontanée (`SeedBank-sol`) ramène
  des pionnières en quelques saisons même sur un jardin saccagé. C'est
  le fonctionnement normal d'un sol vivant.
- **Pas de bouton « recommencer »** — run éternel = éternel. Pour un
  autre jardin : déménager ou créer un autre profil.

### Difficulty / accessibilité
- **Pas de mode difficulté classique** (le jeu n'est pas un jeu de score).
- **Réglages d'aide modulaires** (menu Options) :
  - Vitesse simulation : 30 à 180 s/semaine, défaut 60 s
  - Verbosité notifications : silencieux / important / tout (défaut important)
  - Encyclopédie de démarrage : vierge / amorcée (défaut) / fournie
  - Carnet interprétatif anticipé : OUI/NON (défaut NON, préserve la méthode)
- **Mode debug champs écologiques** (overlay heatmaps) = toggle libre
  Options dès le début, étiqueté « affichage technique — déconseillé en
  première découverte ». Accessibilité > récompense punitive.
- **Page d'accueil minimale** au premier lancement : 4-5 pictogrammes
  silencieux des gestes de base (cliquer, planter, observer, méditer,
  manger). Pas de texte, pas de tutoriel imposé.

## Architecture courante (mise à jour : 2026-06-10)

> **Architecture Godot ACTÉE le 2026-06-07 = Option B** : Python reste le
> moteur (sous-process, pont JSON stdin/stdout), **Godot est une VUE**. Plus
> de portage C# intégral de la simulation — seul le **rendu** se porte.
> Kickoff : `sprints/sprint_integration_godot/00_etat.md`.

### Fonctionnels (C#)
- `core/PlantData.cs` — GrowthStage, PlantData, PlantInstance
- `core/GridField.cs` — GridField, LightField, EcoFields complet
- `core/TileData.cs` — Tile, StakeSlot, ConflictNotification
- `core/PlantCatalogue.cs` — 14 espèces dont indicatrices avec UnlockCondition
- `core/SpriteLoader.cs` — autoload, chargement récursif
- `core/PlantStructure.cs` — miroir `Segment` + chargeur `structure.json`
  (pont JSON, Sprint croissance·4)
- `visuals/PlantRenderer.cs` — rendu pixel des branches (projection `Iso()`,
  LOD silhouette ; compilation à confirmer dans Godot)

### Stubs vides (à écrire — deviendront la VUE, pas un moteur)
- `core/GameManager.cs`, `EcologySystem.cs`, `TurnSystem.cs`, `SeedBankSystem.cs`
- `plants/*`, `ui/*`, `world/SoilField.cs`
- `Main.cs` (la classe s'appelle encore `Node2d`, hors namespace)

### Systèmes à concevoir / dette technique

La **dette technique consolidée** (D1–D33 : magazine, carnet, extension
terrain, pages secrètes, organes comestibles, structure du sol, couleur
physiologique, pont Godot, etc.) vit désormais dans **[`DETTE.md`](DETTE.md)**
— source unique, plus de duplication.

### Échelle spatiale actée (éclairement 2026-05-29, agrandie au Sprint maison 2026-06-07)
- **1 plot = 50×50 cm** ; monde **20×20 m = 1600 plots**, **maison centrale
  8×8×6 m** (paramétrable) + 8 tuiles hétérogènes, **chemins en pierre de
  50 cm** entre tuiles (non simulés ; pas d'ombrage inter-tuiles, seule la
  maison ombrage globalement via `origin_*_cm`)
- Le **plot** ne sert plus qu'à la **chimie du sol** (humidité, fertilité,
  microbiome, soil_memory…). La **position des plantes est continue**
  (pixel-sol `x_cm, y_cm`), plot-foyer = `floor(pos / 50 cm)`.
- **Lumière** : grille pixel-sol **top-down cartésienne** à **2 cm/px**
  (≠ espace iso d'affichage). Empreintes : canopée = disque rayon tabulé par
  stade ; racines = rayon continu → plots exploités (remplace `RootOffsets`).

### Données calibrage
- Sprites tuiles **78×57** sur disque (et non 96×48 codé dans `TileGrid.cs`)
- Sprites plantes : sheets 1408×768 + PNG individuels en RGB sans alpha
- Pas de sprite maison à ce jour

Voir `journal.md` pour le détail de l'avancement et les décisions
historiques.

## Garde-fous spécifiques

- **Français systématique** dans les réponses utilisateur. Conserver les
  identifiants code en anglais ou français selon le fichier existant.
- **Pédagogie explicite** à chaque proposition d'architecture — Nico
  apprend Godot/C# en frontend, vient du C/Python embarqué.
- **Pas de fichier créé sans demande explicite** — concevoir en
  conversation d'abord, puis ne créer que sur « OK », « vas-y », « lets go ».
- **Un fichier modifié à la fois** sauf demande contraire (cette règle
  est suspendue quand une synchro cohérente multi-fichiers est explicitement
  demandée — typiquement avant un commit).
- **Avant tout sprint**, vérifier que git est à jour. Nextcloud a déjà
  perdu transitoirement des fichiers le 2026-05-29.
- **Max 3 questions à la fois.**
- **Mettre à jour `journal.md` à la fin de chaque sprint** — c'est notre
  mémoire partagée des décisions et de l'avancement.
- **Anticiper le coût en tokens et découper les gros sprints.** Avant un
  sprint, classer son ampleur (petit / moyen / gros). Un sprint **gros**
  (touche beaucoup de fichiers couplés, exploration large) se découpe en
  **sous-sprints autosuffisants**, chacun une unité logique testable qui
  **préserve le golden**. Viser 3-6 sous-sprints, jamais 20 (chaque
  sous-sprint relancé à froid repaie son amorçage — le sur-découpage coûte
  aussi).
  - Structure : `sprints/sprint_X/00_etat.md` (état partagé léger, ~20
    lignes : où on en est, décisions, ce qui reste — mis à jour en fin de
    chaque sous-sprint) + `01_*.md`, `02_*.md`… (kickoffs autonomes).
  - Boucle : lancer `0N` → travailler → vérifier le golden → mettre à jour
    `00_etat.md` → commit → **`/clear`** → lancer `0N+1`. Le `/clear` entre
    tronçons est le vrai levier d'économie (le contexte ne se cumule pas).

## Backlog actif

Le **backlog des sprints** (terminés + à venir, avec les kickoffs
autosuffisants de `sprints/`) vit désormais dans **[`BACKLOG.md`](BACKLOG.md)**
— source unique, plus de duplication.

**Prochain sprint** : **Intégration Godot ↔ Python, tranche 1 — pont vivant
minimal** (`sim_server.py` ↔ `SimBridge.cs`). Kickoffs :
`sprints/sprint_integration_godot/00_etat.md` puis `01_pont_minimal.md`.

À l'ouverture d'une session, Nico donne « lis `sprints/sprint_X.md` » (sprint
simple) ou « lis `sprints/sprint_X/00_etat.md` puis `0N_*.md` » (sprint découpé)
et Claude reprend sans contexte préalable. Historique des décisions :
`journal.md` (entrées récentes) + `journal_archive/`.
