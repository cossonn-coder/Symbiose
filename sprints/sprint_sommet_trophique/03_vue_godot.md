# ③ — Vue Godot : sprites campagnol/rapace/couleuvre + signe racinaire

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/faune/trophique/conception_sommet_trophique.md` §5 (③). Prérequis : ①② faits.
> **Golden INTACT — vue pure, aucune écriture moteur.** Tronçon vue obligatoire
> (règle projet : chaque sprint se termine par sa vue Godot).

## Contexte pont (déjà OK — RIEN à changer côté Python)
La sérialisation faune est **déjà par espèce** (`tools/simserver/serialize.py:238` —
`sprites[tile] = {f.spec.name: [...]}` sur `eco.populations`). Les 3 nouvelles espèces
(`campagnol`, `rapace`, `couleuvre`) sont donc **exposées automatiquement** par le pont
dès ①②. Vérifier le numéro de protocole (`tools/simserver/version.py`) : bump seulement
si l'ajout d'espèces le justifie (cohérence avec les bumps ⑥ précédents), sinon laisser.

## Objectif
Rendre visibles les 3 espèces et le nouveau signe racinaire, côté C# (Godot est une
VUE, pas le moteur). Reproduire le patron ⑥b (table sprite PAR ESPÈCE).

## Fichiers (C#)
- `visuals/MacroLife.cs` : ajouter `campagnol`/`rapace`/`couleuvre` à la **table sprite
  par espèce** (même mécanisme que les 15 espèces existantes, clé = nom d'espèce reçu
  du pont). Placeholder procédural acceptable si le PNG manque (cf. autres espèces) :
  rongeur brun bas au sol, rapace silhouette en vol (plus haut / plus grand), couleuvre
  ondulée au sol près des piles. L'`activite` du champ pilote déjà l'animation.
- `visuals/PlantRenderer*.cs` : mapper le signe `rongeur_racinaire` (émis par
  `sim/semiologie.py` en ①) sur un rendu — teinte/texture « flétrissure par la base /
  tige écorcée au collet », dans l'esprit de la sémiologie D48 (`ColorantTints` +
  canal texture). Distinct du criblage foliaire du ravageur.
- Encyclopédie (rendu voix naturaliste, côté vue) : câbler les entrées des 3 espèces
  comme pour les espèces faune existantes (blurb déjà fourni par `faune_encyclo.py`).

## Filet de compilation
`dotnet build Symbiose.csproj` doit rester vert (SDK 8.0 sur la VM, `~/.dotnet`).
Le F5 visuel reste à Nico.

## Golden
**INTACT** (aucune écriture moteur). Lancer `python3 -m tests.test_golden` pour le
confirmer et le consigner dans `00_etat.md`.

## Ce qu'il NE faut PAS faire
- Aucune modif `data/code/` (moteur). Si un manque moteur apparaît, le verser en dette,
  pas le corriger ici.
- Pas de GDScript (C# only). Pas de sprite maison inventé.
- Ne pas relever la barre de taille (résorption `/refactor` si dépassement signalé).

## F5 (Nico)
- Campagnol au sol sur zones à racines (monticules) ; rapace en vol au-dessus ;
  couleuvre près des piles au soleil ; plante rongée au collet lisible et distincte du
  criblage foliaire ; boom-bust visible dans la durée. Verser tout écart en dette ciblée.

## Après ③ (maintenance D61 — clôture du sprint)
- `docs/meta/calibrage/conception_completude_ecosysteme.md` : T1 (D1) et T7 (B4) ⚠️ → ✅, « Incarné par » =
  `rapace`/`couleuvre` / `campagnol`. Lancer `/audit-projet ecosysteme`.
- `DETTE.md` (D61 pointeur) + `BACKLOG.md` + `journal.md` mis à jour.
