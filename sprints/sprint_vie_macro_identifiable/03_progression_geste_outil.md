# ③ Progression geste / outil / technique — combiné usage + succès (D60)

> Kickoff autosuffisant. Reprise à froid : `CLAUDE.md` + `00_etat.md` + ce fichier.
> Dépend de ① (table de classification `sim/encyclopedie_types.py`). Golden
> **NEUTRE** (tout côté pont / état joueur, hors tick). Tests joueur.

## Pourquoi ce tronçon existe
Décision QB : geste/outil/technique ont des fiches **3 niveaux** gatées palier.
Or ces objets sont aujourd'hui **plafonnés à palier 1** : `sim/maitrise_detection`
ne crédite QUE plantes + concepts (`NATURE_REQUISE`, `famille_de`). Sans robinet de
preuves neuf, N2/N3 seraient du contenu MORT (~100 textes jamais atteints). On
ouvre donc une **progression combinée** (décision Nico) à deux volets.

## Modèle (décision figée §3.4 du doc de conception)
Robinet de preuves à DEUX volets, tout hors tick :

1. **Usage répété** — chaque utilisation RÉUSSIE d'un geste (`cmd_action` renvoie
   `result.applied == True`) crédite une preuve de **poids LÉGER** sur :
   - le **geste** employé (clé de `COUTS`, ex. `"arroser"`) ;
   - ses **outils** et sa **technique** (membres de `OBJETS_TOUCHES[verb]`, classés
     via `type_de` de ①).
2. **Succès écologique** — quand `detecter` (tronçon i4 maîtrise, déjà en place)
   IMPUTE une amélioration au geste du joueur (levée de stagnation / reproduction
   provoquée), crédit d'une preuve **BONUS de poids FORT** sur le geste imputé.

Courbe `preuves_requises` géométrique existante (`sim/maitrise.py`). Poids
léger/fort = **placeholders nommés, calibrage D12.4**.

## Fichiers à toucher
- **MODIFIER `sim/maitrise.py:enregistrer_preuve`** — ajouter un paramètre
  `poids: float = 1.0` : `o["preuves"] += poids * _facteur_spillover(...)`. Défaut
  1.0 = comportement actuel (rétro-compatible ; les appels existants et le golden
  restent identiques). C'est ce qui permet un crédit fractionnaire (usage) vs fort
  (succès).
- **CRÉER `tools/simserver/geste_maitrise_pont.py`** (ou étendre `maitrise_pont.py`
  si ça reste sous ~300 LDC) — les deux volets, côté PONT :
  - `crediter_usage(gs, player, verb)` : appelé depuis `cmd_action` quand
    `result.applied` est vrai. Résout `{verb} ∪ OBJETS_TOUCHES[verb]`, filtre aux
    objets **déjà découverts** (palier ≥ 1 — gate d'observation cohérent avec la
    découverte à l'usage ci-dessous), crédite `enregistrer_preuve(..., poids=LEGER)`
    sur chacun. ⚠️ Ne crédite PAS la cible vivante (l'espèce a sa propre voie via
    `detecter`) — seulement geste/technique/outil.
  - `decouvrir_a_usage(gs, player, verb)` : à la 1ʳᵉ utilisation réussie, DÉCOUVRE
    (palier 0→1) le geste + sa technique + ses outils (`observer`/`decouvrir`).
    C'est le **canal de découverte neuf** de Q3 (un geste ne se survole pas). Idempotent.
  - `PLACEHOLDER` poids : `PREUVE_USAGE_LEGER` (< 1, ex. 0.34) et
    `PREUVE_SUCCES_FORT` (≥ 1, ex. 1.0) — calibrage D12.4.
- **MODIFIER `tools/simserver/actions.py:cmd_action`** — après `result = self._do_action(...)`,
  si `result.get("applied")` : appeler `decouvrir_a_usage` puis `crediter_usage`.
  Placement APRÈS le geste (on ne crédite un usage que réussi). Reste hors tick,
  golden neutre (le driver golden n'appelle jamais `cmd_action`).
- **MODIFIER le crédit succès** — le volet 2 s'appuie sur `detecter`, qui renvoie
  déjà `credits = [(objet, palier)]` et impute via la fenêtre `noter_geste`. Mais
  `detecter` crédite l'ESPÈCE/le CONCEPT sur une zone, pas le GESTE. Deux options,
  choisir la plus SOBRE :
  - (préférée) dans le **pont** `observer_apres_tick` (`maitrise_pont.py`), après
    l'appel à `detecter`, pour chaque zone où un geste a été imputé et a produit une
    amélioration, créditer le geste correspondant en poids fort. ⚠️ La difficulté :
    `detecter` ne dit pas QUEL verbe. La fenêtre `_detection["gestes"]` stocke
    `(semaine, zone)` sans le verbe. → **étendre `noter_geste` pour mémoriser le
    verbe** `(semaine, zone, verb)` (additif, rétro-compatible : `verb` optionnel),
    et exposer depuis `detecter` les zones effectivement créditées afin que le pont
    retrouve le(s) verbe(s) imputable(s) et les crédite en poids fort. Garder ça
    minimal et testé.
  - Documenter le choix retenu dans `00_etat.md`.

## Ce qu'il NE faut PAS faire
- Ne PAS déplacer la logique de détection dans le tick (elle reste au-dessus).
- Ne PAS créditer la cible vivante via le volet usage (double comptage).
- Ne PAS rédiger les corpus (④⑤) — ici on ne fait QUE la progression + découverte.
- Ne PAS changer les poids « en dur » ailleurs : un seul endroit de placeholders.
- Ne PAS casser les appels existants de `enregistrer_preuve` (défaut poids=1.0).

## Golden
NEUTRE. Tout vit dans le pont (`cmd_action`, `observer_apres_tick`) et l'état
joueur `maitrise`. Le golden écolo tourne sans serveur → jamais appelé. Vérifier
`python3 -m tests.test_golden` inchangé.

Tests joueur (nouveau `tests/test_progression_geste.py`) :
- usage réussi → geste/technique/outils découverts (palier 1) puis crédités léger ;
- N usages → franchit un palier (courbe géométrique) ;
- usage refusé (`applied == False`) → aucun crédit ;
- succès écologique imputé → crédit fort sur le geste (palier monte plus vite) ;
- `enregistrer_preuve(..., poids=1.0)` identique à l'ancien comportement.

## Points F5
Aucun (backend/pont). L'effet visible (fiches N2/N3 qui se débloquent) se voit au ⑥.
