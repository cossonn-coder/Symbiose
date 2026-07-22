# Tranche 4 — Caméra (D35) + Actions joueur (le monde devient jouable)

> **Kickoff autosuffisant.** Lire d'abord `00_etat.md` (Option B actée ;
> tranches 1-3 CLOSES : pont `sim_server.py` ↔ `SimBridge.cs`, monde complet
> rendu dans `WorldView`, boucle hybride Planification↔Saison↔Pause animée
> avec step en Task de fond, confirmé F5). But de la tranche : **(A)** les
> contrôles caméra demandés par Nico post-t2 (D35 : déplacement, zoom par
> paliers, rotation par quarts de tour) puis **(B)** les premières **actions
> joueur** : clic → commande JSON → Python valide et applique (coût Vigueur)
> → snapshot frais rendu. Ampleur : **gros** → **2 volets séquentiels avec
> F5 intermédiaire** ; si une session n'y suffit pas, committer le volet A
> seul (il lève D35 et se suffit). Fichiers : volet A = `world/WorldView.cs`
> (+ `visuals/PlantRenderer.cs` si l'orientation l'exige) ; volet B =
> `tools/sim_server.py` + `tests/test_sim_server.py` + `WorldView.cs`.
> **AUCUNE modification du moteur** (`sim/`, `plants/`, `fields/`) : le
> serveur APPELLE des façades existantes — golden intact (`16a1b937…`).

## 📖 Pédagogie — les trois problèmes de la tranche

**1. Le picking = inverser la projection.** `WorldToScreen` est une
application LINÉAIRE (matrice 2×2) : `sx = (x−y)·0.78 ; sy = (x+y)·0.39`.
Déterminant non nul → inversible analytiquement :
`x = sx/(2·0.78) + sy/(2·0.39) ; y = −sx/(2·0.78) + sy/(2·0.39)`.
Côté Godot, `GetGlobalMousePosition()` rend la souris **déjà** en coordonnées
canvas (pan/zoom de la Camera2D défaits par le moteur) — il ne reste que
`ScreenToWorld`, l'inverse écrit UNE fois à côté de `WorldToScreen` (leçon
D2 : jamais deux projections « presque pareilles »). Avec la rotation (volet
A), inverser AUSSI la permutation d'orientation, dans l'ordre inverse.

**2. La rotation n'est PAS une rotation du canvas.** Décision t2 (D35) : une
vue iso pivotée de 90° = les MÊMES losanges 2:1 vus depuis un autre coin du
monde — pas un canvas tourné (qui donnerait des losanges penchés). Donc :
une **orientation ∈ {0,1,2,3}** appliquée DANS `WorldToScreen` comme
transformation monde→monde AVANT la projection iso (quart de tour autour du
centre du monde (1000,1000) cm : `(x,y) → (y, 2000−x)` et itérations).
Conséquence : à chaque rotation, tout ce qui a été positionné via
`WorldToScreen` doit être **reconstruit** — on a déjà tout pour ça
(`BuildGround`/`BuildHouse`/`ApplySnapshot`) : garder le dernier snapshot en
champ et `RebuildWorld()` (vider, reconstruire sans fondu). 1188 polygones +
~170 plantes = instantané, pas d'optimisation à inventer. Les façades
visibles de la maison changent selon l'orientation — la reconstruction de
`BuildHouse` doit choisir les 2 faces côté caméra (aujourd'hui codées en dur
est+sud).

**3. Qui décide quoi (protocole d'action).** Règle Option B : **Python
possède les RÈGLES** (validité, coût Vigueur, effet), **Godot transmet
l'INTENTION** (verbe + cible). Ni validation côté C# (divergence garantie),
ni « le serveur devine la cible » : la vue résout le clic en une désignation
NON-AMBIGUË et neutre (plot `(tile,r,c)` ou plante par position), le serveur
fait foi. Analogie embarqué : le maître SPI envoie une commande structurée,
l'esclave répond ACK/NAK + données — jamais le maître n'écrit directement
dans les registres internes de l'esclave.

## État de départ (acquis t1-t3)

- `WorldView.cs` : scène principale, projection unique `WorldToScreen`
  statique (0,78/0,39 px/cm), caméra de cadrage fixe zoom 0,5, machine à
  états Planification↔Saison↔Pause (Espace), `ApplySnapshot` en diff par clé
  `tile|species|x_cm|y_cm`, HUD label provisoire. `PlantRenderer.Iso`
  **délègue** à `WorldToScreen`.
- `sim_server.py` (protocole v0) : `init`/`step_week`/`snapshot`/`quit`.
  `game_state` du serveur = `{current_player: "joueur_1", week, log}` —
  **la Vigueur joueur n'y est PAS encore branchée**.
- Côté moteur, TOUT existe déjà (sprints Vigueur/maîtrise/D31.3, 2026-06-04) :
  - `sim/actions.py` — **8 gestes** : `manger` (coût NUL, gain ∝ maturité),
    `recolter`, `deraciner`, `tailler(cible="apex"|"branche")`, `ecraser(r,c,
    urgence=bool)` (× `URGENCE_MULT`=1,5 si urgence — **la couture
    préparation/réaction existe déjà**), `favoriser_auxiliaire(tile)`,
    `becher(r,c)`, `grelinette()` ; table `COUTS` + `cout_action` (maîtrise).
  - `sim/vigueur.py` — `ensure_player`, `tick_player_vigueur` (régen
    +10/sem), `refill_saison` (plein au passage de saison), `spend`/`gain`.
- **`planter` et `arroser` N'EXISTENT PAS côté moteur** → EXCLUS de cette
  tranche (règle projet : toute mécanique Godot doit avoir son équivalent
  Python AVANT intégration). À graver au backlog comme sprint Python dédié
  (geste planter = pont `PlayerSeedBank` → tuile ; arroser = geste sur le
  champ humidité).

## Volet A — Caméra (D35, pure vue, `WorldView.cs`)

1. **Déplacement** : flèches (maintien), vitesse constante en px ÉCRAN
   (ressenti identique à tout zoom), dans `_Process`. Borné au rectangle du
   monde + marge (~10 %) — on ne se perd pas dans le gris.
2. **Zoom par paliers à la MOLETTE** (décision Nico 2026-06-10 : molette,
   pas de touches) : molette haut = palier supérieur, bas = inférieur
   (`InputEventMouseButton`, `WheelUp`/`WheelDown`). Paliers
   `{0.5, 1, 2, 4, 8, 16, 32}` — les paliers < 4 sont **provisoires** (vue
   d'ensemble sur placeholders vectoriels, aucun artefact possible) ; la
   règle projet « ×4-×32, jamais de fraction » s'appliquera strictement
   quand les sprites pixel art remplaceront les `Polygon2D` (D34). Zoom
   **centré sur la souris** si simple, sinon centre écran (défaut sobre).
3. **Rotation par quarts de tour** : `PageDown` = horaire, `PageUp` =
   anti-horaire (touches univoques en AZERTY ; les vrais bindings = sprint
   UI). Champ `Orientation` (0..3) lu par `WorldToScreen` (cf. pédagogie 2),
   `RebuildWorld()` à chaque changement (sol + maison reconstruits, plantes
   re-créées du dernier snapshot SANS fondu). Vérifier `PlantRenderer` :
   si `Iso` projette des offsets monde via `WorldToScreen`, la rotation est
   gratuite (linéarité) ; sinon l'adapter — la plante doit « tourner » avec
   le monde (son phototropisme penche vers la maison quelle que soit la vue).
4. **Affichage des commandes possibles** (décision Nico 2026-06-10) : le HUD
   liste à l'écran ce que le joueur PEUT faire — une légende discrète (coin
   bas-gauche, même `CanvasLayer` que l'horloge, petite police) :
   « Espace lancer/pause · flèches déplacer · molette zoom ·
   PageUp/Down pivoter ». Au volet B, s'y ajoutent les gestes `1..8` avec
   leur nom (et le coût refusé/accepté reste au HUD du haut). Toujours
   PROVISOIRE (philo #5/#6 : pas de tutoriel imposé — la vraie v1 aura la
   page d'accueil pictogrammes ; ici c'est l'instrument de validation).
5. L'horloge/HUD t3 et la boucle saison **continuent de fonctionner pendant**
   pan/zoom/rotation (aucune interaction entre caméra et machine à états).

## Volet B — Actions joueur (protocole v1 : serveur + vue)

### Côté Python (`tools/sim_server.py` + tests — PAS le moteur)

6. **Brancher la Vigueur joueur** (façades existantes) : `ensure_player` à
   l'`init` ; `tick_player_vigueur` à chaque `step_week` ; `refill_saison`
   quand la saison du compteur change. Snapshot enrichi (lecture seule) :
   `"player": {"vigueur": x, "vigueur_max": y}`. `ENGINE_VERSION` → "0.2.0".
7. **Commande `action`** :
   `{"cmd":"action", "verb":"manger", "target":{...}, "params":{...}}` →
   réponse `{"ok":true, "result":{"applied":bool, "cost":…, "gain":…,
   "vigueur":…, "message":…}, "snapshot":{…}}` (snapshot frais TOUJOURS
   joint : l'effet est visible immédiatement, un seul aller-retour).
   Verbe inconnu / cible introuvable / Vigueur insuffisante → `applied:false`
   + message, le serveur SURVIT (même règle que les commandes malformées v0).
8. **Désignation des cibles** (décision proposée, cf. pédagogie 3) :
   - plot : `{"tile":"T3","r":2,"c":5}` (becher, ecraser) ;
   - tuile : `{"tile":"T3"}` (favoriser_auxiliaire) ; rien (grelinette) ;
   - **plante : par position** `{"tile":"T3","x_cm":…,"y_cm":…}` + match
     epsilon (0,1 cm) côté serveur — le snapshot n'expose pas d'id moteur et
     les plantes ne bougent jamais : la position EST l'identité (déjà la clé
     du diff t3). Pas d'id inventé avant d'en avoir besoin.
   - `params` : `{"cible":"apex"|"branche"}` (tailler), `{"urgence":bool}`
     (ecraser — la vue envoie `urgence=true` si phase Saison, `false` en
     Planification : la machine à états t3 alimente la couture déjà codée).
9. **`tests/test_sim_server.py` étendu** (golden joueur du protocole) :
   vigueur présente et régénérée, refill au passage de saison, manger
   (gain, plante par position), deraciner (plante disparaît du snapshot
   suivant), cible introuvable → `applied:false` + serveur survivant,
   déterminisme 2 runs avec mêmes actions. **Golden écolo intact**
   (`16a1b937…` — les actions ne sont jamais déclenchées par `test_golden`).

### Côté C# (`WorldView.cs` — UI minimale de validation)

10. **Sélection du verbe au clavier** : touches `1..8` (l'ordre de la table
    `COUTS` ; affichées dans la légende des commandes du volet A·4, avec le
    nom du geste). Aucun menu — les vrais outils/boutons = sprint UI.
11. **Clic gauche = exécuter** : `ScreenToWorld(souris)` → désignation selon
    le verbe (plante la plus proche dans un rayon de tolérance ~30 cm monde,
    ou plot/tuile contenant le point) → commande `action` (en Task, même
    pattern qu'un step : UNE requête en vol, pipe maître/esclave) →
    `ApplySnapshot` de la réponse (un déracinement s'efface en fondu t3).
12. **HUD enrichi** (toujours provisoire) : 2ᵉ ligne « Vigueur 85/100 —
    geste : manger [3] ». Refusé (`applied:false`) → message console +
    flash du label (pas de popup).
13. **Actions et phases** : autorisées dans les DEUX phases (préparation en
    Planification, réaction en Saison — philo météo §deux temps), seule
    l'`urgence` change. En Saison, l'action peut attendre qu'un step en vol
    se termine (file d'UNE intention max, sinon ignorer le clic — pas de
    queue à inventer).

## Critères de succès (vérifiables, F5 Nico)

Volet A :
- [ ] Flèches : la vue se déplace, bornée au monde ; **molette** : paliers
      de zoom nets ; le monde reste lisible à ×4.
- [ ] PageUp/PageDown : le monde pivote par quarts de tour (la maison montre
      d'autres façades, les plantes penchent dans le bon sens), l'horloge et
      la saison en cours n'en souffrent pas.
- [ ] La **légende des commandes** est lisible à l'écran (Espace / flèches /
      molette / PageUp-Down) sans consulter aucun doc.
- [ ] `python3 -m tests.test_golden` inchangé (rien de Python touché).

Volet B :
- [ ] HUD : Vigueur visible, régénère pendant la saison, pleine au passage
      de saison.
- [ ] `manger` sur une plante mûre : gain de Vigueur affiché ; `deraciner` :
      la plante s'efface en fondu, Vigueur débitée ; en Saison `ecraser`
      coûte plus cher qu'en Planification (URGENCE_MULT visible).
- [ ] Action refusée (Vigueur insuffisante, clic dans le vide) : message,
      pas de crash, le serveur répond toujours.
- [ ] `tests/test_sim_server.py` vert ; golden écolo intact (`16a1b937…`).

## Points ouverts (défaut sobre + signaler)

- **Paliers < ×4 provisoires** (cf. volet A·2) : à re-trancher à l'arrivée
  des sprites D34.
- **Curseur/surbrillance de la cible** (plot survolé, plante sélectionnée) :
  hors tranche — un simple print de la cible résolue suffit à valider ;
  le feedback visuel riche = sprint UI.
- **`observer`/`crediter_succes`** (maîtrise §4.3) : PAS branchés ici — le
  câblage maîtrise↔pont (détection de succès `maitrise_detection.py` côté
  serveur) mérite sa propre tranche, ne pas l'entamer en passant.
- **Sauvegarde des actions (replay)** : le flux JSON est enregistrable par
  construction — rien à faire maintenant, noter seulement que le format de
  commande v1 devient un contrat (versionné par `ENGINE_VERSION`).

## Dette / liens

- **Lève D35** (volet A). **D34** (sprites tuiles) inchangée — les
  placeholders tournent très bien.
- Grave au backlog : **gestes `planter` + `arroser`** = sprint Python dédié
  (moteur d'abord, pont ensuite).
- Prépare la **t5 (organes + overlays + vie macro)** : `ecraser` vise le
  champ `ravageur` (D31) — quand les sprites de vie macro arriveront, le
  picking de cette tranche les ciblera tel quel.

## Boucle de travail (rappel)

Volet A (`WorldView.cs`) → F5 Nico (critères A) → volet B (serveur + tests
PUIS vue) → golden + `test_sim_server` → F5 Nico (critères B, avec
`DebugSecondsPerWeek`≈3) → mettre à jour `00_etat.md` (tranche 4 ✅ +
décisions) → entrée `journal.md` → commit → `/clear` → tranche 5 (kickoff
`05_*.md` à écrire avant). Si la session sature après le volet A : committer
« t4 volet A (caméra D35) » seul, le volet B repart de ce kickoff.
