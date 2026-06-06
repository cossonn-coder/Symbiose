# Dette D23 — Catalogue d'arbres pérennes étendu

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. Ampleur **petite** (surtout des données + calibrage
> d'allure). ⚠️ **Hérite de la décision class-based vs data-driven de D26** — si tu
> prévois D26, fais-le avant (ou en même temps).

## Ce que c'est, en une phrase
Ajouter les **arbres pérennes manquants** au catalogue (poirier, prunier,
châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier, érable…) — différés au
moment de la conception comme « post-validation du squelette pérenne » (DETTE.md
D23), squelette désormais **validé** (5 arbres tournent depuis le Sprint éclairement).

## L'état du moteur aujourd'hui (vérifié)
- **Squelette pérenne validé** : `plants/perennials.py` — `PerennialWoody(PlantBase)`
  (courbe d'âge `age_curve = [(age_years, height_cm, canopy_radius_cm), …]`,
  `longevity_years`, `foliage_density` saisonnière, caduc nu l'hiver). 5 arbres
  calibrés : `Fig` (80 ans), `AppleTree` (70), `CherryTree` (60), `WalnutTree` (200),
  `OakTree` (500). Chacun = une classe avec son `age_curve` + ses défauts de gènes.
- **Inscription** : `plants/catalogue.py::PERENNIAL_CATALOGUE` (dict clé → classe).
- **Compat repro** : `genetics.species_compatible` = même `family` → un 2ᵉ Prunus
  (prunier à côté du cerisier) sera **interfécond** par construction.
- **⚠️ Croissance procédurale (D29)** : `AppleTree` est en cours de **migration
  procédurale** (tronçon Croissance·3bis, `procedural_growth=True`, override
  `PerennialWoody` résolu). Les **autres** arbres restent sur `age_curve`. Tout nouvel
  arbre peut donc **soit** rester `age_curve` (simple), **soit** naître procédural (si
  3bis est fait et que tu veux la cohérence). → cf. choix ci-dessous.

## Ce qui est déjà tranché (ne pas re-débattre)
- Squelette pérenne = **bon** (5 arbres tournent 500 ans sans crash).
- Les arbres existants couvrent déjà **3 strates** (jardin / intermédiaire / lisière).
- Compat reproductive familiale acquise.

## 🔵 Choix de design à trancher
### Choix 1 — Quelles espèces, pour quels rôles de strate/écologie ?
**Sujet hors ton expertise** (botanique) → livrable = un **tableau éditorial à
relire**, pas une décision dans le vide. Esquisse de candidats par rôle (à valider) :
- **Vergers / fruitiers** (famille Rosaceae, déjà ouverte) : **poirier** (Pyrus),
  **prunier** (Prunus, interfécond avec le cerisier).
- **Grands forestiers / lisière** : **châtaignier** (Castanea), **frêne** (Fraxinus),
  **tilleul** (Tilia, mellifère), **érable** (Acer).
- **Pionniers de lumière / sols humides** : **bouleau** (Betula, pionnier),
  **saule** (Salix, bord de mare → lien D15 tuile « mare »), **aulne** (Alnus,
  **fixateur d'azote** comme les Fabaceae → rôle écologique fort), **peuplier**
  (Populus, croissance rapide).
> À trancher **avec toi** : la liste exacte et leur **calibrage d'allure** (hauteurs,
> longévité, caractère caduc/persistant) — c'est de l'agronomie, je te le présente
> comme doc à étudier.

### Choix 2 — Nouvelles familles d'arbres = étendre `SOIL_SIGNATURE` + `family_effects`
Plusieurs candidats sont de **familles neuves** (Betulaceae pour bouleau/aulne,
Salicaceae pour saule/peuplier, Fagaceae pour châtaignier+chêne, etc.). Comme pour
D26, chaque famille neuve demande sa **signature de sol** et ses **effets famille**
(p.ex. l'aulne **fixe l'azote** → effet famille proche des Fabaceae). → **Coordonner
avec D26** (même travail d'extension de familles). Si tu fais D26 d'abord, D23 en
hérite l'infrastructure.

### Choix 3 — `age_curve` ou procédural pour les nouveaux ?
- **(A) ⭐ `age_curve` pour tous les nouveaux** (sauf si tu veux le procédural) :
  simple, calque exact des 5 existants, **pas de calibrage de structure de segments**.
- **(B) Procédural** (si Croissance·3bis est fait) : cohérence visuelle à terme, mais
  chaque arbre demande de calibrer `emit_length_cm`/`max_segments`/`wood_persistence`
  (cf. 3bis) — coûteux × N arbres.
> Reco : **(A)** d'abord (catalogue vite étoffé), migration procédurale plus tard
> espèce par espèce (le procédural et l'`age_curve` cohabitent déjà par design).

## Périmètre
1. **Audit botanique** (livrable éditorial à relire) : liste finale + `age_curve` +
   `longevity_years` + rôle écologique + famille de chaque arbre.
2. **Extension familles** : `SOIL_SIGNATURE` + `family_effects` pour les familles
   neuves (coordonné D26).
3. **Ajout** des classes (ou entrées data si D26=B) dans `perennials.py` +
   `PERENNIAL_CATALOGUE`.
4. **Calibrage d'allure** (boucle-sonde comme pour la tomate/pommier) si procédural ;
   sinon vérifier que l'`age_curve` est croissante/bornée.

## Hors périmètre
Le **rendu** (sprites/organes). La migration **procédurale** systématique (par espèce,
plus tard). Le portage C# (D24). Les espèces **herbacées/annuelles** neuves (← D26).

## Golden / vérification
Ajouter un arbre **présent dans le scénario golden** re-fige le golden (sa canopée
change le `LightField`) → **re-figeage maîtrisé**, validé avant capture. Un arbre
**absent** du scénario golden ne le touche pas (golden intact). `main.py` 500+ ans
sans crash, allures croissantes/bornées. MAJ `DETTE.md` D23 + `BACKLOG.md`.
