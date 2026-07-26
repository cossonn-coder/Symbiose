# 2026-07-26 — Sprint PÉRIPHÉRIE (D73) — CLOS

`/sprint-auto sprint_peripherie` (①→⑦, puis passe `/refactor` auto-légère).
Implémente la conception figée le matin même (voir entrée 143). Le sujet en une
phrase : **le jardin n'est pas une île** — la périphérie agit d'abord sur le
jardin (cinq flux entrants), puis le joueur agit sur la périphérie (sept gestes
de paysage). Golden **`57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`
INCHANGÉ du premier au dernier tronçon**, `dotnet build` VERT, protocole pont
**0.5.41**.

## Les cinq décisions de conception, telles qu'elles ont tenu au code

- **D-1 — maille 4 secteurs cardinaux, vérité côté Python.** L'état vit dans
  `game_state["ceinture"]` (`fields/peripherie.py`), à la maille qui existait
  déjà côté vue (N/E/S/O, bande de 9 m). `DecorLayer.BuildProfile` **cesse
  d'être générateur** : la couture T4 de D58 était écrite pour ça. Tenue sans
  entorse — et c'est ce qui a fait **disparaître D92 par construction**.
- **D-2 — UN seul sprint, ordre interne entrant → sortant.** Vérifiée à
  l'usage : les points de greffe existaient tous (abri, lumière, seedbank,
  hydrologie, outils), donc le couplage entrant a coûté **3 tronçons**, pas une
  fondation. Aucun tronçon n'a eu besoin de rouvrir le précédent.
- **D-3 — « comptabilisé » = ledger + trace dans le milieu + matière.** Les
  trois formes sont livrées, et **aucun indicateur d'impact cumulé** (#5) : le
  bois tombe en **parcelles de litière `bois`** aux plots du bord (pas de nature
  `"bois"` dans `mulch_stock`, précision Nico respectée à la lettre — la pile
  l'accepte, le bac le refuse), la trace persiste dans le secteur
  (`souche_memory`, `entaille_cm`, densité), et le ledger consigne.
- **D-4 — essence dominante par secteur, pas de forêt d'espèces.** Tirée du
  seed dans le catalogue ligneux existant ; un secteur `foret` voisin d'une
  `riviere` devient **ripisylve** (aulne/saule). L'essence décide du rejet de
  souche — et « recéper une hêtraie, c'est l'abattre » est **littéral dans le
  code** : `couper_secteur` renvoie le geste dont la cinétique s'applique, donc
  `receper` sur hêtre/bouleau renvoie `"abattre"`. Le geste n'est jamais bloqué,
  rien ne l'annonce (#6) ; le ledger, lui, le consigne.
- **D-5 — une seule espèce ajoutée : le SAULE.** `plants/perennials.Willow`,
  famille **Salicaceae** neuve, avec ses **5 voix** (⑥). Il rend enfin cohérentes
  les deux tables qui le citaient **sans espèce** depuis le ① (`ESSENCES_RIPISYLVE`,
  `ESSENCES_QUI_REJETTENT`). Noisetier et prunellier/ronce **écartés** (portés
  côté agrégat par le charme et le bouleau) → notés au backlog du thème.

## Les trois trous de l'amorce, comblés

- **T1 — le brise-vent POREUX est la leçon centrale.** Mais la règle des manuels
  (portée 20-30 H) ne s'exprime **pas** à cette échelle : derrière une lisière de
  15 m, un jardin de 20 m tient entre 0 et 1,3 H. Ce qui s'exprime à 0-3 H est la
  **turbulence de décollement** ⇒ la porosité module la réduction du vent moyen
  **linéairement** et la **rafale quadratiquement**
  (`turbulence *= 1 + TURBULENCE_MUR·(1−φ)²`). Leçon émergente, zéro tutoriel :
  *une lisière trop dense abrite du vent constant mais fait tomber des rafales*
  — et **abattre partiellement peut améliorer l'abri**. Mesuré au ② : une lisière
  dense abrite ×1,80 mais turbule ×3,24.
- **T2 — « corridor faune → `habitat_fn` » était un piège #2.** Formulé en
  **champ du milieu** `eco.lisiere` (∈ [0,1], gradient sur 8 plots, combiné entre
  bords par MAXIMUM — un coin n'est pas deux fois une lisière) + réponse
  **déclarée par guilde** (`TrophicSpec.lisiere_w`, défaut 0.0 ; 6 guildes
  renseignées, hérisson 0.30 en tête, **14 restent à 0.0** dont les ravageurs de
  culture). Le milieu porte l'information, la guilde y répond.
- **T3 — la rivière n'a pas de grille hydraulique hors jardin.** Le barrage est
  donc une **condition aux limites** : `tick_berge` pousse ou retire de l'eau
  dans les pores des 3 premiers plots du bord, **juste avant `tick_hydrology`**,
  et tout le reste ÉMERGE du circuit existant (surplus → lame de surface →
  ruissellement → `marais_memory` → `est_marais`). Zéro ligne de physique neuve.
  *Piège trouvé au ③* : `humidite.add` écrête **silencieusement** à `HUM_CAP` —
  sans routage explicite du surplus vers `eau_surface`, **aucun marécage de berge
  ne pouvait naître**.

## Les sept tronçons

### ① Ceinture 4 secteurs déterministe — `12c0aa6`
`fields/peripherie.py` (79 LDC) : canaux-sentinelles tranche `91_00x`,
`generer_ceinture(seed)` en 3 passages (type → couplage falaise → scalaires +
essence). **Rien n'est branché** (neutralité structurelle : pas même un
ré-export). **D92 refermée et mesurée** sur 300 000 seeds : 4 côtés identiques
**96,0 % → 2,7 %**, terrains portant une falaise **0 % → 52,0 %**. Deux
correctifs par rapport au C# : décalage par côté sur **deux grands premiers**
(`7 919`/`104 729` — l'avalanche de `_hash_noise` seule ne décorrélait pas
`cote±1`) et adjacence de falaise **symétrique** avec condition réalisable.
`test_peripherie` 16/16.

### ② La lisière ombre et abrite — `79059bb`
Géométrie MONDE de la bande (`MONDE_CM = 2000`, miroir de `WorldView.WorldCm` —
le moteur n'avait **aucune** constante d'emprise globale). `light.compute` traite
les occulteurs en **rectangles balayés** comme la maison, mais à ombre
**PARTIELLE** (`att *= 1 − opacité`) ; `abri._obstacles` passe en 5-uplets avec
`poro` (`None` = branche historique bit-identique, cf. D94). Champ neuf
**`eco.turbulence`** (LAZY, plafond 2.0, unique lecteur `_wind_damage`).
**Zéro `if saison`** : l'asymétrie hiver/été sort de `solar_slice` — lisière SUD,
bord nord **−49 % en hiver, −0 % en été**. Caches prouvés par sentinelle dans le
champ. 38/38.

### ③ Graines, berge et corridor — `bb92e5d`
Helper géométrique partagé `plots_de_bord(...)` — **générateur** en
O(portée × côté), jamais un balayage de grille (réflexe D32) ; une tuile loin du
bord ne rend RIEN. Trois flux : **pluie de graines** (patron exact de
`tick_late_succession_enrichment`, table écologique par type de secteur, portée
4 plots — c'est le support mécanique qui manquait au **canal d'acquisition #3**),
**nappe de berge** (T3), **corridor** (T2, mémoïsé sur `(types, tile_origin)`).
71/71. *Écart assumé et signalé* : `secteur_neutre()` est une **prairie**, et une
prairie sème et porte un ourlet ⇒ une ceinture « neutre » n'est plus neutre pour
ces deux flux. L'interrupteur qui protège le golden reste l'**ABSENCE** de
ceinture — ce qui est le cas du golden.

### ④ `abattre`, `receper`, `eteter` — `4901d30`
Découpage en **deux** responsabilités (écart motivé au kickoff qui n'en prévoyait
qu'une) : `fields/peripherie.py` porte les mutations d'état **PURES** + les
cinétiques (zéro RNG, zéro coût), `sim/actions/paysage.py` (neuf) la couche
JOUEUR (gate d'outil → coût → matière → ledger). Bénéfice : `tick_repousse`
s'importe depuis `fields` dans `boucle.py`, **aucune remontée de `sim.engine`
vers `sim.actions`**. Cinétiques déterministes : trogne **5 ans** (densité
conservée, hauteur ×0.6) · taillis **10** · abattage **30**, avec un **plancher
pionnier** à 4 ans ⇒ le vide se remplit vite, la structure est lente. Outils
hache/serpe/pioche + `GESTE_UNLOCK` (`eteter ← ("action","receper")` : la trogne
s'apprend après le taillis, pas en achetant un outil). Palier de coût neuf
**`TRES_ELEVE = 60`** — le barème s'arrêtait à `ELEVE`, ce qui aurait mis abattre
et recéper au même prix alors que leur **asymétrie est toute la leçon**. 76/76.

### ⑤ `endiguer`, `deriver`, `entailler` — `6ebd66e`
Les gestes du **milieu pur** (#1 dans sa forme la plus nette : aucun être vivant
touché). Le cœur du tronçon tient en deux lignes : la distinction
**FORME / ARTEFACT** — `creuser` relève la ligne d'eau **et** sa référence
naturelle, `endiguer`/`deriver` seulement la ligne d'eau ⇒ **émergence gratuite** :
un barrage qui rompt (8 ans) rend l'eau à la mare creusée avant lui, jamais à
zéro ; refaire le geste = **entretien** (mesuré : entretenu tous les 3 ans, un
ouvrage tient 12 ans). `entailler` est le **seul geste irréversible du jeu**, et
c'est écrit dans les données (aucune entrée de falaise dans `CINETIQUES` ;
vérifié sur 10 000 ticks). Érosion greffée sur `structure_sol`/`om_stable`, avec
**trois émergences que rien ne produit explicitement** : l'étêtage n'érode pas,
une éclaircie légère non plus, et l'érosion **cesse d'elle-même** quand la
densité revient. Signe `🪨` **une fois par épisode** (sans ce verrou, une
cicatrice de falaise noierait le carnet). 59/59.

> *Écart assumé* : le signe d'érosion **n'est pas** dans `sim/semiologie.py`
> comme le disait le kickoff — ce module est la sémiologie **FOLIAIRE** et son
> invariant est que chaque détecteur réutilise le seuil de la mécanique qui
> blesse le tissu. Une érosion ne blesse aucune feuille : un détecteur foliaire
> aurait été un signe qui **ment sur sa cause**. Rendu par le canal des signes du
> **MILIEU** (marqueur de log par tuile, patron de `tick_rosee`).

### ⑥ Le saule et ses 5 voix — `eb6861c`
Aucune écologie : de la donnée éditoriale, une table de classification, un
parseur. Le tronçon **referme ce que ④ et ⑤ avaient ouvert** —
`test_encyclopedie` repasse de **64/68 à 68/68** (il était rouge **avant** le
sprint : c'était le compteur du ⑥). Saule au catalogue (D-5) ; `TECHNIQUES` gagne
`terrassement` (⚠️ pré-existant : la technique de `creuser`/`drainer` tombait
dans `OUTILS` par défaut et se voyait réclamer une fiche d'objet — cause des
7 « outils muets ») ; corpus geste/technique/outil à 3 niveaux ; **le ledger a
enfin ses lecteurs** — `sim/evenements.py` reconnaît les quatre marqueurs
`🪓 ⛏ 🚧 🪨`, testés **AVANT** le filtre `@(r, c)` (ce sont des faits de
**secteur**, sans position — sans ça la ligne était silencieusement ignorée) ;
9 concepts de carnet ; pages **P38→P42**. L'API historique `_evenements`
(détection de maîtrise D12) reste **aveugle** à ces lignes ⇒ zéro régression.
91/91.

> Deux extensions de périmètre **assumées et signalées** : 3 gestes hors sprint
> (`pincer`, `arracher`, `glaner`) étaient muets depuis leur propre sprint et
> bloquaient un invariant **tout-ou-rien** ; et `creuser`/`drainer` n'avaient en
> fait **aucune** fiche, contrairement à ce qu'affirmait le kickoff ⑤.
> Deux tests recalibrés d'un **snapshot** vers un **invariant** (patron du ④ sur
> `test_acquisition_outils`) : nombre de fiches, ids de pages.

### ⑦ Le décor cesse d'être décoratif — `41beea1`
Pont : `tools/simserver/peripherie_route.py` (neuf) — bloc `ceinture` **OPT-IN**
(4 secteurs × 10 champs) + les 6 gestes de secteur. **La mécanique ne fuit pas**
vers la vue (horloges, `densite_avant`, `erosion_signalee`,
`ligne_eau_naturelle` restent côté moteur — les exposer inviterait à les
recalculer en C#, invariant « Godot bête », vérifié par test). `creuser` **n'a
pas été dupliqué** : le routeur l'aiguille sur la **forme du target** (patron
d'`ecraser`). Ceinture posée à l'init pour `full`/`propre` — **pas** pour `smoke`
(fixture du golden) ni pour les bancs thématiques (un banc force UNE condition).
Côté vue : `DecorLayer` **consomme** (`DuPont = false` ⇒ décor d'avant au pixel
près, aucune sentinelle à semer), **cinq retours visuels tous dérivés de l'état**
(clairière, trogne, ligne d'eau, entaille, éboulis — aucune jauge, #5),
`Motif.Friche` en 5ᵉ motif, aulne et saule ajoutés aux silhouettes, clic **hors**
jardin résolu en `cote` (`world/WorldView.Peripherie.cs` — le picking de
`WorldView` n'utilise pas l'input de Godot, les deux domaines sont **disjoints**),
6 gestes kind `'L'` + 3 pictogrammes, banc `bancs/peripherie.py` (4 tuiles
**collées aux bords** — sans contact `plots_de_bord` ne rend rien et on croirait
à un bug). Protocole **0.5.41**. 50/50, `dotnet build` VERT.

## Arbitrage d'orchestration en cours de sprint

**`eco.lisiere` rendu sensible à la DENSITÉ, pas au seul type** (au ④). Le ③
avait indexé le corridor sur le seul **type** de secteur, ce qui tenait tant que
la ceinture était figée ; le ④ la fait bouger, et un corridor **inerte après un
abattage** aurait rendu le geste destructeur creux sur ce flux. Modèle retenu :
le type reste l'**archétype**, la densité en module l'**intensité** — fonction
**affine et monotone croissante** (aucune non-linéarité inventée : elle reste du
côté de l'abri, T1), avec un **socle** `LISIERE_SOCLE = 0.25` qui est
**écologique** et non un garde-fou numérique (une trouée fraîche n'est pas du
béton : il reste la litière, le bois mort, l'ourlet) — et qui garantit en prime
que l'**ordre des archétypes tient**. Seuls les types à strate ligneuse sont
modulés. Mesuré : abattage du bord nord ⇒ corridor **−63 %** aux trois premières
rangées, rien ne bouge loin du bord, et après 30 ans de repousse il revient
**exactement** à sa valeur d'origine (rien n'est épuisable, #4).

## Le golden n'a JAMAIS été re-figé

`57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da` du premier au
dernier commit, **passe `/refactor` incluse**. C'est la prédiction du repérage de
conception qui se vérifie : le golden ne pose **ni maison ni ceinture**, et toute
la mécanique du sprint est **opt-in** (`ceinture is None` ⇒ champs `None` ⇒ termes
sautés ⇒ bit-identique). Chaque tronçon a livré sa **suite de neutralité**
(E, L, X, AC, AH) qui compare les champs **au bit près** avec et sans ceinture, y
compris sur une ceinture **neutre**. Le « re-figeage LARGE » que l'amorce
annonçait a donc été **évité entièrement**.

**Perf** : mesurée au ⑦ sur `full` (seed 11, médiane de 10 ticks, 2 passes
croisées) — **447/483 ms avec ceinture contre 450/512 ms sans : dans le bruit**,
conforme à l'estimation < +2 %. Les caches `geom_key`/`_signature` absorbent une
ceinture quasi statique, exactement comme prévu.

## Passe `/refactor` de fin de sprint — `18b5eb4`

Auto-légère : ne traite que ce que le sprint vient de faire dépasser la bande.
Deux scissions, refactor **PUR** golden-gaté :
`tests/test_peripherie.py` **415 → 30 LDC** (entrée mince) → paquet
`tests/peripherie/` (`harness` + un module par tronçon ①②③, ordre d'exécution et
compteur identiques) ; `sim/encyclopedie_corpus.py` **402 LDC → paquet** par
thème (potager/ligneux/fonctionnelles/concepts/adventices), avec vérification
**programmatique** que `FICHES`/`CONCEPTS` sont égaux **et dans le même ordre**
que l'original — l'ordre fait partie de l'API (`encyclopedie.lister()`). Tous les
fichiers issus des scissions sont 🟢.

## Notes

- **Deux rouges à la recette finale, tous deux PRÉ-EXISTANTS** et vérifiés
  identiques sur l'arbre propre (`git stash -u`) : `test_sim_server` 269/270
  (« le pommier pré-âgé a noué des fruits réels » → 0 fruits @ S52, décalage
  phénologique déjà connu) et `tests/bancs/test_edaphique` 6/7.
- **DETTE** : **D73 → CLOSE** · **D92 → ABSORBÉE** et mesurée · **D93 →
  PÉRIMÉE** (le gating par outil existait déjà, `sim/outils.py` + `GESTE_UNLOCK`,
  D82 — résidu = 1 ligne de tag récompense) · **D94** confirmée par
  l'implémentation (`poro=None` est le marqueur de la branche historique) ·
  **D95** ouverte (rien ne crédite les 4 concepts de carnet neufs — moitié
  interprétative écrite et jamais servie, même cas que `carnivorie`/`maladie`) ·
  **D96** (`test_sim_server` flaky sous charge : le bloc `perf` n'est pas
  neutralisé pour l'égalité « snapshot == état du dernier step ») · **D97**
  (`tests/test_croissance.py` 422 LDC 🔴, pré-existant → `/refactor` ciblé) ·
  **D98** (`encyclopedie_corpus.CONCEPTS`, 5 entrées, importé nulle part —
  apparemment supplanté par `concept_corpus.FICHES_CONCEPT`) · **D99**
  (`eco.lisiere`/`eco.turbulence`/`eco.vent` absents de `get_field` ⇒ pas
  d'overlay F6). **BACKLOG** mis à jour (+ noisetier et prunellier/ronce
  consignés comme **écartés**, décision D-5).

## Reste F5 Nico — aucun bug connu, **que du calibrage**

Le F5 n'a **pas** été simulé : `dotnet build` est vert mais aucun rendu n'a été
observé sur la VM (Godot n'y est pas). Point d'entrée : `init config="peripherie"`
(banc dédié — falaise 9 m au nord · rivière `ligne_eau +40` à l'est · forêt 18 m
en **charme**, qui rejette, au sud · friche à l'ouest ; les 3 outils et les
2 marqueurs d'expérience sont **posés**, pas achetés).

**Le décor**
1. **La falaise mange-t-elle l'écran ?** 52 % des terrains en portent une (① —
   arithmétique de la règle, très au-dessus du plancher ≥ 5 %) **et** sa face
   dessinée est désormais `altitude_relative` (300→1200 cm contre 190/470 cm
   codés en dur). Deux leviers : tirage de conversion côté ①, ou facteur
   d'échelle côté vue.
2. **`DensiteRef = 0.95` / `HauteurRefCm = 2000`** : le décor est globalement
   **plus bas et plus clair** qu'au F10 (une lisière moyenne rend ~79 % des
   arbres à ~60 % de leur taille). Voulu — il dit la vérité du moteur — à juger
   à l'œil.
3. **`Motif.Friche`** : « prairie + ronciers de 2,5 m » est une invention du ⑦
   (le moteur ne donne pas de hauteur à une friche). Hautes herbes ? Genêts ?
4. **`LigneEauPleineCm = 200`** : ±200 cm double/annule la largeur du lit —
   est-ce qu'un barrage se **VOIT** en un geste ?

**Les gestes**
5. **`TRES_ELEVE = 60`** (palier neuf) : sur un plafond de 100, abattre est
   faisable **une fois par recharge**. À arbitrer si le barème doit rester à
   4 paliers.
6. **`LIGNE_EAU_PAS_CM = 30`** sur des bornes (−150, +120) : gorger une berge
   demande 2-3 endiguements. Un barrage se **sent**-il en 1 geste ou en 5 ?
7. **`ENTAILLE_PAS_CM = 150`** : raser une falaise de 8 m = 6 coups de pioche à
   60 de Vigueur. Volontairement lourd (irréversible).
8. **`BOIS_COUPE_PAR_CM = 0.002`** : raser 20 m de front rend ~26 unités de
   litière `bois` sur une tuile. On croule sous le bois, ou c'est dérisoire ?
9. **`OUVRAGE_RUPTURE_ANS = 8`** ≈ 7 h de jeu à 60 s/semaine : assez long pour
   qu'on oublie l'ouvrage, assez court pour que la leçon arrive.
10. **`endiguer`/`deriver` ouverts par `("action","creuser")`** (la bêche n'a pas
    de marqueur d'outil) — si Nico préfère un marqueur `bêche` à l'Atelier,
    c'est 1 entrée + 2 conditions.
11. **Palette** : 6 verbes de plus, dans **aucun slot par défaut** (ils arrivent
    par l'auto-remplissage D2 et le cycle Tab) — la colonne gauche reste-t-elle
    lisible ?

**Les flux**
12. **`LISIERE_SOCLE = 0.25`** : part de l'effet de lisière qui survit à une
    coupe rase. Il fixe **de combien** le corridor tombe (mesuré −63 %).
13. **`EROSION_STRUCTURE = 0.003` / `EROSION_HUMUS = 0.0006`** (calés du même
    ordre que la battance de pluie sur sol nu) et **`EROSION_DENUDATION_MIN =
    0.25`** (en-dessous, une éclaircie est gratuite) : ça se voit assez, ou trop ?
14. **L'ombre de lisière entre de ~7 m dans le jardin en été au sud**, là où la
    table de conception annonçait 0 : l'occulteur est **toute la bande**, donc sa
    face proche est **au bord** du jardin (le kickoff le définissait ainsi, suivi
    au mot — aucune constante de retrait spéculative ajoutée). Si Nico veut
    retrouver la table : une constante `RETRAIT_LISIERE_CM` dans `rect_secteur`.
15. **Le banc démarre semaine 1** (début printemps) : **l'ombre d'hiver de la
    lisière sud, qui est la leçon centrale du ②, ne se voit PAS à cette date.**
    Une entrée dans `BANC_WEEK_DEPART` (~semaine 47) suffit à la constater
    d'emblée.

**Le texte**
16. **Attribution des 4 concepts de carnet** : `eteter → lisiere` est le choix le
    moins évident, `abattre → brise_vent` fait porter au geste la leçon T1. Trois
    lignes si Nico préfère un autre découpage. (Et rien ne les crédite encore →
    **D95**.)
17. **Le saule n'est calibré à la sonde par personne** (`growth_speed`,
    `gravitropism_gain`, `age_curve` = décalque de l'aulne poussé d'un cran) : il
    n'est semé ni au golden ni à un banc, donc rien ne l'exerce. À voir le jour
    où le joueur en plante un — la lettre d'Odette (`lettre_saule_tetard`) rend
    ce cas possible.
18. Les **3 fiches de gestes hors sprint** écrites au ⑥ pour débloquer un
    invariant tout-ou-rien (`pincer`, `arracher`, `glaner`) sont à **relire côté
    éditorial** — annulables sans rien casser d'autre que le compteur du test.
