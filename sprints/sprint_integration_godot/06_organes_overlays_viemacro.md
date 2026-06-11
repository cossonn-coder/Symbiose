# Tranche 6 — Organes procéduraux · Vie macro visible · Overlays debug

> **Kickoff autosuffisant** (démarrage à froid : lire `00_etat.md` d'abord).
> Dernière tranche de CONTENU du sprint Intégration (après : t7 = packaging
> PyInstaller). Ampleur : **gros** → **3 volets committables séparément**,
> chacun vérifiable par un F5 Nico, témoin de build incrémenté à chaque volet
> (`WorldView.Build` = « t6·A … », « t6·B … », « t6·C … »).
> Golden écolo `16a1b937…` **intact par construction** : tout est LECTURE
> (snapshot/commandes), le tick moteur n'est jamais touché.

## Ce qu'on construit, en une phrase
Le jardin cesse d'être des bâtons : **feuilles/fleurs/fruits procéduraux**
(volet A), **insectes et vers visibles** (volet B), **heatmaps des champs
écologiques en mode debug** (volet C).

## État de départ (rappels du pont, t1-t5)
- Protocole v1 (`0.2.1`) : `init/step_week/snapshot/action/quit`, snapshot =
  horloge + bloc `player` + plantes (`tile`, `species`, `x_cm/y_cm`, `stage`,
  `stage_name`, `height_cm`, `segments` bruts de `structure_to_dict()`).
- Côté vue : `WorldView.cs` (scène principale, caméra D35, gestes 1..8,
  boucle Planification↔Saison↔Pause, perfs F4, ombres O) ;
  `PlantRenderer.cs` (segments + ombre-capsule dans nœud enfant `PlantShadow`
  — leçon perf C2 : le soleil ne redessine QUE les ombres) ; surbrillance
  taille t5 (`HighlightSegment`, `FindSegmentGlobal`).
- Si Godot a besoin d'une donnée : on l'**expose en lecture** (snapshot ou
  commande), on ne change JAMAIS la logique moteur.

---

## Volet A — organes procéduraux (le gros morceau visuel)

**Source à porter** : `tools/render_structure.py` §« ORGANES PROCÉDURAUX »
(`_draw_organs`, `_organ_sites`, `_leaf_color`, `_is_leafy` + constantes
`LEAF_*`, `MAX_FRUITS`, `ORGAN_PALETTE`, `AUTUMN_LEAVES`, `REPRO_BY_SEASON`).
Les organes ne sont PAS stockés par le moteur (§J : reconstructibles à la
volée depuis segments + profil espèce + saison) — c'est un PUR rendu.

1. **Python — exposer les 3 hints au snapshot** (lecture seule, par plante) :
   - `foliage_density` : `cls.foliage_density_at(plant, saison)` (float 0..1,
     déjà saisonnier — caduc l'hiver → 0) ;
   - `organ` : stade reproducteur visible (`"flower"|"fruit_unripe"|
     "fruit_ripe"|null`) lu dans `REPRO_BY_SEASON` — **importer la table
     depuis `tools.render_structure`** (outil→outil, zéro duplication, zéro
     moteur touché). Espèce absente de la table → repli `DEFAULT` raisonnable
     (fleur au printemps, fruit mûr en été/automne, rien l'hiver) ;
   - `organ_site` : `cls.organ_site` (`"terminal"|"lateral"`).
   Signalé : le VRAI état reproducteur (maturité réelle, déplétion par
   `manger`) = D19/D33, sprints moteur dédiés — ici on rend le proxy
   saisonnier du prototype, fidèle au SVG validé.
2. **C# — dessiner dans `PlantRenderer`** (après le bois, avant la
   surbrillance) :
   - **Feuilles** : mêmes règles que le prototype — segments « feuillés »
     (apex OU `thickness ≤ 1.6 cm`), 1 feuille/11 cm, déport latéral 7 cm
     tiré au hash, ellipse ~7 cm, couleur palette espèce × saison (printemps
     clair, automne tiré dans `AUTUMN_LEAVES`, hiver = rien si caduc),
     opacité ~0.92, densité < 1 → sous-échantillonner les feuilles.
   - **Fleurs/fruits** : aux bouts d'apex (`terminal`) ou des latéraux hors
     meneur (`lateral`), plafond 10 ; fleur = 5 pétales + cœur, fruit =
     disque + reflet.
   - **Hash C# local** (pas de parité bit-à-bit avec le SVG requise — c'est
     de la décoration de vue ; il faut juste la STABILITÉ inter-frames et
     inter-sessions) : petit hash entier déterministe sur (index segment,
     index feuille), pas de `Random`.
   - **Perf (leçon C2)** : les organes se redessinent avec la plante
     (`SetStructure`/saison) — JAMAIS par frame ni au balayage du soleil.
     La saison change → un seul `QueueRedraw` par plante (à l'ApplySnapshot).
3. **Mesure** : taille snapshot avant/après (3 hints ≈ +60 o/plante,
   négligeable attendu — vérifier au test).

## Volet B — vie macro visible (D31 côté vue)

**Source** : `fields/population.py` — 4 guildes (`ravageur`, `auxiliaire`,
`pollinisateur`, `vers_de_terre`) dans `eco.populations`, et l'échantillonneur
**PUR et déterministe** `sample_sprites(field, seed)` → `SpriteSample{guild,
row, col, slot, x_frac, y_frac, activite}` (positions par `_hash_noise`,
indépendantes de la semaine : un slot vit toujours au même point, il
apparaît/disparaît quand la densité franchit son seuil — modèle tranché
CONCEPTION_VIE_MACRO §3).

4. **Python — bloc `sprites` au snapshot** : par tuile, concat des
   `sample_sprites` des 4 guildes (l'échantillonnage se fait CÔTÉ SERVEUR —
   la vue n'a pas besoin de `_hash_noise`). Champs : `guild`, `r`, `c`,
   `x_frac`, `y_frac`, `activite`. **Mesurer la taille** (borné par
   `SPRITES_PAR_PLOT_MAX` × plots ; si > ~100 Ko de plus, compacter en
   tableaux par guilde — mesurer AVANT d'optimiser).
5. **C# — dessiner les sprites** : nouveau nœud par tuile (ou un
   `MacroLife : Node2D` global, ZIndex entre sol et objets). Par guilde une
   FORME/COULEUR distincte mais **AUCUN nom affiché** (philo : visible dès le
   début, non identifiable sans maîtrise — l'identification = tranche
   maîtrise future). Suggestion sobre : ravageur = point sombre, auxiliaire =
   point clair, pollinisateur = point jaune qui erre plus large, vers =
   petit tiret terre au sol. **Errance locale** ∝ `activite` autour du point
   d'ancrage (sin/cos sur l'horloge frame, amplitude quelques px — pur
   `_Process` du nœud sprites, pas de tween par sprite).
6. **Diff doux** : apparition/disparition d'un slot entre deux snapshots →
   petit fondu (comme les plantes t3), pas de pop sec.
7. Bonus de cohérence : `ecraser` affiche déjà « ravageurs 0.80 → 0.60 » —
   maintenant on VOIT les points disparaître au même plot.

## Volet C — overlays debug (heatmaps)

8. **Python — commande `fields`** (le snapshot hebdo n'embarque PAS les
   grilles — volume) :
   - `{"cmd":"fields"}` → `{"ok":true,"fields":[noms…]}` : registre découvert
     dynamiquement = attributs `GridField` de `EcoFields` (humidité,
     fertilité, microbiome, soil_memory*, om_*, temperature, disturbance…)
     + `populations` (les 4 guildes) + lumière si disponible par plot.
   - `{"cmd":"fields","field":"microbiome"}` → par tuile : `rows`, `cols`,
     `values` (liste row-major). Champ inconnu → `ok:false`, serveur survit.
9. **C# — overlay heatmap** : touche **F6** = ON/OFF, **Maj+F6** = champ
   suivant (cycle sur la liste du serveur). Rendu sobre : un `Polygon2D`
   teinté par plot (réutiliser la maille de `BuildGround`), ou une seule
   `ImageTexture` rows×cols par tuile en filtre Nearest étirée sur la tuile
   (moins de nœuds — au choix de l'implémentation, dire pourquoi). Dégradé
   bleu→rouge + nom du champ + min/max au HUD perfs. Rafraîchi à chaque
   snapshot appliqué SI l'overlay est ON (une requête `fields` par semaine,
   pipe maître/esclave : passer par la même file que step/action — UNE
   requête en vol, leçon t4·B).
10. **Étiquetage** : c'est le « mode debug champs écologiques » de la
    conception (Options plus tard) — au HUD, suffixe « (debug) ». Philo #5 :
    autorisé hors HUD primaire.

## Critères de succès (F5 Nico, par volet)
- [ ] **A** : au fil des saisons un pommier fleurit (printemps), fructifie
      vert (été), fruits rouges + feuillage jaune/rouge (automne), nu
      (hiver) ; la tomate garde son cycle propre ; pas de chute de FPS
      (vérifier F4 avant/après).
- [ ] **B** : des points vivants peuplent les tuiles, plus nombreux où ça
      fleurit/paille ; écraser un plot → des points y disparaissent ;
      aucune étiquette de nom.
- [ ] **C** : F6 affiche une heatmap lisible qui suit la simulation
      (humidité qui sèche, microbiome qui s'étend) ; Maj+F6 change de champ ;
      OFF = coût strictement nul.
- [ ] Protocole : `test_sim_server` étendu (hints organes présents et
      cohérents — caduc hiver = 0 ; bloc sprites borné et déterministe ;
      commande `fields` liste + grille + refus champ inconnu) ; golden écolo
      `16a1b937…` intact ; `ENGINE_VERSION` → **0.3.0**.

## Contraintes & rappels
- **GDScript interdit, namespace `Symbiose`** ; un volet = un commit
  (Python+tests puis C#, ou ensemble si le volet est petit).
- Le moteur n'est JAMAIS modifié — adaptateur `sim_server.py` et outils
  seulement. Toute envie de toucher `sim/`/`fields/` = STOP, dette/backlog.
- Témoin de build à incrémenter À CHAQUE volet (piège sync Nextcloud).
- Mesurer les tailles de snapshot après A et B (la règle : mesurer avant
  d'optimiser) ; noter les chiffres dans `00_etat.md`.
- `DebugSecondsPerWeek=3` encore actif — utile pour valider A (saisons
  rapides) ; à remettre à 0 en fin de sprint.
- Ne PAS entamer en passant : identification des guildes par maîtrise
  (tranche future), D19 organes comestibles/déplétion, D33 couleur
  physiologique (les organes posent la BASE, le câblage état→couleur est un
  sprint dédié), D34 assets tuiles. Backlog intact.
