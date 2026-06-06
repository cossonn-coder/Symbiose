# Dette D26 — Diversification écologique du catalogue

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. Ampleur **GROSSE** → se découpe (voir §Découpage).
> **Une décision structurante (class-based vs data-driven) précède tout le reste.**

## Ce que c'est, en une phrase
**Étendre le catalogue d'espèces** (aujourd'hui ~17 espèces, 5 familles, peu
d'archétypes) vers une diversité écologique crédible — **après** avoir tranché *comment*
on décrit une espèce (classes Python héritées vs données pures), car cette décision
conditionne le coût de chaque espèce ajoutée.

## L'état du moteur aujourd'hui (vérifié)
- **Architecture class-based** : `plants/base.py` définit `PlantBase` (ABC) puis les
  **familles** comme sous-classes (`Solanaceae`, `Fabaceae`, `Asteraceae`, `Lamiaceae`,
  `Poaceae`) portant des `family_effects` partagés ; `plants/species.py` et
  `plants/perennials.py` définissent les **espèces** comme sous-classes de famille,
  avec leurs `growth_stages`/`age_curve`, défauts de gènes, `port_archetype`, etc.
- **Catalogue** : `plants/catalogue.py` = 3 dicts (`PLANT_CATALOGUE`, `WEED_CATALOGUE`,
  `PERENNIAL_CATALOGUE`) mappant clé → classe.
- **Espèces actuelles** (17) : annuelles/herbacées (`BursaPastoris`, `MedicagoLupulina`,
  `PoaAnnua`, `Taraxacum`, `Tomato`, `Pepper`, `Bean`, `Clover`, `Sunflower`, `Basil`,
  `Yarrow`, `Phacelia`) + 5 arbres (`Fig`, `AppleTree`, `CherryTree`, `WalnutTree`,
  `OakTree`).
- **`SOIL_SIGNATURE`** (signature de besoins de sol par famille) et `family_effects`
  sont **par famille** : ajouter une famille = les étendre (DETTE.md D26 le note).
- **La compatibilité reproductive est familiale** : `genetics.species_compatible` =
  même `family`. Donc toute nouvelle espèce hérite du bon comportement de repro **par
  construction** si elle est bien rangée dans sa famille.

## Pourquoi cette dette dépend des autres (séquencement)
DETTE.md D26 : « À séquencer **après** Sprint éclairement (D21 = strates/ligneux,
nouveaux archétypes) et une décision **class-based vs data-driven**, en coordination
avec la génétique (D22). » → Aujourd'hui éclairement ✅, génétique ✅. **Il reste la
décision de structure** + l'arrivée de la **croissance procédurale (D29)** qui ajoute
un **profil de croissance par espèce** : chaque nouvelle espèce devra désormais
décrire sa **vitesse + son `port_archetype`** (cf. `CONCEPTION_CROISSANCE.md` §E).
→ **Reco de timing** : faire D26 **une fois D29 stabilisé** (au moins le profil par
espèce du tronçon 2), sinon on ajoute des espèces qu'il faudra re-profiler.

## 🔵 Choix de design à trancher (LE point structurant — à faire EN PREMIER)
**Class-based (actuel) vs data-driven.** C'est *la* décision : elle fixe le coût
marginal de chaque espèce ajoutée, donc la faisabilité d'un gros catalogue.

### Option A — Rester class-based (héritage Python) — sobre, recommandé si catalogue modéré
Chaque espèce = une classe. Familles = sous-classes intermédiaires portant le commun.
- **Pour** : zéro refactor, le moteur est déjà comme ça ; l'héritage exprime
  *naturellement* « famille → espèce » (les `family_effects`, `SOIL_SIGNATURE`,
  `species_compatible` tombent juste) ; type-checking, autocomplétion, code lisible
  pour toi (profil Python). Idéal jusqu'à ~30-50 espèces.
- **Contre** : ajouter 80-120 espèces (backlog lointain) devient verbeux ; pas
  éditable hors-code (un ami non-dev ne peut pas ajouter une plante) ; difficile à
  exposer côté Godot/C# (D24 devra re-déclarer chaque classe).

### Option B — Data-driven (table de données + un seul moteur d'espèce générique)
Chaque espèce = une **entrée de données** (dict/JSON/TOML) ; une seule classe
`Species` générique lit la table ; les familles = des **gabarits de données** hérités
par merge.
- **Pour** : ajouter une espèce = ajouter une ligne (pas de code) ; éditable hors-dev ;
  **partageable Python ↔ C#** (même fichier de données → D24 énormément simplifié) ;
  scalable vers 80-120 espèces. Cohérent avec le reste du moteur qui est **déjà
  data-driven** (gènes, `OBJETS_TOUCHES`, `TrophicSpec`, table de maîtrise).
- **Contre** : **refactor non trivial** des 17 espèces existantes + des
  `growth_stages`/`age_curve`/`family_effects` vers la table ; risque de **re-figer le
  golden** si un détail de comportement change pendant la migration (à faire à
  iso-comportement, espèce par espèce, golden vérifié à chaque étape — exactement le
  patron du refactor structurel D28).

### Option mixte C — Data-driven pour les *paramètres*, classes pour le *comportement rare*
La plupart des espèces = données ; les rares qui ont une **mécanique unique** (un
effet famille spécial) gardent une classe. Pragmatique.

> **Ma recommandation, nuancée :**
> - Si ton horizon réaliste est **~30 espèces** et que tu restes mono-dev Python :
>   **Option A**, n'over-engineere pas (CLAUDE.md §2). Tu ajoutes des classes, point.
> - Si tu vises **le grand catalogue** (80-120, backlog) **et/ou** tu veux alléger
>   D24 (portage C#) **et/ou** permettre l'édition par tes proches : **Option B**, et
>   c'est le bon moment de la faire **avant** que le catalogue grossisse (migrer 17
>   espèces est faisable, migrer 100 ne l'est plus).
> - **Le déclencheur** : la croissance procédurale (D29) ajoute déjà un schéma
>   d'attributs par espèce sur `PlantBase`. Si tu sens que ce schéma « veut être une
>   table », c'est le signe pour **B**. Décision = la tienne — c'est le choix le plus
>   structurant de tout ce dossier de dette.

## Découpage (sprint GROS)
1. **Décision** class-based vs data-driven (ci-dessus) — **conversation, pas code.**
2. **(Si B) Refactor d'infrastructure** à iso-comportement : table d'espèces + moteur
   générique, **17 espèces migrées une à une, golden vérifié à chaque pas** (patron
   D28). **(Si A)** : rien, on passe à 3.
3. **Audit botanique** des familles/strates à ajouter (livrable **éditorial à
   relire** — sujet hors ton expertise : ne pas trancher dans le vide) : quelles
   familles (Apiaceae, Brassicaceae, Cucurbitaceae… ?), quels archétypes manquants,
   quels rôles écologiques (fixateurs, dynamiseurs, couvre-sol, mellifères).
4. **Extension des données partagées** : `SOIL_SIGNATURE` + `family_effects` pour les
   nouvelles familles ; `genetics`/`species_compatible` les couvre déjà.
5. **Ajout incrémental** des espèces (chacune avec son profil de croissance D29), par
   petits lots, **golden re-figé de façon maîtrisée** (chaque espèce qui pousse dans
   le scénario change le golden — comme la migration tomate/pommier).

## Hors périmètre
Le **grand catalogue final** (80-120, backlog lointain) — ici on diversifie
*raisonnablement*. Le **rendu** des nouvelles espèces (sprites/organes procéduraux,
Godot). Le portage C# (D24). Les arbres pérennes supplémentaires = **dette D23** (sa
propre kickoff, hérite de la décision A/B prise ici).

## Golden / vérification
- Phase 2 (si refactor B) : **golden INTACT à chaque pas** (iso-comportement, c'est le
  critère dur — comme D28).
- Phase 5 (ajout d'espèces vivantes dans le scénario) : **re-figeage maîtrisé**,
  validé avant capture, dérive localisée. `test_genetique`/`test_auxiliaires` doivent
  rester cohérents. `main.py` 500+ ans sans crash. MAJ `DETTE.md` D26 + `BACKLOG.md`.
