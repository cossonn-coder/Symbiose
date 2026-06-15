# Sprint D12·i4 — Détection de succès branchée (Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico apprend Godot/C# en frontend,
> vient du C/Python embarqué ; expert Python/simulation).

## Ce que c'est, en une phrase

**Dernier des 4 tronçons de l'impl. D12** — le plus délicat. Jusqu'ici, les
preuves de maîtrise arrivent **par injection** (l'API `crediter_succes` /
`enregistrer_preuve` est appelée à la main dans les tests). i4 **branche la
détection automatique** : la couche gameplay **lit les signaux que le tick émet
déjà** (§9.1) et en déduit, toute seule, quand un **succès** a eu lieu — *une
action joueur dont l'effet émergent améliore le résultat au-delà du cours
spontané, et qui est observée* (§9.0). Elle appelle alors `enregistrer_preuve`
sur le bon objet, avec la bonne *nature de preuve* (§9.2/§9.3).

**Le golden écolo NE bouge PAS** (`c950f06c…` engine / `b005d9ba…` champ).
**Garde-fou absolu de ce tronçon** : la détection vit **AU-DESSUS du tick**, elle
*lit* le résultat d'un `tick_semaine` (le `log` + l'état des plantes/champs après
coup) — elle n'ajoute **aucun état au tick déterministe** et n'écrit **rien**
dans `engine`. §9.6 le dit : « Aucun de ces états ne vit dans le tick
déterministe → golden intact. » Si tu te retrouves à modifier `sim/engine.py`,
tu fais fausse route.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_MAITRISE.md` **§9 en entier** — c'est LA spec de ce
   tronçon (conçue exprès, sous-sprint D12.1) :
   - **§9.0** le pivot : ce qu'est (et n'est pas) un succès. Ni un émergent pur
     (« ça pousse tout seul » = bonnes conditions, pas maîtrise), ni une action
     simplement payée (cliquer ne suffit pas). C'est **l'intervention qui change
     la trajectoire pour le mieux**, opérationnalisée par des **signaux déjà
     émis** (un stress présent qu'on lève, ou un stress qui frappe les
     non-protégés et que la préparation prévient).
   - **§9.1** la table des **signaux que le tick émet déjà** (lecture moteur) —
     ta matière première. Stade (`advance_stage`/🌱), santé (🪦 mort, +1
     convalescence), mort par cause, reproduction (🌰 + tag `auto`/`biparental`/
     `introgr.`), floraison/récolte, météo/aléa (dégât médié → **log VIDE si zéro
     perte** = signe de protection réussie), stagnation (`⏸ sec`/`🌑 ombre`/
     `❄ froid`), succession (recrue **férale** établie), champs (trajectoire fin
     de saison), actions joueur.
   - **§9.2** être vivant : nature de preuve **croissante** par palier (1→2 lever
     une stagnation ; 2→3 amener à reproduction ; 3→4 optimiser récolte/repro
     répétée en pleine santé ; 4→5 = §9.4).
   - **§9.3** concept transversal : toujours « grâce à ton intervention » (le
     stress doit être **levé/prévenu par une action**, jamais émergent pur).
   - **§9.4** palier 5 (transcendant) = **conjonction** action experte **ET**
     naturalisation férale (génération auto-semée non replantée qui boucle son
     cycle en pleine santé). Le **seul** endroit où « ça pousse tout seul »
     compte — et seulement *conjoint* à une action experte.
   - **§9.5** outil/structure/technique : **patron** (« action payée ET effet
     visé observé = 1 preuve »), câblage réel → D29/D30/D31 (pas ici).
   - **§9.6** **implications pour la couche maîtrise (LIS DEUX FOIS)** : l'état
     gameplay nouveau minimal — (i) **tag de provenance** par plante (*féral* vs
     *replanté*) pour §9.4(b) ; (ii) **fenêtre d'imputation** liant un geste
     joueur à l'amélioration qu'il produit. **Gate d'observation** : un succès se
     registre **quand il est observé**. Les **Nᵢ** (répétitions/palier) →
     calibrage D12.4 (tu poses la *nature* de la preuve, pas le *nombre*).
2. `sprints/sprint_D12_impl/00_etat.md` — découpage + décisions actées (i1/i2/i3).
   Rappel architecture : `maitrise.py` **pur** (importe `plants` seul) ;
   `actions.py` = couche d'orchestration (voit Vigueur **et** Maîtrise) ; sens de
   dépendance **Vigueur → Maîtrise**, jamais l'inverse.
3. Code — où sont les signaux et les leviers :
   - `data/code/sim/engine.py` — `tick_semaine` et les `_*` qui **émettent le
     `log`** (lignes à marqueurs : `🌱` `advance_stage`, `❄/🌑/⏸` stagnation,
     `🪦` mort, `🌰` reproduction avec tag `auto/biparental/introgr.`, `🍂`
     nécromasse). **Tu LIS ce `log` et l'état post-tick ; tu n'y touches pas.**
     `_reproduction` (l.364) crée les **recrues férales** (banque-sol, non
     replantées) — c'est la source du tag provenance §9.4(b).
   - `data/code/sim/actions.py` — i2 y a posé `observer`/`crediter_succes`
     (injection des gains §4.3) ; i3 y a posé `cout_action`. Les gestes joueur
     (`recolter`/`deraciner`/`ecraser`/`becher`/`grelinette`/`favoriser_auxiliaire`)
     sont les **événements-déclencheurs** côté joueur de la fenêtre d'imputation
     (geste à la semaine *t* → amélioration observée dans une fenêtre [t, t+N]).
   - `data/code/sim/maitrise.py` — l'API que la détection APPELLE :
     `decouvrir` (gate de découverte), `enregistrer_preuve` (le crédit de preuve
     qui fait monter les paliers). **La détection est un PRODUCTEUR de preuves ;
     `maitrise.py` reste le réceptacle pur.**
   - `data/code/tests/test_vigueur.py` (section F/G) + `tests/test_maitrise.py` —
     les golden joueur à garder verts + le patron de test à étendre.

## Périmètre — où vit la détection (décision d'architecture à trancher)

> **Point ouvert majeur i4 (défaut sobre proposé, à confirmer en début de
> tronçon, signaler le choix).** La détection lit l'état **après** `tick_semaine`
> et mute `game_state["maitrise"]`. Elle ne peut pas vivre dans le tick (golden).
> Deux logements possibles :
>
> - **(a) défaut proposé — nouveau module `sim/maitrise_detection.py`**, appelé
>   par le *driver* de session **après** chaque `eng.tick_semaine()` (et au
>   passage de saison pour les signaux « trajectoire fin de saison »). Il importe
>   `maitrise` + `plants` (reste au-dessus du tick) ; `engine` ne l'importe
>   JAMAIS (pas d'inversion de couche). Symétrique de la façon dont la Vigueur a
>   son `tick_player_vigueur` appelé par le driver, pas par le cœur écolo.
> - (b) l'étendre dans `actions.py`. **Rejeté par défaut** : `actions.py` est
>   event-driven *par geste joueur* ; la détection est event-driven *par tick*
>   (cadence différente) → un module dédié est plus lisible et testable.
>
> Choisis (a) sauf raison contraire. Garde le module **pur au sens golden** :
> il ne fait jamais avancer la simulation, il l'observe.

### A. L'état gameplay minimal (§9.6) — au-dessus du tick, par avatar

Deux nouveautés, logées dans `game_state["maitrise"][player]` (en miroir des
`objets` d'i1), **jamais dans `PlantInstance`** (sinon risque de fuite golden) :

1. **Tag de provenance** — une structure latérale qui marque chaque plante
   *replanté par le joueur* vs *féral* (auto-semé par `_reproduction`/succession).
   Le défaut : une plante non marquée par un geste joueur de plantation est
   **férale**. (Il n'y a pas encore de geste `planter` codé — flag : à la
   première plantation joueur, on marquera ; d'ici là, **toute** plante établie
   par le tick est férale, ce qui est correct pour §9.4(b).) Clé d'identité de
   plante à choisir (objet Python `id()` instable entre runs → préfère une clé
   stable : `(tile_id, position, espèce)` ou un compteur d'instance). **Décision à
   poser + documenter.**
2. **Fenêtre d'imputation** — un petit journal des gestes joueur récents
   `(semaine, action, cible)` pour relier un geste à l'amélioration qu'il produit
   dans `[t, t+N]`. `N` (largeur de fenêtre) = **placeholder nommé → D12.4**.

### B. La détection — lire les signaux, en déduire les preuves

Pour chaque transition de §9.1 lue **après** le tick, décider s'il y a succès et
crédite la preuve sur le **bon objet** avec la bonne **nature** (§9.2/§9.3) :

- **Lever une stagnation** (`⏸/🌑/❄` présent en *t*, puis `🌱 advance_stage` de
  la **même plante** en *t+k* dans la fenêtre, **après un geste joueur** imputable)
  → preuve sur l'**espèce** (palier 1→2) + le **concept** lié (eau/lumière/météo).
- **Amener à reproduction** (`🌰` avec tag `biparental`, dans la fenêtre d'un geste
  `favoriser_auxiliaire`) → preuve espèce (2→3) + concept **pollinisation**.
- **Optimiser en pleine santé, répété** (`recolter`/repro **et** `health==3`,
  plusieurs fois) → preuve espèce (3→4).
- **Protection météo réussie** (`_mediated_damage` renvoie un **log vide** sous
  paillage/voile *là où des exposés souffrent*) → preuve concept **météo/climat**.
- **Naturalisation §9.4(b)** (recrue **férale** qui atteint jeune/adulte en pleine
  santé dans le sol façonné) — composante du palier 5, **conjointe** à une action
  experte (§9.4(a)). Tag provenance requis ici.

> **Gate d'observation (§9.6)** : un succès ne se registre que s'il est
> **observé** (le joueur regarde / une notification est émise). En l'absence d'UI,
> **défaut sobre proposé** : la découverte préalable de l'objet (`palier ≥ 1`)
> tient lieu de gate minimal (on ne crédite de preuve que sur un objet déjà
> découvert) — l'observation fine (carnet/notif, D14) se branchera dessus. Poser
> + documenter.

### C. Garder l'injection ouverte

`crediter_succes`/`observer`/`enregistrer_preuve` **restent appelables à la main**
(les tests i1–i3 en dépendent). i4 **ajoute** un producteur automatique ; il ne
**remplace** ni ne supprime l'injection (philo « ne jamais jeter de code »). La
détection *appelle* la même API.

## Hors périmètre (gated — NE PAS faire ici)

- **Toucher `sim/engine.py`** (ajouter un hook, un champ, un état au tick) →
  **interdit** : ça re-figerait le golden. La détection LIT, point.
- **Câbler de vrais outils/structures/techniques** (leur donner un état moteur) →
  D29/D30/D31. Ils restent des clés string à palier 0 (patron §9.5).
- **Calibrage** : largeur de fenêtre `N`, Nᵢ (répétitions/palier), seuils → **D12.4
  post-test**. Pose des **placeholders nommés**, pas les bons chiffres.
- **UI / carnet / notifications** (la vraie « observation ») → D14. Ici, gate
  minimal = découverte préalable.
- **Geste `planter`** (marquage *replanté* explicite) → pas encore codé ; d'ici là
  toute plante établie par le tick est férale (correct pour §9.4(b)).
- **Portage C#** → D24.

## Garde-fous (non négociables)

- **GOLDEN ÉCOLO INTACT** — avant *et* après : `python3 -m tests.test_golden` →
  **`c950f06c…`** et `python3 -m tests.test_population` → **`b005d9ba…`**. La
  détection ne touche RIEN dans le tick.
- **`maitrise.py` reste pur** (importe `plants` seul ; jamais `vigueur`/`engine`/
  `actions`). La détection (module dédié) peut importer `maitrise` + `plants`,
  jamais l'inverse — **`engine` n'importe jamais la détection** (pas d'inversion
  de couche).
- **`tests/test_maitrise` (35/35) et `tests/test_vigueur` (103/103) restent
  verts.** L'injection manuelle continue de marcher.
- **Couche `sim`** : imports absolus, lancement depuis `data/code/`. **Déterminisme
  total** (aucun RNG ; la détection est une fonction pure de l'état post-tick).
  **`main.py` doit toujours tourner.**
- **Ne jamais jeter/supprimer de code.** Tronçon **additif** : un module neuf + un
  appel dans le driver. L'API d'injection d'i1–i3 reste intacte.

## Golden joueur — étendre la couverture

Nouveau scénario (dans `tests/test_maitrise.py` ou une nouvelle section de
`tests/test_vigueur.py` — choisis, documente) : piloter un mini-`engine` sur une
fenêtre **scriptée et déterministe** où une stagnation est **levée après un geste
joueur**, et vérifier que la détection crédite **toute seule** une preuve sur la
bonne espèce + le bon concept (palier qui monte sans appel manuel à
`enregistrer_preuve`). Vérifier aussi le **négatif** : une amélioration **sans**
geste joueur imputable (émergent pur, hors fenêtre) ne crédite **rien** (§9.0 — «
ça pousse tout seul » ≠ maîtrise). Et le tag **férale** d'une recrue de
`_reproduction`. Le golden écolo, lui, ne bouge pas (la détection lit, le tick est
inchangé).

## Ampleur

**Gros-moyen** — le plus délicat des 4. Peu de lignes de *crédit* mais une vraie
**machine à états** (fenêtre d'imputation + tag provenance + lecture des marqueurs
de log) et plusieurs **décisions d'architecture** (logement du module, clé
d'identité de plante, gate d'observation minimal). Découpe possible si ça déborde :
**(α)** état minimal + tag provenance + fenêtre d'imputation (la plomberie, testée
seule) ; **(β)** les règles de détection §9.2/§9.3 par signal ; **(γ)** la
conjonction palier 5 §9.4. Si tu découpes, mets à jour `00_etat.md` et garde
chaque morceau golden-vert.

## À la fin

- MAJ `sprints/sprint_D12_impl/00_etat.md` (i4 ✅ → **impl. D12 COMPLÈTE**, golden
  vérifiés).
- MAJ `journal.md` (entrée : détection branchée, **golden écolo `c950f06c…`/
  `b005d9ba…` VÉRIFIÉS INCHANGÉS**, golden joueur étendu, décisions d'archi posées).
- MAJ `DETTE.md` (D12 → i4 fait, impl. Python complète ; reste D12.2 conception
  bloquée + D12.4 calibrage + D12.5 C#) + `BACKLOG.md` (ligne sprint impl. D12·i4).
- Mémoire `project_status` : impl. D12 complète ; prochain = D12.4 calibrage
  post-test (jeu en main) **ou** un autre sprint au choix de Nico.
- Puis commit. (Plus de `/clear` à enchaîner : c'est le dernier tronçon de D12.)
