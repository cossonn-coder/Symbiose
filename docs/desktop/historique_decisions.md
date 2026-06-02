# Historique & décisions — Symbiose

Document de contexte (knowledge file). **Trace condensée** de la chronologie du projet et des décisions structurantes. À lire pour comprendre **pourquoi** le code est dans son état actuel. Le fichier source plus détaillé est `journal.md` à la racine du repo.

---

## Chronologie résumée

### 2026-05-29 — Reprise du projet

Projet repris après plusieurs semaines de pause. Travail en SSH depuis téléphone sur VM Debian. Trois sessions enchaînées en un jour :

- **Sprint 0** — gel infrastructure : `CLAUDE.md`, `journal.md`, mémoire, init git. Incident Nextcloud pendant la session (sous-dossiers temporairement disparus, revenus à la fin de la synchro) → **règle durable : toujours travailler avec un dépôt git sain.**
- **Sprint conception** — 12 décisions structurantes redéfinissant le jeu. **Bascule majeure** : Symbiose n'est plus un « roguelike écologique » mais un **sandbox écologique évolutif à run éternel**. Tout le vocabulaire roguelike (shop, runs, héritage entre runs) est obsolète.
- **Sprint conception bis** — 6 zones blanches refermées (sauvegarde, météo, profils, lore, panne sèche, accessibilité). Format challenge constructif identique au Sprint conception.

Puis :

- **Zone Z7** — éclairement spatial pixel-exact identifié comme 7e zone blanche majeure. Décisions actées (granularité pixel, 4 tranches + intégrale, hauteurs cm, `genetic_factor × growth_factor`, 5 arbres pérennes calibrés).
- **Sprint conception éclairement & reproduction** — recadrage Z7 après lecture du code. **Option A** (lumière+plantes au pixel, sol au plot), échelle 50 cm / 2 cm/px, soleil astronomique, pérennes polymorphes, **génétique biparentale par introgression**. Implémentation scindée en deux sprints (éclairement puis génétique).

### 2026-06-02 — Sprint sol vivant

- **Sprint sol vivant** (Python pur) — passage du sol de **décor réactif** à **organisme**. OM v4 (cascade fresh/active/stable), racines spatiales sur `root_plots`, boucle rhizosphère (exsudats ↔ microbiome), vitalité dérivée. **D10 levée côté Python.** Mycorhizes (chantier C) différées en extension future.
- **Consolidation sol vivant** — puits microbien modulé par la famine. Le microbiome devient un solde apports/pertes.
- **Kickoff mini-sprint succession** (D25) — diagnostic posé : un sol saccagé reste 100 % Bourse-à-pasteur sur 150 ans même quand le sol redevient riche. La succession ne favorise les pérennes que sur sol pauvre, et la banque de graines ne contient que `pioneer` après une phase pionnière.

---

## Décisions structurantes les plus pesantes

À retenir absolument — ce sont celles qui contraignent les choix de code en aval.

### Vision

- **Sandbox éternel, pas roguelike** (2026-05-29). Jardin unique persistant, pas de game over, pas de bouton « recommencer ». Pour un autre jardin : déménager ou créer un autre profil.
- **Vigueur unifiée Qi+Mana** — pas de nouveau champ pour le Qi, les champs écologiques existants sont le « Qi territorial ». Chaque être vivant a sa Vigueur (≡ Mana).
- **5 paliers par famille et par concept** (pas par espèce) — découverte → investissement → maîtrise → expertise → transcendant. Transcendant = non-action existentielle.
- **Méthode scientifique** comme levier d'apprentissage. Aucune action n'est punitive en soi — c'est l'écosystème qui répond.
- **Action directe possible mais coûteuse** (assouplissement de la règle historique « le joueur n'agit que sur le milieu »). Écraser un nuisible coûte Vigueur et augmente `disturbance` localement.
- **Trois voix narratives diégétiques** (encyclopédie / carnet auto / pages secrètes). Pas de narrateur externe, pas de PNJ, pas de quête imposée.
- **Magazine de botanique** remplace le shop. Achat par Vigueur joueur + maîtrise. « Tu achètes du savoir avec ton énergie vitale, et tu ne peux acheter que ce que tu es prêt à comprendre. »
- **Auxiliaires visibles dès le début, non identifiables sans maîtrise** — posture du naturaliste débutant.
- **Démarrage 3 écoles** (friche pionnière / sol modeste / jardin abandonné). C'est une ambiance, pas une difficulté.
- **Extension de terrain par maîtrise** — pas d'achat, pas de conquête. La connaissance ouvre l'espace.

### Persistance

- **Auto-save uniquement au passage de saison.** Pas intra-saison. Perdre une saison en cas de crash = accepté.
- **JSON lisible**, un seul save par profil, pas de save-scumming.
- **Pas de migration de save < v1.0** — `engine_version` dans le save, casse explicite sinon.
- **Profils multiples**, un avatar = nom + encyclopédie + paliers + banque de graines + Vigueur max. Le terrain est séparé de l'avatar.
- **Déménagement** : le savoir voyage (avatar), le territoire non.
- **Pas de multijoueur synchrone** (incompatible pause libre + temps lent). Asynchrone + co-saison hot-seat = backlog v2.0+.

### Météo

- **Préavis par signes diégétiques** (oiseaux, ciel, anneau lunaire, brume, sol craquelé). Pas d'icône calendrier.
- **Action en deux temps** : préparation (planification, Vigueur modérée) + réaction (saison, Vigueur élevée).
- **~20 % imprévisible** jusqu'au palier transcendant en météo. **Au transcendant : tout devient prévisible** — récompense rare qui cristallise la philo non-action.

### Difficulty

- **Pas de mode difficulté classique.** Réglages d'aide modulaires (vitesse simulation, verbosité notif, encyclopédie de démarrage, carnet interprétatif anticipé).
- **Mode debug champs écologiques en toggle libre dès le début** — accessibilité > récompense punitive.
- **Page d'accueil minimale** : 4-5 pictogrammes silencieux. Pas de tutoriel.

### Architecture éclairement (Option A)

- **Canopée + lumière au pixel**, **chimie du sol au plot**. Maillage adapté au phénomène.
- **Position des plantes continue** (pixel-sol), plot-foyer = `floor(pos / 50 cm)`.
- **Espace de simulation lumière = top-down cartésien**, jamais l'espace iso d'affichage.
- **Soleil astronomique** par latitude ~49°N, 4 tranches + intégrale, déterministe.
- **Ombre = capsule** rasterisée, `foliage_density` par espèce, plancher diffus 15 %.

### Pérennes

- **Base commune polymorphe** avec les annuelles (même interface lumière). Seule la croissance diffère (stades discrets vs courbe d'âge).
- `age_years` (+1/52 par tick), courbe âge → (hauteur, rayon) par interpolation spline monotone.
- `foliage_density` saisonnière (caduc nu l'hiver).
- **Noyer/chêne = sujets de lisière** (un chêne mûr fait la taille du jardin entier — aucune échelle ne le rend « une plante parmi d'autres »).

### Génétique

- **Deux banques** : `SeedBank-sol` (intrinsèque terrain) + `SeedBank-joueur` (transportable).
- `genetic_factor` = vecteur de gènes extensible (`hauteur` rempli, le reste en attente).
- **Héritage biparental** par moyenne + mutation gaussienne. Pollinisation par espèce, rayon modulé par les pollinisateurs auxiliaires.
- **Hybridation inter-espèces par introgression sur espèce fixe** — l'enfant garde l'espèce de la mère, les gènes du père décalent ses facteurs. Pas de nouvelles `PlantData` générées.

---

## Dette technique consolidée (D1-D25)

| Code | Description | Priorité |
|---|---|---|
| D1 | Fichiers transitoirement perdus le 2026-05-29 (Nextcloud) | ✅ mitigé par init git |
| D2 | Mismatch dimensions tuiles : 78×57 réel vs 96×48 codé dans `TileGrid.cs` | 🔴 |
| D3 | Mismatch noms sprites : catalogue C# attend `basil_*`, fichiers nommés `basilic_*` | 🔴 |
| D4 | Sprite maison absent — pièce centrale du design 3×3 sans visuel | 🔴 |
| D5 | `effects.py` jamais porté en C# | 🟡 |
| D6 | `engine.py` jamais porté en C# (boucle 52 semaines, succession, aléas) | 🟡 |
| D7 | Stubs vides hors namespace `Symbiose` (`Main`, `EcologySystem`, etc.) | 🟡 |
| D8 | `Main.tscn` obsolète (Node vides en français), à supprimer/refaire | 🟡 |
| D9 | Conflit de nom `PlantInstance` (data vs Node Godot) | 🟡 |
| D10 | Divergence Python ↔ C# : OM tri-compartiment | ✅ (OM) / 🟡 (PathogenPressure) |
| D11 | Moteur Python à étendre : **Vigueur universelle** (joueur + plantes + auxiliaires + nuisibles) | 🟡 |
| D12 | Moteur Python à étendre : **paliers de maîtrise** (méta-état joueur, conditions de passage) | 🟡 |
| D13 | Système **Magazine de botanique** à concevoir (coût Vigueur + maîtrise, déblocage espèces) | 🟡 |
| D14 | Système **Carnet auto** à concevoir (enregistrement événements, indexation, bascule descriptif → interprétatif) | 🟡 |
| D15 | Mécanique d'**extension du terrain par maîtrise** (tuile thématique apparaît au palier) | 🟢 |
| D16 | Décaler le tirage météo en `forecast` 1-2 semaines en avance dans `engine.py` (signes diégétiques) | 🟡 |
| D17 | Séparer `SeedBank-joueur` de `SeedBank-sol`, Python puis C#. **Couplé à D22** dans le Sprint génétique | 🟡 |
| D18 | Système de **pages secrètes** à concevoir (sources, lieu, volume cible v1.0, contenu narratif) | 🟢 |
| D19 | Action gameplay **« manger »** à concevoir (organes consommables → Vigueur joueur) | 🟡 |
| D20 | **Éclairement spatial pixel-exact (Option A)** — Sprint éclairement | 🟡 |
| D21 | **Système temporel des pérennes ligneuses** (base commune polymorphe avec annuelles) — Sprint éclairement | 🟡 |
| D22 | **Héritage génétique de la graine** (vecteur extensible, biparental, introgression) — Sprint génétique | 🟡 |
| D23 | **Catalogue arbres pérennes étendu** (poirier, prunier, châtaignier, frêne, tilleul…) | 🟢 |
| D24 | **Portage C# de la logique sol vivant** (uptake spatial, exsudats, microbiome→uptake, vitalite()) — à absorber dans Sprint 3 | 🟡 |
| D25 | **Succession écologique pionnier → pérenne** (diagnostiqué le 2026-06-02) — mini-sprint dédié | 🟡 |

Légende : 🔴 critique · 🟡 important · 🟢 cosmétique ou différable · ✅ levée

---

## Anti-patterns confirmés

À ne pas refaire — leçons apprises.

- **Mocker la donnée à la place de la modéliser.** Le moteur Python est canon ; ne pas inventer un comportement C# sans équivalent Python. La D10 (divergence OM) a coûté un sprint dédié pour réaligner.
- **Coder avant d'avoir conçu.** Le Sprint conception éclairement a montré qu'un kickoff écrit la veille (D20 « pixel exact ») pouvait masquer des frictions majeures (confusion plot/tuile, lumière pixel ↔ photosynthèse par plot). Toujours lire le code avant d'acter une archi.
- **Sur-outiller tôt.** Sprint 0 a explicitement reporté la création de skills/agents Claude au Sprint 2. Garder l'outillage minimal tant que le besoin ne se manifeste pas concrètement.
- **Bypasser la pause Nextcloud.** Si on ne commit pas avant un changement gros, on s'expose à une perte transitoire (déjà arrivée le 2026-05-29). **Init git puis commit à chaque sprint.**
- **Demander une rafale de questions sur un sujet bio/éco** — Nico préfère lire un dossier d'étude tranquillement et trancher après. Voir l'étude `sprints/etude_sol_vivant.md` comme modèle.

---

## Pour ouvrir une nouvelle session

Workflow Nico ↔ Claude au 2026-06-02 :

1. Charger `CLAUDE.md` (automatique).
2. Charger les knowledge files `vision.md` / `architecture.md` / `historique_decisions.md` (ce fichier).
3. Selon l'objectif :
   - **Continuer un sprint** : « lis `sprints/sprint_X.md` ».
   - **Ouvrir un sujet nouveau** : décrire l'intention, attendre que Claude pose ≤3 questions de cadrage.
   - **Question rapide** : poser direct.
4. À la fin de toute session structurante : **mettre à jour `journal.md`** avec une entrée datée + commit dédié.
