# Sprint conception — Hormones de croissance (auxine / dominance apicale, D29)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> **Conception SEULE** (décision Nico, cadrage 2026-06-04) : ce sprint produit un
> document à étudier, **aucun code moteur**. L'implémentation Python est un sprint
> ultérieur. Français + pédagogie (Nico : ingénieur électronique embarqué,
> expert Python/simulation, **débutant Godot/C#** ; la **biologie végétale est
> hors de son domaine** → tu lui RÉDIGES le volet bio à étudier, tu ne lui poses
> pas de questions de botanique à trancher — cf. retour « pédagogie domaine »).

## But en une phrase

Concevoir la **réponse hormonale à la taille** (dette **D29**) : couper l'apex
d'une plante lève la **dominance apicale**, l'**auxine** cesse d'inhiber les
bourgeons latéraux → ils débourrent → ramification, port buissonnant, mise à
fruit. Le geste joueur est `tailler` (surfacé au Sprint conception Vigueur §3.3,
jamais codé). Livrable : **`data/code/CONCEPTION_HORMONES.md`**.

## Lis d'abord, dans cet ordre

1. **`data/code/CONCEPTION_VIGUEUR.md` §3.3** (l'action `tailler` telle que
   surfacée : coût `MODÉRÉ`, effet géométrique immédiat en v1, réponse
   architecturale renvoyée à D29) + §3.6 (points ouverts) + le bloc D29 de la
   section dette en fin de fichier.
2. **`DETTE.md`** — la ligne **D29** (définition de référence : auxine, dominance
   apicale, débourrement latéral, ramification, redirection de croissance).
3. **`data/code/plants/base.py`** — LE modèle de plante actuel, qui cadre toute
   l'abstraction possible :
   - `GrowthStage` (empreintes métriques par stade : `canopy_height`,
     `canopy_radius`, `root_radius`, `foliage_density`, `strate`) ;
   - `PlantInstance` (point `x_cm,y_cm` + `current_stage` + `growth_factor`
     [intégration lumière] + `stress_memory` + `genes`) ;
   - `PlantBase` (interface lumière polymorphe `height_at`/`canopy_radius_at`/
     `foliage_density_at`, traits par espèce : `reproduction_rate`,
     `maturity_years`, `pollination_*`…).
   **Constat structurant** : une plante = **un point + des stades + des
   disques** (canopée/racines). **Aucune topologie de branches/bourgeons/tige.**
   `advance_stage` est discret (semis→jeune→adulte→mature). C'est la matière dont
   tu disposes pour faire ÉMERGER la réponse à la taille.
4. **`data/code/CONCEPTION_MAITRISE.md` §9.5** (patron de succès outil/structure/
   **technique** : « action payée ET effet visé observé = 1 preuve » — `tailler`
   est précisément une « technique » déclarée §10.3) + `sim/actions.py` (le seam
   `cout_action` et le branchement des 6 gestes existants : modèle à suivre pour
   `tailler`).
5. **Mémoire perf** (`perf_profile_simulation`) : ~177 ms/tick moyen sur 432
   plots, **LightField = 53 % du CPU**, marge gameplay **×339**, coût ∝ taille de
   canopée. → matière chiffrée pour le **volet B (faisabilité topologique)**.

## Contraintes non négociables (les garde-fous du projet)

1. **GOLDEN ÉCOLO NEUTRE AU REPOS.** Comme la Vigueur (gène `vigueur` enveloppé
   non recâblé) et la Maîtrise (couche au-dessus du tick), **une plante jamais
   taillée doit se comporter EXACTEMENT comme aujourd'hui** → golden
   `c950f06c…` (engine) / `b005d9ba…` (champ) **intacts**. Tout état hormonal
   nouveau doit avoir un **repos strictement neutre** (valeur par défaut = no-op
   sur la croissance). Le golden est une succession spontanée **sans joueur** →
   personne ne taille → aucune réponse hormonale ne s'y déclenche. **Si la
   conception impose un état lu par le tick au repos non neutre, elle a un bug de
   design.** C'est le critère #1 à vérifier à chaque choix de modélisation.
2. **Philosophie de design (CLAUDE.md).** `tailler` est une **action directe sur
   le vivant** : permise mais **coûteuse en Vigueur** (philo #1 — la solution
   facile s'use). MAIS la réponse (débourrement, ramification, mise à fruit) doit
   **ÉMERGER d'un modèle hormonal déterministe**, JAMAIS d'un bonus/malus direct
   scripté sur la plante (philo #2). Toute la finesse du sprint est là : le geste
   est direct, la réponse est émergente.
3. **Déterminisme total** (philo #3) : aucun RNG ; même seed + mêmes gestes →
   même réponse. Si un aléa est utile (variabilité du débourrement), il passe par
   `_hash_noise` comme le reste du moteur.

## Ce que la conception doit produire — `CONCEPTION_HORMONES.md`

> Un seul fichier (pas de sous-découpage : la conception est une unité, cf. les
> sprints conception Vigueur / Maîtrise / Vie macro). Structure proposée :

### A. La biologie, rédigée POUR Nico (à étudier, pas à trancher)
Auxine (où elle est produite : le bourgeon apical ; ce qu'elle fait : inhibe les
latéraux = **dominance apicale**), levée de dominance à la coupe, **débourrement**
des bourgeons axillaires, conséquences : ramification, port buissonnant, **mise à
fruit** (beaucoup d'espèces fruitent sur le bois latéral / les rameaux de l'année).
Cas du **gourmand** (tomate indéterminée) et de la **taille de fructification**
(arbre fruitier). Ton « naturaliste qui observe ». Schémas ASCII bienvenus.

### B. Faisabilité topologique — POINT OUVERT n°1 (à instruire ET trancher ici)
**Décision Nico** : topologie de branches/bourgeons **seulement si le CPU et la
RAM peuvent se le permettre ET si l'affichage peut suivre** ; sinon repli sur une
abstraction scalaire. → Instruis les **deux** budgets, puis **recommande** :
- **Calcul** : la marge est large (×339, cf. perf). Estime le coût d'une topologie
  *légère* (quelques « charpentières » + bourgeons abstraits par plante × N
  plantes) vs le scalaire. La RAM (27 Mo aujourd'hui) n'est pas le sujet.
- **Rendu (le vrai mur)** : les plantes sont des **sprites PNG par stade**, pas un
  rendu végétal procédural. Une vraie ramification à l'écran demanderait un
  système de rendu **qui n'existe pas** (squelette/L-system/variantes de sprites).
  Évalue ce que l'affichage *peut* refléter sans ce système.
- **Tranche** entre trois options et justifie : **(i) topologie réelle** (riche,
  mais rendu à construire) ; **(ii) scalaire émergent** (1-2 variables d'état,
  léger, golden-safe, dans l'échelle « plante = point ») ; **(iii) hybride léger**
  (un petit nombre de pseudo-charpentières abstraites, reflétées par des variantes
  de sprite/échelle, sans vrai moteur de branches). Donne la reco + le pourquoi.

### C. Le modèle retenu
La/les variable(s) d'état hormonal (ex. niveau de dominance apicale, potentiel de
ramification, réserve d'auxine), leur **repos neutre** (critère golden #1), et le
**mapping coupe → réponse émergente** sur les variables EXISTANTES : `canopy_radius`
(s'étale en buisson), `canopy_height` (baisse), `foliage_density`, **mise à fruit**
(`reproduction_rate` / floraison — par un modèle, pas un `+=`), `growth_factor`.
Cinétique (débourrement en N semaines), déterminisme, bornes anti-emballement.

### D. L'action `tailler`
Le geste (couper l'**apex** vs couper une **branche**), coût Vigueur `MODÉRÉ`
(§3.3), ce qu'il **écrit** dans l'état hormonal, et le **hook géométrique
immédiat** (réduction d'empreinte → lumière livrée aux strates basses — la « v1 »
jamais codée). Place dans `sim/actions.py` (modèle des 6 gestes existants : coût
via `cout_action`, action binaire/graduée, mutation au-dessus du tick).

### E. Liens Vigueur + Maîtrise
- **Vigueur** : coût du geste (déjà §3.3) + éventuel petit gain si organe mûr
  récupéré à la coupe.
- **Maîtrise** : `tailler` est une **« technique »** (objet de maîtrise déclaré
  §10.3) ; son **succès** suit le patron §9.5 (« action payée ET effet visé
  observé = 1 preuve » — ici : taille → débourrement/mise à fruit observés). Dis
  comment la détection de succès (`sim/maitrise_detection.py`, i4) s'y branchera
  (sans la coder).

### F. Démonstrateur (périmètre ciblé — décision Nico)
**Tomate indéterminée** (gourmands) + **un fruitier** (pommier ou figuier du
catalogue — choisis et justifie). Définis un **trait par espèce** « réponse à la
taille » (porté par `PlantBase`, défaut **insensible** = neutre golden) : quelles
espèces répondent, comment, lesquelles ignorent la coupe (une graminée ne
rebourgeonne pas comme une tomate). Généralisable au reste du catalogue plus tard.

### G. Points ouverts → calibrage post-test
Cinétique de débourrement, ampleur de la ramification, seuils de mise à fruit,
coût exact du geste : **placeholders nommés**, calibrage jeu en main (pas les bons
chiffres ici).

## Hors périmètre (NE PAS faire ici)

- **Tout code moteur** : ce sprint est conception seule. (Le hook `tailler` dans
  `actions.py`, l'état hormonal sur `PlantInstance`, le câblage croissance → sprint
  d'impl ultérieur.)
- **Système de rendu végétal procédural Godot** (squelette/L-system) : évalué en
  §B comme contrainte, **pas conçu** ici (ce serait un sprint frontend dédié).
- **Portage C#** → D24.
- **Modèle d'organes fin** (feuille/fleur/fruit distincts) → D19 ; **bouture** (cas
  dégénéré de reproduction) → D22 ; ne pas les rouvrir.

## Garde-fous spécifiques au sprint

- **Pas de fichier créé sans OK** au-delà de `CONCEPTION_HORMONES.md` (le livrable
  attendu). Concevoir en conversation, écrire le doc sur « vas-y ».
- **Max 3 questions à la fois** ; défaut sobre + signaler quand tu tranches seul.
- **Ne rien jeter** : `tailler` v1 (effet géométrique) est conservé comme socle, la
  réponse hormonale se branche par-dessus.
- **Mettre à jour `journal.md`, `DETTE.md` (D29), `BACKLOG.md`** en fin de sprint.

## Ampleur

**Conception MOYENNE** — un seul fichier livrable, mais un vrai point dur à
instruire (faisabilité topologique : calcul vs rendu) et un verrou de design
récurrent (neutralité golden au repos). Pas de découpage en sous-sprints.

## À la fin

- Écrire `data/code/CONCEPTION_HORMONES.md` (volets A–G).
- MAJ `journal.md` (entrée : conception D29, décision topologie/scalaire tranchée
  + pourquoi, démonstrateur retenu), `DETTE.md` (D29 → conçu, pointe le doc),
  `BACKLOG.md` (sprint conception hormones ✅, ligne sprint d'impl. à venir).
- Mémoire `project_status` : D29 conçu ; prochain = impl. Python des hormones.
- Puis commit.
