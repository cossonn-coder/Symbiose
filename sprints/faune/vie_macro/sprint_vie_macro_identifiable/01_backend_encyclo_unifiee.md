# ① Backend encyclopédie unifiée + type (D60)

> Kickoff autosuffisant. Reprise à froid : lire `CLAUDE.md` + `00_etat.md` + ce
> fichier suffit. Golden **NEUTRE** (aucune écriture dans le tick).

## Objectif
Transformer l'encyclopédie plante-only en un **lecteur multi-règnes taggué par
type**. Après ce tronçon, `cmd_encyclopedie` renvoie un index d'entrées
découvertes **taguées** `{cle, type, titre}` et sert la fiche de n'importe quel
type (dispatch). Aucun corpus de texte neuf ici (les corpus concept/technique/
outil/geste sont ④⑤) — mais le PLOMBERIE de l'unification est posée, avec les
sources déjà existantes : plantes (inchangé), animaux (`faune_encyclo`, mono),
champignon (fiche générique unique).

## Les 7 types
`plante · animal · champignon · concept · technique · outil · geste`.

## Fichiers à toucher / créer
- **CRÉER `sim/encyclopedie_types.py`** — la **table de classification string→type**
  (source de vérité unique) + `type_de(cle) -> str|None`. C'est le module pivot :
  - plantes = clés de `{**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}` → `"plante"` ;
  - animaux = clés de `FAUNE_ENCYCLO` (`fields/faune_encyclo.py`) → `"animal"` ;
  - champignon = la clé générique `"champignon"` (constante) → `"champignon"` ;
  - concepts = clés de concept transversal (eau, lumière, météo, pollinisation…) —
    liste dérivée de `sim/maitrise_detection.CONCEPT_PAR_STAGNATION` (valeurs) +
    `["pollinisation"]` ; expose une constante `CONCEPTS` → `"concept"` ;
  - **technique vs outil** : les deux vivent mêlés dans les tuples de
    `sim/actions/couts.py:OBJETS_TOUCHES`. Range chaque string via un **set
    explicite** `TECHNIQUES` (semis, arrosage, récolte, arrachage, bêchage,
    ameublissement, taille, compostage, apiculture, jardinage_hors_sol,
    aménagement-habitat) ; tout autre membre des tuples `OBJETS_TOUCHES` = `"outil"`
    (arrosoir, sécateur, bêche, grelinette, fourche, bac-à-compost, pile-à-bois,
    ruche, équipement-apicole, pot, bac, amendement). Dérive les deux ensembles
    depuis `OBJETS_TOUCHES` pour ne rien rater : `outils = (tous les membres) −
    TECHNIQUES`.
  - gestes = clés de `sim/actions/couts.py:COUTS` → `"geste"`.
  - `type_de` renvoie `None` pour une clé qu'aucune catégorie ne réclame (robuste :
    l'index ignore alors l'entrée, pas de crash).
  - ⚠️ Une clé pourrait tomber dans deux catégories : garde un **ordre de
    priorité** déterministe (plante → animal → champignon → concept → technique →
    outil → geste) et signale (assert de test) qu'aucune collision réelle n'existe
    aujourd'hui.
- **CRÉER `sim/champignon_encyclo.py`** — la **fiche générique champignon** (1
  niveau) : constante `CLE_CHAMPIGNON = "champignon"` + un dict `{blurb,
  interconnexions}` (réseau mycélien, décomposeurs, mycorhizes ; interconnexions =
  bois mort, humus, racines). Miroir minimal de `faune_encyclo`. Donnée pure.
- **MODIFIER `sim/encyclopedie.py`** — c'est le dispatcheur :
  - `encyclopedie_index(gs, player)` → liste de dicts `{cle, type, titre}` pour
    TOUTES les clés découvertes (palier ≥ 1), pas seulement les plantes. Parcourt
    `M.ensure`… non : lit les objets découverts via `maitrise` (les clés au palier
    ≥ 1) et tague chacune par `type_de`. **Ordre stable** : garde l'ordre corpus
    par type puis l'ordre des types. `titre` = le nom lisible (pour les plantes =
    la clé ; pour animal = la clé ; concept/geste/… = la clé — le joli libellé
    viendra du corpus au ④⑤, ici la clé suffit).
  - `encyclopedie_lire(gs, player, cle)` → **dispatch par `type_de(cle)`** :
    - plante → comportement ACTUEL (FICHES, `min(palier, 3)`) — inchangé ;
    - animal → `{cle, type:"animal", niveau_max:1, niveaux:{1: blurb},
      interconnexions:[…]}` depuis `encyclo_meta` (mono-niveau, cap palier 1) ;
    - champignon → fiche générique (mono-niveau) ;
    - concept/technique/outil/geste → lit un corpus 3-niveaux **quand il existera**
      (④⑤) ; d'ici là renvoie ce qui est disponible ou `None` proprement (pas de
      crash) — prévois le point d'extension (un registre `CORPUS_PAR_TYPE`).
  - garde le no-op golden : sans couche maîtrise/joueur → index `[]`, lire `None`.
- **MODIFIER `tools/simserver/voix.py:cmd_encyclopedie`** — accepte un **filtre**
  optionnel `msg.type` : si fourni, l'index est restreint à ce type. La fiche
  (`msg.espece` → renommer sémantiquement possible en `msg.cle`, garde `espece`
  en repli pour ne pas casser le client C# existant) passe par le dispatch. Le
  pont reste bête : il relaie, ne classe pas (la classification vit en Python
  source de vérité).

## Ce qu'il NE faut PAS faire
- Ne PAS rédiger les corpus concept/technique/outil/geste (c'est ④⑤). Ici on pose
  le registre `CORPUS_PAR_TYPE` **vide/partiel** et le dispatch, pas le texte.
- Ne PAS toucher au tick, à `engine`, à `fields` (sauf lecture de `faune_encyclo`).
- Ne PAS ajouter d'état neuf dans `game_state` : l'index/lire dérivent de
  `maitrise` + corpus (comme aujourd'hui).
- Ne PAS casser le contrat C# actuel (`EncyclopediePanel` lit `index` = liste de
  strings, `fiche` = {espece, niveau_max, niveaux}). ⚠️ On PASSE l'index à une
  liste de DICTS taggués : c'est un changement de forme **assumé**, la vue est
  mise à jour au tronçon ⑥. En attendant, `dotnet build` peut casser sur
  `EncyclopediePanel` — c'est PRÉVU (⑥ répare la vue) ; note-le, ne bricole pas la
  vue ici.

## Golden
NEUTRE. Aucun chemin ne touche le tick. Vérifier `python3 -m tests.test_golden`
inchangé. Ajouter/adapter `tests/test_encyclopedie.py` : alignement des clés,
`type_de` couvre toutes les clés attendues sans collision, index taggué, dispatch
animal/champignon mono-niveau, filtre par type.

## Points F5
Aucun (backend pur). Le rendu 7 onglets est ⑥.
