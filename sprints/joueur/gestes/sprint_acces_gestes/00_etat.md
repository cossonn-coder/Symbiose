# Sprint ACCÈS AUX GESTES — état

> Sprint ① de la refonte de l'accès aux gestes (3 sprints). Conception figée le
> 2026-11-12 : `docs/joueur/gestes/conception_refonte_palette.md` (à lire en entier).
> Suite : `sprint_palette_tiroir` puis `sprint_icones_curseur`.

## But
Rendre **tous** les gestes du moteur atteignables en jeu normal et jouables dans la
vue. Aujourd'hui 20 gestes gatés sur 32 ne s'ouvrent jamais (poule-œuf : la
technique n'est découverte qu'en utilisant le geste qu'elle verrouille) et 10 gestes
n'existent pas dans la vue. Ferme D133.

## Décisions clés (Nico, 2026-11-12)
- On **garde** `GESTE_UNLOCK` ; on **ajoute** `PORTES_TECHNIQUE` : franchir une porte
  DÉCOUVRE la technique (palier 1), ce qui rend vraies les conditions existantes.
- Quatre portes : Atelier, geste de base voisin, observation, courrier.
- Posséder une structure offerte vaut l'avoir posée.
- Trois états : inconnu / pressenti (calculé) / ouvert. Pressenti = silhouette +
  phrase d'ambiance, jamais la piste.
- `FAMILLE_GESTE` (8 familles) vit en Python, exposée au pont.
- Test d'atteignabilité permanent.

## Golden
`b4a921f8…` (`tests/golden_hash.txt`). **INTACT sur les 4 tronçons** : état joueur
opt-in, hooks au-dessus du tick. S'il bouge : fuite dans le tick → annuler, ne
jamais re-figer.

## Tronçons
| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_portes_atteignabilite.md` — table des portes, conditions `stock`/`compte`, test du point fixe | intact | **FAIT** 2026-11-12 |
| ② | `02_atelier_courrier_observations.md` — outils neufs, récompense `technique`, lettres, marqueurs d'observation | intact | **FAIT** 2026-11-12 |
| ③ | `03_pressentis_familles_pont.md` — pressentis + phrases, familles, routes supports/couvertures, snapshot, bump pont | intact | **FAIT** 2026-11-12 (pont **0.6.12**) |
| ④ | `04_vue_minimale_banc.md` — gestes manquants dans `Gestes[]`, banc F5 | intact | **FAIT** 2026-11-12 (build C# vert, F5 attendu) |

## Interdits communs à tous les tronçons
- Ne JAMAIS lancer `tests/test_epaisseur_500ans`.
- Pas de `ps aux` / `pgrep -f` ; `uptime` pour la charge.
- Ne supprimer aucun code existant (macros, anciens tests).
- Aucun appel DeepSeek de routine ; un besoin de fouille = kickoff incomplet → le
  consigner ici.

## Constats d'exécution
### ① (2026-11-12) — golden intact `b4a921f8…`
- `deblocage.py` : formes `stock`/`compte`, `PORTES_TECHNIQUE`, `compter_geste`,
  `VERBES_COMPTES` ; `evaluer_deblocages` découvre d'abord les techniques. 150 LDC →
  pas de module frère `deblocage_tables.py`.
- `DECLENCHEURS` est désormais dérivé des DEUX tables et descend dans les `et`
  (sinon `posseder_greffoir`, cité sous un `et`, n'y était pas). Il contient donc les
  `posseder_*` neufs — sans effet tant que le ② ne les pose pas.
- Pont : `compter_geste` appelé dans `cmd_action` à côté de `marquer_action`. Un
  achat de botte de paille passe aussi par `cmd_action` → la porte `paillage` est
  réévaluée sans toucher `sim/outils.py`.
- **`broyer` est fermé jusqu'au ②** (plus de `maitrise paillage`, broyeur pas encore
  vendu). L'aide de `tools/bancs/automate_demo.py --amorce-maitrise` dit encore
  « paillage ouvre pailler/broyer » : seul `pailler` s'ouvre. Texte non retouché.
- `gestes_comptes` : aucun sérialiseur de save ne liste `actions_faites` ni
  `marqueurs_ecolo` aujourd'hui ; rien à brancher. À revoir quand la save existera.
- `planter_conteneur` est dans `GESTE_UNLOCK` mais pas dans `COUTS` (antérieur au
  sprint) : le test vérifie les deux ensembles.
- Test : `MARQUEURS_PROMIS_PAR_2` (5 marqueurs) à **vider au ②** — le cas `[0]` du
  test échoue dès qu'un de ces marqueurs est vendu, pour forcer le resserrage.
  Événements tenus pour atteignables : `merle_seme`, `grimpante_sans_appui`,
  `lettre_greffe`, `lettre_essaim` — au ② de les poser réellement.
- Suites : atteignabilite 34/34, deblocage 24/24, palette 22/22,
  acquisition_outils 16/16 ; voisines (paillage, automate ②, périphérie ×3,
  progression_geste, vision, bouture) vertes.

### ② (2026-11-12) — golden intact `b4a921f8…`
- **Atelier** : `broyeur`, `pots`, `tuteurs`, `greffoir`, `voile` dans `OUTILS` (coûts
  placeholders 30 à 60). `broyer` s'ouvre donc en jeu. `cmd_atelier` calcule
  `possede` par `outils._possede` pour tous les outils. `AtelierPanel.cs` liste ce
  que le pont envoie : les cinq outils y paraissent sans toucher au C# (libellé = clé
  brute, à habiller au sprint palette).
- **Fiches** : `broyeur`, `pot`, `tuteur`, `greffoir` existaient. Seul le **voile**
  manquait. Le test d'encyclopédie exige fiche ⇔ membre d'`OBJETS_TOUCHES` : `voile`
  a donc rejoint le tuple de `poser_voile` (`sim/actions/couts.py`), ce que le kickoff
  ne prévoyait pas. Effet : état joueur seul (découverte et crédit d'usage du voile).
- **Récompense `technique`** — écart au kickoff : `("technique", objet)` découvre la
  technique ; `("technique", objet, marqueur)` pose SEULEMENT le marqueur et laisse la
  porte décider. Raison : découvrir `greffe` à la lettre ouvrirait `greffer` sans le
  greffoir, contre la conception §3.2 (« lettre ET greffoir »). L'essaim, lui, ouvre
  l'apiculture dans le même appel (sa porte ne lit que la lettre).
- Réévaluation placée dans `sim/quetes.py` (`_reevaluer_gestes`, import local de
  `sim.actions.deblocage`, pas de cycle). Elle FUSIONNE les gestes ouverts dans
  `gestes_debloques_recents` (notification du snapshot) au lieu de l'écraser.
- **Bac d'Odette** : `_offrir_structure` marque `poser_bac` si le bac est réellement
  posé (pas de monde, ou tuile déjà pourvue → pas de marqueur).
- **Lettres** : `lettre_pots_amelie` (sem. 6), `lettre_haricots_rames_gaston` (10),
  `lettre_greffe_augustin` (20, donneur NEUF, ancien pépiniériste),
  `lettre_essaim_bertrand` (24). **À surveiller** : le plafond est de 6 lettres
  actives et `lettre_kiwi_reve` occupe une place pour toujours (cible hors
  catalogue). Sans désir comblé, les lettres de greffe et d'essaim n'arrivent pas ;
  or la greffe n'a QUE la porte « lettre et greffoir ». Atteignable, mais derrière
  d'autres désirs à combler. Non mesuré en jeu.
- **Observations** (`tools/simserver/maitrise_pont.py`, registre
  `MARQUEURS_OBSERVATION`) : `merle_seme` sur l'événement `frugivorie` du merle (ligne
  « fruits pris », pas la ligne « semée sous les perchoirs » qui supposerait un
  perchoir) ; `grimpante_sans_appui` par lecture de l'état après tick : grimpante
  vivante, libre, plus haute que sa hauteur autoportante, d'une espèce déjà survolée
  par le joueur. Balayage arrêté une fois le marqueur posé. Sonde hors monde : haricot,
  lierre et jasmin libres dépassent ce seuil [3 espèces, croissance plein soleil].
  Non vérifié dans une partie réelle (lierre accroché au mur de la maison ?).
- **Test** : `MARQUEURS_PROMIS_PAR_2` retiré ; le cas `[0]` vérifie que tout
  `posseder_*` cité est vendu et que tout événement cité a un poseur. Cas neufs dans
  `tests/test_courrier_enseigne.py` (fichier créé plutôt que d'étendre
  `test_quetes.py`, déjà à 314 LDC) et `test_acquisition_outils.py` (chaîne tuteurs →
  `poser_tuteur` → `palisser` + `poser_perchoir` : D133).
- Aide d'`automate_demo.py` corrigée (« paillage ouvre pailler »).
- `sim/quetes.py` est à 300 LDC, bord de la bande verte.
- **Pour le ③** : l'achat d'un outil ne remonte pas `debloques` dans la réponse de
  `cmd_action` (`acquerir_outil` consomme la liste, antérieur au sprint) ; consigner
  dans `version.py` le changement de sens de `possede` et les récompenses neuves.
- Aucune fouille DeepSeek. Aucun C# touché.

### ③ (2026-11-12) — golden intact `b4a921f8…`, pont **0.6.12**
- **Modules neufs** : `sim/pressentis.py` (table `INDICES_TECHNIQUE`,
  `PHRASE_PRESSENTI`, `gestes_pressentis`, `bloc_pressentis`), `sim/actions/familles.py`
  (`FAMILLES`, `FAMILLE_GESTE`, `BLOC_FAMILLES`), `tools/simserver/supports_route.py`.
  Rien ajouté à `sim/quetes.py` ni à `sim/geste_corpus.py` (353 LDC).
- **Lettre active** : ni condition neuve dans `deblocage`, ni marqueur. Les pressentis
  vivent dans `sim/` au-dessus de `deblocage` et de `quetes`, et lisent
  `Q.quetes_actives` : une lettre active dont la récompense est `("technique", t…)`.
  Deux formes d'indice locales : `("lettre", t)` et `("geste", verbe)`.
  `deblocage` gagne seulement l'alias public `condition_remplie`.
- **Technique d'un geste** : le 1ᵉʳ élément d'`OBJETS_TOUCHES` est fiable sur les 32
  gestes gatés (vérifié par test) ; seul `planter_conteneur` est nommé à la main.
- **Phrases** : 15, une par technique de geste gaté (pas seulement les 8 portes),
  pour qu'aucun pressenti ne parte sans phrase. Toutes à la première personne ;
  le test refuse chiffre, « Atelier », « lettre », tournure de consigne.
- **Écart — forme de `familles`** : `{ordre: [...], gestes: {famille: [verbes]}}` et
  non `{ordre, de: {verbe: famille}}`. Le serveur sérialise en clés triées
  (`sort_keys`) : un dict perdrait l'ordre d'affichage dans la famille.
  Envoyé à chaque snapshot (`SimBridge.Init` ne rend que `world` à la vue).
- **Écart — gating au pont** : le pont n'applique `est_debloque` sur AUCUN geste de
  tuile (choix documenté dans `deblocage.py` : pas de gating dur) ; seuls les gestes
  de paysage le vérifient, dans leur façade. Les routes neuves suivent ce chemin :
  un geste fermé envoyé à la main est exécuté. Le test du pont pose d'ailleurs un
  treillis sans l'avoir ouvert. À trancher par Nico si un refus dur est voulu
  (il toucherait tous les gestes, pas ce tronçon).
- **Routes** : `poser_perchoir` a déménagé dans `supports_route.py` (contrat
  inchangé). `palisser` distingue quatre refus sans coût (pas de plante, pas un
  sarmenteux, déjà attachée, aucun support à portée). `actions.py` : 345 → 335 LDC.
- **Trou connu des indices** : `abattre`, `receper`, `eteter` n'ont aucun indice
  (essartage, taillis, trogne). L'indice « outil vu à l'Atelier » de la conception
  §3.4 n'a pas d'état pour le porter (rien ne note qu'on a ouvert l'Atelier). Ces
  gestes passent d'inconnu à ouvert à l'achat. `entailler` est pressenti dès le
  premier `creuser` (technique `terrassement` découverte à l'usage).
- **À surveiller au F5** : avec l'encyclopédie « amorcée », toute espèce grimpante
  déjà connue fait pressentir le palissage dès l'ouverture ; `couper`/`tailler` sont
  pressentis dès le premier `pincer`. Non mesuré en partie réelle.
- **Taille** : `tools/simserver/serialize.py` est à **398 LDC** (394 avant, +4) : au
  bord du rouge, candidat `/refactor` avant tout ajout.
- **Pour le ④** : la vue lit `player.gestes_pressentis` ([{verbe, phrase}]) et
  `player.familles` ; cibles des verbes neufs dans `version.py` (0.6.12). Aucune
  constante de version n'est vérifiée côté C# (`SimBridge` l'affiche seulement).
- Suites : golden intact ; pressentis 49/49 (neuve) ; sim_server 349/349 (dont 27
  neufs, section 24) ; atteignabilite 36/36 ; deblocage 24/24 ; palette 22/22 ;
  courrier_enseigne 42/42 ; acquisition_outils 32/32 ; merle_seme 18/18 ; quetes
  52/52 ; progression_geste 15/15 ; peripherie_pont, quatre_feuilles verts.
- Aucune fouille DeepSeek. Aucun C# touché (pas de `dotnet build`).

### ④ (2026-11-12) — golden intact `b4a921f8…`, build C# vert (0 avertissement)
- **Vue** : neuf entrées ajoutées en fin de `Gestes[]`, AUCUN kind neuf, donc
  `WorldView.ActionDispatch.cs` (394 LDC) n'est pas touché. Supports `m`, `palisser`
  `p`, couvertures et `poser_ruche` `q`, `recolter_miel` `s` (branche « retourner » :
  on clique la ruche ; `FindStructureIndex` rend la structure du plot, le pont refuse
  si ce n'est pas une ruche). Formes vérifiées contre `supports_route.py` et
  `structures_route.py`, puis jouées par l'oracle.
- **Mulch** : `Natures` = feuilles, paille, brf, aiguilles. Les feuilles sont en TÊTE
  (seul mulch d'un débutant) : la nature par défaut de `pailler` change donc de paille
  à feuilles. Couleur `feuilles` ajoutée à `MulchLayer` (elle tombait sur le repli).
- **Pictogrammes** : un glyphe provisoire par geste neuf (sinon quatre cases
  identiques). `GesteIcon.cs` passe à **312 LDC** (bande 300-400, une seule
  responsabilité ; refait au sprint `icones_curseur`).
- **Atelier, courrier** : rien à corriger, les deux panneaux listent ce que le pont
  envoie (libellé d'outil = clé brute).
- **Banc `acces_gestes`** (`bancs/acces_gestes.py`) : tuile 12×12 au coin sud-est
  (au nord-ouest le toit de la maison la cache à l'écran), départ semaine 24. Deux
  forçages étrangers au déblocage : ceinture (charmaie à l'est) et Vigueur 3000.
  Aucune maîtrise, aucun marqueur, aucun geste posé.
- **Oracle** `tests/bancs/test_acces_gestes.py` : 56/56. Il n'envoie JAMAIS un geste
  fermé (assertion), sinon `bouturer` envoyé à la main s'ouvrirait seul. 46 verbes
  ouverts à la fin (45 entrées de `Gestes[]` + `grelinette`).
- **Écart — porte `grimpante_sans_appui`** : le kickoff prévoyait « une grimpante
  sans appui » sans préciser. Un haricot semé à l'ouverture met 32 semaines à
  dépasser sa hauteur autoportante [seed 42, n=1 run] (la sonde du ② était hors
  monde, plein soleil). Le banc porte donc un JASMIN de trois ans : marqueur posé
  1 semaine après son survol. En jeu réel, cette porte par le haricot est lente.
- **Écart — durées** : « en quelques minutes » ne tient pas pour deux portes.
  Phacélies en fleur (essaim) ~10 semaines, merle ~12 semaines après l'ouverture
  [seed 42, n=1 run]. Turbo conseillé. Les autres portes sont immédiates.
- **Constat F5 important** : les dix cases sont pleines dès l'ouverture (gestes de
  base). Un geste qui s'ouvre n'entre donc dans aucune case et aucun flash ne le
  signale (`FlashGesteDebloque` ne vise qu'un geste en case). On le trouve par clic
  droit sur une case. Vu à la capture. C'est l'objet de `sprint_palette_tiroir`.
- **Banc de vue** `world/WorldView.BancAccesGestes.cs` + option `-A` de
  `tools/capture_vm.sh` (non prévus au kickoff, nécessaires pour la capture
  « après ») : achète des outils par le pont, relève la palette au journal
  `[AccesGestes]`. Captures REGARDÉES : menu du clic droit avant (creuser, drainer,
  glaner) et après achat de tuteurs + voile (+ tuteur, treillis, pergola, voile,
  cloche, ombrière), puis les six pictogrammes en case. NON vus à l'écran :
  pictogrammes de `palisser`, `poser_ruche`, `recolter_miel` ; aucun des neuf gestes
  n'a été CLIQUÉ dans la vue (seul le pont les a exécutés).
- `Basilics` et `tomates` du banc sont des semis : les désirs à récolte (Amélie,
  Odette) ne sont pas comblés vite ; pots et compostage ont leur autre porte.
- Clôture : D133 close côté code (`DETTE.md`), `BACKLOG.md`,
  `docs/joueur/gestes/backlog_gestes.md`, `journal/183_…`, index `journal.md`.
- Suites : golden intact ; banc acces_gestes 56/56 ; sim_server 349/349 ;
  atteignabilite 36/36 ; deblocage 24/24 ; palette 22/22 ; pressentis 49/49 ;
  courrier_enseigne 42/42 ; nucleation 7/7. Aucune fouille DeepSeek.

## §REPRISE
Sprint **CLOS côté code** (①→④). Reste le **F5 de Nico**, puis
`/sprint-auto sprint_palette_tiroir`.

### Recette F5 — banc `acces_gestes`
Au sélecteur de monde, choisir le banc **`acces_gestes`** (catégorie
`acces_gestes`). La tuile est au coin sud-est. Hub de la maison → onglets
**Atelier** et **Courrier**. Un geste ouvert n'entre pas seul dans la barre :
**clic droit sur une case** → le choisir dans le menu. Vigueur 3000 au banc.

Une ligne par porte (quoi faire → quoi voir) :
1. **Départ** → le menu du clic droit ne propose que creuser, drainer, glaner.
2. **Glaner ×3** sur le coin de feuilles mortes (ouest de la tuile) → `poser bac`,
   `poser pile` et `pailler` au menu. Pailler : nature `feuilles` par défaut (N).
3. **Poser un bac, une pile** → composter, retourner, épandre, empiler bois.
4. **Creuser** un plot → endiguer, dériver.
5. **Pincer ×6** une lavande + **planter ×6** → bouturer.
6. **Atelier** : sécateur → couper (puis couper une lavande → tailler) ; broyeur →
   broyer (le pommier mort) ; pots → poser pot, poser bac (puis poser un pot →
   déplacer, planter en pot) ; tuteurs → tuteur, treillis, pergola (puis poser un
   tuteur → palisser, perchoir) ; voile → voile, cloche, ombrière ; hache → abattre ;
   serpe → recéper (puis recéper la forêt de l'est → étêter) ; pioche → entailler.
7. **Courrier** : lancer la saison. Semaine 1 : lettre de Gaston comblée (palissage)
   et d'Augustin comblée ; avec le **greffoir** de l'Atelier → greffer (cerisier
   puis pommier). ~10 semaines (Turbo) : phacélies en fleur → essaim de Bertrand →
   `poser ruche` ; poser une ruche → `récolter miel`.
8. **Observation** : survoler le **jasmin** (nord de la tuile), passer une semaine →
   palissage (si pas déjà ouvert par les tuteurs). ~12 semaines : le merle prend des
   cerises → perchoir (si pas déjà ouvert par un tuteur).
9. **Les neuf gestes neufs à CLIQUER** (jamais cliqués dans la vue) : tuteur,
   treillis, pergola (un point de la tuile) ; palisser (cliquer le jasmin, un tuteur
   à son pied) ; voile, cloche, ombrière (un plot) ; poser ruche (un plot) ; récolter
   miel (cliquer la ruche). Vérifier que chaque objet posé se VOIT.

Points à juger : lisibilité des pictogrammes provisoires ; paillis de feuilles
visible (roux) ; gestes pressentis (non affichés par cette vue, sprint suivant) ;
seuils des portes (R7) ; faut-il un refus dur du pont sur un geste fermé.

Captures VM : `tools/capture_vm.sh -b acces_gestes -w 0 -z 2 -c 1700,1700 -A tuteurs,voile -n 240`
Oracle : `cd data/code && python3 -m tests.bancs.test_acces_gestes`
