<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

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
