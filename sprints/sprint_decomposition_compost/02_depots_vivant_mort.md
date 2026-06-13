# Sous-sprint ② — Dépôts vivant & mort : `tailler`→bois, squelette persistant, abscission, écraser-squelette

> **Kickoff autosuffisant (démarrage à froid).** Lire d'abord `00_etat.md`
> (§Acquis ①) et `data/code/CONCEPTION_DECOMPOSITION_COMPOST.md` (§2 surtout).
> ① a posé l'infrastructure parcelles + `deposer_litiere`. ② **alimente** enfin
> les tissus `bois`/`feuille`/`fruit`/`fleur` par les **vrais dépôts** du vivant
> et du mort. Il ne crée **aucun organe-fruit traçable** (③), **aucune
> attraction animale** (④), **aucune structure posable** (⑤).

## Ampleur & risque (à lire avant de coder)
Sous-sprint **GROS** (le plus lourd des 6). Trois phases **dans cet ordre**,
chacune testable ; **A|B est un point de coupe valide** si le budget tokens
serre (commit après A, reprendre B/C en session suivante) :
- **A — Dépôts immédiats** : `tailler`→`bois` ; à la mort, **dépôt des tissus
  mous** (feuille/fruit/herbacé) au lieu du `add_necromass` générique. Pas encore
  de persistance. *(Golden re-figé : la mort dépose d'autres tissus.)*
- **B — Squelette persistant** : la plante morte **reste** dans `tile.plants`
  (drapeau), **fragmente** son bois sur des semaines, **ombre = silhouette nue**.
  *(Golden re-figé : le bois sort lentement + nouvelle ombre dégressive.)*
- **C — Abscission d'automne + écraser-squelette**. *(Golden re-figé : dépôts
  feuille saisonniers.)*

> **Risque #1 = l'ombre du squelette** (phase B). Tout le reste réutilise des
> seams existants ; la silhouette nue est le SEUL mécanisme vraiment neuf et la
> principale cause de dérive golden au-delà des dépôts. Le garder **simple**
> (cf. §B.3).

---

## Acquis ① réutilisés
- `eco.deposer_litiere(r, c, tissu, masse)` — **unique** point de dépôt, fusion
  par tissu. Tissus disponibles : `diffus`/`feuille`/`fleur`/`herbace`/`fruit`/
  `bois` (table `TISSU`, `fields/ecofields.py`). En ① seuls `diffus` (exsudats)
  et `herbace` (nécromasse générique + inject) sont alimentés.
- `eco.add_necromass(r,c,biomass,harvested)` route aujourd'hui vers `herbace`.
  ② le **raffine** (mous vs bois) ou le contourne selon le site.

## Architecture du squelette — la décision centrale (phase B)
**Fait déterminant** : `is_alive` ≡ `health > 0` (`plants/base.py:338`), et
**tous** les passages de l'engine gardent déjà `if not plant.is_alive: continue`
(croissance, compétition, repro, uptake, météo… ~15 sites). Donc **laisser une
plante morte dans `tile.plants` est automatiquement ignoré** par toute la
biologie du vivant. Les SEULS sites qui *agissent* à la mort sont ceux qui font
`add_necromass(...)` **puis** `tile.plants = [p for p in ... if p.is_alive]`
(le filtre de retrait).

→ **Décision** : à la mort, **ne plus retirer** la plante ; la marquer squelette
et la laisser en place. Un **nouveau pass `tick_skeletons`** gère sèche→couchée→
fragmentation et **retire** la plante quand son bois est épuisé. Aucune des
boucles « vivant » ne change (elles skippent déjà sur `is_alive`).

**Deux points qui NE skippent PAS sur `is_alive` et qu'il faut traiter** :
1. **Ombre** (`fields/light.py:195` : `alive = [p for p in plants if p.is_alive]`)
   → un squelette n'ombre pas par défaut. Lui donner une **silhouette nue**
   (§B.3).
2. **Vérifier l'occupation/germination** : la succession doit pouvoir germer
   **sous** un squelette (§2.2 conception). Aujourd'hui la mort libère le plot
   par retrait ; en gardant la plante, s'assurer que le contrôle d'occupation
   (compétition intra-plot, `CONCEPTION_COMPETITION_INTRAPLOT`) filtre bien
   `is_alive` (a priori oui — re-grep au démarrage : `grep -rn "is_alive" sim/`).

---

## Phase A — Dépôts immédiats

### A.1 `tailler` dépose du `bois` (`sim/actions.py:390`)
Aujourd'hui `tailler` appelle `atteindre_segment(plant, seg_id, 1.0)` (écimage
du sous-arbre) **sans rien déposer** — la masse coupée disparaît. Désormais :
calculer la **masse du sous-arbre retiré** et `deposer_litiere(r,c,"bois",masse)`
au plot-foyer de la plante (`floor(x_cm/50), floor(y_cm/50)`, cf. `position`).

> **Seam à ouvrir** : `atteindre_segment` (`sim/growth.py:271`) **ne retourne
> rien** ; `_rebuild` retire le sous-arbre en silence. Deux options (choisir,
> figer) :
> - (a) faire **retourner** à `atteindre_segment`/`_rebuild` la **liste des
>   segments retirés** (propre, mais touche un seam partagé par `ecraser_plante`
>   — vérifier l'appelant : il ignore la valeur de retour, donc compatible).
> - (b) calculer la masse **avant** l'appel via `_subtree(seg_id, _children(...))`
>   (réutilise les helpers privés de growth — couplage, mais zéro changement de
>   signature).
> Préférer **(a)** (le bois doit venir de ce qui a RÉELLEMENT été retiré, collet
> protégé inclus → si rien n'est retiré, rien n'est déposé).

**Proxy de masse d'un segment** : `length_cm` (× un facteur `BOIS_PAR_CM`, knob
à poser ; aligné sur l'esprit de `NECROMASS_PER_CM=0.03`). Diamètre = raffinage
futur (placeholder : longueur seule). Le **gain Vigueur** du joueur reste
**inchangé** (on récupère ET on rend au sol).

`ecraser_plante` (`actions.py:461`) frappe le **même** seam : si l'option (a) est
choisie, il déposera **aussi** du bois sur écimage NET — **cohérent et voulu**
(un coup de pied qui casse une branche la met au sol). Le noter.

### A.2 Mort → dépôt des tissus mous (les ~6 sites de `add_necromass`)
Sites de mort dans `sim/engine.py` (grep `add_necromass` au démarrage ; ~lignes
**159** semis/fonte, **403** sénescence, **492** compétition, **526/543**
fongique/dégâts, **610** annuel, **746** autre dégât) + `actions.py:333/350`
(récolte/déracinage joueur).

En phase A (sans persistance encore) : remplacer le `add_necromass(∝ hauteur)`
générique par un **dépôt de tissus mous** ∝ hauteur : `deposer_litiere` en
`feuille` (caducs/feuillus) ou `herbace` (annuelles/tiges molles) selon la
plante (`plant_class.deciduous` existe, `base.py:429`). Le **bois** de la phase A
reste routé en `herbace` **provisoirement** (la fragmentation lente est la
phase B). Garder `necromass_biomass(p)` comme proxy de masse.

> Garder `add_necromass` comme **helper** mais lui passer le `tissu` (nouveau
> param avec défaut `herbace` → compat) plutôt que dupliquer la logique
> export/BIOMASS_EXPORT à chaque site.

---

## Phase B — Squelette persistant

### B.1 État post-mortem (`plants/base.py`, `PlantInstance`)
Ajouter (defaults → plantes vivantes inchangées, golden de structure intact) :
```python
morte:       bool  = False
stade_mort:  str   = ""        # "" vivant · "seche" debout · "couchee" au sol
bois_restant: float = 0.0      # réservoir de bois à fragmenter
semaines_mort: int  = 0        # compteur sèche→couchée
```
À la mort (les ~6 sites) : au lieu de retirer, **dépose les tissus mous** (A.2)
**et** initialise `morte=True, stade_mort="seche", bois_restant = part bois ∝
hauteur`. **Ne pas** filtrer hors de `tile.plants`.

### B.2 Nouveau pass `tick_skeletons` (engine, après la mort/avant le nettoyage)
Pour chaque plante `morte` :
1. `stade_mort=="seche"` : `semaines_mort += 1` ; si `≥ T_SECHE` → `"couchee"`.
2. Fragmentation : `d = bois_restant × FRAG_RATE × speed_local` (réutiliser la
   modulation microbiome/vers de `tick_decomposition` — facteur identique) ;
   `deposer_litiere(r,c,"bois",d)` ; `bois_restant -= d`.
3. `bois_restant ≈ 0` → **retirer** enfin la plante (`tile.plants` filtré ici,
   sur `morte and bois_restant<ε`, PAS sur `is_alive`).

> Les filtres `tile.plants = [... if p.is_alive]` des sites de mort **doivent
> disparaître** (sinon la plante morte est retirée immédiatement et il n'y a pas
> de squelette). Le **seul** retrait survit dans `tick_skeletons` (bois épuisé).
> **Piège** : bien vérifier qu'aucun `if p.is_alive` requis ailleurs ne casse
> (repro/seedbank lisent `is_alive` → OK, ils skippent le mort).

### B.3 Ombre = silhouette nue (`fields/light.py`) — **le risque #1, garder simple**
Inclure les squelettes dans `infos` (l.198-202) avec une **densité de feuillage
réduite** : un tronc nu projette une ombre **dégressive**, pas la canopée pleine.
Modèle proposé (placeholder, calibrage post-test) :
- `seche` : `foliage_density × SILHOUETTE_SECHE` (ex. 0.3, bois nu + brindilles) ;
- `couchee` : ombre ≈ 0 (au sol).
Réutiliser la géométrie existante (`current_height`, `canopy_radius_at`) ; ne
**rien** ajouter à `LightField` au-delà de la liste source. **Alternative de
repli** (si la dérive golden devient ingérable) : squelette = **ombre nulle**
(comme un caduc en hiver, `base.py:512`) → on perd la silhouette mais ② reste
borné ; le rendu visuel viendra en ⑥. **Trancher et noter dans `00_etat`.**

---

## Phase C — Abscission & écraser-squelette

### C.1 Abscission d'automne (`sim/engine.py`, logique saisonnière)
À l'**automne**, les plantes **vivantes** `deciduous` larguent leur feuillage sur
**1–2 semaines** → `deposer_litiere(r,c,"feuille",masse)` avec `masse ∝ proxy
feuillage` (`foliage_density_at × current_height` ou équivalent). Localiser le
hook « changement de saison »/semaine d'automne (grep `saison`/`"automne"` dans
engine). Persistants : rien. Événement **léger** (un dépôt borné par caduc).

### C.2 Écraser un squelette → au sol (`sim/actions.py:ecraser_plante`)
Si la cible est un **squelette** (`plant.morte and stade_mort=="seche"`) :
forcer `stade_mort="couchee"` **et** accélérer la fragmentation (ex. déposer
tout de suite une fraction de `bois_restant`, ou bump d'un multiplicateur). Pas
de `health` (déjà morte). Même seam/philosophie que l'écrasement du vivant.

---

## Recâblage & constantes (knobs à poser, post-test)
Dans `fields/ecofields.py` (près de la table TISSU / NECROMASS_PER_CM) :
`BOIS_PAR_CM`, `T_SECHE`, `FRAG_RATE`, `SILHOUETTE_SECHE`, fenêtre d'abscission,
part bois vs mous d'une nécromasse (`FRAC_BOIS_MORT`).

## Procédure de re-figeage (maîtrisé, annoncé — comme ①)
1. Coder phase par phase ; après chaque phase lancer le golden.
2. `python3 -m tests.test_golden` → FAIL attendu ; noter l'ancien hash
   (`f75d1c21…` après ①) → nouveau. `python3 -m tests.test_population` re-fige
   aussi (les vers lisent le frais, qui change avec le bois lent).
3. **Déterminisme** : `h1 == h2` (deux runs). Squelettes itérés en **ordre
   stable** (ordre de `tile.plants`, jamais de set/dict non ordonné dans le
   tick). Fragmentation = pur calcul, zéro RNG.
4. Re-capturer (`--capture`), MAJ `00_etat.md` (hashes + cause de dérive par
   phase) + `journal.md`, commit.

## Critères de fin (DoD)
- [ ] `tailler` dépose du `bois` ∝ sous-arbre retiré (gain Vigueur inchangé).
- [ ] Les ~6 sites de mort déposent les **tissus mous** ; plus de retrait
      immédiat ; plante morte conservée et marquée squelette.
- [ ] `tick_skeletons` : sèche→couchée→fragmentation `bois`→retrait final.
- [ ] Ombre de squelette : silhouette nue **ou** nulle (décision notée).
- [ ] Abscission d'automne (caducs → `feuille`) ; `ecraser`-squelette → couchée.
- [ ] Golden + population **re-figés**, `h1 == h2`, dérive expliquée par phase.
- [ ] Suites vertes (mêmes que ①) ; `main.py 30` exit 0.
- [ ] `00_etat.md` + `journal.md` à jour. Commit.

## Pièges identifiés
- **Le filtre de retrait** : retirer les `tile.plants = [... if p.is_alive]` des
  sites de mort est la modif la plus sensible — un oubli = pas de squelette ; un
  retrait mal placé = plante morte qui rejoue la biologie. Centraliser le **seul**
  retrait dans `tick_skeletons`.
- **Ordre des passes** : `tick_skeletons` doit tourner **après** que la mort a
  marqué les squelettes, et la fragmentation alimente la litière **avant**
  `tick_decomposition` du tick suivant (cohérence de cascade — figer l'ordre).
- **`atteindre_segment` partagé** : modifier son retour impacte `tailler` ET
  `ecraser_plante` — vérifier les deux appelants.
- **Double comptage de masse** : la part « mous » + la part « bois » d'une mort
  ne doivent pas dépasser `necromass_biomass(p)` (la hauteur reste le proxy de
  masse TOTALE) — répartir, pas dupliquer.
- **Déterminisme** : squelettes en ordre `tile.plants` ; aucun `set`/`dict` dans
  le chemin du tick.

## Ce que ② NE fait pas (rappel)
Pas d'organe-fruit traçable / `manger` ciblé (③), pas d'attraction animale (④),
pas de bac/pile/gestes composter (⑤), pas de rendu visuel du post-mortem (⑥).
Les fruits/fleurs tombés restent gérés génériquement ici ; le **suivi
par-organe** est ③.
