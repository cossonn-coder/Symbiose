# ⑤ Vue Godot — le semis qui attend se dit, les rejets du figuier se voient

À lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/regeneration/conception_releve_ligneuse.md`. Prérequis : ①-④ faits.

## Objectif
Le joueur doit pouvoir **lire** la banque de semis (philo #5 : indice, pas chiffre).

## À faire
1. **Voix de l'être** (Python, `data/code/sim/voix_etres.py` + `sim/voix_etres_corpus.py`) :
   aujourd'hui `besoins_plante` dit « ombre » dès `shade_memory` > ~0,2 (rampe
   0,2→0,8). Pour un **ligneux** dont `shade_memory` est sous son `seuil_ombre`
   (①) mais ombragé, dire un thème neuf `attente` à la place de `ombre`, p. ex.
   « J'attends sous {voisin}. Je pousse à peine ; qu'une trouée s'ouvre et je
   partirai. » (2 variantes comme les voisins du corpus). Au-delà du seuil, `ombre`
   comme avant. Voir comment `_ombreur` remplit `{voisin}`.
2. **Figuier** : vérifier que le rendu d'un ramet de figuier (petit arbre
   procédural) s'affiche comme les autres recrues (aucun code C# attendu ; s'il en
   faut, le justifier dans `00_etat.md`).
3. Pont : bump de version **seulement** si un champ du snapshot change
   (`tools/simserver/version.py` + tests qui épinglent la version).
4. `dotnet build Symbiose.csproj` vert (depuis la racine du dépôt).

## Tests
Test de la voix `attente` (semis ligneux ombragé sous le seuil → `attente` ; au
delà → `ombre` ; herbacée → `ombre`), suites `voix_etres`, `test_sim_server`,
golden INCHANGÉ. **Jamais `test_epaisseur_500ans`.**

## Points F5 (pour Nico)
- Run turbo `verger_mur`, quelques années : survoler un jeune arbre sous un
  fruitier → info-bulle « j'attends… » ; plus de semis fondant à l'ombre.
- Vers l'an 30-40 (mort du cerisier/pommier fondateur) : un semis voisin repart.
- Figuier : des rejets apparaissent au pied, aucune recrue loin de lui.

## Clôture du sprint (orchestrateur)
`00_etat.md` → CLOS ; `DETTE.md` D130 (fermée ou reliquats chiffrés) ;
`BACKLOG.md` ; entrée `journal/` + index `journal.md`.
