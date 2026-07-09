# Sprint RENDU AMBIANCE (D58) — état vivant (carnet de conception)

> Carnet de bord `/conception`, mis à jour à chaque décision. Reprise à froid :
> lire `CLAUDE.md` + ce fichier. NE FIGE RIEN tant que Nico n'a pas validé.

## Sujet
D58 — « Rendu graphique attractif » : vraies fleurs/feuilles par espèce, maison
normande dessinée, décor d'ambiance (forêt/rivière/falaise), **+ animation vent
des plantes** (addendum Nico).

## Phase courante
**FIGÉ (2026-07-09) — prêt pour `/sprint-auto`.** Conception :
`docs/conception/CONCEPTION_RENDU_AMBIANCE.md`. 6 kickoffs `01`→`06` présents.
Golden préservé partout (T1 moteur NEUTRE, T2-T6 vue pure).

## Constat de cadrage (VÉRIFIÉ dans le code, 2026-07-09)
D58 date du 2026-07-02 et est **en partie déjà résorbée** depuis :
- **Feuilles par espèce = FAIT** — sprint feuillage clos : `PlantRenderer.Leaf.cs`
  (358 l), `enum LeafShape` 6 archétypes (Elliptique/Lancéolée/Cordée/Lobée/
  Composée/Aciculaire) mappés sur ~20 espèces + nervures + croissance progressive
  + litière (`LeafLitterLayer.cs`). Commit `ff1a52f`.
- **Couleur physiologique = FAIT** — D33 sémiologie foliaire close (`SetSymptoms`).
- **Palette + relief sol = FAIT** — SS② pixel-art (`Palette16.cs`, `SolTexture.cs`).
- **Champignons / faune / vrilles = FAITS** — `CarpophoreLayer`, `MacroLife`,
  `SupportRenderer`.
→ « vraies feuilles par espèce » n'est PLUS le sujet.

## Ce qui reste réellement sous D58 (4 chantiers hétérogènes)
1. **Fleurs par famille (forme)** — couleur/espèce FAITE (`OrganPalette.Flower`),
   mais silhouette encore **5 pétales génériques** ; manquent corolles par famille
   (ombelle Apiaceae, capitule Asteraceae…). Couche B pure, petit, lignée feuillage.
2. **Maison normande dessinée** — aujourd'hui placeholder procédural (D4 🟡,
   `WorldView.Monde.cs`, empreinte iso + 2 façades + toit gris). Cosmétique.
3. **Décor d'ambiance hors-jardin** (forêt/rivière/falaise) — **territoire NEUF**,
   aucune conception. Le monde simulé = 20×20 m ; le décor = ce qu'il y a AUTOUR.
4. **Animation vent des plantes** — **NEUF**, point dur (perf + paradigme).

## Drapeaux remontés (arbitrages en attente)
- **A. Vent vs perf (ROUGE).** Sprint perf rendu plantes clos le 2026-07-09
  (5 FPS → LOD silhouette + culling + plantes rendues STATIQUES, re-`_Draw`
  seulement au tick/zoom). Animer le vent = redessiner les plantes CHAQUE frame
  → rouvre exactement le poste qu'on vient de fermer. À concevoir **perf-first** :
  balancement par transform du Node2D (`_Process`, `skew`/rotation du canvas, GPU
  réutilise le buffer, ≈ gratuit) plutôt que re-`_Draw` des branches ; vent
  limité aux plantes proches / au-dessus d'un palier de zoom.
- **B. Décor : cosmétique pur vs relié moteur.** Règle d'interconnexion « tout
  coexiste ». Deux lectures : (i) backdrop 2D assumé cosmétique (comme le ciel
  météo `WeatherLayer`) ; (ii) représentation de la **friche périphérique**
  (canal d'acquisition #3) / des **extensions par maîtrise** (verger/mare/
  prairie) → relié au moteur. Tranche tout le découpage.
- **C. Procédural vs sprites peints.** Tout le rendu Symbiose est procédural
  déterministe (VM sans Godot/outils d'art → aucun bitmap peint possible côté
  agent). Reco = **rester procédural** (maison colombages + arbres de forêt
  dessinés en C#), cohérent plantes/sol/faune. Sprites peints = hors périmètre
  code (Nico/artiste produit les PNG, l'agent ne câble que le chargement).

## Décisions arrêtées (Nico, 2026-07-09)
- **AJOUT 2026-07-09 (post-figeage) — Feuilles fidèles au modèle réel (T6).**
  Nico : les feuilles restent « ovales ». Vérifié : `PlantRenderer.Leaf.cs`
  synthétise par **amas d'ellipses** → taches. Décision = **contours authorés par
  espèce** (~27), l'amas d'ellipses devenant le **repli LOD intermédiaire**.
  Fidélité livrée **au zoom rapproché ×16+** (physique du pixel : 2-5 px à ×4/×8,
  indistinguable). 3 paliers LOD. Nouveau partial `PlantRenderer.LeafOutline.cs`.
  Couche B pure, golden inchangé. → tronçon **T6**, kickoff `06_feuilles_fideles.md`.
- **Périmètre = 3 chantiers : fleurs-famille + maison normande + décor** (+ T6
  feuilles fidèles, ajouté ci-dessus).
  **Vent EXCLU** de ce sprint → reste ouvert (dette, à concevoir à part vu son
  enjeu perf/paradigme d'animation).
- **Décor = cosmétique MAINTENANT, extensible plus tard.** Backdrop 2D livré
  tout de suite ; prévoir une couture (`SurroundingsProfile`) pour brancher plus
  tard la friche périphérique / les extensions par maîtrise, sans la câbler ici.
- **Procédural déterministe partout** (reco C acceptée par défaut) : maison à
  colombages + décor dessinés en C#, zéro bitmap peint. Cohérent plantes/sol/faune.
- **Tout couche B pure → golden trivialement préservé** à chaque tronçon (rendu
  = vue passive, aucun moteur touché, aucun re-figeage).

## Conception détaillée (arrêtée par l'agent, bio/détails — à valider avant figer)
### Chantier 1 — Fleurs par famille (forme)
Calque du feuillage : `enum FlowerShape` + table `FlowerProfile[species]`, tracé
déterministe (hash) composant des primitives volumées (réutilise
`DrawVolumeEllipse`, invariant ≥2 valeurs). Archétypes fermés (~6), défaut
`Simple` : `Simple` (5 pétales radiaux — Rosaceae : pommier, fraisier ; bourrache),
`Ombelle` (Apiaceae : carotte), `Capitule` (Asteraceae : tournesol, souci,
achillée — disque + rayons), `Papilionacee` (Fabaceae : haricot, trèfle),
`Epi`/grappe verticale (Lamiaceae/Brassicaceae : lavande, thym, moutarde,
phacélie, consoude), `Clochette` (Ericaceae : myrtille). LOD : au dézoom →
`Simple` ou rien. Fichier : nouveau `PlantRenderer.Flower.cs`.
### Chantier 2 — Maison normande = GRANITE + ARDOISE (Cotentin, PAS colombages)
Réf. Nico (maçon+couvreur, Montmartin-sur-Mer/Coutançais). J'ABANDONNE
torchis/chaume. Étend le placeholder D35-aware (extraire `WorldView.Maison.cs`) :
- **Murs** : appareil de **moellons de granite gris-bleu à reflets roux**, joints
  chaux clairs beurrés → texture pierre 2-3 valeurs (grain par hash, cohérent
  `SolTexture`). **Chaînages d'angle** marqués (pierres harpées plus claires),
  **encadrements de baies en granite gris clair** (jambages + linteau + appui à
  larmier).
- **Pignon exposé (ouest/vent)** : **essentage d'ardoise** (bardage d'écailles)
  jusqu'à mi-hauteur, distinct du reste du mur.
- **Toit** : **ardoise gris-bleu foncé**, **forte pente (>45°)**, rangs d'écailles
  (pureau serré), faîtage ; **lucarne à bâtière** sur le versant sud ; débords /
  rives sobres. Remplace la pyramide plate actuelle par 2 pans pentus + croupe.
- **Ouvertures** : porte sud + fenêtres à petits carreaux (menuiserie sombre).
- **Cheminée(s)** : souche en **brique orangée** émergeant du faîtage (statique,
  PAS de fumée = animation différée avec le vent).
- D35 conservé (façades/pans indexés mur-monde). Palette16 étendu (granite gris-
  bleu/roux, granite clair, ardoise, brique orangée, joint chaux).
### Chantier 3 — Décor d'ambiance (organique, cosmétique ; terraforming = DETTE)
Réf. Nico. Nouveau `visuals/DecorLayer.cs`, Node2D DERRIÈRE `_ground` (ZIndex
négatif, hors picking), tournant avec le monde (D35). **Formes ORGANIQUES
sinueuses** (jamais droites, bruit déterministe) qui ouvrent/ferment des espaces.
- **4 motifs** répartis **par seed** autour du jardin (philo #7) : **forêt**
  (essences du catalogue, arbres ADULTES grande taille ; **lisière** depuis le
  bord du jardin s'enfonçant, **densité croissante** jusqu'à forêt profonde),
  **rivière** + **falaise** **COUPLÉES** (l'érosion fluviale a creusé la roche ;
  pente falaise variable douce/verticale/déversante), et **prairie verte fleurie**
  = motif par DÉFAUT du/des côté(s) non occupé(s).
- **Chemins entre tuiles = enherbés (gazon)**, plus le gris pierre `FondPierre`
  actuel → à basculer en vert herbe.
- Couture d'extensibilité : struct `SurroundingsProfile` (placement des zones)
  calculée en C# depuis le seed AUJOURD'HUI, structurée pour être alimentée PLUS
  TARD par le pont (friche périphérique, extensions par maîtrise, parcelles
  d'accueil ouvertes par le décor).
- **HORS PÉRIMÈTRE → DETTE NEUVE « terraforming »** : agir sur le paysage
  (barrage, coupe d'arbres, creuser la falaise, créer une mare…), comptabilisé
  avec conséquences. À concevoir séparément (moteur). Ici : décor cosmétique seul.

## Coût perf estimé (préliminaire)
- Fleurs-famille / maison / décor statique : couche B, ~gratuit (dessin au
  snapshot/init, pas par frame).
- **Vent : le seul poste sensible** — doit rester en transform-only par frame.

## Essences forestières AJOUTÉES au catalogue (Nico 2026-07-09)
Le catalogue a DÉJÀ : chêne (étalé), sapin (conique), noyer, cerisier, figuier,
pommier. On AJOUTE 3 essences normandes manquantes (chacune = vraie espèce
moteur `PerennialWoody` + ses 5 voix, règle projet) :
- **Hêtre** (Fagus sylvatica, Fagaceae = même famille que le chêne) — hêtraie
  cathédrale, port ovoïde dense, grand.
- **Bouleau** (Betula pendula, Betulaceae NEUVE) — pionnier de **lisière**,
  écorce blanche, port élancé pleureur clair.
- **Charme** (Carpinus betulus, Betulaceae) — bocage, tronc cannelé sinueux.
Aulne/saule de ripisylve LAISSÉS à la conception hydrologie (figée) → pas de
doublon. Ces espèces sont ajoutées au moteur mais NON plantées dans le scénario
smoke → **golden NEUTRE** (tronçon catalogue). Le DÉCOR les rend en silhouettes
adultes (voir ci-dessous) ; leur présence au catalogue leur donne encyclopédie +
voix (et prépare l'acquisition future canal #3 friche).

## Rendu procédural des ARBRES ADULTES du décor (réponse à la demande Nico)
Les arbres du décor sont un BACKDROP cosmétique HORS jardin → ils n'utilisent PAS
la structure de segments lourde de `PlantRenderer` (perf : des centaines d'arbres).
Ils sont **peints directement en silhouette ADULTE** — donc « déjà hauts et mûrs
au démarrage » PAR CONSTRUCTION (aucun âge, aucune croissance) :
- **Un arbre = tronc + houppier**, quelques primitives, dessiné UNE FOIS (statique,
  jamais re-`_Draw` par frame → cohérent avec l'exclusion du vent), cullé hors écran.
- **Houppier = amas d'ellipses volumées** (2-3 valeurs + hue-shift sud, invariant
  pixel-art) formant un « nuage » — PAS des branches individuelles (illisibles et
  coûteuses au backdrop). Nombre/placement des blobs = **hash(seed, index arbre)**.
- **Archétype de port par essence** (table C# `TreeSilhouette`, comme `LeafProfile`) :
  `Etale` (chêne, dôme large bas), `Ovoide` (hêtre, œuf dense haut), `Elance`
  (bouleau, houppier léger ouvert, tronc clair), `Sinueux` (charme, tronc cannelé),
  `Conique` (sapin, étages triangulaires). **Rayon de houppier = taille ADULTE**
  (table par essence) → maturité intégrée.
- **Tronc** : 1-2 formes fuselées (`WoodRamp` brun) + signature d'écorce
  (bouleau = clair à chevrons sombres ; charme = cannelures).
- **Couleur de feuillage par essence** (bouleau clair, hêtre vert profond, chêne
  moyen, sapin vert-bleu) + modulation automnale saisonnière optionnelle (réutilise
  `LeafColor`).
- **Lisière → forêt profonde** : densité d'arbres CROISSANTE en s'enfonçant depuis
  le bord (scatter déterministe hash, comme `MacroLife`/litière) ; bord = pionniers
  clairsemés (bouleau), profond = grands arbres denses (chêne/hêtre).
- **Profondeur** : tri par Y de base (les proches masquent les lointains) ; tout
  DERRIÈRE le jardin. **Perf** : quelques milliers de primitives statiques dessinées
  une fois, cullables ; repli = cuire la zone forêt en texture unique si besoin.

## Découpage (6 tronçons, tous golden préservé)
- **T1 — Essences forestières au catalogue** [MOTEUR, golden NEUTRE] : Hêtre,
  Bouleau, Charme (`plants/perennials.py` + `catalogue.py` + 5 voix chacune).
- **T2 — Fleurs par famille** [vue] (`PlantRenderer.Flower.cs`, `FlowerShape`+profils).
- **T3 — Maison normande** [vue] (extraire `WorldView.Maison.cs` ; granite+ardoise+
  pignon essenté+lucarne+cheminée brique, Palette16 étendu).
- **T4 — Décor : ossature** [vue] (`visuals/DecorLayer.cs` : zones organiques par
  seed = placement prairie/forêt/rivière/falaise sinueux + chemins enherbés +
  `SurroundingsProfile`).
- **T5 — Décor : forêt + rivière/falaise détaillés** [vue] (silhouettes d'arbres
  adultes par essence `TreeSilhouette` + lisière→profond ; rivière+falaise
  couplées, pente variable + reflets/dithering ; table décor ↔ essences T1).
- **T6 — Feuilles fidèles au modèle réel** [vue] (`PlantRenderer.LeafOutline.cs` :
  contours authorés par espèce ~27, volume + nervures, palier LOD ×16, repli
  archétype ellipses ; indépendant, dès après T1/T2).
Ordre : moteur d'abord (T1), puis vue (T2→T6). Règle « vue Godot en dernier »
satisfaite. F5 Nico à chaque tronçon. À figer aussi : **DETTE neuve terraforming**
+ **vent** (renvoyé) en dette.

## Carte des tronçons (exécution /sprint-auto)
- `01_essences_forestieres.md` — T1 [moteur, golden NEUTRE]
- `02_fleurs_famille.md` — T2 [vue]
- `03_maison_normande.md` — T3 [vue]
- `04_decor_ossature.md` — T4 [vue]
- `05_decor_motifs.md` — T5 [vue]
- `06_feuilles_fideles.md` — T6 [vue, indépendant]
Ordre imposé : T1 avant T5 (noms d'essences), T4 avant T5 (zones). T6 indépendant.

## Avancement
- **T1 — Essences forestières au catalogue : FAIT (2026-07-09).** Ajout des 3
  classes `PerennialWoody` (gabarit `OakTree`, contenu pur, aucune mécanique
  neuve) : `BeechTree` (Hêtre, Fagaceae, ombre dense), `BirchTree` (Bouleau,
  Betulaceae NEUVE, pionnier léger), `HornbeamTree` (Charme, Betulaceae, bocage)
  dans `plants/perennials.py` ; inscrites `hetre`/`bouleau`/`charme` dans
  `PERENNIAL_CATALOGUE` (`plants/catalogue.py`). Voix : **encyclopédie** 3 niveaux
  chacune (`sim/encyclopedie_corpus.py`, 38→41 fiches, assertion `test_encyclopedie`
  ajustée). **Magazine** = data-driven (dérive familles du catalogue → offre
  automatique, Fagaceae/Betulaceae, aucun code touché). Carnet (`CONCEPT_DE` keyé
  par événement, pas par espèce) et pages (lore optionnel) = pas d'entrée requise.
  **Golden NEUTRE — hash INCHANGÉ** `24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`.
  Suites vertes : golden, encyclopedie (68/68), magazine (23/23), genetique (20/20),
  carnet, pages, catalogue_mulch. NON committé (Nico commit).

## §REPRISE
Sprint FIGÉ. **T1 FAIT** (voir Avancement). Prochain = **T2 fleurs par famille**
(vue, `PlantRenderer.Flower.cs`), kickoff `02_fleurs_famille.md`. Chaque tronçon
restant : golden inchangé + `dotnet build` vert + F5 Nico. Dettes en parallèle :
**D72 vent**, **D73 terraforming** (dans DETTE.md).
