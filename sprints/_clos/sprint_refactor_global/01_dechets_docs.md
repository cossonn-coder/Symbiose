# SS① — Déchets & docs/conception + helper de comptage

> Lire `00_etat.md` d'abord. Tronçon **sans risque golden** (aucun code
> moteur touché) : rodage idéal. Build/golden inchangés par construction.

## Objectif

Dégager le terrain : supprimer les fossiles, regrouper toute la
documentation/conception éparpillée, et **livrer l'outil de mesure des
lignes de code** dont tous les tronçons suivants auront besoin.

## Pré-vol

- `git status` propre, branche à jour.
- Noter le hash golden de référence (sera comparé en fin de tronçon, doit
  être identique — ici trivialement, on ne touche pas le code) :
  `cd data/code && python3 -m tests.test_golden`.

## Étapes

### A. Helper de comptage `tools/compte_ldc.py`

Petit script (lui-même < 500 l, évidemment) qui compte les **lignes de
code pur** d'un fichier :
- **Python** : via `tokenize` — exclut lignes vides, lignes de commentaire
  (`COMMENT`) et lignes dont le seul contenu est une chaîne (docstrings).
- **C# / autres** : fallback ligne à ligne — exclut vides, `//`, blocs
  `/* … */`.
- Usage : `python3 tools/compte_ldc.py <fichiers…>` → tableau
  `fichier | total | code | commentaires`, trié décroissant sur `code`.
- Commenté pédagogiquement (Nico découvre `tokenize`).

C'est l'instrument du critère d'acceptation #3 du sprint.

### B. Déchets francs (vérifier mtime avril + inutilité AVANT rm)

Candidats repérés — **confirmer `ls -l` (date) avant suppression** :
- `data/code/sortie.txt` (19 Mo, 13 avril, dump mort) → `git rm`.
- `data/COSSON Nicolas Proposition d'Embauche.pdf` (CV perso hors-sujet)
  → `git rm` (et vérifier qu'aucune autre copie n'est utile).
- `data/code/tools/*.svg` + `*.svg.import` (maquettes générées,
  régénérables par `render_structure.py`) → `git rm`.
- Compléter `.gitignore` si des artefacts régénérables y manquent.

Tout fichier daté mai/juin = NE PAS supprimer.

### C. Regrouper la conception

- Créer `docs/conception/` ; y déplacer (`git mv`) les 11
  `data/code/CONCEPTION_*.md` (ils n'ont rien à faire dans le code source).
- `CONCEPTION_MAITRISE.md` (561 l) dépasse → le scinder en sous-fichiers
  thématiques (`docs/conception/maitrise/…`) avec un index court. Garder
  TOUT le contenu pédagogique.
- Vérifier qu'aucun code/script ne référence ces chemins (grep) ; sinon
  ajuster.

### D. Archiver les sprints clos

- Créer `sprints/_clos/` ; y déplacer les dossiers/fichiers de sprints
  terminés (cf `journal.md` / `BACKLOG.md` pour le statut). En cas de
  doute sur « clos ou actif », **laisser en place** (conservateur).
- `sprint_integration_godot/00_etat.md` (707 l) dépasse : si le sprint est
  encore actif (tranche 7 packaging restante), le scinder ; sinon archiver.
- Le sprint refactor courant et tout sprint actif **restent** dans
  `sprints/`.

### E. `docs/desktop/`

Garder tel quel (décision actée). Juste vérifier qu'aucun des 4 fichiers
ne dépasse 500 l de code… ce sont des docs, hors critère code, RAS attendu.

## Définition de fait

- [ ] `tools/compte_ldc.py` fonctionne sur un `.py` et un `.cs`.
- [ ] Fossiles supprimés (dates vérifiées), `git status` cohérent.
- [ ] `docs/conception/` peuplé ; plus aucun `CONCEPTION_*` dans `data/code`.
- [ ] `CONCEPTION_MAITRISE` < 500 l code après scission.
- [ ] Sprints clos sous `sprints/_clos/`.
- [ ] Golden vert, hash **identique** (sanity : on n'a touché aucun code).
- [ ] `00_etat.md` mis à jour (statut SS① ✅ + note de bord) → commit → `/clear`.

## Commit suggéré

`refactor(sprint·global) : SS① — déchets purgés, conception regroupée sous docs/, helper compte_ldc, sprints clos archivés`
