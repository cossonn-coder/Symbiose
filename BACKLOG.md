# Backlog — SYMBIOSE

> **Index de pointeurs.** Depuis le tronçon ③ du sprint de rangement
> documentaire (2026-07-22), le backlog est **éclaté par thème** sous
> `docs/<type>/<theme>/backlog_<theme>.md` — même convention que
> [`journal.md`](journal.md). Ce fichier ne contient plus d'entrée de sprint :
> il dit où elles vivent. Pour ajouter un sprint au backlog, écrire sa ligne
> dans le fragment de son thème (et créer le fragment si le thème n'en a pas).
>
> Chaque sprint à venir possède un **kickoff autosuffisant** sous
> `sprints/<type>/<theme>/` — les sprints actifs suivent la **même taxonomie**
> que `docs/` depuis le tronçon ⑤ (cf. `docs/ARBORESCENCE.md` §7). À l'ouverture
> d'une nouvelle session, donner à Claude l'instruction « lis
> `sprints/<type>/<theme>/sprint_X/00_etat.md` » suffit à reprendre sans le
> contexte de la session précédente.
>
> Dette technique → [`DETTE.md`](DETTE.md) · Journal → [`journal.md`](journal.md)
> · Carte de la documentation → [`docs/ARBORESCENCE.md`](docs/ARBORESCENCE.md)

## Sprint en cours

**Sprint FLUIDITÉ AN 2 (D114 recadrée) CLOS le 2026-10-23** (`/sprint-auto`, ①→⑤, golden `fecccded…` jamais re-figé, pont 0.5.57) : tick an 2 −21,8 % [n=3+3 runs entrelacés, VM], réponse −37 %, cadence banc E 1 s/sem 7,5 → 3,0-3,75 s/sem [n=8 runs, VM] ; cible PC ≤ 1,5 s/sem **non tenue sur VM**, à trancher par **3 rapports PC** (protocole `sprints/perf/fluidite/sprint_fluidite_an2/00_etat.md` §F5) ; D114 close → [D116](DETTE.md) (poste restant). F5 Nico de nouveau possible. **Prochain = 2, sprint B vue (D112) → `/conception`.** **File priorisée validée par Nico le 2026-10-22 (retour F5), à faire DANS L'ORDRE :**

1. ~~**Sprint A « le sol qui respire »**~~ CLOS 2026-10-23 (moteur, [D111](DETTE.md)) → `/conception` : bilan hydrique (le sol
   se dessèche), champignons (bois mort au sol, fructification la semaine après la pluie, ~10 espèces
   comestibles / vénéneuses / psychédéliques avec leurs voix), nectar par espèce. Puis re-mesurer D110 (g).
1bis. ~~**URGENT — perf du tick**~~ CLOS 2026-10-23 (sprint FLUIDITÉ AN 2, D114 close → [D116](DETTE.md) : rapports PC à fournir) ; **rapports PC reçus le 2026-10-26** : 3,33-3,75 s/sem [n=3 runs, PC], cible recadrée à ≤ 2 s/sem → `/conception` D116 + lisière D112 (c)(j). **CONÇU le 2026-10-26** → sprint `sprints/perf/fluidite/sprint_fluidite_pc/` (4 tronçons : banc 3 phases + instruments, bug F10, lisière DA SNES ×2), prêt pour `/sprint-auto sprint_fluidite_pc` ; puis 1 run PC → 2ᵉ `/conception D116` (leviers). **Sprint CLOS le 2026-10-26** (①→④, golden intact `fecccded…`, pont 0.5.58) : banc 3 phases + instruments, bug F10 tracé, lisière DA SNES complète ; **attend le run PC de Nico** (protocole `00_etat.md` §F5) → 2ᵉ `/conception D116`. **Run PC reçu + 2ᵉ `/conception D116` FIGÉE le 2026-10-26** → sprint `sprints/perf/fluidite/sprint_fluidite_pc_leviers/` (5 tronçons, golden intact : outil à-coup de zoom, butineurs/pollen en lot, décor et plantes prêts par palier, pont delta 0.6.0, lisière côté caméra devant + bilan) — **prochain = `/sprint-auto sprint_fluidite_pc_leviers`**, puis 1 run PC → 3ᵉ temps D116 (moteur si 2 s/sem non tenu). Retours visuels hors sprint inscrits en D112 (k)(l)(m). **Sprint LEVIERS CLOS le 2026-10-26** (①→⑤, golden intact `fecccded…`, pont 0.6.0) : outil à-coup de zoom (touche Z), butineurs/pollen en lot, décor/plantes prêts par palier, pont delta, lisière côté caméra devant le jardin ; VM phase A 2,80 → 2,10 s/sem, B 1,67 → 1,32 s/sem [n=1 run chacun, VM] — **attend le run PC de Nico** (protocole `sprints/perf/fluidite/sprint_fluidite_pc_leviers/00_etat.md` §F5) → 3ᵉ temps D116 (moteur si 2 s/sem non tenu), puis D112 vue. **Run PC reçu le 2026-10-29 → D116 CLOSE par Nico** (2,23-2,86 s/sem [n=1 run, PC], jugé suffisant pour tester ; archivée lot I de `DETTE_ARCHIVE.md`). **Prochain = 2, D112 vue → `/conception`.** **Run PC reçu le 2026-10-27** (A 2,78 s/sem [n=1 run, PC], cible non tenue) → **sprint PARTAGE (3ᵉ temps D116) CLOS côté code le 2026-10-28** (①→④, golden intact `fecccded…`, pont 0.6.0) : GC gelé, `_snapshot` par segment, régulateur 15 FPS en retard, banc de partage, instruments GPU au rapport Z ; VM A 2,10 → 2,01 s/sem [n=1 run chacun, VM] — **attend UN run PC** (protocole + règles de lecture `sprints/perf/fluidite/sprint_fluidite_pc_partage/00_etat.md` §4), puis D112 vue.
2. **Sprint B « ce qui est cassé à l'écran »** (vue, [D112](DETTE.md)) : bêtes et carpophores non dessinés,
   maison en verre, périphérie qui exige F10, bugs de la heatmap du vent + vent en tête de F6, jauges Maj+F3,
   F11 « spray ».
   **CONÇU le 2026-10-29** (`/conception D112`, périmètre = tout D112 + brief DA 16 bits de Nico) → sprint
   `sprints/rendu/pixelart/sprint_casse_ecran/` (7 tronçons, golden intact : charte + banc de mesure, défauts,
   palette indexée + éclat côté soleil, paliers hauts dans la même grammaire, faune en icônes, lisière animée,
   bilan) — **prochain = `/sprint-auto sprint_casse_ecran`**. Nuit → [D117](DETTE.md).
   **Sprint CLOS côté code le 2026-10-30** (①→⑦, golden intact `fecccded…`, pont 0.6.1) — **attend le F5 de Nico**
   (protocole `sprints/rendu/pixelart/sprint_casse_ecran/00_etat.md` §F5) ; restes (o)→(s) en [D112](DETTE.md), dont
   à-coups de zoom +20 % [VM] à confirmer au PC.
   **F5 de Nico le 2026-10-30 → D112 FERMÉE** (archive lot J). Retours répartis en 3 dettes ouvertes en échange de
   D112/D99/D110 : [D118](DETTE.md) DA partout + **fiche morphologique par espèce → sprite** + rivière Est animée + perf
   ×32 (7 FPS) et à-coups ; [D119](DETTE.md) faune (densités réelles : le hérisson est un visiteur, ~0,01 individu
   attendu sur 400 m² ; bêtes qui s'activent) ; [D120](DETTE.md) monde `full` (tout a faim, carence K, mare au NE).
   **Prochain = choix de Nico** entre D120 (moteur, rapide), D118 (A) (conception morphologique, gros) et D119.
   **D120 CONÇUE le 2026-10-30** → `sprints/champs/sol/sprint_sol_nourricier/` (5 tronçons) — **code CLOS le 2026-10-30 (golden `4c696821…`), F5 Nico reçu → D120 FERMÉE**, retours mare → **D121** → `sprints/champs/eau/sprint_mare_vivante/` **code CLOS + F5 validé le 2026-10-30 → D121 FERMÉE** ; **D122 calendrier** (deux conventions de saison dans le moteur, ~11 sem. de décalage) **CONÇUE le 2026-10-30** → `sprints/champs/climat/sprint_calendrier_unique/` (4 tronçons : mesure → décalage climat → recalibrage → vue) **code CLOS le 2026-10-30** (golden `bfe6f889…`) **F5 validé le 2026-11-02 → D122 FERMÉE**, retours → **D123** (automne invisible, à concevoir) + **D119 (c)** (butineurs dès l'an 1) ; **D123 CONÇUE le 2026-11-02** → `sprints/rendu/ambiance/sprint_automne_visible/` (6 tronçons, avec les arbres de D118) **code CLOS le 2026-11-02** (golden `ac48b170…`), **F5 validé le 2026-11-02 → D123 FERMÉE**, retour → **D124** (branches des arbres de lisière en hiver, marguerites en quadrillage) **CONÇUE le 2026-11-02** → `sprints/rendu/ambiance/sprint_lisiere_nue/` (3 tronçons) **code CLOS le 2026-11-02** (golden `ac48b170…`, pont 0.6.4), **F5 validé le 2026-11-02 → D124 FERMÉE**, retours → **D125 FERMÉE le 2026-11-02** (brume, zoom, neige) → **D126 trèfle dominant CONÇUE le 2026-11-02** → `sprints/vegetal/catalogue/sprint_trefle_dominant/` (4 tronçons) **code CLOS le 2026-11-04** (golden `a10b7225…`, pont 0.6.5), **F5 validé le 2026-11-04 → D126 FERMÉE**, reste → **D127** (pires ticks au PC, à trancher au prochain rapport C, pont 0.6.6) ; puis le reste de D118 (**formes des plantes CONÇUES le 2026-11-04** → `sprints/rendu/pixelart/sprint_formes_plantes/`, 6 tronçons, golden intact visé, prochain = `/sprint-auto sprint_formes_plantes`), puis D119. **À-coups de tick notés** (pire tick 10,2 s en s67 contre 4,5 s en s72 à plantes égales [n=1 run, PC]) : Nico, « ça gène oui mais pas au point que ça soit injouable », pas de sprint pour l'instant.
   **`sprint_formes_plantes` CLOS côté code le 2026-11-05** (reste de D118 (A), golden `a10b7225…`, pont 0.6.8) : F5 attendu ; D118 réduite. **Prochain = D119 après F5.**
   **`sprint_houppier` CLOS côté code le 2026-11-05** (①→⑤, golden `a10b7225…`) : F5 attendu, §F5 de son `00_etat.md` ; D118 réduite. **Prochain = D119 après F5.**
   **D129 CONÇUE le 2026-11-05** → `sprints/vegetal/croissance/sprint_verger_vivant/` (4 tronçons : bourgeons dormants, floraison réaliste, fruits par cohorte, vue fleurs et fruits ; golden intact attendu). **Code CLOS le 2026-11-06** (①→④, golden `a10b7225…`, pont 0.6.9) : F5 attendu, cf. `00_etat.md` §F5.
   **D127 outillage des runs longs CONÇU le 2026-11-06** → `sprints/perf/run_eternel/sprint_chronique_especes/` (4 tronçons, golden intact : causes de mort lues au carnet, chronique des espèces côté serveur, outil sans écran + run `verger_mur` 200 ans sur la VM, section du rapport C) — **CLOS le 2026-11-06** (①→④, golden `a10b7225…` intact, pont 0.6.10, F5 rapport C attendu) ; reste dans D127 : relève des ligneux morte à l'ombre (à concevoir), pires ticks PC.
   **D130 relève des ligneux CONÇUE le 2026-11-06** → `sprints/vegetal/regeneration/sprint_releve_ligneuse/` (5 tronçons, golden inchangé attendu : banque de semis, pose sous la couronne, figuier réaliste à rejets, mesure 200 ans `verger_mur`, vue). **Suivant : D42 dispersion animale** (merle, geai), décision Nico.
   **Frein des rejets du figuier (reliquat D130) CONÇU le 2026-11-09** → `sprints/vegetal/regeneration/sprint_frein_rejets_figuier/` (5 tronçons, golden inchangé attendu : pas de clonage en hiver, rejets de souche à la mort, puis après une perte de couronne, voix + mesure 200 ans, vue Godot qui absorbe le ⑤ de la relève). **CLOS côté code le 2026-11-09** (①→⑤, golden `a10b7225…` intact, pont inchangé, F5 attendu) ; sprint relève CLOS par absorption ; **F5 validé le 2026-11-09, D130 fermée** (lot Q de `DETTE_ARCHIVE.md` ; extinction du figuier et du pommier vers l'an 175 acceptée, cohérente avec le modèle). Puis D42. D131 (gel des rameaux) ouverte.
   **D42 zoochorie CONÇUE le 2026-11-09** → `sprints/faune/vie_macro/sprint_zoochorie/` (8 tronçons : grain sauvage, chute unifiée + glandée + chêne/hêtre fruitiers, noisetier, merle + perchoir, geai + écureuil + ceinture, mulot (golden re-figé annoncé), voix + mesure 200 ans + banc `nucleation`, vue Godot). Prêt pour `/sprint-auto sprint_zoochorie`. **CLOS côté code le 2026-11-12** (①→⑧, golden `b4a921f8…`) : F5 attendu sur le banc `nucleation` (§REPRISE du `00_etat.md`) ; D132 (relève du verger), D133 (perchoir jamais ouvert en jeu), D134 (reliquats §7) ouvertes.
   **`sprint_houppier` CONÇU le 2026-11-05** → `sprints/rendu/pixelart/sprint_houppier/` (5 tronçons, golden intact attendu) : arbres denses, grimpantes sans fin de pousse, fruits des arbres. Passe avant D119 (décision Nico).
   **REFONTE DE L'ACCÈS AUX GESTES CONÇUE le 2026-11-12** (D133 + D118 (b)-(e)) → `docs/joueur/gestes/conception_refonte_palette.md`, trois sprints sous `sprints/joueur/gestes/` : `sprint_acces_gestes` (4 tronçons, ferme D133) → `sprint_palette_tiroir` (3) → `sprint_icones_curseur` (4) ; golden intact. **`sprint_acces_gestes` CLOS côté code le 2026-11-12** (①→④, golden intact, pont 0.6.12, banc `acces_gestes`, F5 attendu). **`sprint_palette_tiroir` CLOS côté code le 2026-11-13** (①→③, golden intact, pont 0.6.13 : tiroir par familles, réglages cliquables, silhouettes des pressentis, Ctrl+molette, D118 (b)(c) ; recette F5 dans son `00_etat.md`). **`sprint_icones_curseur` CLOS côté code le 2026-11-13** (①→④, golden intact, pure vue : 46 icônes dans la palette maître, curseur à l'icône du geste, animations d'exécution et de refus, D118 (d)(e)). **Refonte close côté code ; prochain = F5 de Nico sur les trois sprints** (recettes dans leurs `00_etat.md`). **F5 reçu le 2026-11-13 → D133 close, retours en D136. GESTES LISIBLES CONÇU le 2026-11-13** (D136 (a)-(f)) → `sprints/joueur/gestes/sprint_gestes_lisibles/` (6 tronçons, golden intact) — **`sprint_gestes_lisibles` CLOS côté code le 2026-11-13** (①→⑥, golden intact, pont 0.6.16, banc `gestes_lisibles` + mode testeur touche B ; F5 attendu, recette dans son `00_etat.md`), puis, dans l'ordre, `/conception` **outils_atelier** (tous les outils à trouver, fabriquer, réparer : mini-jeu visuel) et `/conception` **automate_intention** (un automate qui joue pour la diversité, la récolte, la luxuriance). Restent : D136 (g) structures en volume, (h) paysage après la rivière, D137 fruits récoltés.
3. **À concevoir ensuite** : rosace des vents (objet à débloquer à l'atelier : direction + force) ;
   refonte esthétique de la périphérie (falaise / rivière / forêt sans continuité) ; zooms forts trop loin
   de la forme réelle des feuilles.

Fait hors sprint le 2026-10-22 : interrupteur **« Vigueur infinie (test) »** dans Paramètres, **ON par
défaut** pendant la phase de test (pont 0.5.49) — ⚠️ le repasser à OFF (`_vigueurInfinie` dans
`world/WorldView.Parametres.cs`) avant toute distribution (tranche 7 packaging).

Dernier sprint clos : **FLUIDITÉ AN 2** (ci-dessus, journal [`158`](journal/158_2026-10-23_sprint-fluidite-an2-CLOS.md)).

Précédent : **INFO-BULLE DU VIVANT** — **CLOS le 2026-10-22** (`/sprint-auto` ①→③, golden intact
`22768f33…`, pont 0.5.48) : bêtes et champignons nommés après observation en 3 saisons, rôle + abondance +
nourriture, seuil de visibilité des symptômes mesuré, voix « plante saine », Maj+F3 technique. **Reste F5 Nico**
(procédure `sprints/narration/semiologie/sprint_infobulle_vivant/00_etat.md` §F5). Journal :
[`154`](journal/154_2026-10-22_sprint-infobulle-vivant-CLOS.md).

Précédent : **PLANTE ASSEMBLÉE** — **CLOS le 2026-10-20** (`/sprint-auto` ①→⑦, golden intact
`22768f33…`, pont 0.5.46) : Decor/couvre-sol/maison en maillage, plantes en pages d'atlas communes (×4 VM
2 013 → 111 draw calls [VM, n=1]), banc accéléré Maj+E, kit d'éléments + plante assemblée à ×0,5/×1/×2,
corpus des signes + info-bulle 2 niveaux + Maj+F3 technique + onglet Signes. **Reste F5 Nico** (procédure PC
E + Maj+E, 3 questions de ressenti) et reliquats D110. Journal : [`153`](journal/153_2026-10-20_sprint-plante-assemblee-CLOS.md).

Précédent : **PERF VUE** — **CLOS le 2026-10-19** (`/sprint-auto` ①→⑤, golden intact `22768f33…`) :
banc E (touche E au F5), vie macro en présence (pont 0.5.45, fuite corrigée), ombres en un
maillage, à-coups GC/cuisson/priorité serveur. **PC de Nico : ×4 = 32,5 FPS** (avant 1-3), 60 FPS raté —
reste le seul rendu CPU (~2 000 draw calls, ~14 µs chacun). Doc : [`conception_perf_vue.md`](docs/perf/lod/conception_perf_vue.md) ;
journal [151](journal/151_2026-10-19_sprint-perf-vue-CLOS.md). **Ensuite : sprint « plante
assemblée »** (kit de sprites d'éléments réutilisables, silhouettes par palier au lieu de blobs,
pixels plus fins ; absorbe D109 d/e/f : draw calls ≲ 1 000 à ×4, chute à 5 FPS en accéléré, légende F1 coupée) + **légende des signes** (carnet = observé, encyclopédie = appris, info-bulle technique au survol plantes et animaux) — conçu (cf. ci-dessus).

Précédent : **RENDU VISIBLE (D106)** — **CLOS le 2026-10-16** (T1→T7, golden intact `22768f33…`) :
sol en un maillage par tuile · survol paresseux · marge + semaine paresseuse hors
champ · paliers ×0,5 → ×32 + tapis par plot · planche des paliers (touche **L**).
Reste **F5 Nico** (critère D1 : 30 FPS ×0,5-×2, 60 FPS ≥ ×4 sur son PC). Bilan :
`sprints/perf/lod/sprint_rendu_visible/00_etat.md`. Reliquats → D109.

Précédent : **JARDIN VIVANT (sprint A rendu)** — CLOS le 2026-10-15 (T0→T5) ; reste
F5 Nico (« le jardin est-il beau et vivant ? »). Doc :
[`conception_jardin_vivant.md`](docs/rendu/pixelart/conception_jardin_vivant.md).
**Prochain : sprint B** (faune D44 + ses paliers de zoom, champignons, fumée de
cheminée, eau) à concevoir (`/conception`) ; D108 états visuels du sol à concevoir.

Dernier sprint clos : **PÉRIPHÉRIE — le jardin n'est pas une île** (D73,
2026-07-26, `/sprint-auto` ①→⑦ + passe `/refactor`) — la périphérie cesse d'être
un décor : **ceinture de 4 secteurs cardinaux en vérité Python**
(`fields/peripherie.py`, **D92 refermée** — 4 côtés identiques 96,0 % → **2,7 %**,
falaise 0 % → **52,0 %** sur 300 000 seeds), **cinq flux entrants** (ombre de
lisière · abri poreux + champ neuf `eco.turbulence` · pluie de graines · nappe de
berge en condition aux limites · corridor `eco.lisiere` + `lisiere_w` par guilde),
**sept gestes** de paysage (`abattre`/`receper`/`eteter` gatés hache/serpe,
`endiguer`/`deriver`/`entailler` + `creuser` étendu au secteur) avec asymétrie de
réversibilité (trogne 5 ans · taillis 10 · canopée 30 · entaille **jamais** ·
ouvrage rompt à 8), bois rendu en **parcelles de litière `bois`** aux plots du
bord, érosion sur `structure_sol`/`om_stable`, **saule** au catalogue avec ses
5 voix, et `DecorLayer` qui **CONSOMME** le snapshot (couture D58·T4 consommée,
clic hors jardin → `cote`, protocole **0.5.41**) ;
`sprints/champs/peripherie/sprint_peripherie/00_etat.md` (golden `57c166d8…`
**INCHANGÉ du premier au dernier tronçon** — ceinture opt-in, aucun re-figeage ;
`dotnet build` vert ; perf dans le bruit ; reste **F5 Nico**, 6+6 points de
calibrage). **D73 CLOSE**, D92 absorbée, D93 périmée, D94 confirmée,
**D95→D99 ouvertes**.

Sprint clos précédent : **système de quêtes** (D79, 2026-07-24, `/sprint-auto`
①→⑤) — module MOTEUR joueur neuf `sim/quetes.py` (opt-in, conditions cumulées par
hook geste + conditions d'état sur snapshot hors tick, déclenchement déterministe
par palier/saison, plafond 6) + corpus de **lettres anonymes** `sim/quetes_corpus.py`
(voix épistolaire, progression diégétique #5) + récompenses (simples + rares :
vivace déjà enracinée par vraie croissance, structure gratuite ; outil différé
→ **D93**) + pont `courrier` + panneau C# `CourrierPanel` au hub + banc F5
`bancs/courrier.py` ; `sprints/joueur/automate/sprint_quetes/00_etat.md`
(golden INTACT `57c166d8…` de bout en bout, `dotnet build` vert, pont 0.5.40,
`test_quetes` 52/52, reste F5 Nico). **D79 CLOSE**.

(Sprints clos plus anciens : voir [`journal.md`](journal.md) — mémoire d'inoculum
du sol D10, migration des arbres D91, lisibilité du décor D83…)

## Backlog par thème

| Thème | Fragment |
|---|---|
| `champs/climat` | [climat](docs/champs/climat/backlog_climat.md) |
| `champs/eau` | [eau](docs/champs/eau/backlog_eau.md) |
| `champs/lumiere` | [lumière](docs/champs/lumiere/backlog_lumiere.md) |
| `champs/peripherie` | [périphérie](docs/champs/peripherie/backlog_peripherie.md) |
| `champs/sol` | [sol](docs/champs/sol/backlog_sol.md) |
| `faune/mycelium` | [mycélium](docs/faune/mycelium/backlog_mycelium.md) |
| `faune/pollinisation` | [pollinisation](docs/faune/pollinisation/backlog_pollinisation.md) |
| `faune/trophique` | [réseau trophique](docs/faune/trophique/backlog_trophique.md) |
| `faune/vie_macro` | [vie macroscopique](docs/faune/vie_macro/backlog_vie_macro.md) |
| `joueur/automate` | [jardinier automate](docs/joueur/automate/backlog_automate.md) |
| `joueur/gestes` | [gestes](docs/joueur/gestes/backlog_gestes.md) |
| `joueur/interface` | [fenêtrage UI](docs/joueur/interface/backlog_interface.md) |
| `joueur/maitrise` | [maîtrise](docs/joueur/maitrise/backlog_maitrise.md) |
| `joueur/outils` | [outils & conteneurs](docs/joueur/outils/backlog_outils.md) |
| `joueur/vigueur` | [Vigueur](docs/joueur/vigueur/backlog_vigueur.md) |
| `meta` | [transverse projet & portage C#](docs/meta/backlog_meta.md) |
| `meta/calibrage` | [calibrage global & bancs d'essai](docs/meta/calibrage/backlog_calibrage.md) |
| `narration/voix` | [voix narratives](docs/narration/voix/backlog_voix.md) |
| `perf/lod` | [LOD](docs/perf/lod/backlog_lod.md) |
| `perf/run_eternel` | [run éternel](docs/perf/run_eternel/backlog_run_eternel.md) |
| `perf/scatter` | [scatter](docs/perf/scatter/backlog_scatter.md) |
| `rendu/ambiance` | [ambiance](docs/rendu/ambiance/backlog_ambiance.md) |
| `rendu/spatial` | [modèle spatial & vue](docs/rendu/spatial/backlog_spatial.md) |
| `vegetal/allelopathie` | [allélopathie](docs/vegetal/allelopathie/backlog_allelopathie.md) |
| `vegetal/catalogue` | [catalogue](docs/vegetal/catalogue/backlog_catalogue.md) |
| `vegetal/croissance` | [croissance](docs/vegetal/croissance/backlog_croissance.md) |
| `vegetal/floraison` | [floraison](docs/vegetal/floraison/backlog_floraison.md) |
| `vegetal/genetique` | [génétique](docs/vegetal/genetique/backlog_genetique.md) |
| `vegetal/grimpantes` | [grimpantes & luxuriance](docs/vegetal/grimpantes/backlog_grimpantes.md) |
| `vegetal/sante` | [santé](docs/vegetal/sante/backlog_sante.md) |
| `champs/sol` | [pistes de génération de terrain](docs/champs/sol/backlog_generation_terrain.md) |
| `rendu/pixelart` | [pistes rendu pixel-art](docs/rendu/pixelart/backlog_pixelart.md) |
| `meta` | [archives + idées longue traîne](docs/meta/backlog_historique.md) |

## Kickoffs de dette dormante — `sprints/dette_kickoffs/`

> Écrits le 2026-06-06 : **un kickoff autosuffisant par dette sans sprint** (les
> dettes C# ont déjà les leurs : sprint_1/2/3/4). Carte + ordre recommandé + choix
> de design à trancher dans **`sprints/dette_kickoffs/00_index.md`**.

| Dette | Kickoff |
|---|---|
| D13 — Magazine de botanique | `sprints/dette_kickoffs/D13_magazine_botanique.md` |
| D14 — Carnet auto | `sprints/dette_kickoffs/D14_carnet_auto.md` |
| D15 — Extension du terrain par maîtrise | `sprints/dette_kickoffs/D15_extension_terrain.md` |
| D12.2 — Table palier→déblocage (après D13/D14/D15) | `sprints/dette_kickoffs/D12_2_table_deblocage.md` |
| D18 — Pages secrètes | `sprints/dette_kickoffs/D18_pages_secretes.md` |
| D19 — Organes comestibles (manger) | `sprints/dette_kickoffs/D19_organes_comestibles.md` |
| D23 — Catalogue d'arbres pérennes étendu | `sprints/dette_kickoffs/D23_catalogue_arbres.md` |
| D26 — Diversification écologique | `sprints/dette_kickoffs/D26_diversification_ecologique.md` |
| D30 — Champ structure/compaction du sol | `sprints/dette_kickoffs/D30_structure_compaction_sol.md` |
| D32 — Optimisation du LightField (perf) | `sprints/dette_kickoffs/D32_optim_lightfield.md` |
