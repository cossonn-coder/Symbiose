# Journal Symbiose

Trace écrite vivante du développement. Une entrée par sprint, par décision
structurante, ou par incident notable. À jour à la fin de chaque session.

**Conventions** :
- Dates en `YYYY-MM-DD`.
- Une entrée commence par un titre `## YYYY-MM-DD — Titre court`.
- Les décisions sont préfixées `**Décision :**`, les questions ouvertes `**Question :**`.
- Les éléments de backlog sont en bas de fichier dans la section dédiée.

---

## Index

- [2026-05-29 — Sprint 0 : reprise et infrastructure documentaire](#2026-05-29--sprint-0--reprise-et-infrastructure-documentaire)
- [2026-05-29 — Sprint conception : redéfinition de la vision du jeu](#2026-05-29--sprint-conception--redéfinition-de-la-vision-du-jeu)
- [Dette technique consolidée](#dette-technique-consolidée)
- [Backlog](#backlog)

---

## 2026-05-29 — Sprint 0 : reprise et infrastructure documentaire

### Contexte

Reprise du projet après une pause de plusieurs semaines. Travail en SSH
depuis téléphone sur VM Debian. Objectif de la session : faire l'état
des lieux complet, poser le `CLAUDE.md`, le `journal.md`, l'index mémoire,
et sécuriser le tout dans un dépôt git initial.

### État des lieux à l'ouverture

**Moteur Python** (`data/code/`) — solide, ~2500 lignes, 500+ ans simulés
sans crash. C'est la source de vérité écologique.

| Fichier | Rôle |
|---|---|
| `models.py` | Hiérarchie classes, instances, tuiles, rondelles, registre d'effets |
| `fields.py` | GridField, LightField, DisturbanceField, SeedBank, EcoFields |
| `effects.py` | Système d'effets hybride probabiliste |
| `engine.py` | Boucle 52 semaines, succession, transitions saisonnières |
| `main.py` | Scénario test (5 plantes, 1 tuile, durée paramétrable) |

**Portage Godot/C#** — fondations posées dans `core/`, orchestration vide.

Fonctionnels (~1700 lignes) : `PlantData.cs`, `GridField.cs`, `TileData.cs`,
`PlantCatalogue.cs` (14 espèces dont indicatrices), `SpriteLoader.cs`.

Le `GridField.cs` C# est **plus avancé** que la version Python :
- OM tri-compartiment (fresh / active / stable) au lieu d'un seul champ
- Pression pathogène scalaire par tuile
- Rain feedback couplé à la densité végétale

Stubs vides (12 fichiers) : `GameManager`, `EcologySystem`, `TurnSystem`,
`SeedBankSystem`, tout `plants/`, `ui/`, `visuals/`, `world/SoilField.cs`,
`Main.cs` (classe nommée `Node2d`, hors namespace).

Non portés : `effects.py`, `engine.py` (toute la logique de simulation
hebdomadaire et la succession écologique).

**Configuration Godot** :
- Godot 4.6 .NET, C# .NET 8 ✓
- 1920×1080, filtre Nearest ✓
- Seul `SpriteLoader` en autoload
- `run/main_scene` pointe vers `TileGrid.tscn` (et non `Main.tscn` qui est
  un brouillon obsolète avec des Node vides en français)

**Sprites** :
- `tile_terre.png` mesure **78×57** sur disque alors que `TileGrid.cs`
  code une grille en 96×48 → décalages garantis
- Plusieurs PNG de plantes sont des sprite sheets 1408×768 non parsés
- Le basilic a 4 stades en PNG individuels mais en RGB **sans canal alpha**
- Catalogue C# cherche `tomato_*`, `basil_*`, `bean_*` — sur disque les
  fichiers sont nommés en français (`basilic_*`, `tomates`, `haricot`)
- **Pas de sprite maison** — pourtant pièce centrale du design 3×3

### Incident Nextcloud

Pendant la session, le dossier projet a temporairement perdu plusieurs
sous-dossiers (`plants/`, `ui/`, `visuals/`, `world/`, `data/code/`, ainsi
que `Main.cs`, `project.godot`, `Symbiose.csproj`, etc.) suite à une
synchronisation Nextcloud. La synchronisation s'est terminée et tout est
revenu. Conséquence durable : **toujours travailler avec un dépôt git
sain** pour éviter une perte définitive lors d'un prochain incident sync.

### Décisions du Sprint 0

- **Décision** : adopter le `CLAUDE.md` global de Karpathy (déjà installé
  dans `~/.claude/CLAUDE.md`) et lui adjoindre un `CLAUDE.md` projet
  spécifique à Symbiose contenant identité, source de vérité, stack,
  philosophie, archi courante, garde-fous, backlog.
- **Décision** : tenir un `journal.md` à la racine du projet versionné
  avec le code. C'est la mémoire partagée Nico ↔ Claude des décisions.
- **Décision** : initialiser un dépôt git local pour geler l'état après
  l'incident Nextcloud, sans pousser vers un remote pour l'instant.
- **Décision** : reporter la création des skills et agents au Sprint 2,
  quand le besoin se manifestera concrètement. Ne pas sur-outiller.
- **Décision** : ajouter `.claude/settings.local.json` au `.gitignore`
  (permissions par machine, non partageables).
- **Décision** : prioriser l'alignement Python ← C# (faire évoluer Python
  vers OM tri-compartiment et pathogen_pressure) plutôt que de régresser
  le C#, pour conserver Python comme référence à jour.

### Ce qui a été produit dans le Sprint 0

- `.gitignore` étendu (Claude settings, `__pycache__`)
- `CLAUDE.md` projet (≈110 lignes)
- `journal.md` (ce fichier)
- Système mémoire initialisé (index + 3 fichiers essentiels)
- Premier commit git de l'état complet

---

## 2026-05-29 — Sprint conception : redéfinition de la vision du jeu

### Contexte

Session de challenge constructif à la demande de Nico — « pose-moi des
questions et challenge ma conception ». Format : 12 questions structurantes
posées par Claude, 12 réponses tranchées par Nico, sur la nature même du jeu.

Avant cette session, le `CLAUDE.md` décrivait Symbiose comme un
« roguelike écologique » avec runs, shop inter-run, extinction et reset.
Cette session a montré que **ce cadre n'était plus aligné** avec ce que
Nico imagine vraiment. Tout a été redéfini.

### Les 12 décisions structurantes

**1. Sandbox écologique évolutif, pas roguelike.**
Run éternel. Le mot « roguelike » et son vocabulaire dérivé (shop
inter-run, extinction = fin de run, héritage sol entre runs) sont
obsolètes. Le jardin est unique, persistant, et grandit avec le joueur.

**2. Vigueur unifiée — Mana propre + Qi = champs écologiques.**
Inspiration croisée Qi chinois (énergie circulante) et Mana polynésien
(énergie propre à chaque être). Modèle minimaliste : pas de nouveau
GridField pour le Qi, les champs existants (`microbiome`, `soil_memory`,
`om_*`, `fertilite`) modélisent déjà le territoire énergétique. La
Vigueur (≡ Mana) est ce que chaque être vivant — joueur, plante,
auxiliaire, nuisible — puise dans le territoire et y dépose à sa mort.

**3. Apprentissage par paliers de maîtrise** : découverte → investissement
→ maîtrise → expertise → transcendant. Granularité : **par famille
botanique et par concept écologique transversal** (succession,
polyculture, eau, compost…), pas par espèce individuelle. Évite l'UI
catastrophique (5 paliers × 100 espèces = 500 jauges).

**4. Méthode scientifique préférée** comme levier d'apprentissage.
Observer → formuler hypothèse → expérimenter → conclure. Le jeu
récompense trial & error, prise de risque, diversification d'idées.

**5. Transcendant = non-action existentielle.** Récompense ultime :
un écosystème auto-suffisant qui n'a plus besoin du joueur. Mitigations
contre la fin d'engagement : perturbations (météo extrême, nouvelles
espèces, usure structures) entretiennent le besoin, et la lenteur du jeu
rappelle le joueur par sessions espacées.

**6. 15 minutes d'action ininterrompue par saison**, en temps réel
(1 semaine = 60 secondes). Rythme soutenu au début, s'apaise avec la
maîtrise — ce qui prépare et justifie le palier transcendant.

**7. Découpage phase planification / phase saison clairement délimité :**
- Phase **planification** (entre deux saisons, temps figé) :
  plantation, achat magazine, aménagement de structures lourdes
  (mare, pergola, haie), changement de configuration, consultation
  longue de l'encyclopédie ;
- Phase **saison** (15 min temps réel) : arrosage ciblé, tuteurer,
  écraser un nuisible visible, paillage local, récolte, consultation
  rapide du carnet.

**8. Trois écoles de démarrage au choix** : friche pionnière, sol
modeste, jardin abandonné. Le joueur choisit son ambiance de départ.

**9. Quatre canaux d'acquisition d'espèces :**
- (a) succession spontanée (le sol décide selon `niche_index`) ;
- (b) événements rares (cadeaux du monde — bouture voisin, graine
  d'oiseau, vent…) ;
- (c) exploration de friche périphérique (abstraite au début, monde
  évolutif en backlog lointain) ;
- (d) **magazine de botanique** — déblocage par Vigueur joueur + niveau
  de maîtrise. Remplace le shop sans rompre la philosophie : tu achètes
  du savoir avec ton énergie vitale, et tu ne peux acheter que ce que tu
  es prêt à comprendre.

**10. Encyclopédie + carnet auto, dispositifs distincts :**
- **Encyclopédie** type wiki, se complète aux découvertes selon
  paliers (voir = entrée basique, cycle complet = description biologique,
  plusieurs cycles avec succès = effets écosystémiques).
- **Carnet auto** consultable, indexé, **descriptif au début**
  (faits bruts, le joueur infère) et **interprétatif au seuil de
  maîtrise** (le carnet propose des causes une fois le concept maîtrisé).
  Préserve la méthode scientifique.

**11. Auxiliaires visibles dès le début mais non identifiables sans
maîtrise.** Modèle technique : champ ambiant GridField pour la dynamique
écologique + sprites apparents visibles. Tu vois l'insecte avant de
connaître son nom — posture du naturaliste débutant.

**12. Extension du terrain par maîtrise écologique.** Démarrage à
9 tuiles dont la maison centrale. Maîtriser une famille botanique fait
apparaître une **tuile thématique** (verger, mare, prairie aromatique…)
— pas d'achat, pas de conquête : la connaissance ouvre l'espace.

### Modèle de Vigueur du joueur (à ajuster post-test)

- Montant initial : **100**
- Régénération continue : **+10 par semaine simulée**
- Régénération totale au passage de saison
- Sources extérieures : récolte de plantes mûres, méditation au foyer
- **Vigueur max augmente avec le niveau de maîtrise** — boucle de
  progression : plus on sait, plus on peut, plus on vit le jardin

### La maison normande = hub vivant (5 fonctions actives)

- Atelier (créer/réparer structures persistantes)
- Semis intérieur (germination hors saison)
- Magazine de botanique (déblocage espèces)
- Carnet (consultation centralisée)
- **Foyer** — nouveau lieu, point de récupération de Vigueur

### UX du volume cognitif

432 plots à surveiller × 15 min temps réel = **3 mitigations actives
simultanément** :
- Pause libre à volonté
- Notifications hiérarchisées (seuls les événements importants remontent)
- Zoom contextuel (×4 vue globale → ×32 vue un plot)

### Implications immédiates sur la philosophie

La règle #1 de la philosophie historique (« le joueur agit sur le MILIEU,
jamais directement sur les plantes ») est **partiellement assouplie** :
le joueur peut écraser un nuisible visible, mais l'action coûte de la
Vigueur et augmente `disturbance` localement — donc rappelle des
nuisibles. La permaculture s'enseigne par l'usure de la solution facile.
Voir [[feedback-design]] mémoire mise à jour.

### Zones blanches restantes (à traiter dans la suite de la session)

1. Cycle de sauvegarde (run éternel = persistance critique)
2. « Gérer » les aléas météo : mécanique précise
3. Multiples jardins / multijoueur
4. Lore / narration (qui est le joueur ? la maison normande ?)
5. Conditions de panne sèche (tout meurt)
6. Difficulty / accessibilité

---

## Dette technique consolidée

| Code | Description | Priorité |
|---|---|---|
| D1 | Fichiers transitoirement perdus le 2026-05-29 (Nextcloud). Mitigé par init git. | 🔴 → ✅ mitigé |
| D2 | Mismatch dimensions tuiles : 78×57 réel vs 96×48 codé dans `TileGrid.cs` | 🔴 |
| D3 | Mismatch noms sprites : catalogue C# attend `basil_*`, fichiers nommés `basilic_*` | 🔴 |
| D4 | Sprite maison absent — pièce centrale du design 3×3 sans visuel | 🔴 |
| D5 | `effects.py` jamais porté en C# | 🟡 |
| D6 | `engine.py` jamais porté en C# (boucle 52 semaines, succession, aléas) | 🟡 |
| D7 | Stubs vides hors namespace `Symbiose` (Main, EcologySystem, etc.) | 🟡 |
| D8 | `Main.tscn` obsolète (Node vides en français), à supprimer/refaire | 🟡 |
| D9 | Conflit de nom `PlantInstance` (`core/PlantData.cs` data vs `plants/PlantInstance.cs` Node Godot) | 🟡 |
| D10 | Divergence Python ↔ C# : OM tri-compartiment et `PathogenPressure` n'existent qu'en C# | 🟢 |
| D11 | Moteur Python à étendre : **Vigueur universelle** (joueur + plantes + auxiliaires + nuisibles), couche transversale à concevoir | 🟡 |
| D12 | Moteur Python à étendre : **paliers de maîtrise** (méta-état du joueur, conditions de passage par famille et concept) | 🟡 |
| D13 | Système **Magazine de botanique** à concevoir (coût Vigueur + maîtrise, déblocage espèces) | 🟡 |
| D14 | Système **Carnet auto** à concevoir (enregistrement événements, indexation, bascule descriptif → interprétatif) | 🟡 |
| D15 | Mécanique d'**extension du terrain par maîtrise** (tuile thématique apparaît au palier maîtrise d'une famille) | 🟢 |

---

## Backlog

### Sprint 0 — gel et infrastructure documentaire — TERMINÉ ✅
- [x] État des lieux complet
- [x] `CLAUDE.md` projet
- [x] `journal.md` initial
- [x] `.gitignore` étendu
- [x] Système mémoire initial
- [x] Premier commit git

### Sprint conception — redéfinition de la vision du jeu — TERMINÉ ✅
- [x] 12 décisions structurantes actées
- [x] `journal.md` enrichi
- [x] `CLAUDE.md` réécrit (vision actualisée)
- [x] Fichiers mémoire rafraîchis
- [x] Commit dédié

### Sprint conception bis — zones blanches restantes — À FAIRE
- [ ] Cycle de sauvegarde (run éternel)
- [ ] Mécanique de gestion des aléas météo
- [ ] Multiples jardins / multijoueur
- [ ] Lore / narration
- [ ] Conditions de panne sèche
- [ ] Difficulty / accessibilité

### Sprint 1 — recalibrage visuel
- [ ] Mesurer dimensions exactes de tous les sprites attendus
- [ ] Décider format final tuile (78×57 conservé, ou re-générer en 96×48)
- [ ] Générer sprite maison (calcaire gris, toit ardoise, volets bois)
- [ ] Réécrire `world/TileGrid.cs` pour grille 3×3 tuiles + maison centrale
- [ ] Aligner nomenclature sprites ↔ catalogue (`SpriteName` dans
      `PlantCatalogue.cs` ou renommage des fichiers)
- [ ] Vérifier en éditeur Godot que la grille s'affiche correctement

### Sprint 2 — fondations orchestration
- [ ] `Main.cs` propre, dans namespace `Symbiose`, classe `Main : Node2D`
- [ ] `core/GameManager.cs` — singleton état global, GameState analogue
      au `game_state` dict de Python
- [ ] `core/TurnSystem.cs` — phases (planification / saison)
- [ ] Nouvelle `Main.tscn` qui remplace le brouillon obsolète

### Sprint 3 — portage simulation
- [ ] Porter `effects.py` → `core/EffectSystem.cs` (mutations + résolveur)
- [ ] Porter `engine.py` → `core/EcologySystem.cs` (tick hebdo, succession,
      aléas, transitions saisonnières)
- [ ] Tests de cohérence : lancer 1 an de simulation côté Python ET C#
      avec mêmes seeds, comparer états finaux
- [ ] Réconcilier dette D10 (porter v5 vers Python ou geler la divergence)

### Sprint 4 — affichage écologique
- [ ] `PlantNode.cs` — Sprite2D plante, ancrage bas-centre, ZIndex
- [ ] `CameraSystem.cs` — zoom par paliers ×4/×8/×16/×32 snap pixel-perfect
- [ ] `LightOverlay.cs` — ombre dynamique maison (Light2D + LightOccluder2D)
- [ ] Premier test bout-en-bout : 1 tuile + 5 plantes + 1 an simulé visible

### Backlog lointain
- Shop roguelike (inter-run et intra-run)
- Bilan écologique fin de run (narratif)
- Journal Connaissance (dans la maison)
- Vue loupe Z3 (gestes fins)
- Catalogue étendu 80–120 espèces
- Cartes événements (météo + narratifs)
- Sprint version physique (STL plantes, cartes MTG)
