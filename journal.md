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
| D16 | Décaler le tirage météo en `forecast` 1-2 semaines en avance dans `engine.py`, pour alimenter les signes diégétiques (Z2) | 🟡 |
| D17 | Séparer `SeedBank-joueur` (transportable, suit l'avatar au déménagement) de `SeedBank-sol` (intrinsèque au terrain), Python puis C# (Z3) | 🟡 |
| D18 | Système de **pages secrètes** à concevoir — sources, lieu de consultation, volume cible v1.0, génération de contenu (Z4) | 🟢 |
| D19 | Action gameplay **« manger »** à concevoir (organes consommables → Vigueur joueur) (Z5) | 🟡 |
| D20 | **Éclairement spatial pixel-exact** : `LightField` v2 avec ombres portées par canopées et structures, 4 tranches + intégrale, recalcul hebdo (Z7) | 🟡 |
| D21 | **Système temporel des pérennes ligneuses** : âge en années, courbe pluri-décennale, distinct du `GrowthStage` (Z7) | 🟡 |
| D22 | **Héritage génétique de la graine** : `genetic_factor` ∈ [0.7, 1.3], hérité à la fécondation, généralisable (hauteur, vigueur, résistance) (Z7) | 🟡 |
| D23 | **Catalogue arbres pérennes étendu** : poirier, prunier, châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier, érable… — différé post-validation squelette (Z7) | 🟢 |

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
| Sprint éclairement (Z7, D20-D22) | `sprints/sprint_eclairement.md` |
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
- [ ] Implémentation : reportée au sprint dédié

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
