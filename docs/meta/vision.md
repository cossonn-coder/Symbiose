# Vision du jeu — Symbiose

Document de contexte (knowledge file). Décrit **ce qu'est le jeu** et **pourquoi** chaque mécanique existe. Référence pour les sessions Claude. La vision a été figée lors d'une série de sprints conception fin mai 2026.

---

## Identité

**Symbiose est un sandbox écologique évolutif en permaculture** — jardin éternel à un seul run. Pas un roguelike. Le mot et son vocabulaire dérivé (« shop inter-run », « extinction = fin de run », « héritage entre runs ») sont obsolètes depuis le 2026-05-29.

Le jardin est **unique, persistant, et grandit avec le joueur**. Le sol porte la mémoire de tout ce qui a été fait, et l'apprentissage du joueur s'inscrit dans ses paliers de maîtrise.

Deux versions développées en parallèle :
- **Version vidéo** (Godot 4 / C#) — actuellement priorité 1
- **Version physique** (tuiles 3D imprimées + cartes MTG) — backlog v2.0+

Public : amis et famille de Nico (ingénieur électronique à Grenoble). Pas un jeu commercial. Pas un jeu de score.

---

## Mécaniques centrales

### Vigueur unifiée (Qi + Mana)

Inspiration croisée Qi chinois (énergie circulante) et Mana polynésien (énergie propre). Chaque être vivant possède sa **Vigueur** (≡ Mana, énergie propre). Les **champs écologiques existants** (`microbiome`, `soil_memory`, `om_*`, `fertilite`) modélisent le **Qi territorial** — pas de nouveau champ pour ça.

La Vigueur se puise dans le territoire et y retourne à la mort.

**Modèle Vigueur joueur** (base, à ajuster post-test) :
- Montant initial 100, +10/semaine simulée, full au passage de saison.
- Sources extra : récolte plantes mûres, méditation au foyer, **manger** une feuille/fleur/fruit (Vigueur ∝ maturité de l'organe).
- **Vigueur max augmente avec les paliers de maîtrise.**
- **La vitesse de régen passive augmente aussi avec la maîtrise** — plus on comprend l'écologie, plus vite on se ressource au jardin.

### Paliers de maîtrise

**5 paliers** par famille botanique **et** par concept écologique transversal (succession, polyculture, eau, compost, sol, lumière, météo/climat…) :

**découverte → investissement → maîtrise → expertise → transcendant**

Granularité voulue : par famille botanique + par concept, **pas par espèce individuelle** (évite l'UI catastrophique de 5 paliers × 100 espèces).

Effets du palier :
- Déblocage entrées de magazine
- Apparition tuile thématique (extension de terrain)
- Bascule du carnet en interprétatif sur le concept concerné
- Augmentation Vigueur max joueur
- Vitesse de régen Vigueur ↑

**Transcendant = non-action existentielle** : l'écosystème devient auto-suffisant, le joueur n'a plus besoin d'agir. Les perturbations (météo, nouvelles espèces, usure structures) entretiennent l'engagement à très long terme.

### Apprentissage par méthode scientifique

Observer → formuler hypothèse → tester → conclure. Trial & error, prise de risque, diversification d'idées sont récompensés. **Aucune action n'est punitive en soi** — c'est l'écosystème qui répond.

### Trois voix narratives diégétiques

Pas de narrateur externe omniscient, pas de PNJ, pas de quête imposée. Histoire émergente via les événements rares (bouture, oiseau, vent).

- **Encyclopédie** — wiki ingame qui se complète aux découvertes. Voir une espèce = entrée basique ; cycle complet = description bio ; cycles répétés avec succès = effets écosystémiques. Voix « naturaliste qui observe », tutoiement écologique.
- **Carnet auto** — enregistrement automatique des événements, consultable, indexé. **Descriptif au début** (faits bruts, le joueur infère), **interprétatif au seuil de maîtrise** du concept concerné (le carnet propose des causes). Voix interne à la première personne. Préserve la méthode scientifique pendant l'apprentissage, révèle les causes une fois la compréhension intériorisée.
- **Pages secrètes** — connaissances perdues, éparses, ésotériques. Trouvées par hasard, gagnées après une belle réalisation, découvertes en fouillant. Voix multiples : extraits poétiques, savoirs paysans, herbiers anciens, citations type Fukuoka / Sackville-West / sorcières médicinales. Consultation pressentie : **coffret au grenier de la maison normande**.

### Acquisition d'espèces — 4 canaux

1. **Succession spontanée** — le sol décide selon `niche_index` (déjà dans le moteur Python)
2. **Événements rares** — bouture voisin, graine d'oiseau, coup de vent
3. **Exploration de friche périphérique** — abstraite au début, monde évolutif en backlog lointain
4. **Magazine de botanique** — déblocage par Vigueur joueur + niveau de maîtrise. Remplace le shop sans rompre la philo : tu achètes du savoir avec ton énergie vitale, et tu ne peux acheter que ce que tu es prêt à comprendre.

### Auxiliaires

**Visibles dès le début, non identifiables sans maîtrise.** Modèle technique : champ ambiant `GridField` pour la dynamique + sprites apparents pour la perception. Tu vois l'insecte avant de connaître son nom — posture du naturaliste débutant.

### Maison normande — hub vivant (5 fonctions)

À **Montmartin-sur-Mer** (Normandie, calcaire gris, toit ardoise, volets bois, vent de la Manche). Tuile centrale de la grille 3×3.

- **Atelier** — créer/réparer structures persistantes
- **Semis intérieur** — germination hors saison
- **Magazine de botanique** — déblocage espèces
- **Carnet** — consultation centralisée
- **Foyer** — point de récupération de Vigueur (cheminée, ambiance contemplative)

### Démarrage du jardin — 3 écoles au choix

- **Friche pionnière** — terrain riche en pionnières (orties, chénopode, plantain), sol pauvre mais vivant
- **Sol modeste** — moyen sur tous les axes, polyvalent
- **Jardin abandonné** — résidus d'horticulture, vivaces dormantes, sol moyennement bon

Le joueur choisit son **ambiance de départ**, pas un mode de difficulté.

### Extension du terrain par maîtrise

**Démarrage à 9 tuiles** dont la maison centrale (donc 8 tuiles cultivables). Maîtriser une famille botanique fait apparaître une **tuile thématique** :
- Solanaceae → serre / coin chaud
- Fabaceae → légumière
- Asteraceae → prairie mellifère
- Lamiaceae → coin aromatique
- Poaceae → friche basse / prairie

**Pas d'achat, pas de conquête : la connaissance ouvre l'espace.**

### UX du volume cognitif

**432 plots × 15 min temps réel** = trois mitigations actives simultanément :

- **Pause libre** à volonté
- **Notifications hiérarchisées** (seuls les événements importants remontent)
- **Zoom contextuel** ×4 (vue globale) → ×32 (vue d'un plot)

### Boucle planification ↔ saison

- **Phase planification** (entre saisons, temps figé) : plantation, achat magazine, structures lourdes (mare, pergola, haie), consultation longue de l'encyclopédie. Coût Vigueur modéré.
- **Phase saison** (15 min temps réel, 1 sem = 60 s) : arrosage ciblé, tuteurer, écraser un nuisible visible, paillage local, récolte, consultation rapide du carnet. Coût Vigueur élevé pour l'action directe.

### Gestion des aléas météo

Préavis par **signes diégétiques** (oiseaux qui se regroupent, ciel qui se charge, anneau lunaire, brume, sol qui craquelle) — **pas d'icône calendrier**. L'interprétation explicite débloque au palier de maîtrise du concept « météo / climat ».

Action joueur en **deux temps** :
- **Préparation** (phase planification, temps figé) : paillage profond, voiles d'hivernage, brise-vent, structures persistantes. Coût Vigueur modéré.
- **Réaction** (phase saison, temps réel) : arrosage ciblé, sauver une plante précise, secouer une branche givrée. Coût Vigueur élevé (urgence).

La permaculture (préparation) reste mieux rétribuée que le sapeur-pompier (réaction).

**~20 %** d'événements météo restent **imprévisibles** tant que le joueur n'a pas atteint le palier transcendant en météo. **Au transcendant : tout devient prévisible** — récompense rare qui cristallise la philo non-action.

### Profils, avatars, déménagement

- **Profils multiples** sur la même installation. Un profil = un **avatar joueur** (nom, encyclopédie, paliers, banque de graines, Vigueur max courante) + un ou plusieurs **terrains**.
- **Déménagement** : un avatar peut migrer d'un terrain à un autre. Il **emporte** son savoir, ses paliers, ses graines, sa Vigueur max. Le **terrain reste lui-même** (sol, climat, friche, mémoire). **Le savoir voyage, le territoire non.**
- **Encyclopédie + paliers strictement par avatar** — pas de méta-savoir inter-avatars. Nouvel avatar = repart de zéro.
- **Pas de multijoueur synchrone** (incompatible avec pause libre et temps lent). Multijoueur asynchrone (visite d'un jardin d'ami en lecture) + co-saison hot-seat 2 joueurs = backlog v2.0+.

### Cycle de sauvegarde

- **Auto-save uniquement au passage de saison.** Pas d'auto-save intra-saison. Perdre une saison en cas de crash est accepté — la saison est un bloc dramatique qui pèse.
- **JSON lisible**, pas binaire — debug + curiosité future du joueur (« je veux grep mon propre journal dans 5 ans »).
- **Un seul save par profil.** Pas de save-scumming, pas de slots de backup.
- **Pas de migration de save < v1.0** — champ `engine_version` dans le save, casse explicite sinon.
- **Seed d'origine du terrain persistée** dans le profil : permet de re-générer le même point de départ (debug, partage école avec un ami).

### Conditions de panne sèche

**Pas de game over.** La succession spontanée (`SeedBank-sol`) ramène des pionnières (orties, chénopode, plantain) en quelques saisons même sur un jardin saccagé. C'est le fonctionnement normal d'un sol vivant.

**Pas de bouton « recommencer »** — run éternel = éternel. Pour un autre jardin : déménager ou créer un autre profil. Une même seed d'origine peut être re-générée sans bouton dédié.

L'action « manger » + la régen Vigueur croissante avec la maîtrise garantissent que le joueur peut toujours se ressourcer dans son jardin.

### Difficulty / accessibilité

- **Pas de mode difficulté classique** (le jeu n'est pas un jeu de score).
- **Réglages d'aide modulaires** (menu Options) :
  - Vitesse simulation : 30 à 180 s/semaine, défaut **60 s**
  - Verbosité notifications : silencieux / **important** / tout
  - Encyclopédie de démarrage : vierge / **amorcée** / fournie
  - Carnet interprétatif anticipé : OUI / **NON** (préserve la méthode)
- **Mode debug champs écologiques** (overlay heatmaps humidité, fertilité, microbiome, disturbance) = toggle libre Options dès le début, étiqueté « affichage technique — déconseillé en première découverte ». **Accessibilité brute > récompense punitive.**
- **Page d'accueil minimale** au premier lancement : 4-5 pictogrammes silencieux des gestes de base (cliquer, planter, observer, méditer, manger). Pas de texte, pas de tutoriel imposé. Le jeu se découvre par l'action.

---

## Z7 — Éclairement spatial pixel-exact + pérennes + génétique

Zone blanche résolue le 2026-05-29 après le Sprint conception bis. Découpée en **deux sprints d'implémentation** : éclairement (D20-D21) puis génétique/reproduction (D17+D22).

### Architecture lumière = Option A (maillage adaptatif)

- **Canopée + lumière au pixel-sol** (top-down cartésien, **2 cm/px**) — structure fine = gameplay des ombres.
- **Chimie du sol au plot** (50 cm) — phénomène diffus, le pixel n'apporte rien.
- **Position des plantes continue** (pixel-sol `x_cm, y_cm`), plot-foyer = `floor(pos / 50 cm)`.
- Espace de simulation lumière = **top-down cartésien**, jamais l'espace iso d'affichage.

### Modèle d'ombre

- **Soleil astronomique** : azimut/élévation calculés par latitude ~49°N (Montmartin-sur-Mer), déterministe. **4 tranches** (matin/midi/soir/nuit) + intégrale journalière. L'intégrale pilote la photosynthèse.
- `longueur_ombre = hauteur / tan(élévation)`, direction opposée à l'azimut. Ombre = **capsule** (disque de canopée glissé sur la longueur d'ombre), rasterisée en pixels-sol.
- **Opacité d'ombre variable par espèce** → champ `foliage_density` (noyer dense ~0.8, bouleau léger ~0.4). Mécanique permaculture : choisir un arbre à ombre légère pour un sous-étage.
- Cumul **multiplicatif** des ombres + **plancher de lumière diffuse ~15 %** (rien ne descend à 0 → sous-bois viable).

### Pérennes ligneuses (D21)

- **Base commune polymorphe** avec les annuelles : `current_height`, `canopy_radius`, `foliage_density`, `root_radius`. Le LightField/photosynthèse les traitent uniformément. Seule la **logique de croissance** diffère (stades discrets vs courbe d'âge).
- `age_years` (+1/52 par tick) ; courbe âge → (hauteur, rayon) = **interpolation spline monotone** entre points tabulés.
- `foliage_density` **saisonnière** — caduc nu l'hiver (levier permaculture majeur : soleil d'hiver sous fruitier caduc, ombre d'été).
- **Arbres requalifiés** : figuier/pommier = jardin, cerisier intermédiaire, **noyer/chêne = sujets de lisière** (un chêne mûr fait la taille du jardin entier).

### Génétique & reproduction (D17 + D22)

- **Deux banques distinctes** : **SeedBank-sol** (génétique vectorielle par espèce, liée au terrain, brassage féral) + **SeedBank-joueur** (lots par espèce, transportable, suit l'avatar lors du déménagement).
- `genetic_factor` devient un **vecteur de gènes extensible** (`{hauteur, vigueur, résistance, sécheresse…}`), seul `hauteur` rempli pour l'instant.
- **Héritage biparental** : père compatible à portée de pollinisation ; `gène_enfant = moyenne(parents) + mutation gaussienne` ; sinon autofécondation. **Pollinisation par espèce** (anémogame/entomogame), rayon modulé par les **pollinisateurs auxiliaires** (favoriser les auxiliaires → meilleures graines).
- **Hybridation inter-espèces** par **introgression sur espèce fixe** — l'enfant garde l'espèce de la mère, les gènes du père décalent ses facteurs vectoriels (parfois hors [0.7, 1.3] = vigueur hybride). **Pas** de génération de nouvelles `PlantData`.

### Hauteurs structures actées

- Mare : 0 cm
- Brise-vent (haie taillée) : 150 cm
- Pergola : 250 cm
- Maison normande : 700 cm

### 5 arbres pérennes premiers calibrés (D21)

| Arbre | 5 ans | 10 ans | 20 ans | 50 ans | Centenaire |
|---|---|---|---|---|---|
| Figuier | 200 | 400 | 500 | — | — |
| Pommier | 200 | 350 | 500 | 700 | — |
| Cerisier | 250 | 500 | 700 | 900 | 1000 |
| Noyer | 300 | 600 | 1000 | 1500 | 2500 |
| Chêne | 200 | 400 | 700 | 1500 | 3000 |

Catalogue arbres étendu (poirier, prunier, châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier, érable…) = dette **D23**, différée post-validation squelette.

### 14 espèces actuelles — hauteurs potentielles (cm)

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

**Hauteurs = potentiels**, modulés par `genetic_factor × growth_factor`. Deux haricots côte à côte n'ont jamais exactement la même taille — sélection artificielle possible émergente.
