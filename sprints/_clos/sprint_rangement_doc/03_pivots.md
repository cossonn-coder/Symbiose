# ③ Pivots : backlog éclaté, journal et dette par renvoi

**Préalable** : lire `00_etat.md` — **décision 2**, qui est l'arbitrage central de
ce tronçon. Les trois pivots ne sont **pas** traités de la même façon.

## Rappel de l'arbitrage (ne pas ré-ouvrir)

| Pivot | Traitement | Motif |
|---|---|---|
| `BACKLOG.md` (239 l) | **éclaté physiquement** par thème | contenu réellement sécable, aucun ID à préserver |
| `journal/` (126 entrées) | **renvois** — entrées inchangées | la chronologie est sa valeur ; une entrée touche souvent 3 thèmes |
| `DETTE.md` (96 l, ~90 `Dxx`) | **renvois** — table canonique inchangée | les `Dxx` sont cités dans le code et les sprints, ils doivent rester stables et uniques |

## A — Éclater `BACKLOG.md`

1. Pour chaque thème ayant des items : créer `docs/<type>/<theme>/backlog_<theme>.md`
   contenant les entrées correspondantes, **texte repris verbatim** (ne rien
   reformuler, ne rien « figer » qui ne l'était pas).
2. `BACKLOG.md` **reste à la racine** mais devient un **index de pointeurs** —
   exactement le motif déjà en place pour `journal.md` (voir son en-tête, il
   documente sa propre convention : s'en inspirer pour la rédiger).
   Il conserve : l'intro, le sprint en cours, et la liste des liens par thème.
3. Les sections historiques (« Sprint 0 », « Sprint conception »… lignes ~94-172)
   sont des **archives** : les regrouper dans `docs/meta/backlog_historique.md`
   plutôt que de les disperser par thème — elles racontent une chronologie, pas
   un thème.
4. Les sections « Pistes » (lignes ~173-238) partent au thème concerné
   (génération de terrain → `champs/sol/`, pixel-art → `rendu/pixelart/`).

## B — Renvois `journal_<theme>.md`

Dans chaque dossier de thème **ayant au moins 2 entrées de journal concernées** :

```markdown
# Journal — <thème>

> Renvois vers les entrées datées de `journal/`, qui restent la source
> canonique et chronologique. Rien n'est dupliqué ici.

- [2026-07-13 — Sprint santé & résilience CLOS](../../../journal/116_....md)
- ...
```

Établir la correspondance en croisant les **slugs** des noms de fichiers de
`journal/` avec les thèmes (`ls journal/` suffit : les slugs sont parlants,
ex. `117_2026-07-13_conception-allelopathie-FIGEE.md` → `vegetal/allelopathie/`).
Une entrée peut légitimement apparaître dans **plusieurs** fichiers de renvoi.

## C — Renvois `dette_<theme>.md` + colonne Thème

1. **Ajouter une colonne `Thème`** à la table de `DETTE.md` — c'est le levier le
   plus efficace : la table reste unique et devient filtrable d'un coup d'œil.
2. Pour chaque thème ayant **au moins un `Dxx` ouvert**, créer
   `docs/<type>/<theme>/dette_<theme>.md` : liste des `Dxx` avec leur libellé
   court et un lien vers `DETTE.md`. **Ne pas recopier la description complète**
   (source unique — le projet a explicitement supprimé la triple maintenance au
   Sprint refactor structurel du 2026-06-03, ne pas la réintroduire).

## Garde-fou de prolifération

**Ne créer un fichier de renvoi que s'il a de la matière.** Un thème sans dette
ouverte n'a pas de `dette_<theme>.md`. Objectif : des fichiers utiles, pas 90
coquilles vides. C'est le même esprit que le garde-fou de taille des fichiers.

## Pas d'`INDEX_*.md` racine

Le brief amont en prévoyait trois. Ils deviennent **sans objet** avec l'arbitrage
modulé : `journal.md` et `DETTE.md` **sont déjà** les index globaux, et
`BACKLOG.md` le devient en A.2. En créer trois de plus dupliquerait la fonction.

## Vérification

- `grep -c '^| D' DETTE.md` → inchangé (aucun `Dxx` perdu).
- Chaque `Dxx` ouvert apparaît dans exactement un `dette_<theme>.md`.
- Aucun item de `BACKLOG.md` perdu : comparer avec `git show HEAD:BACKLOG.md`.
- `cd data/code && python3 -m tests.test_golden` → **inchangé**.

## Commit

`docs(rangement) ③ : backlog éclaté par thème, renvois journal + dette`

Puis cocher ③ dans `00_etat.md`.
