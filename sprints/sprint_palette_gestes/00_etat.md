# Sprint PALETTE DE GESTES PERSONNALISABLE — carnet de conception (00_etat)

> Carnet VIVANT (`/conception`, §0bis) — mis à jour à chaque décision.
> Reprise à froid : lire `CLAUDE.md` + ce fichier. Phase actuelle = **A (challenge)**.

## Sujet
Palette de gestes **personnalisable façon palette de peinture** : le joueur
compose lui-même son jeu d'outils à portée de main — une **sélection choisie**
de gestes (et de **combinaisons de gestes**), puisée dans un **catalogue de base**
+ des gestes **débloqués**. Remplace l'actuel accès « touches 1..9 + Tab cyclique »
devenu ingérable.

## Existant (relevé à froid, 2026-07-10)
- **24 gestes** codés en dur dans `world/WorldView.Actions.cs` (`Gestes[]`),
  ordre = table `sim/actions/couts.COUTS`. Kinds de cible : p/q/t/m/x/a/s/E/P/C/U/D.
- Accès : **touches 1..9** (ne couvrent QUE les 9 premiers) + **Tab** cycle TOUTE
  la palette + modificateurs **S** (graine), **B** (substrat), **N** (nature mulch).
- Gestes à **2 temps** existants : `deplacer_pot`, `epandre` (saisir → poser).
- **AUCUN gating** aujourd'hui : les 24 gestes sont tous disponibles dès le départ.
- Corpus narratif des gestes : `sim/geste_corpus.py` (fiche 3 niveaux/geste, encyclopédie).
- HUD actuel = **provisoire/debug** (`WorldView.Hud.cs`), la légende reconnaît que
  la liste des gestes « débordait » → confirme le besoin.
- Maîtrise (D12) : état Python `game_state["maitrise"][player]`, paliers 0..5 par
  objet (famille/concept/**technique/outil**). Débloque déjà : terrain, magazine,
  carnet interprétatif, Vigueur max. **Ne débloque PAS de gestes aujourd'hui.**
- Philo cadre : #5 (pas de chiffres HUD primaire, indices VISUELS → palette d'icônes OK),
  #6 (pas de tutoriel imposé, apprentissage diffus → gating dur = tension à arbitrer),
  #1 (action directe coûteuse → une combinaison ne doit pas gommer l'usure).
- CLAUDE.md : page d'accueil = 5 pictogrammes « gestes de base » (cliquer, planter,
  observer, méditer, manger) → notion de « base » déjà posée.

## Décisions arrêtées
- **D1 — Combinaisons = macros joueur enregistrées** (choix Nico). Le joueur
  compose ses propres outils (esprit « paint »). Modalité exacte (séquence
  temporelle vs pinceau composite ; cible unique vs zone balayée) = QO1.
- **D2 — Déblocage hybride, toujours SOFT/diégétique** (Nico) : deux voies —
  (a) **par connaissance/maîtrise** (techniques savantes : bouture, greffe… se
  révèlent au palier concerné), (b) **par action réalisée** (faire/poser X ouvre
  le geste Y). Jamais de gating dur type skill-tree (respecte philo #6).
- **D3 — L'état de déblocage vit côté Python** (`game_state`, par avatar, comme
  maîtrise/encyclopédie) car il doit PERSISTER dans la save JSON. La palette
  Godot le LIT dans le snapshot. → périmètre = **vue + données Python légères**
  (à confirmer QO2), golden intact (données/état, pas de logique sim).
- **D4 — Le cadre accueille des gestes FUTURS** (bouture, greffe n'existent pas
  dans les 24 actuels) — règle « le catalogue grandit avec les idées ». Ce sprint
  pose le CADRE d'accès/déblocage ; l'implémentation des nouveaux gestes eux-mêmes
  peut être un sprint à part (arbitrage de périmètre à trancher).

- **D5 — Macros = séquence sur la cible cliquée** (Nico, QO1). 1 slot macro =
  suite de gestes rejouée sur le MÊME point/cible au clic (planter→pailler→arroser
  ici). Chaque sous-geste paie sa Vigueur (philo #1 préservée). Pas de pinceau
  balayé (écarté : viderait la Vigueur d'un coup, gommerait l'usure du geste).
- **D6 — Périmètre = vue + état/données Python** (Nico, QO2). `game_state` porte
  `gestes_debloques` (par avatar, persisté) + table `GESTE_UNLOCK` data-driven ;
  exposé au pont ; palette = C#. Golden intact (état/données, pas de logique sim).
- **D7 — Bouture ET greffe IMPLÉMENTÉES dans ce sprint** (Nico, QO3), moteur
  complet + voix. → GROS sprint, découpage 5 tronçons (voir ci-dessous).

## Acquis moteur réutilisables (vérifiés à froid)
- `sim/clonal.py` : clonage exact pour la BOUTURE (copie `genes`+`expression`,
  `tile.add_plant`, coût = bouffée `stress_memory` sur la mère). Modèle prêt.
- `plants/genetics.species_compatible(a,b)` = même famille → GATE de la GREFFE.
- `GENE_NAMES` : 10 gènes ; scinder aérien/racinaire pour la greffe (voir design).
- Golden = smoke 2 tuiles×4 ans, N'INVOQUE AUCUN geste → ajouts moteur NEUTRES.

## Design proposé (à valider — Phase A)
Voir le message de conception à l'écran. Découpage pressenti (perf-first, vue en dernier) :
- **① Déblocage (Python)** : `game_state["gestes_debloques"]`, table `GESTE_UNLOCK`
  (par maîtrise / par action), hook d'évaluation + notif diégétique, expo snapshot.
  Set de BASE = gestes toujours dispo. Golden NEUTRE.
- **② Bouture (moteur + voix)** : geste `bouturer` 2 temps (mère bouturable → plot),
  clone génétique (réutilise clonal), flag espèce `bouturable`, coût/échec
  déterministes ; fiche geste + technique + concept carnet. Golden NEUTRE.
- **③ Greffe (moteur + voix)** : geste `greffer` 2 temps (greffon → porte-greffe),
  gate `species_compatible`, modèle aérien(scion)/racinaire(porte-greffe) ; voix.
  Golden NEUTRE.
- **④ Palette UI (C#)** : remplace touches 1..9/Tab ; slots curables façon paint,
  lit `gestes_debloques` du snapshot, câble tous les gestes existants + bouture/greffe.
- **⑤ Macros + banc F5** : enregistrement + rejeu séquence sur cible ; persistance
  layout palette ; banc d'observation F5. Vue finale.

- **D8 — Greffe = modèle aérien/racinaire** (Nico). Le porte-greffe adopte
  `plant_class` + gènes AÉRIENS du greffon (`hauteur`, `phenologie_florale`,
  `resistance_pathogene`, + ce qui régit fleur/fruit) ; conserve ses gènes
  RACINAIRES (`tolerance_secheresse`, `tolerance_asphyxie`, `tolerance_ombre`,
  `vigueur`) + son établissement (âge/racines → démarrage rapide). Gate =
  `species_compatible` (même famille).
- **D9 — Gestes de BASE** (Nico) : planter, arroser, recolter, manger, tailler,
  ecraser, becher (ameublir), favoriser_auxiliaire. GATED : compost (poser_bac/
  poser_pile/composter/empiler_bois/retourner/epandre), conteneurs (poser_pot/
  poser_bac_culture/deplacer_pot/planter_conteneur), supports (poser_tuteur/
  poser_treillis/poser_pergola/palisser), paillage (pailler/broyer), ruche
  (poser_ruche/recolter_miel), bouture, greffe. (Calibrage F5, ajustable.)
- **D10 — Layout palette persisté** (Nico) : `game_state["palette"][player]` =
  slots curés + macros, par avatar, un seul save (règle projet).
- **D11 — Disposition palette = COLONNE À GAUCHE, une ICÔNE par geste** (Nico,
  2026-07-10). La palette s'affiche en colonne verticale sur le bord GAUCHE de
  l'écran (remplace le HUD debug de la liste 1..9/Tab). Chaque geste a sa propre
  icône (pictogramme muet, philo #5 : pas de texte en HUD primaire). Les gestes
  débloqués apparaissent, les verrouillés non (ou grisés — calibrage F5). Tronçon ④.

- **D12 — Chaînes de déblocage diégétiques en CASCADE + 3ᵉ voie émergente**
  (Nico, 2026-07-10). Le déblocage n'est pas une table plate : c'est une
  ARBORESCENCE narrative où **outil → geste rudimentaire → palier → geste
  savant**. Exemple canonique donné par Nico :
  - posséder/utiliser le **sécateur** (outil) débloque **`couper`** (geste
    rudimentaire) ;
  - **couper une branche** (action réalisée) débloque **`tailler`** (nouvelle
    action, plus fine) ET ouvre un **palier de maîtrise** « taille » ;
  - **`tailler` niveau 2** ET **`planter` niveau 2** (deux paliers) débloquent
    **`bouturer`** OU d'abord une **PAGE SECRÈTE** qui explique la bouture ;
  - **3ᵉ VOIE — découverte par EXPÉRIMENTATION émergente** : si le joueur
    **plante une branche taillée** et la **garde humide longtemps** jusqu'à ce
    qu'elle **s'enracine**, il débloque **`bouturer`** par la pratique (il a
    reproduit le phénomène → il en a la maîtrise). C'est la méthode scientifique
    (philo #6) : observer → tenter → réussir → comprendre.
  Conséquences de modèle : (a) `GESTE_UNLOCK` doit supporter des conditions
  **COMPOSÉES** (ET de plusieurs paliers) et des conditions d'**événement
  écologique émergent** (une bouture spontanée réussie = un marqueur au ledger),
  pas seulement palier/action simple ; (b) un déblocage peut passer par une PAGE
  SECRÈTE intermédiaire (lien avec les voix narratives) ; (c) `couper` est un
  geste rudimentaire NEUF, ancêtre de `tailler` (à distinguer : `couper` = brut,
  `tailler` = savant/ciblé). ✅ INTÉGRÉ : doc §3.2/§3.4/§3.5 + kickoffs ①
  (grammaire `GESTE_UNLOCK` étendue : `et`/`ou`/`evenement` + chaîne
  sécateur→couper→tailler→bouturer, `couper` geste neuf, `tailler` passe GATED)
  et ② (marqueur `bouture_spontanee`).

## CONCEPTION FIGÉE (2026-07-10) — prête pour /sprint-auto
Arbitrages D1→D11 tranchés. Doc maître :
`docs/joueur/gestes/conception_palette_gestes.md`. Découpage figé (perf-first, vue
en dernier), golden NEUTRE/INTACT partout (référence
`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`) :

- **① Déblocage Python** (`01_deblocage_python.md`) — `gestes_debloques[player]`
  + table `GESTE_UNLOCK` (maîtrise / action) + hook `evaluer_deblocages` + expo
  snapshot. Set de BASE (D9). Pont → 0.5.23. Golden NEUTRE.
- **② Bouture** (`02_bouture.md`) — geste `bouturer` 2 temps, flag `bouturable`,
  réutilise `sim/clonal.py` (clone génétique + stress mère). Voix. Pont → 0.5.24.
- **③ Greffe** (`03_greffe.md`) — geste `greffer` 2 temps, gate
  `species_compatible`, modèle aérien(greffon)/racinaire(porte-greffe) D8. Voix.
  Pont → 0.5.25.
- **④ Palette UI** (`04_palette_ui.md`) — C# : colonne GAUCHE + 1 icône/geste
  (D11), lit `gestes_debloques`, câble tous les gestes + bouture/greffe. Golden
  intact.
- **⑤ Macros + banc F5** (`05_macros_banc.md`) — séquence rejouée sur la cible
  (chaque sous-geste paie sa Vigueur, D5), layout persisté `palette[player]`
  (D10), banc d'observation. Pont → 0.5.26. Golden intact.

## Avancement
- **① Déblocage Python — FAIT (2026-07-10)**. Golden INCHANGÉ
  (`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`). Pont
  bumpé **0.5.22 → 0.5.23**. Livré :
  - **Nouveau** `data/code/sim/actions/deblocage.py` (94 LDC pur) : `GESTES_BASE`
    (frozenset), table data-driven `GESTE_UNLOCK` (grammaire D12 : `maitrise`/
    `action`/`et`/`evenement`, liste = OU), `DECLENCHEURS` (dérivé), état par avatar
    `init_gestes_debloques`/`est_debloque`/`marquer_action`/`marquer_evenement`,
    évaluateur récursif `_cond_remplie`, hook `evaluer_deblocages` (renvoie les
    verbes nouvellement ouverts, triés), expo `gestes_debloques`.
  - `couts.py` + `geste_corpus.py` : geste BRUT NEUF **`couper`** (ancêtre de
    `tailler`, D12) — coût MODERE, objets `("taille","sécateur")`, fiche 3 niveaux.
    `tailler` reste GATED (chaîne sécateur→couper→tailler). `type_de("couper")=geste`
    (dérivé de COUTS) → test_encyclopedie 68/68.
  - `sim/actions/__init__.py` : ré-export de l'API déblocage.
  - **Pont** : `actions.py` route `couper` (alias brut de `tailler`, segment_id=None)
    + après tout geste appliqué, marque le déclencheur + `evaluer_deblocages`
    (`result["debloques"]`). `maitrise_pont.observer_apres_tick` : voie savoir après
    les crédits de palier (`gestes_debloques_recents`). `serialize.py` : bloc
    `player` gagne `gestes_debloques` (liste triée) + `debloques_recents`.
  - **Test** `tests/test_deblocage.py` (24/24) : BASE, voie savoir/action/événement,
    chaîne D12, condition composée, idempotence, no-op golden.
  - **Save JSON** : pas de couche save (de)sérialisation à ce jour (game_state en
    mémoire) → rien à câbler ; l'état est déjà JSON-sérialisable (sets → futur write).
  - **F5 Nico** : câbler la palette ④ ; calibrage des conditions/BASE ; `posseder_secateur`
    reste un marqueur d'outil à poser par le futur flux d'acquisition d'outils.
- **② Bouture (moteur + voix) — FAIT (2026-07-10)**. Golden INCHANGÉ
  (`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`). Pont
  bumpé **0.5.23 → 0.5.24**. Livré :
  - **Nouveau** `data/code/sim/actions/bouture.py` (30 LDC pur) : `peut_bouturer`
    (gate = flag espèce `bouturable` ET vivante ET mûre ET Vigueur-plante ≥ seuil,
    réutilise `sim/clonal.py`), `bouturer` (clone exact `genes`+`expression` via
    `tile.add_plant`, coût Vigueur joueur binaire tout-ou-rien, bouffée
    `stress_memory` sur la mère, marqueur `bouture_spontanee` au ledger D12).
  - **Flag `bouturable`** (défaut False → golden NEUTRE) sur `PlantBase`, posé True
    sur 8 espèces du catalogue existant : Mint, Thyme, Lavender, Comfrey, Raspberry,
    Fig, Ivy, Jasmine (littéraux seuls, règle de couche `plants` respectée).
  - **Voix** : `couts.py` (`bouturer`=MODERE, objets `("bouture","sécateur")`),
    `geste_corpus.py` (fiche geste 3 niveaux), `technique_corpus.py` (fiche technique
    `bouture` 3 niveaux), `encyclopedie_types.py` (`bouture` ∈ TECHNIQUES),
    `carnet.py` (`("bouture", None)` → concept `reproduction`).
  - `sim/actions/__init__.py` : ré-export de l'API bouture.
  - **Pont** : `simserver/actions.py` route `bouturer` à 2 temps (mère par
    `target.x_cm/y_cm`, plot par `params.r/c`, serveur STATELESS) ; version bumpée
    0.5.24 + commentaire.
  - **Tests** : `tests/test_bouture.py` (27/27 : clone, refus non-bouturable/jeune/
    morte/Vigueur, flag défaut, type_de), `tests/simserver/bouture.py` (routage +
    refus de désignation sans coût), câblé section 19 dans `test_sim_server.py`
    (253/253). test_encyclopedie/deblocage/carnet/maitrise/genetique verts.
  - **F5 Nico** : mémoire des 2 clics côté Godot (serveur stateless) ; palette ④
    câblera l'icône `bouturer` ; calibrage des espèces bouturables.
- **③ Greffe (moteur + voix) — FAIT (2026-07-11)**. Golden INCHANGÉ
  (`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`). Pont
  bumpé **0.5.24 → 0.5.25**. Livré :
  - **Nouveau** `data/code/sim/actions/greffe.py` (35 LDC pur) : partition D8
    `GENES_AERIENS` (`hauteur`, `phenologie_florale`, `resistance_pathogene`,
    `rusticite_froid`, `port_trapu`) / `GENES_RACINAIRES` (= reste de `GENE_NAMES`,
    dérivé — un gène neuf tombe côté racinaire, choix conservateur) ; `peut_greffer`
    (gate = les deux VIVANTS + `plant_class.greffable` + même FAMILLE via
    `species_compatible`) ; `greffer` (coût Vigueur ÉLEVÉ binaire tout-ou-rien →
    recomposition : `plant_class` + gènes aériens du greffon, gènes racinaires +
    établissement âge/stade/racines du porte-greffe INCHANGÉS → précocité ; greffon
    CONSOMMÉ `health=0`+`morte`). DÉTERMINISTE, zéro RNG (philo #3).
  - **Flag `greffable`** (défaut False → golden NEUTRE) sur `PlantBase`, posé True
    sur 4 ligneuses fruitières : Fig (Moraceae), AppleTree, CherryTree, Raspberry
    (Rosaceae → paires greffables intra-famille).
  - **Voix** : `couts.py` (`greffer`=ELEVE, objets `("greffe","greffoir")`),
    `geste_corpus.py` (fiche geste `greffer` 3 niveaux), `technique_corpus.py` (fiche
    technique `greffe` 3 niveaux), `outil_corpus.py` (fiche outil `greffoir` 3
    niveaux — outil NEUF dérivé), `encyclopedie_types.py` (`greffe` ∈ TECHNIQUES,
    `greffoir` auto-dérivé outil), `carnet.py` (`("greffe", None)` → concept
    `reproduction` + gabarit dédié descriptif/interprétatif).
  - `sim/actions/__init__.py` : ré-export de l'API greffe.
  - **Pont** : `simserver/actions.py` route `greffer` à 2 temps (porte-greffe par
    `target.x_cm/y_cm` = cible primaire, greffon par `params.scion_x_cm/scion_y_cm`,
    même tuile, serveur STATELESS) ; version bumpée 0.5.25 + commentaire. Gate lu en
    amont pour message clair, refus de même-plante.
  - **Tests** : `tests/test_greffe.py` (31/31 : recomposition aérien/racinaire,
    établissement conservé, refus familles≠/non-greffable/mort/Vigueur, flag défaut,
    type_de geste/technique/outil, partition disjointe), `tests/simserver/greffe.py`
    (routage + refus de désignation sans coût), câblé section 20 dans
    `test_sim_server.py` (**259/259**). Golden + encyclopedie (68/68) + bouture +
    deblocage + carnet verts.
  - **F5 Nico** : mémoire des 2 clics côté Godot (serveur stateless) ; palette ④
    câblera l'icône `greffer` ; calibrage des espèces greffables + coût ÉLEVÉ.
- **④ Palette UI (C#) — FAIT (2026-07-11)**. Golden INCHANGÉ
  (`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`). Aucun
  fichier moteur touché (pur vue, Option B). `dotnet build` VERT. Livré :
  - **Nouveau** `world/GesteIcon.cs` (197 LDC) : icône MUETTE procédurale par
    geste (hérite de `Button` → clic/focus/tooltip gratuits, fond natif effacé,
    pictogramme peint dans `_Draw`). ~16 pictogrammes primitifs par famille
    (goutte/ciseaux/pousse/fruit/tas/pot/treillis/ruche/bouture-tige/greffe-T…)
    + couleur par famille. États `Actif` (cadre lumineux) / `Verrouille` (grisé +
    `Disabled` inerte). Libellé au SURVOL seulement (`TooltipText`, philo #5).
  - **Nouveau** `world/WorldView.Palette.cs` (88 LDC, partial) : colonne
    verticale gauche (`CanvasLayer` + `VBoxContainer`, y=150 sous l'horloge),
    une `GesteIcon` par entrée de `Gestes[]` (ordre inchangé, index aligné sur
    `_gesteIndex`). `ApplyGestesDebloques(ouverts, recents)` lit
    `player.gestes_debloques` du snapshot (TOLÉRANT : clé absente → tout ouvert),
    reconstruit la visibilité SEULEMENT au changement d'empreinte triée
    (event-driven). Verrouillés = visibles+grisés+inertes (calibrage F5).
    `debloques_recents` → flash vert de l'icône (notif diégétique, philo #6,
    pas de pop-up). `UpdatePaletteSelection` synchronise l'entrée active
    (source de vérité = `_gesteIndex`, câblée depuis `SelectGeste`).
  - `WorldView.Actions.cs` : 2 gestes AJOUTÉS à `Gestes[]` — `bouturer` (Kind
    `'b'`, 2 temps : mère position continue → plot `params.r/c` même tuile) et
    `greffer` (Kind `'g'`, 2 temps : greffon `params.scion_x_cm/y_cm` →
    porte-greffe cible primaire, même tuile). État de saisie `_grabbedMother`/
    `_grabbedScion` (réinitialisés dans `SelectGeste`). Routage conforme au pont
    (`simserver/actions.py` §bouturer/greffer, 0.5.24/0.5.25).
  - `WorldView.Snapshot.cs` : bloc `player` lit `gestes_debloques` +
    `debloques_recents` → `ApplyGestesDebloques`.
  - `WorldView.cs` : `BuildPalette()` appelée dans `_Ready` (après `BuildHud`,
    avant le 1er `ApplySnapshot`).
  - `WorldView.Hud.cs` : HUD action rappelle l'état de saisie bouturer/greffer ;
    légende debug corrigée (palette gauche = source de vérité, Tab/1..9 =
    accélérateurs). Le HUD debug ne LISTE plus les gestes (la palette les montre).
  - **F5 Nico** : (a) valider la colonne gauche cliquable + lisibilité des 26
    pictogrammes procéduraux (calibrage possible sprites dédiés) ; (b) filtrage
    par déblocage (gestes GATED masqués/grisés selon `gestes_debloques`) ;
    (c) `bouturer`/`greffer` sélectionnables + gestes 2 temps (mère→plot,
    greffon→porte-greffe) ; (d) flash vert d'un geste fraîchement débloqué ;
    (e) arbitrer masquer VS griser les verrouillés (aujourd'hui : grisé).
    NB : mémoire des 2 clics côté Godot OK (serveur stateless).
- **⑤ Macros + persistance layout + banc F5 — FAIT (2026-07-11)**. Golden
  INCHANGÉ (`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`).
  Pont bumpé **0.5.25 → 0.5.26**. `dotnet build` VERT. Livré :
  - **Python (données/pont, golden NEUTRE)** :
    - **Nouveau** `sim/actions/palette.py` (60 LDC) : `FAMILLE_CIBLE`/`famille_cible`
      (dérive la famille de cible d'un verbe depuis les Kinds), `macro_coherente`
      (une macro = gestes de MÊME famille → un clic les nourrit tous),
      `init_palette`/`palette_layout` (lecture pure `{slots, macros}` par avatar),
      `definir_palette` (valide cohérence PUIS écrit transactionnellement, refus en
      bloc si macro mixte). Ré-exporté par `sim/actions/__init__.py`.
    - **Pont** : commande NEUVE `palette` (`tools/simserver/palette_cmd.py`
      `PaletteCmdMixin` + dispatch `server.py`) qui appelle `definir_palette` et
      renvoie le layout ou un `ok:false` + message (transaction). `serialize.py` :
      bloc `player` gagne `palette` (= `{slots, macros}` de l'avatar). Version
      0.5.26 (`version.py`) + commentaire.
    - **Nouveau banc** `bancs/palette_gestes.py` (33 LDC) : tuile « PALETTE » 6×6,
      6 Lavender mûres (bouturables) + AppleTree/CherryTree mûrs (greffables
      Rosaceae), banque de graines ; hook `post_init` NEUF `BANC_POST_INIT`
      (`bancs/__init__.py`) qui force maîtrise `taille`/`semis`/`greffe` puis
      `evaluer_deblocages` → bouturer+greffer OUVERTS. `cmd_init` (`commands.py`)
      appelle le hook après `ensure_player`. **Jamais monté en smoke/full** → golden
      intact.
    - **Tests** : `tests/test_palette.py` (22/22 : familles, défaut, persistance,
      transaction/refus incohérent, forme, lecture pure, no-op golden),
      `tests/simserver/palette.py` (`test_palette_pont` : banc monté, palette défaut
      exposée, bouturer/greffer ouverts, macro cohérente persistée + relue au
      snapshot, macro incohérente refusée sans écrasement), câblé section 21 dans
      `test_sim_server.py` (**269/269**). Assertions de version 0.5.25→0.5.26 dans
      conteneurs/structures/voix.
  - **C# (vue, Option B, `dotnet build` vert)** :
    - **Nouveau** `world/WorldView.Macros.cs` (138 LDC, partial) : `ApplyPalette`
      (lit `player.palette.macros` du snapshot, TOLÉRANT clé absente),
      ENREGISTREMENT (touche **K** bascule `_recording` ; sélectionner un geste
      l'AJOUTE via `RecordGesteSiEnCours` ; re-K → `PersistMacro` envoie
      `SimBridge.Palette(macros:…)`), REJEU (touche **J** arme ; le clic capture le
      POINT + Maj et enfile les indices ; `DrainMacro` dépile un sous-geste par
      frame dès que le pipe est libre, via `TryAction` → chaque geste PAIE sa
      Vigueur, philo #1).
    - `WorldView.Actions.cs` : `SelectGeste` route vers l'enregistrement si
      `_recording`, sinon `ResetMacroState`. `WorldView.Snapshot.cs` : appelle
      `ApplyPalette`. `WorldView.Controls.cs` : touches K/J + clic prioritaire
      `LancerMacroSiArmee`. `WorldView.cs` : `DrainMacro()` dans `_Process` (après
      la file d'intention). `WorldView.Hud.cs` : préfixe HUD ● REC / ▶ macro armée.
    - **Nouveau** `core/SimBridge.cs` `Palette(slots, macros)` (envoi cmd `palette`).
  - **F5 Nico** : (a) monter le banc (`init config="palette_gestes"`) pour tester ;
    (b) K enregistre une séquence cohérente (ex. planter→arroser), re-K persiste,
    J + clic la rejoue au point ; (c) vérifier que chaque sous-geste débite la
    Vigueur ; (d) une macro incohérente (familles mêlées) est refusée par le pont
    (message HUD) ; (e) calibrage : un seul slot macro rejoué (le n°1) — sélecteur
    multi-macro à ajouter si souhaité.

## §REPRISE
**SPRINT TERMINÉ (2026-07-11).** Tous les tronçons ①→⑤ FAITS. Golden intact
`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`, pont 0.5.26,
suite pont 269/269, `dotnet build` vert. Reste = **F5 Nico** (recette ci-dessus
par tronçon) + calibrages notés. Aucune reprise de dev nécessaire.

## Coût perf estimé
Négligeable (couche vue/UX + état persisté). Hook déblocage event-driven (hors
tick) ; une macro = N appels pont séquencés, aucun calcul sim par tick ;
bouture/greffe event-driven comme tous les gestes.
