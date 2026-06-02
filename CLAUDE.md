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

Le moteur Python dans `data/code/` (`models.py`, `fields.py`, `effects.py`,
`engine.py`, `perennials.py`, `main.py`) est la **source de vérité écologique**
du jeu.

- Toute mécanique Godot doit avoir un équivalent Python ou être propagée
  vers Python avant intégration.
- Quand Python et C# divergent (cf entrée D10 du `journal.md`), prioriser
  l'alignement vers Python sauf décision explicite contraire de Nico.
- `main.py` tourne — il a simulé 500+ ans sans crash. C'est la référence
  comportementale.

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

Pour le détail historique, voir `data/code/models.py` et `data/code/fields.py`.

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
432 plots × 15 min temps réel = trois mitigations actives simultanément :
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

## Architecture courante (mise à jour : 2026-05-29)

### Fonctionnels (~1700 lignes C#)
- `core/PlantData.cs` — GrowthStage, PlantData, PlantInstance
- `core/GridField.cs` — GridField, LightField, EcoFields complet
- `core/TileData.cs` — Tile, StakeSlot, ConflictNotification
- `core/PlantCatalogue.cs` — 14 espèces dont indicatrices avec UnlockCondition
- `core/SpriteLoader.cs` — autoload, chargement récursif

### Stubs vides (à écrire)
- `core/GameManager.cs`, `EcologySystem.cs`, `TurnSystem.cs`, `SeedBankSystem.cs`
- `plants/*`, `ui/*`, `visuals/*`, `world/SoilField.cs`
- `Main.cs` (la classe s'appelle encore `Node2d`, hors namespace)

### Non-portés
- `effects.py` → pas encore en C#
- `engine.py` → pas encore en C# (boucle 52 semaines + succession)

### Systèmes à concevoir (Sprint conception + bis + zone Z7)
- **Vigueur universelle** (D11) — couche transversale (joueur + plantes +
  auxiliaires + nuisibles)
- **Paliers de maîtrise** (D12) — méta-état du joueur, conditions de
  passage par famille et concept
- **Magazine de botanique** (D13) — déblocage espèces, coût Vigueur +
  maîtrise
- **Carnet auto** (D14) — capture événements, indexation, bascule
  descriptif → interprétatif
- **Extension de terrain par maîtrise** (D15) — apparition tuile thématique
- **Forecast météo** (D16) — décaler le tirage `random.choice` 1-2 sem
  en avance dans `engine.py`, alimenter les signes diégétiques
- **SeedBank-joueur ↔ SeedBank-sol** (D17) — séparer la banque
  transportable (suit l'avatar au déménagement) de la banque intrinsèque
  au terrain, Python puis C#
- **Pages secrètes** (D18) — sources de drop, lieu de consultation,
  volume cible v1.0, contenu narratif. Session future dédiée.
- **Action « manger »** (D19) — organes consommables → Vigueur joueur
- ✅ **Éclairement spatial — Option A** (D20) — **fait en Python le 2026-06-02**
  (Sprint éclairement). `LightField` v2 **analytique** dans `fields.py` :
  ombres-capsules astronomiques ~49°N, 4 saisons × 3 tranches + intégrale
  journalière, `foliage_density` par espèce, cumul multiplicatif, plancher 15 %,
  auto-ombrage exclu (tri hauteur-décroissante). **Pas de grille pixel** côté
  moteur (la grille 2 cm/px reste pour le **rendu Godot**). Position des plantes
  **continue côté lumière** (`x_cm, y_cm`), sous-sol indexé au plot
  (`plot_foyer`). Portage C# = dette D24.
- ✅ **Pérennes ligneuses** (D21) — **fait en Python le 2026-06-02**.
  `perennials.py` : `PerennialWoody` surcharge l'interface lumière polymorphe
  (`age_years`, courbe d'âge interpolée, `foliage_density` saisonnière — caduc
  nu l'hiver). 5 arbres : figuier/pommier = jardin, cerisier intermédiaire,
  **noyer/chêne = lisière**. Portage C# = dette D24.
- **Héritage génétique de la graine** (D22) — **vecteur de gènes extensible**
  (hauteur d'abord), héritage **biparental** (pollinisation par espèce
  modulée par les auxiliaires), hybridation inter-espèces par **introgression
  sur espèce fixe**. Couplé à D17 dans le **Sprint génétique/reproduction**.
- **Catalogue arbres pérennes étendu** (D23) — différé post-validation
  du squelette (poirier, prunier, châtaignier, frêne, tilleul, bouleau,
  saule, aulne, peuplier, érable…)

### Échelle spatiale actée (Sprint conception éclairement, 2026-05-29)
- **1 plot = 50×50 cm** ; monde 3×3 tuiles × (6×8 plots) = **432 plots =
  12×9 m ≈ 108 m²**
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

## Backlog actif

Chaque sprint à venir possède un **kickoff autosuffisant** dans
`sprints/`. À l'ouverture d'une nouvelle session, Nico donne
l'instruction « lis `sprints/sprint_X.md` » et Claude reprend sans
contexte préalable.

| Sprint | Kickoff |
|---|---|
| ✅ **TERMINÉ 2026-06-02** — Sprint sol vivant (OM v4 + racines spatiales + boucle rhizosphère + vitalité ; D10 levée côté Python) + consolidation puits microbien. Chantier C mycorhizes différé (extension future) ; portage C# = dette D24 | `sprints/sprint_sol_vivant.md` |
| ✅ **TERMINÉ 2026-06-02** — Mini-sprint succession (D25 levée : gradient pionnier → prairie ∝ maturité du sol + amorçage banque en propagules vivaces). Couvert installé bascule vers prairie vivace ~80 % sur ~30 ans, stable 500 ans. Portage C# = dette D24 | `sprints/sprint_succession.md` |
| ✅ **TERMINÉ 2026-06-02 (Python)** — Mini-sprint mortalité réaliste / sénescence (D27 : santé dynamique + sénescence par âge + fonte des semis + maladies fongiques + ravageurs régulés par **prédateurs émergents** + renouvellement + nécromasse ∝ hauteur + résistance des sujets établis). 500 ans stables, arbres meurent de sénescence, plus de zombies à 1/3. Renouvellement provisoire (→ D17+D22) ; champ auxiliaire dédié = sprint futur ; portage C# = dette D27/D24 | `sprints/sprint_senescence.md` |
| Sprint diversification écologique (D26 : étendre le catalogue d'espèces — à séquencer après éclairement D21 + décision class-based/data-driven, coordonné D22). Pas encore de kickoff | — |
| Sprint 1 (recalibrage visuel + grille 3×3 + maison) | `sprints/sprint_1_recalibrage_visuel.md` |
| Sprint 2 (orchestration C# : Main, GameManager, TurnSystem) | `sprints/sprint_2_orchestration.md` |
| ✅ **TERMINÉ 2026-06-02 (Python)** — Sprint éclairement (D20+D21 levées Python) : `LightField` v2 analytique (ombres-capsules astro, intégrale, auto-ombrage exclu) + `perennials.py` (5 arbres, courbe d'âge, caduc) + position continue côté lumière + extensibilité catalogue (`STRATE_DEFAULTS`). 500 ans stables. Portage C# + parité = dette D24 ; nouvelle cible succession ~65 % (mosaïque) actée | `sprints/sprint_eclairement.md` |
| Sprint génétique/reproduction (Z7, D17+D22 : banques + héritage biparental) | `sprints/sprint_genetique.md` |
| Sprint 3 (portage simulation — peut absorber le sprint éclairement) | `sprints/sprint_3_portage_simulation.md` |
| Sprint 4 (Vigueur, paliers, encyclopédie, carnet, magazine, foyer) | `sprints/sprint_4_mecaniques_conception.md` |

Pour l'historique des décisions, voir `journal.md`.
