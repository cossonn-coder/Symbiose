# ⑤ Vue Godot — le semis qui attend, les rejets au pied (absorbe la relève ⑤)

À lire d'abord : `CLAUDE.md`, `00_etat.md`,
`docs/vegetal/regeneration/conception_rejets_de_souche.md` §7,
`../sprint_releve_ligneuse/05_vue_godot.md` (le tronçon absorbé — sa partie 1
« voix `attente` » est à faire ICI, telle qu'écrite là-bas ; son point F5
« rejets du figuier au pied en continu » est PÉRIMÉ).
Prérequis : ①-④ faits.

## À faire
1. **Voix `attente`** du semis ligneux ombragé sous son `seuil_ombre` : exactement
   la partie 1 de `../sprint_releve_ligneuse/05_vue_godot.md` (`sim/voix_etres.py`
   + `sim/voix_etres_corpus.py`).
2. **Voix de l'être d'un rejet** : si `voix_etres` a un thème d'origine/naissance,
   un rejet peut dire qu'il part de la souche (« Je pars de la vieille souche… »,
   2 variantes) ; sinon ne rien inventer, le noter.
3. **Rendu** : un rejet est un petit arbre procédural comme une recrue ;
   vérifier qu'il s'affiche au pied du squelette sans code C# (s'il en faut, le
   justifier dans `00_etat.md`).
4. **Pont** : bump de version seulement si un champ du snapshot change
   (`tools/simserver/version.py` + tests qui épinglent la version).
5. `dotnet build Symbiose.csproj` vert (racine du dépôt).

## Golden
**INCHANGÉ**. S'il bouge : STOP.

## Tests
Voix `attente` (ligneux ombragé sous le seuil → `attente` ; au-delà → `ombre` ;
herbacée → `ombre`), suites `voix_etres`, `test_sim_server`, `tests.test_golden`.
**Jamais `test_epaisseur_500ans`.**

## Points F5 (pour Nico)
- Run turbo `verger_mur` : plus de colonie de figuiers ; le figuier reste seul.
- Tailler sévèrement le figuier → au printemps, quelques rejets au pied.
- À la mort d'un fruitier âgé : rejets au pied du squelette (sauf sapin, et sauf
  arbre mort d'ombre).
- Survoler un jeune arbre sous un fruitier → « j'attends… ».

## Clôture (orchestrateur)
- Ce sprint → CLOS dans `00_etat.md`.
- `../sprint_releve_ligneuse/00_etat.md` : ⑤ « absorbé par
  `sprint_frein_rejets_figuier` ⑤ » → sprint relève CLOS.
- `DETTE.md` : D130 fermée (ou reliquats chiffrés) ; D131 (gel des rameaux)
  reste ouverte. `BACKLOG.md` ; entrée `journal/` + index `journal.md`.
