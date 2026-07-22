# ② Déplacement des docs de conception, études et meta

**Préalable** : lire `00_etat.md` puis la table de mapping de `01_structure_carte.md`
— elle fait foi, ne pas la ré-arbitrer. Le tronçon ① a créé les dossiers.

## Objectif

Déplacer les 56 `CONCEPTION_*.md` + les 3 docs `maitrise/` + les 4 `desktop/`
+ les 5 `amorce/` + les 2 études de `sprints/` vers leur thème, **via `git mv`**.
**Aucun contenu n'est édité dans ce tronçon** — déplacement et renommage seuls.
Les liens cassés sont réparés au tronçon ④, c'est normal et attendu ici.

## Règle de renommage

- `CONCEPTION_SOL_PH.md` → `conception_sol_ph.md`
- `etude_*.md` gardent leur nom (déjà conformes).
- `docs/amorce/BRIEF_CLAUDE_WEB.md` → `meta/amorce/brief_claude_web.md`.
- Tout en **minuscules, `snake_case`, sans accents dans le nom de fichier**.
- Les `maitrise/01_modele.md` etc. gardent leur numérotation (ordre de lecture).

## Méthode

Un `git mv` par fichier, en suivant la table. Exemple :

```bash
git mv docs/conception/CONCEPTION_SOL_PH.md docs/champs/sol/conception_sol_ph.md
```

⚠️ **Ne pas scripter en aveugle avec une boucle de conversion automatique** : la
table associe chaque doc à un thème qui n'est **pas** déductible de son nom
(ex. `MODELE_SPATIAL` → `rendu/spatial/`, `EQUILIBRE_INVASION` → `faune/trophique/`).
Suivre la table ligne à ligne.

## Cas particuliers

- `docs/conception/` doit finir **vide** puis être supprimé du suivi git.
- `docs/desktop/` idem.
- `docs/amorce/` est déplacé **en bloc** vers `meta/amorce/` (contenu historique,
  aucun tri interne).
- Les `README.md` de thème créés au ① ne sont pas touchés.

## Vérification

- `ls docs/conception docs/desktop 2>&1` → « No such file or directory ».
- `find docs -name 'conception_*.md' | wc -l` → **56**.
- `git status` ne montre que des `R` (renommages), **aucun `D` + `A` isolé** :
  si git n'a pas détecté un renommage, le `git mv` a été mal fait.
- `cd data/code && python3 -m tests.test_golden` → **inchangé**.

## Commit

`docs(rangement) ② : git mv des 56 conceptions + études + meta vers les thèmes`

Puis cocher ② dans `00_etat.md` et y noter tout écart de mapping constaté.
