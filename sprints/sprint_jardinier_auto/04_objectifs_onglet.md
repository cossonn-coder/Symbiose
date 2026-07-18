# ④ Objectifs (cœur mécanique) + onglet

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md` (§8). Prérequis : ①②③ faits.

## Objectif
Donner à l'automate des **objectifs** `(geste, quantité, cible)` (ex. « récolter 1
tomate », « récolter 10 pommes de terre »), injectables au début ou en phase de
planification. L'objectif **biaise la priorisation** et **compte la progression**.
Un **onglet** projette la trace filtrée sur l'objectif + les événements du monde.
**SCOPE = cœur mécanique seulement** (le système de quêtes complet est en D79, ne
PAS l'implémenter).

## Fichiers à toucher / CRÉER
- `tools/jardinier_auto/objectifs.py` (CRÉER) — dataclass
  `Objectif(geste: str, quantite: int, cible: str, id: str)` (`cible` = clé d'espèce
  du catalogue ou type de structure) + état `objectifs_actifs` sous
  `game_state["automate_objectifs"]` (liste, opt-in) + `progression` par objectif
  (compteur). API : `ajouter_objectif(gs, obj)`, `objectifs_actifs(gs)`,
  `incrementer(gs, obj_id)`, `est_accompli(obj)`.
- `tools/jardinier_auto/boucle.py` — étape **Prioriser** : bonus de priorité aux
  gestes candidats dont la cible correspond à un objectif actif (biais, pas
  exclusivité). Après un geste-cible réussi, `incrementer` le/les objectif(s)
  correspondants ; à `quantite` atteinte → objectif accompli, consigné.
- `tools/jardinier_auto/onglet.py` (CRÉER) — `onglet(gs, obj_id) -> dict` : projette
  `automate_journal` filtré sur `objectif_id == obj_id` + les **événements du monde**
  lus dans le `log` du tick (`game_state["log"]`) survenus pendant la fenêtre active
  de l'objectif. Lecture pure, aucune machinerie neuve.
- `tools/jardinier_auto/trace.py` — les entrées de geste portent déjà `objectif_id?`
  (posé en ①/§6) ; s'assurer qu'il est renseigné quand le geste sert un objectif.

## Modèle / points précis
- **Injection** : au début (avant la boucle) OU « en phase de planification » — pour
  le cœur headless, cela signifie simplement `ajouter_objectif` peut être appelé
  entre deux ticks (temps figé côté automate). La distinction planification/saison
  est une notion de la VUE (⑥) ; ici on autorise l'ajout à tout tick.
- **Biais de priorisation** : ne PAS transformer l'automate en mono-tâche. Un
  objectif RELÈVE la priorité des gestes servant sa cible, sans supprimer les autres
  soins (le jardin doit rester tenu). Garder le tri stable (départage inchangé).
- **Comptage** : `recolter` sur la cible → +1 (ou + nombre d'organes récoltés selon
  la sémantique retenue en ②/`part_recoltee`). Documenter le choix en tête de fichier.
- **Couplage impasse (§7)** : si la cible d'un objectif est **absente du monde** ET
  qu'aucun moyen ne permet de l'obtenir (pas de graine en banque-joueur, pas de
  succession possible), consigner une **impasse `objectif_inatteignable`**. Réutiliser
  `impasses.py` du ②.

## Golden attendu
**INCHANGÉ.** `automate_objectifs` est opt-in, hors tick, jamais créé par le golden.

## Ce qu'il NE faut PAS faire
- NE PAS implémenter les quêtes diégétiques (courrier voisin/oncle/enfant), les
  objectifs à condition d'état (« kiwi de 5 m » = hauteur, « trèfles fleuris » =
  floraison), le panneau Godot ni les voix narratives → **tout ça = D79**.
- NE PAS faire planter l'automate depuis la banque pour « fabriquer » une cible si
  ce n'était pas déjà dans son périmètre — un objectif inatteignable est une
  **impasse à signaler**, pas un comportement neuf à inventer.
- NE PAS toucher le moteur. NE PAS lancer `test_epaisseur_500ans`.

## Vérif de sortie
Golden intact + déterminisme vert. Banc `automate_demo` avec un objectif
`récolter 3 <espèce présente>` : la progression monte, l'objectif s'accomplit,
l'onglet liste les gestes + événements. Un objectif `récolter 1 <espèce absente>` →
impasse `objectif_inatteignable`. Mettre à jour `00_etat.md`.
