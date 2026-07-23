# Tronçon ① — Log exhaustif structuré (fondation)

> Sprint **Automate dirigé par le but** (D87). Conception :
> `docs/joueur/automate/conception_automate_but.md` (§6). Lis `CLAUDE.md` +
> `00_etat.md` + ce fichier — tu démarres à froid, tout est ici.

## Contexte minimal

L'**automate** (`data/code/tools/jardinier_auto/`) est un instrument de test
déterministe qui joue le jardin ENTRE deux ticks, côté appelant (banc/serveur),
**jamais dans `tick_semaine`** (invariant H2 → golden intact). Il écrit déjà une
trace dans `game_state["automate_journal"]` via `trace.py`
(`entree`/`entree_impasse`/`entree_consequence` + `consigner`) — dicts
JSON-sérialisables, append déterministe, jamais lus par le tick.

## Objectif du tronçon

Faire de cette trace un **log exhaustif structuré** qui rendra (aux tronçons ②-⑤)
tout le raisonnement moyens-fins **inspectable** et servira d'**oracle de
déterminisme**. Ce tronçon **pose la fondation** ; il n'ajoute encore aucun
comportement de planification. Aucune nouvelle catégorie n'est ENCORE émise par la
boucle (elles le seront aux tronçons suivants) — on livre le **schéma + les
constructeurs + le filtre + le test oracle**.

## Fichiers à toucher

- `tools/jardinier_auto/trace.py` — enrichir (voir ci-dessous). Fichier existant.
- `tools/jardinier_auto/filtre.py` — **NEUF** : filtrer + rendre (lecture seule).
- `tools/jardinier_auto/profil.py` — ajouter un axe `verbosite_log: int = 1`
  (dataclass frozen ; présent mais non contraignant — le log est toujours complet,
  la verbosité ne filtre qu'à la LECTURE). Documenter que 0=décision / 1=détail /
  2=perception fine.
- `tools/jardinier_auto/__init__.py` — ré-exporter `filtrer`, `rendre` si utile.
- `tests/test_automate_log.py` — **NEUF** : test oracle déterminisme + filtre.

## Modèle — schéma de ligne

Une ligne = dict JSON-sérialisable. **Champs communs** à toutes les catégories :
`categorie`, `semaine` (int), `niveau` (int : 0/1/2), et localisation
`objectif_id` (str|None), `espece` (str|None), `zone` (tuple `(tile_id,r,c)`|None).
Charge spécifique = `detail` (dict).

Catégories (le champ `type` du brief = `categorie`) :
`perception`(2) · `diagnostic`(1) · `plan`(0) · `geste`(0) · `geste_coupe`(1) ·
`veille`(0) · `impasse`(0) · `consequence`(1) · `resultat`(1).

**À faire dans `trace.py`** :
1. GARDER `entree`/`entree_impasse`/`entree_consequence`/`consigner`/`journal`/
   `CLE_JOURNAL` tels quels (rétro-compat D78) mais **normaliser** leur sortie au
   schéma commun : ajouter les champs `niveau`, `espece`, `zone` (dérivables ; pour
   les entrées legacy `espece=None`, `zone=None`, `niveau` = 0 geste/impasse, 1
   consequence) — SANS casser les clés déjà lues (`onglet.py` lit `objectif_id`,
   `categorie`, `semaine`…). Vérifie les lecteurs : `grep -rn automate_journal`,
   `onglet.py`, `rapport.py`, `tools/simserver/automate_cmd.py`.
2. AJOUTER des constructeurs pour les catégories neuves, tous renvoyant le schéma
   commun : `entree_perception`, `entree_diagnostic`, `entree_plan`,
   `entree_geste_coupe`, `entree_veille`, `entree_resultat`. Chacun prend au moins
   `semaine`, la localisation pertinente, et un `detail` dict. **Aucune** n'est
   encore APPELÉE par la boucle à ce tronçon (les tronçons ②-④ les appelleront).
3. Table `_RANG_CATEGORIE = {perception:0, diagnostic:1, plan:2, geste:3,
   geste_coupe:4, veille:5, impasse:6, consequence:7, resultat:8}` pour l'ordre de
   vue trié.

**`filtre.py`** (lecture seule, ne mute JAMAIS le journal) :
- `filtrer(journal, *, categorie=None, espece=None, objectif_id=None, zone=None,
  niveau_max=None) -> list` : sélection par champs (None = pas de contrainte ;
  `niveau_max` garde `ligne["niveau"] <= niveau_max`). Conserve l'ordre du journal.
- `trier(lignes) -> list` : tri stable par `(semaine, _RANG_CATEGORIE[categorie],
  objectif_id or "", zone or ())`.
- `rendre(ligne) -> str` : texte lisible DÉRIVÉ des champs (jamais l'inverse).

## Golden

**INTACT** (`57c166d8…`). Aucune ligne moteur touchée ; le log est hors tick,
opt-in. Vérifie : `python3 -m tests.test_golden` (lancé depuis `data/code/`).

## Test oracle (le livrable clé)

`tests/test_automate_log.py` :
- **Oracle déterminisme** : monter un petit monde, jouer K ticks de l'automate DEUX
  fois (deux `engine` frais, même seed/scénario), asserter que les deux
  `automate_journal` sont **égaux ligne à ligne**. C'est l'oracle qui protègera les
  tronçons suivants.
- **Filtre** : sur un journal fabriqué à la main (ou issu du run), vérifier que
  `filtrer(...)` sélectionne correctement par catégorie/espece/niveau_max et que
  `filtrer` ne mute pas l'entrée. Vérifier `trier` stable.
- **Rétro-compat** : les entrées produites par `entree`/`entree_impasse` gardent
  leurs clés historiques (celles que `onglet.py`/`rapport.py` lisent).

## Ne PAS faire

- NE PAS appeler les nouveaux constructeurs depuis `boucle.py` (c'est ②-④).
- NE PAS toucher le moteur (`sim/`, `fields/`, `plants/`, `world/`) ni le tick.
- NE PAS gater l'écriture par la verbosité (log TOUJOURS complet ; verbosité =
  filtre de lecture seulement).
- NE PAS fusionner avec le carnet diégétique (`sim/journal.py`) — canal SÉPARÉ.
- NE PAS introduire d'horodatage horloge ni d'id non déterministe.

## Fin de tronçon

Golden intact + tests verts → mets à jour `00_etat.md` (§REPRISE : ① fait, canaux
de log prêts, cap sur ②) et commit (`feat(automate ①) : log structuré + filtre +
oracle déterminisme`).
