# Dette D15 — Extension du terrain par maîtrise (tuile thématique)

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. **Conception SEULE d'abord** (`docs/joueur/maitrise/conception_terrain.md`,
> valider avec Nico, puis impl.). Ampleur **moyenne**.

## Ce que c'est, en une phrase
Concevoir l'**extension du terrain par la connaissance** : maîtriser une famille
botanique (ou un concept) **fait apparaître une tuile thématique** (verger, mare,
prairie aromatique…) — **pas d'achat, pas de conquête** : « la connaissance ouvre
l'espace » (CLAUDE.md, philo de la non-action et du run éternel).

## Le contexte (CLAUDE.md + conception + moteur)
- **CLAUDE.md, « Extension du terrain »** : « Par maîtrise écologique **uniquement**.
  Maîtriser une famille fait apparaître une tuile thématique (verger, mare, prairie
  aromatique…). Pas d'achat, pas de conquête. »
- **La maîtrise est prête** (`docs/joueur/maitrise/conception_maitrise.md` §7) : « D15 (extension terrain)
  — tuile thématique apparaît au palier **maîtrise** d'une famille (table de mapping,
  §8) ». Le palier-déclencheur exact = **D12.2** (séparé). D15 définit **ce qui
  apparaît et comment**, pas le seuil.
- **Le monde est une grille de tuiles** : CLAUDE.md « monde 3×3 tuiles × (6×8 plots)
  = 432 plots ». `world/tile.py` (`Tile`, `StakeSlot`, `RONDELLE_TYPES`) ;
  `fields/ecofields.py` dimensionne les `GridField` sur `(rows, cols)`. **Ajouter une
  tuile = agrandir la grille** → **toutes les structures de champ** (humidité,
  microbiome, lumière, populations…) doivent suivre. C'est le vrai enjeu technique.
- **Le terrain porte une seed et un sol propres** (CLAUDE.md, save) : « Seed d'origine
  du terrain persistée ». Une tuile neuve doit être **générée déterministe** depuis la
  seed (bruit spatial `fields/noise.py`), pas posée vide.

## Ce qui est déjà tranché (ne pas re-débattre)
- Extension = **par maîtrise uniquement**. Jamais d'achat ni de conquête.
- Une tuile thématique = **liée à une famille/concept** maîtrisé (verger ↔ Rosaceae
  ligneuses, mare ↔ concept eau/humidité, prairie aromatique ↔ Lamiaceae…).
- **Run éternel / déterminisme** : la nouvelle tuile est générée depuis la seed du
  terrain (hétérogénéité persistante, philo #7).

## 🔵 Choix de design à trancher
### Choix 1 — Géométrie de l'extension (le choix structurant)
- **(A) ⭐ Tuiles « périphériques » pré-câblées, révélées une à une.** Le monde a
  une grille **logique plus grande** que les 3×3 de départ (p.ex. 5×5), mais seules
  les tuiles **débloquées** sont actives/affichées et tickées. Maîtriser fait passer
  une tuile voisine de « friche abstraite » à « active ». **Pour** : la grille ne
  change jamais de dimensions → **champs, lumière, save, golden** restent à taille
  fixe (énorme simplification technique) ; colle au canal « exploration de friche
  périphérique » déjà évoqué (CLAUDE.md). **Contre** : terrain final borné (mais le
  run éternel se joue en *profondeur* écologique, pas en surface — cohérent).
- **(B) Grille qui grandit dynamiquement** : `rows/cols` augmentent à chaque
  déblocage. **Pour** : extension illimitée. **Contre** : **toutes** les structures de
  champ doivent se redimensionner/recopier, le golden devient mouvant, la save se
  complexifie. **Surdimensionné** et risqué.

> Reco : **(A)** — fixe la dimension, révèle des tuiles. C'est le choix qui protège le
> golden et la save, et il suffit largement au gameplay (108 m² → quelques tuiles de
> plus). **(B)** reste possible en backlog si un jour tu veux un terrain « infini ».

### Choix 2 — Qu'est-ce qu'une « tuile thématique » concrètement ?
Une tuile a un **sol** (champs) et un **contenu** (plantes/structures). Le thème agit
sur quoi ?
- **(A) ⭐ Biais de génération du sol + amorçage de banque de graines.** Le verger
  naît avec un sol plus mûr (`soil_memory_deep` élevé) et la `SeedBank-sol` amorcée en
  propagules de la famille thème — le reste **émerge** (philo #2 : on biaise le
  *milieu*, pas les plantes). **Pour** : zéro mécanique neuve, réutilise succession +
  seedbank + génération de sol existantes. **Contre** : le « thème » est subtil (c'est
  voulu : la non-action).
- **(B) Tuile pré-plantée** (verger = pommiers déjà là) : lisible mais viole « jamais
  de plantes posées en dur », casse l'émergence.

> Reco : **(A)** — biais de milieu, pas de plantes cadeau. La prairie aromatique = un
> sol + une banque qui *favorisent* les Lamiaceae, pas un parterre de basilic offert.

### Choix 3 — Réversibilité / déménagement
CLAUDE.md : « le savoir voyage, le territoire non ». Un avatar qui déménage emporte ses
paliers → **débloquerait-il les tuiles du nouveau terrain immédiatement ?**
- **(A) ⭐ Oui** : les tuiles se débloquent selon les **paliers de l'avatar**, donc un
  avatar expérimenté arrivant sur un terrain neuf a déjà accès aux tuiles
  correspondant à sa maîtrise (le terrain reste lui-même : sol/climat/friche). Cohérent
  avec « le savoir voyage ».
- **(B) Non** : les tuiles se re-méritent par terrain. Plus punitif, contredit la
  règle du déménagement.

> Reco : **(A)** — c'est la conséquence directe de « encyclopédie et paliers
> strictement par avatar, le terrain reste intrinsèque ».

## Périmètre — phase CONCEPTION (livrable)
`docs/joueur/maitrise/conception_terrain.md` actant : les 3 choix ; la **carte thème ↔ famille/
concept** (verger/mare/prairie… → quel objet de maîtrise) ; le **mécanisme de
révélation** (tuile périphérique : `actif=False` → `True`, génération déterministe du
sol depuis la seed, amorçage de banque) ; l'**interface** (`tuiles_disponibles(
game_state, player)` lisant les paliers ; `reveler_tuile(...)`) ; et **ce qui est
renvoyé à D12.2** (le *palier* exact qui révèle chaque tuile).

## Hors périmètre
Le **palier-seuil** exact (← D12.2). Le **rendu Godot** de l'apparition de tuile
(frontend). Les **sprites** de tuiles thématiques (assets). L'extension **dynamique**
de grille (Option B, backlog). Portage C# (D24).

## Golden / vérification
Conception = zéro code. À l'impl. **sous Option A** : la grille logique passe à sa
taille cible **dès le départ** avec les tuiles périphériques **inertes** (non tickées
tant qu'inactives) → soit le golden est **étendu une fois proprement** (re-figeage
maîtrisé, comme l'éclairement), soit les tuiles inactives sont strictement neutres et
le golden reste intact — **à valider en conception** (préférer la neutralité si
possible). Tests : une tuile se révèle au bon palier, son sol est généré déterministe,
elle ne s'active pas en deçà du seuil. MAJ `DETTE.md` D15 + `BACKLOG.md`.
