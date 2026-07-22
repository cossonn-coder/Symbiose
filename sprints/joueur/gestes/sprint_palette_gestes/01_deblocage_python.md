# ① DÉBLOCAGE DES GESTES (Python) — kickoff autosuffisant

> Sprint PALETTE DE GESTES. Lire d'abord : `CLAUDE.md` (racine) + `00_etat.md`
> (ce dossier) + `docs/joueur/gestes/conception_palette_gestes.md` §3.3/§3.4.
> Tu démarres à FROID : tout le nécessaire est ici.

## Objectif
Poser l'ÉTAT et les DONNÉES du déblocage des gestes, côté moteur Python
(source de vérité), et l'exposer au snapshot du pont. **Aucune logique de
simulation, aucun geste neuf ici** (bouture/greffe = ②③). Golden NEUTRE.

## Modèle (D2/D3/D6/D9)
- **État par avatar, persisté** : `game_state["gestes_debloques"][player]` =
  `set[str]` (verbes ouverts). Initialisé au **set de BASE** (D9) pour tout
  nouvel avatar. Doit entrer dans la save JSON (sérialisé en `list`, relu en
  `set`) comme `maitrise`/encyclopédie.
- **Set de BASE** (toujours dispo) : `{"planter", "arroser", "recolter",
  "manger", "ecraser", "becher", "favoriser_auxiliaire"}`. (⚠ D12 : `tailler`
  QUITTE la BASE — il devient GATED derrière la chaîne sécateur→couper→tailler,
  voir ci-dessous.)
- **Table data-driven `GESTE_UNLOCK`** : pour chaque geste GATED, sa/ses
  condition(s) d'ouverture. **Grammaire de condition étendue (D12)** — un geste
  peut avoir **plusieurs conditions ALTERNATIVES** (OU implicite : une liste de
  conditions, ouvert si l'UNE passe). Formes atomiques :
  - `("maitrise", objet, palier)` — vrai si `M.palier(gs, player, objet) >= palier` ;
  - `("action", verbe_declencheur)` — vrai si le joueur a réalisé `verbe_declencheur` ;
  - `("et", [cond, cond, …])` — **condition composée**, vraie si TOUTES les
    sous-conditions sont vraies (ex. `tailler` niv.2 ET `planter` niv.2) ;
  - `("evenement", marqueur)` — **voie expérimentale émergente** (D12) : vraie si
    le **marqueur écologique** `marqueur` a été consigné au ledger du joueur (ex.
    une bouture spontanée réussie = une branche taillée plantée qui s'enracine).
    Le marqueur est posé par le MOTEUR quand le phénomène se produit (câblage
    minimal — voir note ci-dessous) ; ici on ne fait que le LIRE.
  Un évaluateur récursif simple (`_cond_remplie(gs, player, cond)`) couvre les 4
  formes. `GESTE_UNLOCK[verbe]` = **liste** de conditions (OU).
- Gestes gated + conditions PROPOSÉES (calibrage F5, ajustable) :
  - **taille (chaîne D12)** : `couper` ← `[("action","posseder_secateur")]` (ou
    `("maitrise","sécateur",1)` si l'outil devient objet de maîtrise ; voie la plus
    simple = un marqueur « sécateur en main ») ; `tailler` ←
    `[("action","couper")]` (couper une branche ouvre le geste fin) ;
    `bouturer` ← `[("et",[("maitrise","taille",2),("maitrise","semis",2)]),
    ("evenement","bouture_spontanee")]` (voie savoir composée **OU** voie émergente).
  - compost : `poser_bac`,`poser_pile` ← `[("maitrise","compostage",1)]` ;
    `composter`,`retourner`,`epandre` ← `[("action","poser_bac")]` ;
    `empiler_bois` ← `[("action","poser_pile")]`.
  - conteneurs : `poser_pot`,`poser_bac_culture` ← `[("maitrise","jardinage_hors_sol",1)]` ;
    `deplacer_pot`,`planter_conteneur` ← `[("action","poser_pot")]`.
  - supports : `poser_tuteur`,`poser_treillis`,`poser_pergola` ←
    `[("maitrise","palissage",1)]` ; `palisser` ← `[("action","poser_tuteur")]`.
  - paillage : `pailler`,`broyer` ← `[("maitrise","paillage",1)]`.
  - ruche : `poser_ruche` ← `[("maitrise","apiculture",1)]` ; `recolter_miel` ←
    `[("action","poser_ruche")]`.
  - `greffer` ← `[("maitrise","greffe",1)]` (câblé en ③, clé POSÉE ici, dispatch
    tolérant si le verbe n'existe pas encore).
  - `deraciner`,`grelinette` : proposition = **BASE** (gestes rustiques). Ajuste
    si Nico corrige en F5.
- **`couper` (geste rudimentaire NEUF, D12)** : ancêtre BRUT de `tailler`. Son
  IMPLÉMENTATION moteur est MINIME — réutilise le seam `tailler` avec une cible
  NON choisie finement (ex. `_segment_cible` par défaut, pas de `segment_id`).
  Le poser ICI (petit) ou en ② est un point ouvert : **proposition = l'implémenter
  ICI** (c'est trivial, un alias de `tailler` sans choix de segment) pour que la
  chaîne D12 soit jouable de bout en bout. Coût = celui de `tailler` (MODERE).
  Ajoute `"couper"` à `COUTS`/`OBJETS_TOUCHES` + une fiche de voix (geste_corpus).
- **Hook d'évaluation** `evaluer_deblocages(game_state, player) -> list[str]` :
  event-driven (hors tick), parcourt `GESTE_UNLOCK`, ouvre tout geste dont la
  condition est remplie ET pas déjà ouvert, renvoie les verbes NOUVELLEMENT
  ouverts (pour la **notification diégétique**). À appeler après un franchissement
  de palier (`crediter_succes`) et après une action déclenchante.
- **Marque d'action réalisée** : un `set` `game_state["actions_faites"][player]`
  alimenté quand un geste GATED de type déclencheur réussit. Le plus simple et
  découplé : une petite fonction `marquer_action(gs, player, verbe)` appelée à la
  fin des dispatch de `poser_bac`/`poser_pile`/`poser_pot`/`poser_tuteur`/
  `poser_ruche` (uniquement ces déclencheurs). Garde le couplage MINIMAL.

## Fichiers à toucher
- **Nouveau** `data/code/sim/actions/deblocage.py` (~1 fichier = 1 responsabilité,
  ≤ 300 LDC) : `GESTES_BASE`, `GESTE_UNLOCK`, `init_gestes_debloques`,
  `est_debloque`, `marquer_action`, `evaluer_deblocages`. Import léger de
  `sim.maitrise as M` (lecture de palier). Ne PAS importer les gestes (couches).
- `data/code/sim/actions/__init__.py` : ré-exporter l'API publique si le paquet
  ré-exporte (regarde comment les autres modules du paquet y figurent).
- Câblage des déclencheurs `("action", …)` : appelle `marquer_action` +
  `evaluer_deblocages` là où le pont dispatch les poses (voir `tools/simserver/
  actions.py` / `conteneurs_route.py` / `commands.py` — repère où `poser_bac`
  etc. sont routés) OU dans les fonctions de geste elles-mêmes si plus propre.
  **Un seul point d'appel par déclencheur.** Ne DUPLIQUE pas la logique.
- Câblage de la voie savoir : après `progression.crediter_succes` (qui franchit
  les paliers), appelle `evaluer_deblocages`. Repère l'appelant de
  `crediter_succes` côté pont (`maitrise_pont.py`/`maitrise_cmds.py`).
- **Save JSON** : ajoute `gestes_debloques` (et `actions_faites`) à la
  sérialisation/désérialisation de la save par avatar. Cherche où `maitrise` est
  sérialisée (`grep -rn "maitrise" data/code` côté save) et fais le miroir
  (set → list au write, list → set au read).
- **Pont / snapshot** : expose `gestes_debloques[player]` (list triée) dans le
  snapshot sérialisé (`tools/simserver/serialize.py` ou là où le bloc `player`
  est construit — `grep -rn "seeds\|maitrise" tools/simserver/`). Bump
  `ENGINE_VERSION` (0.5.22 → 0.5.23) avec un commentaire de version décrivant la
  clé `gestes_debloques` (tolérance pré-0.5.23 : binaire ancien n'émet pas la clé
  → la vue retombe sur « tout dispo », cf. tronçon ④).

## Golden attendu
**INCHANGÉ** (`452b5256de4f6ff23df825b99596efdfde4e6ac87e8035f6b8da809f4dc000b4`).
Le smoke n'invoque aucun geste et n'a aucune maîtrise → BASE seul, aucun unlock,
aucune écriture dans le tick. Vérifie : `cd data/code && python3 -m tests.test_golden`.

## Ne PAS faire
- Pas de geste bouture/greffe ici (②③) — juste POSER leur clé d'unlock.
- Pas de logique de sim, pas d'écriture de champ écolo, rien dans la boucle tick.
- Pas de gating DUR : un geste verrouillé n'existe simplement pas encore dans la
  palette ; le moteur ne « punit » jamais une tentative (côté ④ la palette ne
  propose que l'ouvert).
- Pas de refactor des gestes existants.

## Vérifs de fin
1. Golden inchangé.
2. Un petit test ad hoc (ou REPL) : nouvel avatar → `gestes_debloques` = BASE ;
   forcer `M.palier("compostage")=1` puis `evaluer_deblocages` → `poser_bac`
   ouvert ; simuler `marquer_action("poser_bac")` + `evaluer_deblocages` →
   `composter` ouvert. Range ce script dans `tests/` (on ne jette pas les tests).
3. Snapshot du pont contient `gestes_debloques` (démarrer `sim_server`, un
   `snapshot`, vérifier la clé). Version bumpée + commentaire.
4. MAJ `00_etat.md` (§REPRISE → « ① fait, reste ②③④⑤ »).
