# CONCEPTION — Rendu graphique d'ambiance (D58)

> Cap : rendre le monde de Symbiose **attractif et vivant** au-delà des plantes.
> Trois chantiers cosmétiques — **fleurs par famille**, **maison normande**
> (granite + ardoise du Cotentin), **décor d'ambiance** (forêt / rivière /
> falaise / prairie autour du jardin) — précédés de l'**ajout d'essences
> forestières** au catalogue. Conçu le 2026-07-09 (`/conception`, dette D58).

## 0. Cadre et constat

D58 (« rendu graphique attractif », écrite le 2026-07-02) est **déjà à moitié
résorbée** par les sprints de rendu suivants, vérifié dans le code :

- **Feuilles par espèce = PARTIEL** — `PlantRenderer.Leaf.cs` a bien 6 archétypes
  + nervures + croissance + litière, MAIS chaque feuille est **synthétisée par
  amas d'ellipses fusionnées** (un chêne « lobé » = petites ellipses autour d'un
  centre) → au pixel ça reste des **taches ovales**, pas la silhouette réelle de
  l'espèce. **Nico (2026-07-09) rouvre l'exigence** : chaque feuille doit être
  **fidèle à son modèle botanique réel** → **contours authorés par espèce**
  (T6, §3bis), les ellipses fusionnées devenant le **repli LOD intermédiaire**.
- **Couleur physiologique = FAIT** — D33 sémiologie foliaire (`SetSymptoms`).
- **Palette + relief du sol = FAIT** — SS② pixel-art (`Palette16`, `SolTexture`).
- **Champignons / faune / vrilles = FAITS** — `CarpophoreLayer`, `MacroLife`,
  `SupportRenderer`.

**Ce qui reste réellement sous D58** = 4 chantiers, plus un préalable catalogue.
Deux sujets sont **explicitement exclus** et renvoyés en dette :

- **Vent** (animation du feuillage) → **dette D72**. Motif : entre en collision
  frontale avec le sprint perf du 2026-07-09 (les plantes viennent d'être rendues
  STATIQUES + LOD + culling pour tenir le framerate ; animer le vent = redessiner
  chaque plante par frame). À concevoir **perf-first** séparément (balancement par
  transformation de Node2D, pas re-`_Draw` des branches ; plantes proches seules).
- **Terraforming** (agir sur le paysage : barrage, coupe d'arbres, creuser la
  falaise, créer une mare… comptabilisé, avec conséquences) → **dette D73**.
  Sprint MOTEUR à part. Ici le décor est **cosmétique seul**.

## 1. Philosophie & invariants (hérités du cap pixel-art)

Tout ce document est de la **couche B** (pixellisation, `visuals/`, `world/`) —
sauf le tronçon T1 (catalogue) qui est du **moteur** (`data/code/`) mais reste
**golden-neutre** (espèces inertes hors scénario smoke). Invariants
non négociables :

1. **Couche B = golden préservé.** Le rendu est une vue passive ; il ne touche
   pas la simulation. Aucun re-figeage du golden dans les tronçons de vue.
2. **Déterminisme total** (philo #3) — zéro `Random`. Toute variation (placement
   d'un blob de houppier, d'un arbre de lisière, d'une pierre de mur, d'un
   méandre de rivière) dérive d'un **hash** stable (seed du terrain + indices).
   Re-rendre le même monde donne la même image.
3. **Jamais d'aplat** (E4 pixel-art) — tout volume ≥ 2 valeurs + hue-shift sud
   (`DrawVolumeEllipse`, palette `Palette16`). Le soleil est au **sud** (modèle
   solaire moteur).
4. **Rotation D35** — le monde tourne par quarts de tour ; maison et décor
   doivent suivre le **sud-monde** (comme les façades actuelles et la boussole
   cardinale), pas l'écran.
5. **Procédural déterministe partout** — aucun bitmap peint (la VM n'a ni Godot
   ni outil d'art) ; maison et décor sont **dessinés en C#**, cohérents avec
   plantes / sol / faune.
6. **Hétérogénéité persistante** (philo #7) — l'entourage de chaque terrain
   dérive du seed : deux terrains n'ont pas la même forêt ni le même relief.
7. **Perf-first** — tout est **statique** (dessiné une fois au build du monde et
   à la rotation D35), **cullable** hors écran, **jamais re-`_Draw` par frame**.

## 2. Chantier — Essences forestières au catalogue (T1, moteur)

Nico : « la forêt est une composition des essences présentes dans le catalogue,
tous les arbres étant adultes et de grande taille. » Le catalogue a déjà **chêne**
(étalé), **sapin** (conique), **noyer**, **cerisier**, **figuier**, **pommier**.
On **ajoute 3 essences normandes** manquantes qui couvrent la **lisière** et la
**forêt profonde**, sans doublonner la ripisylve (aulne/saule) que la conception
hydrologie (figée) réserve au bord de rivière :

| Espèce | Latin / famille | Port | Rôle décor |
|---|---|---|---|
| **Hêtre** | *Fagus sylvatica*, Fagaceae (= famille du chêne) | ovoïde dense, grand | hêtraie cathédrale, forêt profonde |
| **Bouleau** | *Betula pendula*, Betulaceae (**neuve**) | élancé, houppier léger, écorce blanche | **pionnier de lisière** |
| **Charme** | *Carpinus betulus*, Betulaceae | tronc cannelé sinueux, houppier moyen | bocage, transition |

**Chaque espèce = vraie classe moteur** `PerennialWoody` (comme `OakTree`) :
`genus`/`name`/`family`, `age_curve` [(âge_ans, hauteur_cm, rayon_cm)] atteignant
une **taille adulte de grande stature**, `port_archetype`, gènes/résistances par
défaut de pérenne. Ajoutées à `PERENNIAL_CATALOGUE` (`plants/catalogue.py`).

**Golden NEUTRE** : ces espèces ne sont **pas plantées** dans le scénario smoke
(2 tuiles × 4 ans) → aucune trajectoire nouvelle, hash inchangé. Le kickoff
vérifie explicitement que le golden ne bouge pas.

### 2.1 — Les 5 voix (règle projet « toute plante ajoutée = toutes ses voix »)

Pour chacune des 3 essences, cf. `CONCEPTION_VOIX_NARRATIVES.md` :
- **Encyclopédie** — fiche 3 niveaux (vue / cycle / effets écosystémiques).
- **Carnet** — concept(s) que l'espèce illustre (via `CONCEPT_DE`) : hêtre =
  ombre dense / humus doux ; bouleau = pionnière de lumière ; charme = bois dur
  du bocage.
- **Pages secrètes** — une page de lore *si* l'espèce en porte (hêtre = « arbre
  cathédrale », bouleau = « arbre de la renaissance » — optionnel).
- **Magazine** — rattachement famille/offre (Fagaceae, Betulaceae).
- **Événements** — marqueurs de cycle de vie au ledger (facultatif ici : arbres
  non plantés au smoke, mais fiche complète pour l'acquisition future).

> Ces voix rendent les essences prêtes pour l'**acquisition canal #3** (friche
> périphérique) : voir la forêt, apprendre une essence, la planter un jour.

## 3. Chantier — Fleurs par famille (T2, vue)

Aujourd'hui la fleur est une **corolle générique 5 pétales** ; seule la **couleur**
est par espèce (`OrganPalette.Flower`). On comble la **forme** par le patron déjà
éprouvé du feuillage (`LeafShape`/`LeafProfile`) : un `enum FlowerShape` + une
table `FlowerProfile[species]`, tracé déterministe composant des **primitives
volumées** (chaque sous-élément passe par `DrawVolumeEllipse` → invariant ≥ 2
valeurs). Fichier neuf `PlantRenderer.Flower.cs` (partial, garde `Organs.cs` court).

### 3.1 — Archétypes d'inflorescence (catalogue fermé, ~6)

| Archétype | Construction pixel | Familles / exemples |
|---|---|---|
| `Simple` (défaut) | 5 pétales radiaux + cœur (l'actuel) | Rosaceae — pommier, fraisier ; bourrache |
| `Ombelle` | N petites fleurs sur pédicelles rayonnants en dôme | Apiaceae — carotte |
| `Capitule` | disque central + couronne de rayons | Asteraceae — tournesol, souci, achillée |
| `Papilionacee` | étendard + 2 ailes + carène | Fabaceae — haricot, trèfle |
| `Epi` | pile verticale de petites corolles | Lamiaceae/Brassicaceae — lavande, thym, moutarde, phacélie, consoude |
| `Clochette` | corolle tubulaire pendante | Ericaceae — myrtille |

Fermé (6 formes couvrent le catalogue). Espèce non mappée → `Simple`. Le mappage
suit la **famille botanique** (déjà connue côté moteur, transportée au snapshot
ou déduite par table C# — cf. kickoff).

### 3.2 — Tracé, coût, LOD

- Placement des sous-corolles par **hash** du segment porteur (jitter stable).
- **Plancher de rayon** (comme les feuilles) : sous ~2-3 px, une corolle
  composée retombe sur une tache simple 1 valeur (illisible sinon).
- **Coût** : `Ombelle`/`Capitule`/`Epi` multiplient les ellipses (borné par le
  plafond d'organes existant `MaxFruits`, proxy fleurs). **LOD** : au dézoom /
  sous le palier organes (`OrganDetailMinZoom`, déjà en place), retour à `Simple`
  ou rien. Aucune régression du sprint perf.

## 3bis. Chantier — Feuilles fidèles au modèle réel (T6, vue)

Réf. Nico (2026-07-09) : « enlever les rendus simplistes de feuille en ovale, que
chaque feuille représentée soit fidèle à son modèle réel. » L'existant
(`PlantRenderer.Leaf.cs`) compose les feuilles à partir d'**ellipses fusionnées**
→ lecture en taches. On remplace, **au zoom rapproché**, par un **vrai contour de
silhouette authoré par espèce**.

### 3bis.1 — Physique du pixel & LOD (attente honnête)

À zoom d'ensemble (×4/×8) une feuille couvre 2-5 px : **aucune** silhouette n'y
est distinguable d'une tache. La fidélité ne « paie » qu'au **zoom rapproché**
(×16/×32), où une feuille couvre assez de pixels. On livre donc **3 paliers LOD** :

- **≥ `LeafOutlineMinZoom` (≈ ×16)** : **contour fidèle authoré** + volume + nervures.
- **[×4, ×16[** : **amas d'ellipses actuel** (les 6 archétypes) = repli intermédiaire.
- **< ×4** : tache/silhouette simple (existant, perf).

C'est la seule cible réaliste au pixel-art — annoncé avant F5.

### 3bis.2 — Contour authoré par espèce

- **`LeafOutline`** = contour **fermé** défini par une **liste de points normalisés**
  dans le repère feuille (axe = longueur, cross = largeur, ≈ [-1,1]), **façonné à
  la main par espèce** d'après sa feuille réelle. Le contour **encode la marge** :
  marge entière = bord lisse ; **dentée/serretée** = petites dents ; **lobée** =
  sinus profonds ; **composée** = rachis + N **folioles** (chacune un petit
  contour denté), traitées à part (feuille composée ≠ un seul limbe).
- Table `LeafOutlines[species]` (en regard de `LeafProfiles`). Les ~27 espèces du
  catalogue reçoivent leur contour ; espèce non mappée → repli archétype/ellipse.
  Exemples de fidélité visée : chêne (lobes arrondis + sinus), figuier (main
  palmée 3-5 lobes profonds), érable/courgette (palmatilobée), pommier/cerisier
  (ovale à marge **dentée**), tomate/carotte/achillée (composée pennée à folioles
  découpées), ail/lavande (ruban linéaire), trèfle (3 folioles obcordées).
- **Dérogation D10 assumée** (déjà actée pour la forme de feuille) : le contour est
  un fait de **rendu**, codé directement en C#, sans maquette SVG Python.

### 3bis.3 — Tracé, volume, nervures (invariants conservés)

1. Transformer les points normalisés → écran via `LeafFrame` (axe/cross) × (rx,ry).
2. **Remplir le polygone** en teinte ombrée, puis re-remplir une **copie réduite
   décalée au sud** en teinte éclairée (calotte lit) → **≥ 2 valeurs** garanties
   (invariant E4 « jamais d'aplat », même logique que `DrawVolumeEllipse`).
3. **Nervures** par-dessus (3ᵉ valeur) : réutiliser les topologies existantes
   (penninerve / palmée / composée) adaptées au contour.
4. **Déterminisme** : contour statique par espèce ; léger jitter d'inclinaison/
   taille par **hash** (comme aujourd'hui). Zéro `Random`.

### 3bis.4 — Perf

- Contour = **un polygone rempli** (+ copie ombrée + nervures) par feuille,
  **uniquement au palier ×16+** où peu de plantes sont à l'écran (culling actif,
  sprint perf du 2026-07-09 préservé). En dessous, on reste sur l'archétype/ellipse.
- **Repli** si lourd au F5 : cuire **un sprite de feuille par espèce** à taille
  fixe (comme `SolTexture`) et le blitter par feuille. À signaler si activé.
- Nouveau partial `visuals/PlantRenderer.LeafOutline.cs` (les contours + le tracé
  polygone) — `PlantRenderer.Leaf.cs` (358 LDC) garde les archétypes/repli ;
  un fichier = un concept (garde-fou taille).

## 4. Chantier — Maison normande = granite + ardoise (T3, vue)

Réf. Nico (regards de maçon + couvreur, Montmartin-sur-Mer / Coutançais) :
ce n'est **pas** la chaumière à colombages du pays d'Auge, mais la **maison de
granite et d'ardoise du Cotentin**. On enrichit le placeholder procédural
existant (`WorldView.Monde.cs`, déjà iso + D35-aware : 4 coins, 2 façades
visibles, toit). Comme le fichier gonfle, on **extrait** tout le rendu maison
dans un partial neuf `WorldView.Maison.cs`.

### 4.1 — Murs (moellons de granite)

- **Appareil de moellons** gris-bleu à **reflets roux**, joints de chaux clairs
  « beurrés » : texture de pierre **2-3 valeurs** (grain déterministe par hash,
  esprit `SolTexture`), pas un aplat.
- **Chaînages d'angle** marqués : pierres harpées plus claires aux arêtes.
- **Encadrements de baies** en **granite gris clair** (jambages + linteau +
  **appui à larmier** légèrement débordant).
- Éclairement **sud-monde** (façade sud claire, nord froide/sombre — hue-shift),
  indexé mur-monde comme aujourd'hui (fait tourner la maison sous D35).

### 4.2 — Pignon exposé (essentage d'ardoise)

Le pignon au **vent d'ouest** est **bardé d'ardoise** (essentage) jusqu'à
mi-hauteur : écailles sombres distinctes de l'appareil de pierre, protection
maritime typique. Rendu = petit motif d'écailles 2 valeurs sur la façade
concernée (choisie par orientation monde).

### 4.3 — Toit (ardoise à forte pente + lucarne)

- **Ardoise gris-bleu foncé**, **forte pente (> 45°)** — remplace la pyramide
  plate actuelle par **2 pans pentus + croupe**, faîte marqué.
- **Rangs d'écailles** (pureau serré, 2 valeurs) → toiture dense, pas un aplat.
- **Lucarne à bâtière** sur le versant **sud** (petit volume saillant + sa
  propre mini-toiture).
- Débords / rives sobres (une ligne d'ombre suffit au pixel).

### 4.4 — Ouvertures & cheminée

- **Porte** au sud + **fenêtres à petits carreaux** (menuiserie sombre, grille
  1 px de croisillons).
- **Souche de cheminée** en **brique orangée** émergeant du faîtage (volume
  2 valeurs). **Pas de fumée** (= animation, différée avec le vent D72).

Palette16 étendu : granite gris-bleu, granite roux, granite clair (encadrements),
ardoise, brique orangée, joint chaux.

## 5. Chantier — Décor d'ambiance (T4 ossature + T5 motifs, vue)

Réf. Nico : formes **organiques sinueuses** (jamais droites) qui ouvrent/ferment
des espaces, réparties **par seed** autour du jardin, avec une **prairie fleurie**
par défaut et des **chemins enherbés** entre les tuiles. Nouveau nœud
`visuals/DecorLayer.cs`, **derrière** `_ground` (ZIndex négatif, **hors picking**),
tournant avec le monde (D35).

### 5.1 — Ossature : zones par seed (T4)

- **`SurroundingsProfile`** — struct calculée en C# depuis le **seed du terrain** :
  pour chaque secteur autour du jardin, quel motif (forêt / rivière / falaise /
  prairie) et son **tracé sinueux** (frontière ondulée par bruit déterministe,
  jamais une ligne droite). **Prairie fleurie = motif par défaut** des côtés non
  occupés.
- **Couplage rivière ↔ falaise** : là où le profil pose une rivière, la falaise
  qui la borde en dérive (l'érosion a creusé la roche) ; pente de falaise
  **variable** (douce / verticale / déversante), tirée du seed.
- **Chemins entre tuiles = enherbés** : le gris pierre `FondPierre` actuel bascule
  en **vert herbe** (gazon), grain léger.
- **Couture d'extensibilité** (cosmétique aujourd'hui, extensible demain) :
  `SurroundingsProfile` est **structurée pour être alimentée plus tard par le
  pont** (friche périphérique, extensions par maîtrise, parcelles d'accueil
  ouvertes par le décor) **sans réécriture** — le calcul C#-depuis-seed d'aujourd'hui
  est le repli par défaut.

### 5.2 — Motifs détaillés (T5)

- **Forêt** — silhouettes d'**arbres adultes** (voir §5.3), avec **gradient de
  lisière** : densité croissante en s'enfonçant depuis le bord du jardin ; bord =
  **pionniers clairsemés** (bouleau), profond = **grands arbres denses**
  (chêne / hêtre).
- **Rivière** — bande d'eau au tracé sinueux, **reflets** par **dithering
  ordonné** (2 teintes de palette, esprit champs SS③), berges herbeuses.
- **Falaise** — paroi rocheuse **étagée** (redans 2-3 valeurs), pente issue du
  profil, sommet végétalisé.
- **Prairie fleurie** — tapis vert + **semis déterministe** de petites fleurs
  (échantillonnage stable façon `MacroLife`/litière).

### 5.3 — Rendu procédural des arbres adultes (détaillé — demande Nico)

Les arbres du décor sont un **backdrop cosmétique hors jardin** : ils n'utilisent
**pas** la structure de segments de `PlantRenderer` (perf — des centaines
d'arbres). Ils sont **peints directement en silhouette adulte**, donc « déjà
hauts et mûrs au démarrage » **par construction** (aucun âge, aucune croissance) :

- **Un arbre = tronc + houppier**, quelques primitives, **dessiné une fois**
  (statique, jamais re-`_Draw` par frame → cohérent avec l'exclusion du vent),
  **cullé** hors écran.
- **Houppier = amas d'ellipses volumées** (2-3 valeurs + hue-shift sud) formant
  un « nuage » — **pas** des branches individuelles (illisibles et coûteuses au
  backdrop). Nombre et placement des blobs = **hash(seed, index arbre)** → chaque
  arbre unique mais reproductible.
- **Archétype de port par essence** — table C# `TreeSilhouette` (comme
  `LeafProfile`), clé = nom d'espèce (contrat partagé avec T1) :
  - `Etale` (chêne) — dôme large et bas, tronc court épais, sinuosité.
  - `Ovoide` (hêtre) — houppier en œuf, dense, haut ; tronc droit net.
  - `Elance` (bouleau) — houppier léger ouvert, tronc **clair élancé**, pointes
    retombantes.
  - `Sinueux` (charme) — tronc cannelé, houppier moyen irrégulier.
  - `Conique` (sapin) — étages triangulaires (conifère).
  - **Rayon de houppier = taille ADULTE** (table par essence) → maturité intégrée.
- **Tronc** — 1-2 formes fuselées (`WoodRamp` brun) + **signature d'écorce** :
  bouleau = tronc clair à chevrons sombres (lenticelles) ; charme = cannelures.
- **Couleur de feuillage par essence** — bouleau clair, hêtre vert profond, chêne
  vert moyen, sapin vert-bleu ; **modulation automnale** saisonnière optionnelle
  (réutilise `LeafColor` du snapshot : la forêt normande rougeoie en automne).
- **Profondeur** — tri par **Y de base** (les proches masquent les lointains) ;
  tout **derrière** le jardin.
- **Perf** — quelques milliers de primitives **statiques** dessinées une fois,
  cullables ; **repli** si nécessaire : cuire la zone forêt en **une texture
  unique** (comme `SolTexture`) et la blitter.

## 6. Tronçonnage (6 tronçons — golden préservé partout)

| Tr | Contenu | Couche | Fichiers | Golden |
|----|---------|--------|----------|--------|
| **T1** | Essences forestières au catalogue (Hêtre, Bouleau, Charme) + 5 voix | **moteur** | `plants/perennials.py`, `plants/catalogue.py`, voix (encyclopédie/carnet/…) | **NEUTRE** (non plantées au smoke) — vérifié |
| **T2** | Fleurs par famille (`FlowerShape` + `FlowerProfile` + tracé + LOD) | vue | `visuals/PlantRenderer.Flower.cs` (+ éventuel champ famille au snapshot) | inchangé |
| **T3** | Maison normande (granite + ardoise + pignon + lucarne + cheminée) | vue | `world/WorldView.Maison.cs` (extrait de `.Monde.cs`), `visuals/Palette16.cs` | inchangé |
| **T4** | Décor : ossature (zones par seed, sinueux, prairie défaut, chemins enherbés, `SurroundingsProfile`) | vue | `visuals/DecorLayer.cs`, `world/WorldView` (câblage), `Palette16.cs` | inchangé |
| **T5** | Décor : forêt (`TreeSilhouette` adultes + lisière) + rivière/falaise couplées + reflets | vue | `visuals/DecorLayer.cs` (+ partial arbres) | inchangé |
| **T6** | **Feuilles fidèles** — contour authoré par espèce (~27), volume + nervures, palier LOD ×16, repli archétype | vue | `visuals/PlantRenderer.LeafOutline.cs` (neuf), `PlantRenderer.Leaf.cs` (branchement LOD) | inchangé |

**Ordre** : moteur d'abord (T1), puis vue (T2→T6). La règle « **le sprint se
termine par un tronçon vue Godot** » est satisfaite (T2→T6 sont tous de la vue).
T6 est **indépendant** (organes végétaux) — peut être fait dès après T1/T2.

**Filet de compilation** : `dotnet build Symbiose.csproj` sur la VM après chaque
tronçon C#. Le **F5 visuel reste à Nico** à chaque tronçon.

**Dépendances** : T5 dépend de T1 (noms d'espèces = clés `TreeSilhouette`) et de
T4 (zones où poser la forêt). T2, T3, T6 indépendants. T3 et T4 étendent tous
deux `Palette16` — regrouper si faits dans la foulée. T6 partage la philosophie
LOD et le voisinage fichier de T2 (organes de `PlantRenderer`).

## 7. Renvois en dette

- **D72 — Vent (animation du feuillage).** Perf-first obligatoire (transformation
  de Node2D, pas re-`_Draw` ; plantes proches seules). Conception séparée.
- **D73 — Terraforming.** Agir sur le paysage du décor (barrage, coupe, creuser,
  mare…) comptabilisé, avec conséquences. Sprint moteur. La couture
  `SurroundingsProfile` (T4) prépare le branchement.

## 8. Liens

- Cap pixel-art : [`CONCEPTION_RENDU_PIXELART.md`](CONCEPTION_RENDU_PIXELART.md)
  (palette `Palette16`, hue-shift sud, dithering, `SolTexture`).
- Feuillage (patron réutilisé pour les fleurs) :
  [`CONCEPTION_RENDU_FEUILLAGE.md`](CONCEPTION_RENDU_FEUILLAGE.md).
- Voix narratives (5 voix des essences) :
  [`CONCEPTION_VOIX_NARRATIVES.md`](CONCEPTION_VOIX_NARRATIVES.md).
- Hydrologie (réserve aulne/saule de ripisylve — pas de doublon) :
  `CONCEPTION_HYDROLOGIE_MARECAGE.md`.
- Dettes : D58 (ce doc), D72 (vent), D73 (terraforming), D4 (maison placeholder).
