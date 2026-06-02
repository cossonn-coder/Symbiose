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
- [2026-05-29 — Sprint conception bis : zones blanches refermées](#2026-05-29--sprint-conception-bis--zones-blanches-refermées)
- [2026-05-29 — Zone Z7 : éclairement spatial pixel-exact](#2026-05-29--zone-z7--éclairement-spatial-pixel-exact)
- [2026-05-29 — Sprint conception éclairement & reproduction (recadrage Z7)](#2026-05-29--sprint-conception-éclairement--reproduction-recadrage-z7)
- [2026-06-02 — Sprint sol vivant : le sol devient organisme (Python)](#2026-06-02--sprint-sol-vivant--le-sol-devient-organisme-python)
- [2026-06-02 — Consolidation sol vivant : puits microbien (Python)](#2026-06-02--consolidation-sol-vivant--puits-microbien-python)
- [2026-06-02 — Mini-sprint succession : gradient pionnier → prairie ∝ maturité du sol](#2026-06-02--mini-sprint-succession--gradient-pionnier--prairie--maturité-du-sol)
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

## 2026-05-29 — Sprint conception bis : zones blanches refermées

### Contexte

Session enchaînée après le Sprint conception. Six zones blanches restaient
à fermer pour figer la cible avant les sprints code. Format identique :
Claude pose la tension + 3 questions max, Nico tranche, on acte.

### Z1. Cycle de sauvegarde

- **Décision** : auto-save **uniquement** au passage de saison. Pas
  d'auto-save intra-saison. Perdre une saison en cas de crash est
  accepté — la saison est un bloc dramatique qui pèse.
- **Décision** : format **JSON lisible**. Pas binaire. Run éternel +
  apprentissage scientifique = le joueur peut vouloir grep son propre
  journal dans 5 ans, et Claude/dev en debug.
- **Décision** : **un seul save par profil** (cohérent avec slots de Z3).
  Pas de save-scumming, pas de slots de backup. Autre jardin = nouveau
  profil ou déménagement.
- **Décision** : champ `engine_version` dans le save. Tant qu'on est
  avant v1.0, on **casse** explicitement les saves antérieurs sans
  migration. Migrations à écrire seulement après v1.0.
- **Décision** : la **seed d'origine** du terrain est persistée dans le
  profil. Permet de re-générer le même point de départ (debug, partage
  d'école avec un ami).

### Z2. Gestion des aléas météo

- **Décision** : préavis météo par **signes diégétiques** (oiseaux,
  ciel, anneau lunaire, brume, sol qui craquelle). Pas d'icône calendrier.
  L'interprétation explicite débloque au palier de maîtrise du concept
  transversal **« météo / climat »** (carnet bascule en interprétatif
  sur ce concept).
- **Décision** : action joueur en **deux temps** :
  - **Préparation** (phase planification, temps figé) : paillage profond,
    voiles d'hivernage, brise-vent, structures persistantes. Coût Vigueur
    modéré + temps.
  - **Réaction** (phase saison, temps réel) : arrosage ciblé, sauver
    une plante précise, secouer une branche givrée. Coût Vigueur élevé.
  - La permaculture (préparation) reste mieux rétribuée que le
    sapeur-pompier (réaction). Voir [[feedback-design]].
- **Décision** : **~20 %** d'événements météo restent **imprévisibles**
  tant que le joueur n'a pas atteint le palier transcendant en météo.
  **Au transcendant météo : tout devient prévisible** — récompense rare
  qui cristallise la philo « transcendant = non-action ».
- **Conséquence Python** : ajouter `forecast` dans `game_state`, décaler
  le tirage `random.choice` 1-2 semaines en avance pour alimenter les
  signes diégétiques. Voir dette D16.

### Z3. Multiples jardins / multijoueur

- **Décision** : **profils multiples** = oui. Un profil = un **avatar
  joueur** (nom, encyclopédie, paliers de maîtrise, banque de graines,
  Vigueur max courante) + un ou plusieurs **terrains**.
- **Décision** : **mécanique de déménagement** — un avatar peut migrer
  d'un terrain à un autre. Il **emporte** son savoir, ses paliers, ses
  graines, sa Vigueur max. Le **terrain reste lui-même** (sol, climat,
  friche périphérique, mémoire). Le savoir voyage, le territoire non.
  - Conséquence design : un avatar expert qui déménage sur une friche
    pionnière démarre fort (Vigueur max élevée, sait reconnaître) mais
    le terrain reste pionnier — il sait vers où le mener, pas où il
    en est.
  - Conséquence technique : séparer `SeedBank-joueur` (récoltée,
    transportable) de `SeedBank-sol` (graines dormantes intrinsèques
    au terrain). Voir dette D17.
- **Décision** : **encyclopédie + paliers strictement par avatar** —
  pas de méta-savoir inter-avatars. Nouvel avatar = repart de zéro.
- **Décision** : **multijoueur synchrone = non**, fermé définitivement
  (incompatible avec la pause libre et le temps lent).
- **Décision** : **multijoueur asynchrone** (visite du jardin d'un ami
  en mode lecture) = backlog **v2.0+**.
- **Décision** : **« co-saison » à 2 joueurs** (15 min synchrones sur
  une parcelle commune, hot-seat ou écran partagé) = nouveau backlog
  **v2.0+**, à explorer après v1.0.

### Z4. Lore / narration

- **Décision** : joueur = **jardinier silencieux nommé**. Le profil
  porte un nom et une banque de graines, c'est tout. Pas de bio, pas
  d'âge, pas de famille imposée. Identité par les gestes.
- **Décision** : pas de cutscene, pas de drame, pas d'ancien jardinier
  évoqué. **Préambule court** (4-6 phrases d'ambiance lues à la création
  de profil), puis on **tombe direct dans le jardin**. Cadre poétique
  permaculturel à Montmartin-sur-Mer, volets bois, sol calcaire, vent
  de la Manche.
- **Décision** : **trois voix narratives diégétiques** distinctes :
  - **Encyclopédie** — voix « naturaliste qui observe », tutoiement
    écologique
  - **Carnet auto** — voix interne à la première personne,
    descriptif → interprétatif
  - **Pages secrètes** (nouveau dispositif) — connaissances perdues,
    éparses, ésotériques. Trouvées par hasard, gagnées après une belle
    réalisation ou découvertes en fouillant. Voix multiples : extraits
    poétiques, savoirs paysans, herbiers anciens, citations type
    Fukuoka / Sackville-West / sorcières médicinales. Lieu de
    consultation pressenti : coffret au grenier de la maison normande.
- Pas de narrateur externe omniscient, pas de PNJ, pas de quête imposée.
  Histoire émergente via les événements rares (bouture, oiseau, vent).

### Z5. Conditions de panne sèche

- **Décision** : **option (a)** — la **succession spontanée** garantit
  la résilience. La `SeedBank-sol` ramène des pionnières (orties,
  chénopode, plantain) en quelques saisons même sur un jardin saccagé.
  Pas d'événement spécial nécessaire : c'est le fonctionnement normal
  d'un sol vivant.
- **Décision** : la **régen passive de Vigueur joueur croît avec la
  maîtrise**. Plus tu connais l'écologie, plus vite tu te ressources
  dans ton jardin. Couplée à « Vigueur max augmente avec paliers » :
  plafond ET vitesse de régen montent.
- **Décision** : **nouvelle action gameplay « manger »** — consommer
  une feuille, une fleur, un fruit rend de la Vigueur (proportionnelle
  à la maturité de l'organe et au type). Geste du jardinier qui goûte.
  Cohérent avec le foyer comme point de récupération. Voir dette D19.
- **Décision** : **pas de bouton « recommencer »**. Run éternel = éternel.
  Si le joueur veut un autre jardin, il déménage (Z3) ou crée un autre
  profil. **MAIS** la seed d'origine du terrain est conservée dans le
  profil (Z1) : un même point de départ peut être re-généré sans avoir
  besoin d'un bouton dédié.

### Z6. Difficulty / accessibilité

- **Décision** : **pas de mode difficulté classique**. Le jeu n'est
  pas un jeu de score.
- **Décision** : **réglages d'aide modulaires** dans menu Options
  dédié, périmètre minimal :
  - **Vitesse de simulation** : 1 semaine = 30 à 180 s, défaut 60 s.
  - **Verbosité des notifications** : silencieux / important / tout.
    Défaut « important ».
  - **Encyclopédie de démarrage** : vierge / amorcée (5 plantes
    communes pré-identifiées) / fournie (tout palier découverte
    révélé). Défaut « amorcée ».
  - **Carnet interprétatif anticipé** : OUI/NON. Défaut NON (préserve
    la méthode scientifique).
- **Décision** : **mode debug champs écologiques** (overlay heatmaps
  humidité, fertilité, microbiome, disturbance…) = **toggle libre dans
  Options dès le début**, étiqueté « affichage technique — déconseillé
  en première découverte ». Accessibilité brute > récompense punitive.
- **Décision** : **page d'accueil minimale** au premier lancement —
  4-5 pictogrammes silencieux des gestes de base (cliquer, planter,
  observer, méditer, manger). Pas de texte, pas de tutoriel imposé.
  Le jeu se découvre par l'action.

### Nouvelles dettes techniques (D16-D19)

- **D16** : décaler le tirage météo en `forecast` 1-2 semaines en
  avance dans `engine.py`, alimenter les signes diégétiques.
- **D17** : séparer `SeedBank-joueur` (transportable, suit l'avatar)
  de `SeedBank-sol` (intrinsèque au terrain) côté Python puis C#.
- **D18** : système de **pages secrètes** à concevoir — sources
  (drop hasard / récompense palier / événement rare), lieu de
  consultation (coffret maison ?), volume cible v1.0 (30-50 pages ?),
  génération de contenu narratif. Mérite une session future dédiée.
- **D19** : ajouter **« manger »** comme action gameplay
  (organes consommables → Vigueur joueur).

### Ce qui a été produit dans le Sprint conception bis

- Cette entrée `journal.md`
- `CLAUDE.md` enrichi (sauvegarde, météo, déménagement, pages secrètes,
  manger, accessibilité dans « Mécaniques centrales »)
- Mémoire actualisée (`project_game_vision.md`, `project_status.md`)
- Commit dédié

---

## 2026-05-29 — Zone Z7 : éclairement spatial pixel-exact

### Contexte

Immédiatement après la clôture du Sprint conception bis, Nico identifie
une **7e zone blanche majeure** non couverte par les 6 précédentes :
**le calcul d'ensoleillement par pixel en fonction des ombres portées
par les canopées et structures, à chaque tranche horaire.**

Argument : en permaculture, la micro-géographie des ombres est
constitutive du gameplay. Tu plantes une salade sous un fruitier
exprès, un brise-vent à l'ouest pour adoucir le soleil couchant, tu
exploites une ombre matinale. Le `LightField` actuel (Python + C#) est
trop pauvre — il n'a pas la notion d'ombres portées.

### Décisions Z7 actées

- **Granularité spatiale : pixel exact** (78×57 par tuile). Coût
  mémoire : ~800 KB à 9 tuiles, ~4,4 MB en long terme. Coût CPU :
  < 1 ms par recalcul complet, hebdomadaire. **Trivial.**
- **Granularité temporelle : 4 tranches** (matin / midi / soir / nuit)
  + **intégrale journalière** d'ensoleillement cumulée par pixel.
  L'intégrale pilote la photosynthèse — c'est elle qui compte
  biologiquement.
- **Hauteur des canopées et structures stockée en cm** (range 0 à
  3000+). `PlantData.canopy_height_potential` par stade pour annuelles,
  par courbe d'âge pour pérennes ligneuses.
- **`current_height` calculée** :
  `canopy_height_potential × genetic_factor × growth_factor`
  - `genetic_factor` ∈ [0.7, 1.3], hérité de la graine (D22)
  - `growth_factor` ∈ [0.4, 1.2], modulé par Vigueur / eau / nutriments
- **Boucle de feedback** : la lumière reçue affecte la hauteur, qui
  affecte les ombres portées, qui affectent la lumière reçue des voisins.
  Émergence écologique.
- **Recalcul hebdomadaire** (à chaque tick simulation). Pas en temps
  réel — inutile.
- **Algorithme** : projection d'ombre trapézoïdale par ombrageur (et
  non raycast par pixel). O(ombrageurs × pixels_par_ombre) ≈ 160 000 ops.

### Hauteurs structures actées

- Mare : 0 cm
- Brise-vent (haie taillée) : 150 cm
- Pergola : 250 cm
- Maison normande : 700 cm

### Arbres pérennes — 5 espèces premières (D21)

| Arbre | 5 ans | 10 ans | 20 ans | 50 ans | Centenaire |
|---|---|---|---|---|---|
| Figuier | 200 | 400 | 500 | — | — |
| Pommier | 200 | 350 | 500 | 700 | — |
| Cerisier | 250 | 500 | 700 | 900 | 1000 |
| Noyer | 300 | 600 | 1000 | 1500 | 2500 |
| Chêne | 200 | 400 | 700 | 1500 | 3000 |

Les autres arbres (poirier, prunier, châtaignier, frêne, tilleul,
bouleau, saule, aulne, peuplier, érable…) constituent la dette D23
(catalogue arbres étendu) — à compléter une fois le squelette validé.

### Audit botanique — 14 espèces actuelles

Hauteurs potentielles (cm) à intégrer dans `PlantData` :

| Espèce | Famille | Type | Semis | Jeune | Adulte | Mature |
|---|---|---|---|---|---|---|
| Tomate | Solanaceae | annuel tuteurée | 5 | 30 | 100 | 150 |
| Basilic | Lamiaceae | annuel bas | 3 | — | 25 | 40 |
| Haricot | Fabaceae | annuel grimpant | 5 | 30 | 150 | 200 |
| Trèfle | Fabaceae | couvre-sol | 2 | — | 15 | — |
| Tournesol | Asteraceae | annuel haut | 5 | 50 | 180 | 250 |
| Poivron | Solanaceae | annuel moyen | 5 | — | 60 | 80 |
| Bourse-à-pasteur | Brassicaceae | adventice | 3 | — | 25 | 40 |
| Minette | Fabaceae | vivace rampante | 3 | — | 30 | — |
| Pâturin | Poaceae | graminée vivace | 3 | — | 30 | — |
| Pissenlit | Asteraceae | rosette + hampe | 3 | 8 | 30 | — |
| Ortie | Urticaceae | vivace haute | 5 | — | 120 | — |
| Prêle | Equisetaceae | vivace moyenne | 5 | — | 60 | — |
| Plantain | Plantaginaceae | rosette plaquée | 3 | — | 15 | — |
| Molène | Scrophulariaceae | bisannuelle haute | 5 | — | 200 | — |

**Important écologique** : ces hauteurs sont des **potentiels**, modulés
par `genetic_factor × growth_factor`. Deux haricots côte à côte n'ont
jamais exactement la même taille. Sélection artificielle possible
émergente (récolter les plantes les plus hautes favorise la lignée).

### Nouvelles dettes techniques (D20-D23)

- **D20** : système d'éclairement spatial pixel-exact (`LightField` v2,
  ombres portées, 4 tranches + intégrale, recalcul hebdomadaire)
- **D21** : système temporel des pérennes ligneuses (âge en années,
  courbe pluri-décennale, distinct du `GrowthStage`)
- **D22** : héritage génétique de la graine (`genetic_factor` ∈ [0.7,
  1.3], distribution gaussienne, hérité à la fécondation, généralisable
  à d'autres caractères que la hauteur)
- **D23** : catalogue arbres pérennes étendu (poirier, prunier,
  châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier,
  érable…) — différée post-validation du squelette

### Sprint dédié créé

Kickoff autosuffisant `sprints/sprint_eclairement.md` rédigé.
Le sprint peut **absorber tout ou partie du Sprint 3 (portage
simulation)** parce que toucher au `LightField` et ajouter la nouvelle
classe `PerennialWoody` impose de toucher au tick hebdomadaire — autant
porter `effects.py` et `engine.py` dans la foulée.

À décider en début de session selon l'énergie disponible.

### Ce qui a été produit pour Z7

- Cette entrée `journal.md`
- `sprints/sprint_eclairement.md` (kickoff autosuffisant)
- `CLAUDE.md` mis à jour (Systèmes à concevoir D20-D23, backlog actif)
- Mémoire actualisée (`project_status.md`)
- Commit dédié

---

## 2026-05-29 — Sprint conception éclairement & reproduction (recadrage Z7)

### Contexte

Session ouverte sur « lis `sprints/sprint_eclairement.md` ». La lecture du
kickoff Z7 **et du code réel** (`fields.py`, `GridField.cs`, `PlantData.cs`,
`TileData.cs`) a fait remonter trois frictions entre l'intention du kickoff
et l'état du code. Plutôt que d'implémenter, on a rouvert la conception et
tranché l'architecture en profondeur. **Session de conception pure — aucun
fichier de code touché.**

### Frictions relevées à la lecture

1. **Confusion d'échelle « tuile » vs « plot »** dans le kickoff. La réalité
   du code : monde 3×3 **tuiles**, une tuile = 6×8 **plots** quinconce
   (= 432 plots, déjà cité dans l'UX), un plot = sprite 78×57 px. Le
   « 78×57 » du kickoff désignait donc **un plot**, pas une tuile — chiffrage
   mémoire faux d'un facteur ~48 (sans conséquence, RAM négligeable).
2. **Lumière pixel ↔ photosynthèse par plot.** Tout le moteur indexe par
   plot ; une ombre pixel-exacte traverse les frontières de plots. Le
   mapping pixel↔plot n'était pas défini : vraie zone blanche.
3. **Inversion de la source de vérité (D10).** `GridField.cs` est en v4
   (OM tri-compartiment, rain feedback, `PathogenPressure`) alors que
   `fields.py` est resté en v3. Le test de parité du kickoff est impossible
   tant que l'OM diverge.

### Décisions structurantes

**1. Architecture lumière = Option A (maillage adaptatif).**
- **Décision** : « stop les plots » pour la lumière et les plantes. **Canopée
  + lumière au pixel** (structure fine = gameplay des ombres), **chimie du
  sol au plot** (phénomène diffus et lent — le pixel n'y apporte rien et la
  diffusion lisse de toute façon). Maillage adapté au phénomène.
- **Décision** : un **seul pont** pixel↔plot, propre et unidirectionnel — la
  photosynthèse lit la lumière-pixel sous l'empreinte de canopée → module la
  croissance. Le souterrain reste entièrement en monde-plot (inchangé).
- **Décision** : l'espace de simulation de la lumière est **top-down
  cartésien** (vue de dessus, en cm), **jamais** l'espace iso d'affichage —
  sinon la perspective fausserait les longueurs d'ombre. Le rendu projette en
  iso après coup.
- Écarté : Option B (tout au pixel — refonte totale, revalidation 500 ans,
  gain nul sur la chimie lisse) et Option C (lumière agrégée par plot —
  contredit « stop les plots » et sous-exploite le pixel).

**2. Calibration de l'échelle spatiale.**
- **Décision** : **1 plot = 50×50 cm** (maille potagère permaculture). Monde
  3×3 tuiles × (6×8) = 432 plots = **12×9 m ≈ 108 m²**, jardin familial
  crédible.
- **Décision** : résolution de l'espace-sol lumière = **2 cm/px** (~270 k
  px-sol monde, ~5,4 MB pour 5 floats/px — négligeable).
- **Décision** : orientation par défaut **Nord en haut, soleil culminant au
  Sud** (à confirmer en implémentation).
- **Décision** : le plot ne porte plus la position des plantes — il ne sert
  **que** de maille à la chimie du sol. La position des plantes devient
  **continue** (pixel-sol `x_cm, y_cm`), plot-foyer = `floor(pos / 50 cm)`.

**3. Modèle d'ombre (D20).**
- **Décision** : angles solaires par **calcul astronomique** (latitude
  ~49°N), déterministe, 4 tranches (matin/midi/soir/nuit) × saisons. Bonus :
  arme le palier « météo/climat » transcendant (tout devient prévisible).
- **Décision** : `longueur_ombre = hauteur / tan(élévation)`, direction
  opposée à l'azimut. Ombre = **capsule** (disque de canopée glissé sur la
  longueur d'ombre), rasterisée en pixels-sol.
- **Décision** : opacité d'ombre **variable par espèce** → nouveau champ
  `foliage_density` (noyer dense ~0.8, bouleau léger ~0.4). Mécanique
  permaculture (choisir un arbre à ombre légère pour un sous-étage).
- **Décision** : cumul **multiplicatif** des ombres ; **plancher de lumière
  diffuse ~15 %** (rien ne descend à 0 → sous-bois et plantes d'ombre
  viables).
- **Décision** : **intégrale journalière** = moyenne des 3 tranches éclairées
  pondérée par l'intensité solaire ; c'est elle qui pilote la photosynthèse.

**4. Empreintes des plantes.**
- **Décision** : canopée = disque de **rayon tabulé par stade** (nouvelle
  donnée à calibrer, comme les hauteurs).
- **Décision** : racines = **rayon racinaire continu** (cm → ensemble de
  plots exploités pour l'uptake). **Remplace** les `RootOffsets` discrets,
  cohérent avec la position continue.
- **Décision** : `current_height = canopy_height_potential × genetic_factor
  × growth_factor` ; boucle de feedback lumière reçue → growth_factor →
  hauteur → ombre des voisins au tick suivant.

**5. Pérennes ligneuses (D21).**
- **Décision** : **base commune polymorphe** — annuelles et arbres exposent
  la même interface (`current_height`, `canopy_radius`, `foliage_density`,
  `root_radius`). Seule la **logique de croissance** diffère (stades discrets
  vs courbe d'âge). Le LightField/photosynthèse les traitent uniformément,
  zéro duplication. (Écarté : classe `PerennialWoody` totalement séparée.)
- **Décision** : `age_years` (+1/52 par tick) ; courbe âge→(hauteur, rayon) =
  **interpolation des points tabulés** (spline monotone), aucun calage.
- **Décision** : `foliage_density` **saisonnière** — un arbre caduc
  (`WinterStrategy = dormant`) perd son ombre l'hiver. Levier permaculture
  majeur (soleil d'hiver sous un fruitier caduc, ombre d'été). Généralisé aux
  vivaces dormantes.
- **Décision** : **arbres requalifiés par taille** — figuier + pommier =
  fruitiers de jardin jouables, cerisier intermédiaire, **noyer + chêne =
  sujets structurants de lisière** (un chêne mûr fait la taille du jardin
  entier ; aucune échelle ne le rend « une plante parmi d'autres »).

**6. Génétique & reproduction (D17 + D22) — élargissement assumé.**
- **Décision** : concevoir **D17 (banque de graines par espèce) et D22
  (héritage) ensemble**, car D22 a besoin d'un porteur que l'actuelle
  SeedBank (densités d'archétypes par plot, sans espèces ni génétique) ne
  fournit pas.
- **Décision** : **deux banques distinctes** — **SeedBank-sol** (génétique
  vectorielle par espèce, liée au terrain, brassage féral conservé) +
  **SeedBank-joueur** (lots par espèce, transportable, suit l'avatar).
- **Décision** : `genetic_factor` devient un **vecteur de gènes extensible**
  (`{hauteur, vigueur, résistance, sécheresse…}`), seul `hauteur` rempli pour
  l'instant.
- **Décision** : héritage **biparental** — père compatible à portée de
  pollinisation ; `gène_enfant = moyenne(parents) + mutation gaussienne` ;
  sinon autofécondation. **Pollinisation par espèce** (anémogame/entomogame),
  rayon modulé par les **pollinisateurs auxiliaires** (vraie mécanique
  permaculture : favoriser les auxiliaires → meilleures graines).
- **Décision** : hybridation inter-espèces autorisée entre espèces proches,
  **par introgression sur espèce fixe** — l'enfant garde l'espèce de la mère,
  les gènes du père décalent ses facteurs vectoriels (parfois hors [0.7,1.3]
  = vigueur hybride). **Pas** de génération de nouvelles `PlantData` (écarté :
  trop lourd, sous-système complet).

**7. Séquencement de l'implémentation — découpage en deux sprints.**
- **Décision** : la conception est close, mais l'implémentation se scinde car
  D17+D22 sont devenus un moteur de génétique des populations dont le coût
  dépasse D20.
  - **Sprint éclairement** = D20 (ombres pixel) + D21 (pérennes) +
    calibration des empreintes/densités + **réalignement OM Python→v4**
    (préalable à toute parité). `genetic_factor` **neutre 1.0** en attendant.
  - **Sprint génétique/reproduction** = D17 + D22 complets.

### Données restant à calibrer (Sprint éclairement, en code)

Rayon de canopée par stade et `foliage_density` des 14 espèces ; rayons
racinaires ; courbes âge→(hauteur, rayon, densité) des arbres ; échelle
cm/px (2 cm/px actée) ; pondération des tranches solaires.

### Zones blanches différées

- **Version physique (tuiles 3D + cartes MTG)** : la bascule pixel découple
  la version vidéo (continue) de la version physique (cases). À traiter dans
  une session dédiée — le moteur Python n'est peut-être plus la source unique
  des deux versions.
- Ordre exact du tick hebdomadaire (croissance / lumière / photosynthèse /
  feedback).
- Profondeur racinaire (modèle resté 2D).
- Confirmation de l'orientation du monde.

### Ce qui a été produit dans cette session

- Cette entrée `journal.md` + dette consolidée affinée (D17, D20-D22)
- `CLAUDE.md` mis à jour (Option A, échelle, backlog scindé)
- `sprints/sprint_eclairement.md` réécrit (recadré Option A, sans génétique)
- `sprints/sprint_genetique.md` créé (D17 + D22)
- Mémoire actualisée (`project_status.md`, `project_python_source.md`)
- Commit dédié

---

## 2026-06-02 — Sprint sol vivant : le sol devient organisme (Python)

### Contexte

Sprint **Python pur** sur le moteur de vérité (`data/code/`), dérivé du dossier
`sprints/etude_sol_vivant.md`. Objectif : faire passer le sol de **décor
réactif** à **organisme** — les racines nourrissent le sol (exsudats), le sol
leur rend des services (minéralisation, uptake), une **vitalité émerge**. Lève
la dette **D10** côté Python (réalignement OM Python → v4 du C#).

Séquence actée (kickoff, validée par Nico) : **socle OM v4 → chantier B
(racines spatiales) → chantier A (boucle rhizosphère) → vitalité dérivée**.
Mycorhizes (chantier C) **différées** en extension future (palier avancé).

### Étape 0 — OM v4 tri-compartiment (D10 levée côté Python)

`organic_matter` mono-compartiment scindé en **`om_fresh` / `om_active` /
`om_stable`** dans `EcoFields`, alignés sur `GridField.cs`. `tick_decomposition`
réécrit en **cascade** : chaque compartiment se décompose à son rythme
(`OM_FRESH_DECAY` 0.08 / `OM_ACTIVE_DECAY` 0.018 / `OM_STABLE_DECAY` 0.0006),
modulé par le microbiome. La masse décomposée se répartit en trois destinations
sommant à 1.0 — **humification** (compartiment suivant), **minéralisation**
(→ `fertilite`, principale sur `active`), **respiration** (perte nette).
Aucune création de carbone. Nécromasse et résidus entrent par `om_fresh`.

### Étape 1 — Chantier B : racines spatiales

`engine.py:_apply_uptake` boucle désormais sur `plant.root_plots` (filtrés aux
bornes), avec `share = 1/nb_plots` (paramètre ajouté à `plant_uptake`) — on
**répartit** la consommation, on ne la duplique pas. Idem pour les
enrichissements `inject_field` « local » (`effects.py`) : répartis sur
l'empreinte racinaire. La **compétition souterraine** devient émergente.

### Étape 2 — Chantier A : boucle rhizosphère ⭐

Nouvelle méthode `engine.py:_apply_exudates` (appelée chaque tick) : chaque
plante vivante dépose des **exsudats** ∝ photosynthèse (lumière reçue × surface
foliaire × santé) sur ses `root_plots` — l'essentiel au `microbiome`, une
fraction (`EXUDATE_OM_SHARE` 0.15) à `om_fresh`. **Rétroaction** : le microbiome
gagne un **bonus d'uptake fertilité** (`UPTAKE_MICRO_BONUS` 0.40, borné).
**Universalisation** : suppression du scripting `microbiome` par famille
(Fabaceae, Medicago) — le microbiome émerge des exsudats de **toutes** les
plantes. Les Fabaceae **gardent uniquement** leur fixation N₂ → `fertilite`.
**Bornage anti-emballement** (piège n°1) : le dépôt microbiome décroît en
×(1 − micro_norm), la boucle converge au lieu d'exploser.

### Étape 3 — Vitalité dérivée

`EcoFields.vitalite(r, c)` — grandeur **dérivée, jamais stockée** (respecte la
décision #2) : combinaison bornée [0,1] de microbiome, `om_active`, `fertilite`,
structure (`om_stable`) moins la perturbation. Intégrée aux logs de saison
(`engine.py`) et au bilan final de `main.py` (carte spatiale + moyenne).
Préfigure la **Vigueur (D11)**.

### Validation (lecture terminal, déterministe)

- **`main.py` 500 ans, exit 0, aucun crash.** Carbone conservé.
- Compartiments aux dynamiques distinctes : `fresh` volatil, `stable`/humus
  monte lentement puis plateau (~6-7).
- **Récit A** (sol nu pauvre micro 0.05) : succession + exsudats → micro 1.3,
  fertilité ↑, vitalité 0.40, 8 plantes.
- **Récit B** (polyculture dense) : sol plus riche que A (fertilité 2-2.8,
  vitalité 0.43-0.46), 11 plantes — la boucle rhizosphère bâtit le sol.
- **Récit C** (sol saccagé : micro/OM à zéro, perturbation 0.9) : régénération
  complète — micro 0→2.1, humus 0→10, fertilité 0→2.95, vitalité 0→0.68 ;
  recolonisation massive (45 pionnières en été). *Observation : la succession
  reste dominée par les pionnières annuelles sous forte perturbation — diversité
  à affiner ultérieurement, hors périmètre de ce sprint.*
- **Déterminisme** confirmé : deux runs identiques au flottant près.

### Ce qui a été produit

- `data/code/fields.py` — OM tri-compartiment, cascade, `vitalite()`, `share`
  + bonus microbiome dans `plant_uptake`, `summary` enrichi
- `data/code/engine.py` — `_apply_uptake` spatial, `_apply_exudates`, log saison
- `data/code/effects.py` — `inject_field` local réparti sur `root_plots`
- `data/code/models.py` — injections `organic_matter` → `om_fresh` ; microbiome
  par famille supprimé (Fabaceae/Medicago gardent N₂ → fertilité)
- `data/code/main.py` — carte de vitalité au bilan final
- `journal.md`, `CLAUDE.md`, mémoire ; commit dédié

### Nouvelle dette

- **D24** (portage C#) : uptake spatial sur `root_plots`, exsudats
  (`_apply_exudates`), bonus microbiome→uptake, et `vitalite()` ne sont **pas
  encore portés** côté C#. À absorber dans le **Sprint 3 (portage simulation)**.

---

## 2026-06-02 — Consolidation sol vivant : puits microbien (Python)

### Contexte

Mini-sprint de calibrage faisant suite au Sprint sol vivant. Deux points
d'attention relevés : (1) le microbiome n'avait **aucun puits** (montait et
plafonnait à 3.0), (2) la succession reste **pionnière** après saccage.

### Axe 1 — Puits microbien modulé par la famine (FAIT)

`tick_decomposition` : ajout d'une mortalité microbienne **modulée par la
disponibilité de carbone frais**. `famine = 1 − min(1, om_fresh/MICROBE_FOOD_REF)`
(0 si rassasié, 1 si épuisé) ; `microbiome *= 1 − MICROBE_DECAY_MAX*famine`.
Le microbiome devient un **solde** apports (exsudats/OM) − pertes : il monte
sous couvert végétal, redescend sur sol nu. Constantes : `MICROBE_FOOD_REF` 1.0,
`MICROBE_DECAY_MAX` **0.006** (0.015 d'abord testé, trop violent → effondrement
à 0.37 ; ramené à 0.006).

**Validé** : `main.py` 500 ans exit 0, déterminisme tenu. Gradient lisible —
sol couvert dense (récit C, 44 plantes) microbiome ~1.5 / vitalité 0.58 ;
sol clairsemé (A/B, 8-11 plantes) microbiome ~0.6 / vitalité ~0.40. Le
microbiome **suit la couverture du sol** sans s'effondrer. Carte de vitalité
`main.py` plus contrastée (plots nus ~0, couverts ~0.5).

### Axe 2 — Diversité de succession (DIAGNOSTIQUÉ, DIFFÉRÉ)

Diagnostic confirmé sur un saccage à perturbation **réaliste** (non pinnée) :
le sol reste **100 % Bourse-à-pasteur (0 pérenne) sur 150 ans** même quand il
redevient riche. Cause double : (1) `_succession`/`_spring_flush` ne favorisent
les pérennes que sur sol **pauvre** (jamais sur sol mûr) ; (2) après une phase
pionnière, la **banque de graines ne contient que `pioneer`** — les pérennes
n'ont aucune source d'amorçage. C'est de la vraie succession écologique
(pionnier → prairie → climax), cœur du « jardin qui mûrit ». **Décision Nico :
différer en mini-sprint dédié** (dette **D25**) plutôt qu'un patch.

### Ce qui a été produit

- `data/code/fields.py` — puits microbien (`MICROBE_FOOD_REF`,
  `MICROBE_DECAY_MAX`, mortalité ∝ famine dans `tick_decomposition`)
- `journal.md`, `CLAUDE.md` (backlog : mini-sprint succession), mémoire ; commit

---

## 2026-06-02 — Mini-sprint succession : gradient pionnier → prairie ∝ maturité du sol

### Contexte

Traite la dette **D25** diagnostiquée le matin même (Consolidation sol vivant,
axe 2). Sprint **Python pur** sur le moteur de vérité. Objectif : faire **mûrir**
la végétation spontanée — un sol redevenu riche restait bloqué 100 % en
pionnières annuelles ; on veut une succession qui progresse vers un couvert de
**prairie vivace** à mesure que le sol mûrit.

### Décisions actées (avec Nico, Partie 3 du kickoff)

1. **Proxy de maturité = `soil_memory_deep`**. Argument décisif : ce champ
   *est déjà* la combinaison composite `micro*0.4 + fert*0.2 + om*0.2 + sig*0.2`
   (cf. `tick_soil_memory`), mais passée dans un **filtre passe-bas décennal**
   (lerp 0.02). Le prendre brut aurait fait osciller la succession ; filtré, il
   donne la bascule lente recherchée. Pas de champ ad hoc.
2. **Gradient 3 paliers** : pioneer → nitrogen_fixer → grass → competitor, par
   rang ∝ maturité (continu, pas de seuil dur).
3. **Trickle de propagules vivaces** ∝ maturité : OUI, faible (dispersion
   lente, diégétique).
4. **Ampleur** : pionnier → prairie seulement. Le climax ligneux relève des
   pérennes (D21, Sprint éclairement).

### Étape 1 — choix d'archétype ∝ maturité (`engine.py`)

Nouvelle fonction module `choisir_archetype(candidates, soil_deep, fertilite)`,
**factorisée** entre `_succession` et `_spring_flush` (supprime la duplication
de la logique `chosen`). Rang de succession = index dans `SEED_ARCHETYPES` ;
`rang_cible = soil_deep * 3` ; on choisit le candidat dont le rang est le plus
proche (tie-break : le plus avancé). **Filet conservé** : `fertilite < 0.3` +
fixatrice candidate → on force la fixatrice (azote limitant). Orphelin `micro`
retiré de `_succession`.

### Étape 2 — amorçage de la banque en propagules vivaces (`fields.py`)

`SeedBank.tick_late_succession_enrichment(soil_deep_field)`, symétrique de
`tick_disturbance_enrichment` (qui n'amorce que `pioneer`). Trickle ∝ maturité :
`SEED_LATE_GAIN` 0.0008, seuil `SEED_LATE_MIN_MATURITY` 0.2 (rien sur sol jeune),
`competitor` gaté à `SEED_COMPETITOR_MATURITY` 0.4 (le plus tardif). Branché dans
`EcoFields.tick_seed_bank`. **C'est l'étape qui débloque tout** : sans graines
vivaces dans la banque, le choix corrigé n'a rien à choisir.

### Étape 3 — reflux + observabilité

Le **frein explicite n'a pas été nécessaire** : une fois les vivaces installées,
`niche_index` réduit la niche libre (root_density + soil_deep) → les pionnières
refluent d'elles-mêmes. `main.py` : ajout d'un **log de composition du couvert
installé par archétype**, échantillonné en **plein été (S26)** pour ne pas
sous-compter les annuelles (mortes à l'hiver).

### Résultats (déterministes, `main.py` 500 ans, exit 0)

- **Flux de germination** : vivaces 0,1 % → **~37 %** en plateau, montée monotone.
- **Couvert installé** (le test clé) : an 10 **17 %** vivace (flush pionnier,
  24 pionnières) → an 30 **84 %** → plateau **~75-90 %** stable jusqu'à l'an 500,
  sans oscillation ni blocage. La fixatrice (Minette) domine le couvert mûr.
- Le couvert (~80 %) est bien plus vivace que le flux (~37 %) : une vivace
  pérenne persiste des années, une pionnière annuelle doit re-germiner — le flux
  sous-estime le couvert. C'est cohérent.

### Aussi

- `main.py` : `N_YEARS` rendu **ajustable via argument CLI** (`python3 main.py 60`),
  défaut 500 — lancer des simus courtes pour gagner du temps. Dernière année
  toujours échantillonnée.
- **Dette de portage** : cette logique de succession n'est pas portée en C# →
  s'ajoute à **D24 / Sprint 3**.
- **Futur sprint diversification écologique** (question de Nico) : le moteur
  accepte facilement de nouvelles espèces (classe + 1 ligne `PLANT_CATALOGUE` ;
  `SOIL_SIGNATURE` indexée par famille). Mais à séquencer **après** le Sprint
  éclairement (D21 apporte les strates/ligneux = nouveaux archétypes) et **après**
  une décision *class-based vs data-driven*, en coordination avec la génétique
  (D22). Noté au backlog (**D26**).

### Ce qui a été produit

- `data/code/engine.py` — `choisir_archetype` + branchement `_succession`/`_spring_flush`
- `data/code/fields.py` — `tick_late_succession_enrichment` + constantes + branchement
- `data/code/main.py` — log composition couvert (S26) + `N_YEARS` ajustable CLI
- `journal.md`, `CLAUDE.md` (backlog), mémoire ; commit

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
| D10 | Divergence Python ↔ C# : OM tri-compartiment. **OM v4 porté en Python le 2026-06-02 (Sprint sol vivant)** — `om_fresh/active/stable` + cascade. Reste `PathogenPressure` (C# seul) à réconcilier. | 🟢 → ✅ (OM) / 🟡 (pathogène) |
| D11 | Moteur Python à étendre : **Vigueur universelle** (joueur + plantes + auxiliaires + nuisibles), couche transversale à concevoir | 🟡 |
| D12 | Moteur Python à étendre : **paliers de maîtrise** (méta-état du joueur, conditions de passage par famille et concept) | 🟡 |
| D13 | Système **Magazine de botanique** à concevoir (coût Vigueur + maîtrise, déblocage espèces) | 🟡 |
| D14 | Système **Carnet auto** à concevoir (enregistrement événements, indexation, bascule descriptif → interprétatif) | 🟡 |
| D15 | Mécanique d'**extension du terrain par maîtrise** (tuile thématique apparaît au palier maîtrise d'une famille) | 🟢 |
| D16 | Décaler le tirage météo en `forecast` 1-2 semaines en avance dans `engine.py`, pour alimenter les signes diégétiques (Z2) | 🟡 |
| D17 | Séparer `SeedBank-joueur` (lots par espèce, transportable, suit l'avatar) de `SeedBank-sol` (génétique vectorielle par espèce, intrinsèque au terrain), Python puis C# (Z3). **Couplé à D22** dans le Sprint génétique/reproduction | 🟡 |
| D18 | Système de **pages secrètes** à concevoir — sources, lieu de consultation, volume cible v1.0, génération de contenu (Z4) | 🟢 |
| D19 | Action gameplay **« manger »** à concevoir (organes consommables → Vigueur joueur) (Z5) | 🟡 |
| D20 | **Éclairement spatial pixel-exact (Option A)** : canopée + lumière au pixel-sol top-down (2 cm/px), chimie du sol au plot (50 cm). Soleil astronomique ~49°N, 4 tranches + intégrale, ombres-capsules, `foliage_density` par espèce, plancher diffus 15 %. Position des plantes continue. **Sprint éclairement** (Z7) | 🟡 |
| D21 | **Système temporel des pérennes ligneuses** : base commune polymorphe avec les annuelles, `age_years`, courbe d'âge interpolée, `foliage_density` saisonnière (caduc), arbres requalifiés (figuier/pommier jardin, noyer/chêne lisière). **Sprint éclairement** (Z7) | 🟡 |
| D22 | **Héritage génétique de la graine** : vecteur de gènes extensible, héritage biparental (pollinisation par espèce, modulée par auxiliaires), hybridation par introgression sur espèce fixe. **Sprint génétique/reproduction**, couplé à D17 (Z7) | 🟡 |
| D23 | **Catalogue arbres pérennes étendu** : poirier, prunier, châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier, érable… — différé post-validation squelette (Z7) | 🟢 |
| D24 | **Portage C# de la logique sol vivant** : uptake spatial sur `root_plots`, exsudats (`_apply_exudates`), bonus microbiome→uptake, `vitalite()` dérivée — codés en Python le 2026-06-02, pas encore en C#. **+ gradient de succession** (`choisir_archetype`, `tick_late_succession_enrichment`, 2026-06-02). À absorber dans le **Sprint 3 (portage)** | 🟡 |
| D25 | **Succession écologique pionnier → prairie** : choix d'archétype ∝ maturité (`soil_memory_deep`) + amorçage de la banque en propagules vivaces. **Traité le 2026-06-02 (mini-sprint succession)** — couvert installé bascule pionnier → prairie vivace (~80 %) sur ~30 ans, stable 500 ans. Portage C# reporté (→ D24) | 🟢 ✅ |
| D26 | **Sprint diversification écologique** : catalogue de test très incomplet (5 familles, 4 archétypes). Étendre les espèces. À séquencer **après** Sprint éclairement (D21 = strates/ligneux, nouveaux archétypes) et une décision *class-based vs data-driven*, en coordination avec la génétique (D22). Étendre `SOIL_SIGNATURE` pour les nouvelles familles | 🟢 |

---

## Backlog

> Chaque sprint à venir possède un **kickoff autosuffisant** dans le
> dossier `sprints/`. À l'ouverture d'une nouvelle session, donner à
> Claude l'instruction « lis `sprints/sprint_X.md` » suffit à reprendre
> sans le contexte de cette session.

| Sprint | Fichier kickoff |
|---|---|
| Sprint 1 (recalibrage visuel) | `sprints/sprint_1_recalibrage_visuel.md` |
| Sprint 2 (orchestration C#) | `sprints/sprint_2_orchestration.md` |
| Sprint éclairement (Z7, D20-D21 : ombres pixel + pérennes + réalignement OM) | `sprints/sprint_eclairement.md` |
| Sprint génétique/reproduction (Z7, D17+D22 : banques + héritage biparental) | `sprints/sprint_genetique.md` |
| Sprint 3 (portage simulation — peut absorber le sprint éclairement) | `sprints/sprint_3_portage_simulation.md` |
| Sprint 4 (mécaniques conception) | `sprints/sprint_4_mecaniques_conception.md` |

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

### Sprint conception bis — zones blanches restantes — TERMINÉ ✅
- [x] Cycle de sauvegarde (run éternel) — JSON, auto-save par saison, seed persistée
- [x] Mécanique de gestion des aléas météo — signes diégétiques + prépa/réaction
- [x] Multiples jardins / multijoueur — avatar transportable, terrain intrinsèque
- [x] Lore / narration — jardinier silencieux + 3 voix (encyclopédie / carnet / pages secrètes)
- [x] Conditions de panne sèche — succession spontanée + manger + régen croissante
- [x] Difficulty / accessibilité — Options modulaires + debug libre + pictogrammes

### Zone Z7 — éclairement spatial — CONCEPTION CLOSE ✅
- [x] Décisions actées (pixel exact, 4 tranches + intégrale, hauteurs cm,
      genetic_factor × growth_factor)
- [x] Audit botanique des 14 espèces actuelles
- [x] 5 arbres pérennes premiers calibrés
- [x] Kickoff sprint éclairement rédigé (`sprints/sprint_eclairement.md`)
- [x] **Recadrage conception (2026-05-29)** : Option A (lumière+plantes au
      pixel, sol au plot), échelle 50 cm / 2 cm/px, soleil astronomique,
      empreintes par stade, pérennes polymorphes, génétique biparentale par
      introgression. Voir entrée *Sprint conception éclairement & reproduction*.
- [x] **Implémentation scindée en deux sprints** : éclairement (D20-D21)
      puis génétique/reproduction (D17+D22)
- [ ] Implémentation : reportée aux deux sprints dédiés

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
- [ ] Porter la logique sol vivant (D24) : uptake spatial, exsudats,
      bonus microbiome→uptake, `vitalite()` dérivée
- [ ] Réconcilier le reste de D10 (`PathogenPressure` C# → Python)

> Extension future (palier de maîtrise avancé) : **chantier C — réseau
> mycorhizien** (`etude_sol_vivant.md` Partie 3), différé hors Sprint 3.

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
