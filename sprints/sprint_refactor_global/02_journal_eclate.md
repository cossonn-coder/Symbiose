# SS② — Journal éclaté (index + journaux par sprint)

> Lire `00_etat.md` d'abord. Tronçon **délicat** : on manipule la mémoire
> narrative partagée. Aucun code moteur touché → golden trivialement
> préservé, mais une perte d'info ici coûte cher. Travailler par copie,
> relire, ne rien jeter.

## Objectif

Casser le monolithe `journal.md` (2385 l) en **un journal par sprint** +
un `journal.md` global réduit à un **index de pointeurs** (< 500 l facile).
Principe : le pointeur pointe vers la donnée ; on ne stocke pas tout dans
un seul fichier.

## Principe de découpe

- Le `journal.md` actuel est chronologique, par entrées de sprint. Chaque
  entrée correspond à un sprint ou sous-sprint identifiable.
- Cible : `journal/` à la racine, un fichier par sprint :
  `journal/AAAA-MM-JJ_nom-sprint.md` (réutiliser la convention déjà vue
  dans `journal_archive/`, qui suit DÉJÀ ce schéma — cohérence).
- `journal_archive/` existant : soit le fondre dans `journal/` (mêmes
  conventions), soit le laisser et que `journal/` ne contienne que les
  entrées du `journal.md` racine. **Décider en ouvrant les deux** ; viser
  l'unification si elle est propre, sinon conservateur.

## Étapes

1. **Inventaire** : lister les sections de `journal.md` (titres de niveau
   `##`/`###` = frontières de sprints). Construire la table
   « section → fichier cible ».
2. **Extraction fidèle** : pour chaque section, créer
   `journal/<date>_<slug>.md` avec le contenu **intégral, inchangé** (copie,
   pas de réécriture — on ne reformule pas la mémoire). Vérifier qu'aucune
   section ne dépasse 500 l ; si une le fait, c'est qu'elle agrège plusieurs
   sous-sprints → la scinder en sous-fichiers.
3. **Index** : `journal.md` devient une liste chronologique de pointeurs
   `- [titre court](journal/<fichier>) — accroche 1 ligne`. Garder en tête
   du fichier une note expliquant le nouveau schéma (pour les futures
   sessions Claude).
4. **Cohérence des liens** : `grep -rn "journal.md" .` (hors `.git`) pour
   repérer les renvois (CLAUDE.md, BACKLOG, kickoffs…). `journal.md` existe
   toujours (devient l'index) donc les liens « voir journal.md » restent
   valides ; vérifier qu'aucun ne pointe vers une ligne/section précise.
5. **Contrôle de complétude** : `wc -l journal/*.md` ; la somme doit
   ≈ couvrir l'ancien contenu (rien perdu). Comparer à l'ancien fichier
   (gardé dans l'historique git de toute façon).

## Garde-fous spécifiques

- **Ne rien reformuler** : extraction = copier-coller fidèle. Le refactor
  de style narratif n'est PAS l'objet (risqué pour la mémoire de Nico).
- En cas de doute sur une frontière de sprint, préférer un fichier un peu
  plus gros (mais < 500) à une coupe qui éparpille une décision.

## Définition de fait

- [ ] `journal/` peuplé, un fichier par sprint, **chacun < 500 l**.
- [ ] `journal.md` = index de pointeurs, < 500 l.
- [ ] Somme des contenus ≈ ancien journal (complétude vérifiée).
- [ ] Liens entrants vérifiés (CLAUDE.md, BACKLOG, sprints).
- [ ] Statut `journal_archive/` tranché (unifié ou laissé) et noté.
- [ ] Golden vert / hash identique (sanity).
- [ ] `00_etat.md` mis à jour → commit → `/clear`.

## Commit suggéré

`refactor(sprint·global) : SS② — journal monolithique éclaté par sprint, journal.md devient index de pointeurs`
