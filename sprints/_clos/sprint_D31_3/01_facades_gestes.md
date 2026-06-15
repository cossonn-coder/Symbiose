# Sprint D31.3 — Façades `vigueur_*` + gestes joueur (vie macroscopique, Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico apprend, vient du C/Python
> embarqué, débutant Godot/C#).

## Ce que c'est, en une phrase

D31.1 a créé les 4 champs de population (visuels) ; D31.2 les a **branchés dans la
sim** (re-figeage golden assumé). D31.3 ajoute la **couche joueur** par-dessus :
des **lectures diégétiques** (`vigueur_*`, « la population de coccinelles est
vigoureuse ») et trois **gestes** qui touchent les champs comme **donnée
d'entrée**. **Cette fois le golden NE re-fige PAS** — exactement comme le sprint
Vigueur (D11) : tout est event-driven, au-dessus du tick déterministe. Si le
golden bouge, c'est un **bug** (fuite dans le tick), pas un re-figeage.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_VIE_MACRO.md` — **§4** (façades `vigueur_*` : pures,
   read-only, `qi_local` **trophique**, populations PAS individus), **§5** (le
   tableau des 3 gestes + « un geste = un individu = un quantum »), **§7** (D19 :
   le gain signé de « manger un individu » reste en dette — **hors périmètre**),
   **§8 #3** (le périmètre exact de D31.3), **§9** (tableau : façades + gestes =
   **golden-neutres**).
2. `data/code/CONCEPTION_VIGUEUR.md` — **§1** (le patron façade dérivée
   read-only, la décision structurante), **§3.2** (tableau actions milieu :
   « Favoriser un auxiliaire », « Grelinette », « Biner / bêcher » — lignes
   164-166), **§3.3** (« Écraser un nuisible » ligne 191 : net négatif sec, la
   pression revient), **§5** (discipline golden : le golden écolo ne récolte/n'agit
   jamais → reste intact).
3. `journal.md` — entrées **`2026-06-04 — Sprint impl. D31.2`** (ce que les champs
   nourrissent maintenant + les 2 hash re-figés) et **`… Sprint impl. Vigueur`**
   (le patron couche joueur, `sim/vigueur.py` / `sim/actions.py` /
   `sim/vigueur_plante.py`, golden joueur `tests/test_vigueur.py` 59/59, golden
   écolo jamais re-figé).
4. Code (patrons à copier) :
   - `data/code/sim/vigueur_plante.py` — **le patron de façade** à reproduire
     (`sante`/`maturite`/`qi_local`/`vigueur_plante` + `decrire_vigueur` :
     descripteur qualitatif, philo #5). Lecture pure, zéro écriture.
   - `data/code/sim/actions.py` — paliers de coût (`NUL/FAIBLE/MODERE/ELEVE`,
     `URGENCE_MULT`), primitives `spend`/`gain` (de `sim/vigueur.py`), et surtout
     **`ecraser` (ligne 105)** qui est aujourd'hui **comptabilité Vigueur SEULE**
     (« aucune entité nuisible n'existe encore » — l'aveu à lever).
   - `data/code/fields/population.py` — `PopulationField.at_plot(r,c)`,
     `activite(r,c)`, la constante **`DENSITE_PAR_SPRITE = 0.06`** (= **un
     quantum** = un individu, ligne 76), et `eco.populations[nom]`.
   - `data/code/world/tile.py` — `StakeSlot.add` (ligne 37) / `get_rondelle_count`
     (ligne 76). **Les rondelles sont au niveau TUILE** (pas par plot). Le champ
     auxiliaire lit déjà la rondelle `auxiliaire` via `_stability_grid`
     (`population.py:273`) → c'est le **terme-source d'habitat** persistant.
   - `data/code/fields/grids.py` — `GridField.add(r,c,delta)` (ligne 47) pour
     retirer/ajouter un quantum à un champ.

## Périmètre — façades + 3 gestes (CONCEPTION_VIE_MACRO §8 #3)

### A. Façades `vigueur_*` (lecture diégétique, golden-neutre)

Quatre fonctions **pures read-only** sur les champs, patron `vigueur_plante.py`
mais avec un `qi_local` **trophique** (la `ressource` du champ, §4) au lieu du sol
racinaire. **Populations, pas individus** : la façade lit la **vitalité d'une
population à un endroit** (densité du champ × richesse de sa ressource), pas une
Vigueur par sprite (les sprites sont des échantillons, ils ne portent rien, §4).

```
vigueur_nuisible(r, c, eco)       # f(ravageur[r,c], ressource = feuillage-hôte)
vigueur_auxiliaire(r, c, eco)     # f(auxiliaire[r,c], ressource = ravageur + nectar/habitat)
vigueur_pollinisateur(r, c, eco)  # f(pollinisateur[r,c], ressource = fleurs)
vigueur_ver(r, c, eco)            # f(vers_de_terre[r,c], ressource = microbiome/OM)
```

Réutilise le scalaire d'`activite()` du champ comme proxy de ressource locale (il
mémorise déjà la dernière grille de ressource, `population.py:157`/`activite`) →
**rien à recalculer**. Ajoute un `decrire_vigueur_pop(v)` qualitatif (voix
naturaliste, « population vigoureuse / clairsemée / florissante » — calibrage des
mots post-test). **Aucune écriture, aucun nouvel état.** Loge ça dans un nouveau
module `sim/vigueur_macro.py` (couche qui lit `fields`, miroir de
`vigueur_plante.py`).

### B. Les 3 gestes (event-driven, dans `sim/actions.py`, golden-neutre)

Tous modifient les champs comme **donnée d'entrée** (comme `arroser` écrit
`humidite`), **hors du tick**. Granularité **§5** : un geste = **un quantum**
(`DENSITE_PAR_SPRITE`), pas toute la population du plot.

1. **Favoriser un auxiliaire** (`favoriser_auxiliaire`, nouveau). Coût `MODÉRÉ`
   (action sur le milieu). Effet : ↑ **terme habitat persistant** du champ
   `auxiliaire`. **Défaut sobre proposé** : poser une **rondelle `auxiliaire`**
   (`StakeSlot.add("auxiliaire")`) — déjà lue par `_stability_grid` comme nectar,
   persistante, zéro machinerie neuve. Pédagogie : rien tout de suite, puis
   **semaines plus tard** les auxiliaires s'installent **et restent** → régulation
   émergente (le canal vertueux, pendant d'« écraser »). ⚠ **Point ouvert**
   (rondelle TUILE vs habitat LOCAL) → voir section dédiée plus bas.
2. **Écraser un nuisible** (`ecraser`, **rendre RÉEL** — lever l'aveu de la
   ligne 105). Coût `MODÉRÉ × URGENCE` (inchangé). Effet : **retirer un quantum**
   de `ravageur` au plot ciblé : `eco.populations["ravageur"].add(r, c,
   -DENSITE_PAR_SPRITE)` (clampé ≥ 0 — `GridField.add` borne déjà). **Binaire**
   tout-ou-rien : n'agit que si le coût est intégralement payé (`spend ≥ 1.0`,
   garde le contrat existant). ⚠ **Changement d'interface** : `ecraser` doit
   recevoir `eco` + le plot cible `(r, c)` (le sprite cliqué). Pédagogie : le champ
   **repousse depuis sa ressource** (l'hôte est toujours là) → **la pression
   revient**. Net négatif sec, le raccourci s'use (philo #1), sans sermon.
3. **Fourche-bêche / bêcher** (`becher`, nouveau). Coût `FAIBLE`. Effet : **tue la
   faune du sol** → ↓ `vers_de_terre` local **+** ↓ `microbiome` local (le malus
   de bêchage de `CONCEPTION_VIGUEUR §3.2`, qui n'avait pas encore d'action pour le
   déclencher). **Visuel avant santé** : la chute de `vers_de_terre` fait
   **disparaître les sprites de vers** (feedback immédiat) *avant* la dette
   différée `microbiome → uptake → vigueur`. La **grelinette** (`grelinette`,
   optionnel — voir point ouvert) ne tue **pas** de vers → contraste enseigné à
   l'œil, pas par un texte.

## Hors périmètre (gated — NE PAS faire)

- **Gain signé « manger un individu »** (manger un nuisible → perte de Vigueur) →
  **D19** (`actions.py:manger` reste à la granularité plante). D31 a fourni le
  prérequis (l'entité ciblable) ; D19 fournira la **valeur nutritive signée par
  espèce**.
- **Sprites « vers morts » transitoires / animations** = **rendu Godot** (C#). Le
  Python ne livre que le **contrat** : la baisse de `vers_de_terre` (→ moins de
  sprites vivants échantillonnés). L'animation de mort est côté D31-rendu, pas ici.
- **Bonus d'aération/infiltration de la grelinette** = **D30** (champ
  structure/compaction). Ne l'invente pas ici (cf. point ouvert).
- **Bénéfice complet structure du sol** (D30), prédateurs de sommet (oiseaux),
  calibrage fin (coûts, seuils des descripteurs, quantum) → post-test / dettes.

## Points ouverts — tranche avec le défaut le plus sobre, signale-le

1. **Favoriser : habitat TUILE ou LOCAL ?** Les rondelles sont **tuile-level**
   (uniforme). Poser un « hôtel à insectes » à **un endroit précis** demanderait un
   **champ habitat persistant par plot** (neuf). **Défaut sobre** : rondelle
   `auxiliaire` (tuile, déjà câblée, persistante). Le placement **local** d'habitat
   est un raffinement → le renvoyer (D30/futur) si ça déborde. Ne crée pas de champ
   neuf juste pour cocher la case.
2. **Grelinette : l'implémenter ou pas ?** Sans le **bonus** d'aération (D30), la
   grelinette n'a, côté Python, qu'un effet : **ne pas** détruire la faune (le
   contraste avec le bêchage). **Défaut sobre** : livrer `grelinette` comme le
   **jumeau qui préserve** (no-op sur `vers_de_terre`/`microbiome`, coût `MODÉRÉ`)
   pour ancrer le couple pédagogique dès maintenant ; son bonus d'aération attendra
   D30. Si tu juges que livrer un geste quasi-no-op est prématuré, documente-le et
   laisse `becher` seul (le contraste viendra avec D30). **Tranche et signale.**

## Garde-fous (non négociables)

- **GOLDEN ÉCOLO INTACT — c'est le test du sprint.** Avant *et* après :
  `python3 -m tests.test_golden` doit afficher **`c950f06c…`** (l'état D31.2) — et
  `python3 -m tests.test_population` doit afficher **`b005d9ba…`**. **Les deux
  hash NE bougent PAS.** Les façades sont des lectures pures ; les gestes sont
  event-driven, jamais appelés par le tick (le golden est une succession spontanée
  **sans joueur**). **Si un hash bouge → tu as une fuite dans le tick : corrige,
  ne re-fige pas.** (C'est exactement la discipline du sprint Vigueur, qui n'a
  jamais re-figé `ee79dd66…`.)
- **Façades = lecture seule.** Aucun `add`, aucun nouvel état stocké, aucun budget
  énergétique. Patron `vigueur_plante.py` à la lettre (§1).
- **Gestes = donnée d'entrée hors tick.** Ils écrivent un champ **avant/entre**
  les ticks (comme `arroser`), au travers de la couche `sim/actions.py` (qui
  orchestre `spend`/`gain` + la mutation écologique). Pas de RNG.
- **Déterminisme préservé** : aucun nouveau tirage. Un geste est déclenché par le
  joueur, pas par le hash du tick.
- **Ne jamais jeter/supprimer de code** : la comptabilité actuelle d'`ecraser` est
  **complétée** (on ajoute l'effet réel), pas réécrite à blanc ; garde son contrat
  binaire tout-ou-rien et son `URGENCE_MULT`.
- **Règle de couches** : `plants ← fields ← sim ← engine ← main`. `vigueur_macro`
  lit `fields` (comme `vigueur_plante` lit `fields.ecofields`). Imports absolus,
  lancement depuis `data/code/`.
- **`main.py` doit toujours tourner.**

## Validation comportementale (au-delà des hash inchangés)

- **Façades** : testables sans monde long — sur un `eco` avec densités connues,
  `vigueur_auxiliaire` croît avec la densité du champ et avec sa ressource ;
  `decrire_vigueur_pop` mappe les seuils. Pure → assert direct.
- **Écraser réel** : après `ecraser` sur un plot à densité connue, le champ
  `ravageur` a **exactement un quantum de moins** (et la Vigueur a baissé de
  `MODÉRÉ × URGENCE`) ; **quelques ticks plus tard la densité remonte** depuis sa
  ressource (preuve « la pression revient », philo #1). Échec si Vigueur
  insuffisante (binaire).
- **Favoriser** : poser l'habitat puis ticker N semaines → la densité
  `auxiliaire` du secteur **monte et se maintient** vs un témoin sans habitat
  (preuve « ils s'installent et restent »).
- **Bêcher vs grelinette** : `becher` fait chuter `vers_de_terre` + `microbiome`
  local ; `grelinette` (si livrée) les laisse intacts. Contraste mesurable.
- **Golden joueur** : si tu ajoutes des gestes au filet `tests/test_vigueur.py`
  (ou un nouveau `tests/test_vie_macro_gestes.py`), garde-le **déterministe** ;
  capture un golden joueur seulement si utile (les asserts comportementaux
  ci-dessus suffisent souvent). **N'étends jamais le golden ÉCOLO.**

## Ampleur

Un seul tronçon autosuffisant (façades + 3 gestes + tests). Comparable à D31.2 en
taille mais **sans re-figeage** (plus simple à valider : les hash écolo ne
bougent pas). Si un point ouvert menace de déborder vers un vrai système sol
(D30) ou habitat local neuf, **tranche sobre et signale** — ne pars pas dans D30.

## À la fin

`DETTE.md` (D31 → D31.3 faite ; D19 garde le gain signé ; D30 toujours ouvert pour
l'aération/habitat local) + `journal.md` (entrée : façades + gestes,
**golden écolo `c950f06c…` / champ `b005d9ba…` VÉRIFIÉS INCHANGÉS**, golden joueur
si touché) + `BACKLOG.md` (D31.3 ✅ → **D31 clos côté Python**, reste portage C#
D24). Puis commit. Mémoire `project_status` : prochain après D31 = D12 paliers.
