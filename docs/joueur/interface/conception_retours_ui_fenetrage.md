# Conception — Retours UI/HUD post-sprint fenêtrage

**Date de figeage :** 2026-07-23
**Type/thème :** `joueur/interface`
**Nature :** pure VUE C#/Godot, sauf l'item 4 (lecture d'état moteur + ajout de
champs de sérialisation, golden neutre).
**Golden :** INCHANGÉ sur T1/T2 ; NEUTRE (snapshot, hors `test_golden`) sur T3.
**Sprint :** `sprints/joueur/interface/sprint_ui_retours_fenetrage/` (3 tronçons).

Prolonge le sprint « fenêtrage UI » (launcher + panneau à onglets). Cinq retours
F5 de Nico, regroupés en trois tronçons.

---

## 0. Constats de terrain (lus dans le code le 2026-07-23)

Ce qui existe déjà — la conception s'appuie dessus, elle n'invente pas :

- **Palette** (`world/WorldView.Palette.cs`) lit déjà `gestes_debloques` du snapshot
  et **grise** les gestes verrouillés (choix assumé « plus pédagogique »). `Gestes[]`
  (`WorldView.Actions.cs:27`) compte ~28 entrées. Accélérateurs = touches **1..9**
  (`WorldView.Controls.cs:42` → `SelectGeste(keycode − Key1)`). Aucun modèle de slot,
  aucune édition.
- **Légende clavier** = `Label legend` (`WorldView.Hud.cs:155`), `PROVISOIRE`, pleine
  largeur à `y = 1080 − 96`, **recouvre le bas du champ de jeu**. Déjà enfant du
  CanvasLayer HUD.
- **Launcher** (`world/WorldView.Selecteur.cs`) = `CanvasLayer` ancré TopLeft, liste
  défilante plafonnée à 360 px (`UiScroll.Envelopper(_liste, 360f)`), **détruit
  (`QueueFree`) au « Lancer »**. `_ExitTree` (`WorldView.cs:372`) ferme proprement le
  pont.
- **État par plante** (`plants/base/instance.py`) = **mémoires scalaires intégrées**
  (`shade_memory`, `drought_memory`, `asphyxie_memory`, `cold_memory`,
  `infection_memory`, `wind_memory`, `root_herbivory_memory`, `stress_memory` ∈ [0,1])
  + `vitalite`/`etat` + `expression` (facteurs par gène adaptogène) + `symptom_marks`
  + `current_stage`/`age_weeks`/`age_years` + `genes`. **Aucun journal chronologique
  par instance.** Le seul chrono = `sim/journal.py` (ledger SPATIAL par zone
  `(tile,r,c)`, par joueur, opt-in, borné 200, dérivé du log texte).
- **Snapshot** (`tools/simserver/serialize.py`) expose déjà par plante :
  species/name/x_cm/y_cm/stage/stage_name/height/segments/strate/silhouette/
  vitalite/etat/genes/leaf_symptoms. **Manquent** : les mémoires, `expression`, l'âge.
- **Picking** : `FindPlant(worldPos, radius)` existe (réutilisé par étiquettes D60,
  survol gènes F7, actions). Nœuds plante indexés par clé `tile|species|x|y`
  (`WorldView.Snapshot.cs:25`), portant les metas tile/lx/ly/species.

---

## 1. Item 1 — Palette de gestes gérable

**Besoin.** Ne montrer que les gestes débloqués, plafonner à 10 (touches 0-9),
choisir par clic droit ce que la palette contient.

**Décision.**
- **Masquer** les gestes non débloqués (renverse le grisé actuel). Un geste verrouillé
  n'occupe **aucun** slot et n'est pas dessiné.
- **Modèle SLOT** : la palette n'affiche plus `Gestes[]` brut mais **10 slots** au plus,
  mappés touches **1-9 puis 0** (slot 0→touche « 1 » … slot 8→« 9 », slot 9→« 0 »).
- **Remplissage automatique** : à défaut d'édition, les slots se peuplent dans l'ordre
  de `Gestes[]` **parmi les seuls débloqués**. Un geste débloqué **au-delà du 10ᵉ
  n'apparaît pas** tant qu'il n'est pas assigné manuellement à un slot.
- **Édition clic droit** : clic droit sur un slot → menu contextuel = liste des gestes
  débloqués **non encore présents** dans la palette (à assigner à ce slot) + « vider ».
  C'est une **préférence d'affichage** (vue), pas un déblocage.
- **Persistance GLOBALE** : le layout des slots est sauvegardé dans `user://` (JSON) et
  rechargé au montage de la palette → survit au retour à l'accueil (item 5, qui
  recharge la scène). Clé = verbe du geste ; un verbe persisté mais non débloqué dans
  le monde courant est ignoré (repli sûr).

**Rationale.** Simple et prévisible : le layout ne bouge pas tout seul. Le coût du
choix « débordement invisible » = un geste débloqué au-delà de 10 est masqué jusqu'à
assignation — acceptable car le HUD signale le déblocage (flash existant) et Nico a la
main. Respecte #6 (on ne montre pas ce qui n'est pas acquis).

---

## 2. Item 2 — Légende clavier hors du champ

**Besoin.** Sortir le texte du bas de la simu, le mettre « dans le HUD ».

**Constat.** La légende est *déjà* dans le HUD ; le problème est qu'elle **recouvre le
bas du champ**. « Dans le HUD » = **hors du champ de jeu** (D54-a : sortir le texte
provisoire de la vue de découverte).

**Décision.** La légende devient un **overlay escamotable**, basculé par **F1**,
**masqué par défaut**. Champ dégagé en jeu ; l'aide reste à un appui de touche pour le
banc de test. Aucune diégétisation ici (D54-a complet = plus tard) — geste minimal.

---

## 3. Item 3 — Launcher pleine hauteur

**Décision.** Le plafond de hauteur de la liste défilante passe de 360 px à la hauteur
d'écran moins les marges et les widgets fixes (titre, filtres, boutons Paramètres/
Lancer). Le `ScrollContainer` interne (`UiScroll`) continue de gérer le débordement.
Trivial, sans arbitrage.

---

## 4. Item 4 — Dossier de plante au clic (outil de test)

**Besoin.** Cliquer une plante et connaître « son historique » — **pour les tests**.

**Décision — FORK A, dossier INSTANTANÉ (pas de chronologie).** Aucun log par instance
n'existe et en ajouter un serait un vrai chantier moteur (coût mémoire en run éternel,
recoupement avec `journal.py`). On expose plutôt l'**état physiologique courant** de la
plante pointée — ce dont un diagnostic F5 a réellement besoin :

- stade + âge (`age_weeks`/`age_years`), vitalité + état (`sain`/`affaibli`/`malade`),
- symptômes actifs (`leaf_symptoms` : cause + intensité),
- vecteur de gènes, facteurs d'`expression` plastique ≠ 1.0,
- **mémoires scalaires** (ombre/soif/asphyxie/froid/infection/vent/herbivorie/stress).

Les mémoires **sont l'histoire compressée** de la plante : `shade_memory = 0.8`
raconte « longtemps à l'ombre » sans mentir sur une chronologie qu'on n'a pas.

**Réalisation.**
- **Pont** : `serialize.py` ajoute au dict plante (vivante) : les 8 mémoires,
  `expression` (dict clé→facteur), `age_weeks`, `age_years`. Pure lecture d'état déjà
  porté par l'instance → **golden NEUTRE** (le snapshot n'est pas figé par
  `test_golden`). Bump de version du pont, annoncé.
- **Vue** : clic gauche en mode « inspecter » (ou réutilisation du picking) →
  `FindPlant()` → panneau **debug** read-only lisant le dict du **dernier snapshot**
  (aucun nouvel appel pont) via la clé d'identité `tile|species|x|y`.
- **Registre debug**, pas diégétique : rang F6/F7, hors HUD de découverte (#5). Ce
  n'est **pas** une voix narrative, ni l'encyclopédie, ni le carnet.

---

## 5. Item 5 — Retour à l'accueil depuis la simu

**Constat.** Le launcher est un `CanvasLayer` **détruit** au lancement ; `_ExitTree`
ferme proprement le pont. Un rechargement de scène redémarre donc tout proprement
(nouveau pont + `BuildSelecteur`) sans démontage manuel des ~20 couches de monde.

**Décision.** **Échap → retour à l'accueil IMMÉDIAT** via
`GetTree().ReloadCurrentScene()`, **sans confirmation** (bancs rejouables, abandon
d'état assumé ; l'auto-save ne se fait qu'au passage de saison de toute façon).
**Précédence** : si un panneau (Consultation/Voix) est ouvert, Échap le **ferme
d'abord** ; ce n'est qu'en l'absence de panneau ouvert qu'Échap revient à l'accueil.

**Vocabulaire.** « Revenir à l'accueil » depuis un banc = changer d'environnement
d'essai, pas « quitter une partie ». Aucun lexique roguelike (#4).

---

## 6. Respect de la philosophie #1-#7

- **#5** : item 2 sort le texte du champ (va dans le sens de #5) ; item 4 est un
  instrument de test isolé du HUD de découverte.
- **#6** : item 1 masque le non-acquis (progression = découverte).
- **#3** : item 4 = lecture d'état déterministe, zéro RNG.
- **#4** : run éternel intact ; « accueil » = launcher de bancs, pas un menu de partie.

---

## 7. Perf

Items 1/2/3/5 négligeables (chrome de vue, rechargement de scène ponctuel). Item 4 :
lecture du dernier snapshot déjà en mémoire + qq scalaires ajoutés à la sérialisation
(par plante vivante, déjà itérée) → coût trivial, aucune boucle nouvelle.

---

## 8. Découpage (3 tronçons, dernier = vue+pont)

- **T1** — Palette gérable (item 1). Pure vue, golden INCHANGÉ.
- **T2** — Chrome & navigation (items 2, 3, 5). Pure vue, golden INCHANGÉ.
- **T3** — Dossier de plante au clic (item 4). Vue + pont, golden NEUTRE annoncé.

---

## 9. Rattachement à la dette

- **D55** (palette de gestes) — item 1 = couche de gestion d'affichage par-dessus.
- **D54-a** (HUD primaire diégétique) — item 2 = premier geste concret (sortir le
  texte du champ).
- **D59** — déjà absorbée par le sprint fenêtrage (rappel).
- **D14** (carnet) / **D60** (survol → nom) — briques réutilisées/voisines de l'item 4,
  mais l'item 4 reste un outil de test **distinct** du carnet interprétatif.
