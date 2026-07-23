# Tronçon ⑤ — Banc « X depuis rien » paramétré + vue Godot

> Sprint **Automate dirigé par le but** (D87). Conception :
> `docs/joueur/automate/conception_automate_but.md` (§6, §7). Lis `CLAUDE.md` +
> `00_etat.md` + ce fichier. ①-④ sont faits : la planification moyens-fins est
> complète côté Python et entièrement tracée dans `automate_journal`.
> **Dernier tronçon = vue Godot** (règle permanente projet).

## Objectif

Deux livrables :
1. **Banc Python paramétré** `banc_culture_depuis_rien(...)` qui déroule la chaîne
   complète « faire advenir une culture depuis rien » pour **n'importe quelle
   espèce**, force chaque branche de l'arbre de résolution, et compose un **récit**
   à partir du **log filtré** — la démo que Nico veut (matrice de test + révélateur
   de bugs bio).
2. **Vue Godot** : l'onglet automate existant surface le **log filtrable**.

## Livrable 1 — banc (`data/code/tools/bancs/`)

Modèle-toi sur les bancs existants (`automate_demo.py`, `jardin_tenu.py`,
`semiologie_ecart.py`) — même style de montage d'`engine`, boucle
`tick_semaine()` + `automate.jouer_tick(engine)`.

Fichier **NEUF** `tools/bancs/culture_depuis_rien.py` :

```
banc_culture_depuis_rien(espece, quantite=N, source_graine="auto", cout_vigueur=False,
                         nb_plants=None, annees=...)
```
- `source_graine ∈ {"auto", "banque", "magazine", "aucune"}` — prépare l'état
  initial pour forcer une branche : `banque` = graine pré-déposée en
  `PlayerSeedBank` ; `magazine` = banque vide + palier 3 famille atteint (offre
  ouverte) ; `aucune` = banque vide + pas d'offre → doit finir en **impasse
  honnête** ; `auto` = ce qui est disponible.
- `cout_vigueur` → `ProfilAutomate(paie_vigueur=cout_vigueur, ...)` (défaut False =
  coût 0, preset LIBRE — voir §7 exigence B). **Réutilise** ce flag, n'en invente
  pas.
- `nb_plants` → surcharge `nb_plants_cible` (défaut `min(N,3)`, ②/§2.2).
- Pose l'objectif `Objectif("recolter", quantite, espece, id=...)` via
  `ajouter_objectif`, marque le jardin cultivé si besoin (`marquer_jardin_cultive`),
  tourne, puis **compose le récit** en lisant `automate_journal` filtré
  (`filtre.filtrer` par `espece`, catégories `plan`/`geste`/`veille`/`impasse`/
  `resultat`, `niveau_max=1`) et `filtre.rendre`.
- Imprime : la chaîne déroulée, l'issue (accompli / veille + chaînon), et pour une
  espèce `fruitier` vs non-`fruitier` la **différence de longueur de chaîne** (C2).
- Prévois un mode « matrice » qui balaie quelques espèces × `source_graine` et
  tabule les issues (révèle les bugs bio par espèce, Q8 — une espèce qui meurt tôt
  ressort en `niche_defavorable`, ce n'est PAS un bug du banc).

**Choix d'espèce démo** (Q8) : pour montrer la chaîne complète qui RÉUSSIT, choisis
une espèce qui survit et fructifie réellement dans le scénario (démarrage chaud, peu
de pression maladie). La tomate peut mourir tôt (`tomate-mort-precoce`) — c'est un
cas de test valide (impasse honnête), pas le cas « succès » à mettre en avant.

## Livrable 2 — vue Godot

Le pont automate existe (`tools/simserver/automate_cmd.py`, `ENGINE_VERSION`
courante `0.5.35`) : commande `automate` opt-in, la vue LIT le bloc `automate` du
snapshot (`serialize.py`) et met en page journal/impasses/onglet. Côté C# :
`world/WorldView.Automate.cs` (touche A / Maj+A).

But : surfacer le **log filtrable** — l'utilisateur coche les **catégories** à voir
(perception/diagnostic/plan/geste/geste_coupe/veille/impasse). Le filtre est une
**vue LECTURE SEULE** : un run filtré et non filtré partagent le même log
sous-jacent (déterminisme préservé).

- **Python/pont** : exposer les lignes de log structurées au snapshot (via
  `serialize.py`/`automate_cmd.py`) avec leurs champs (`categorie`, `semaine`,
  `objectif_id`, `espece`, `zone`, `niveau`, `detail`) — ou un rendu déjà filtrable
  par catégorie. Bump `ENGINE_VERSION` (→ 0.5.36) si le protocole évolue.
- **C#** (`WorldView.Automate.cs`) : ajouter des toggles de catégorie et n'afficher
  que les lignes retenues (filtrage d'affichage, pas de mutation). Reste dans la
  bande de taille (`tools/compte_ldc.py` ; scinde en partial si ça dépasse ~300 LDC).
- **Filet de compilation** : `dotnet build Symbiose.csproj` doit être VERT (le F5
  visuel reste à Nico).

## Golden

**INTACT** (`57c166d8…`). Banc et vue sont hors tick / lecture seule. Vérifie
`python3 -m tests.test_golden`. **NE PAS** lancer `test_epaisseur_500ans`.

## Ne PAS faire

- NE PAS mettre « tomate » en dur dans le banc (paramétré par espèce).
- NE PAS inventer `cout_vigueur_actif` (réutilise `paie_vigueur`).
- NE PAS faire du filtre une écriture (vue lecture seule stricte).
- NE PAS toucher le moteur/tick ni re-figer le golden.

## Fin de sprint

Golden intact + tests verts + `dotnet build` vert → `00_etat.md` (§REPRISE : sprint
CLOS, 5 tronçons, golden intact, reste F5 Nico) + commit (`feat(automate ⑤) : banc
« X depuis rien » paramétré + vue Godot log filtrable`). Signale à Nico les points
**F5** : lancer le banc sur une espèce qui fructifie (chaîne complète), sur une
espèce sans graine (impasse honnête) ; onglet automate → cocher les catégories de
log.
