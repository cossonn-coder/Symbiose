# ⑥ Vue Godot — pétales, fruits, feuilles ; banc `caracteres_vivants`

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §2.1 (couleur) et §4.
> Golden attendu : **INTACT** (vue seulement).

## Objectif
Voir la diversité : un champ de bourraches du bleu au rose, des guides sur les pétales, des
tomates à gros ou petits fruits, des feuilles mates ou luisantes, des ports en flèche ou en
buisson.

## À faire
1. **Rendu** (`visuals/PlantRenderer*.cs`, lire d'abord `PlantRenderer.Flower.cs`,
   `PiecesFleur.cs`, `FleurSnes.cs`, `FruitMur.cs`, `Leaf.cs`, `Ports.cs`) : teinte des pétales
   en **dégradé** sur la palette maître (pas de couleur hors palette : quantifier vers la plus
   proche), guides à nectar (lignes ou œil central contrasté), échelle des fleurs et des
   fruits, matité des feuilles, port. Une variante précuite par combinaison utile, pas de
   calcul par frame.
2. **Banc `caracteres_vivants`** (`data/code/bancs/`) : rangées pré-calculées (déterministes)
   de bourraches, phacélies, tomates et basilics de lignées variées, plus une rangée de
   fraisiers stolonifères. Survol G ouvert.
3. **`dotnet build Symbiose.csproj`** vert. **Capture VM** (`tools/capture_vm.sh`), regarder
   les PNG, planche dans `planche/` du sprint. Mesure FPS du banc consignée.
4. **Recette F5** dans `00_etat.md`.
5. **Clôture D139** : `DETTE.md` (D139 close côté code sur les trois sprints, F5 attendu ;
   D131, D107 restent ouvertes ; ajouter au BACKLOG : signal honnête de couleur après
   pollinisation, `tuberisation`/`epines`/`profondeur_racinaire` le jour où leur mécanique
   existe), `BACKLOG.md`, entrée `journal/` + pointeur `journal.md`, mémoire de statut si
   pertinent.

## Ne PAS faire
- Toucher au moteur. Couleurs hors palette.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
Sprint CLOS côté code, F5 attendu. Commit.
