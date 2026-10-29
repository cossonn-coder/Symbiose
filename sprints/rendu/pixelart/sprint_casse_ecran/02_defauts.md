# ② Défauts : maison en verre, H, jauges Maj+F3, vent en tête de F6, psilocybe

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/conception_casse_ecran.md` §1.
**Golden intact** (pont = lecture + une op debug ; le golden n'utilise pas le pont).
Filets : `dotnet build Symbiose.csproj` ; `python3 -m tests.test_golden` depuis `data/code/`.
Pas d'appel DeepSeek. Ne JAMAIS lancer `test_epaisseur_500ans`. Cinq petits items
indépendants : un commit par item conseillé.

## (b) Maison en verre
Cause vérifiée : `PlantZIndex(strate)` = 10 + rang (`world/WorldView.Luxuriance.cs:55`),
posé sur chaque plante (`WorldView.Snapshot.cs:184,252`) ; dans Godot 4 le `ZIndex` des
enfants **prime** sur le tri Y du parent `Objects` (`YSortEnabled`, `WorldView.cs:317`) ; la
maison (`WorldView.Maison.cs`, ancrée au coin avant) reste à z 0 relatif → elle est dessinée
SOUS toutes les plantes. **Intention** : tout ce qui vit dans `Objects` (maison, plantes,
supports, conteneurs, structures de compost) se trie **par Y** ; la strate (luxuriance ⑥ :
couvre-sol sous les hautes à même pied) ne départage qu'à Y quasi égal. Le placement (léger
biais de Y d'ancrage, `YSortOrigin`, ou autre) est au choix du sous-agent — vérifie
l'invariant luxuriance ⑥ (couvre-sol jamais par-dessus une haute au même pied) ET la maison
(plante derrière = cachée, devant = devant). Vérif capture : banc `full`, ×1 et ×4, 4
rotations, plante NO derrière la maison.

## (n) H rend aussi transparente la lisière côté caméra
`ApplyHouseGhost` (`world/WorldView.Controls.cs:279`) ne module que `_house`. Étendre au
nœud `DecorDevant` (`visuals/DecorLayer.Devant.cs:49`) avec la même opacité, et ré-appliquer
après reconstruction de `DecorDevant` (rotation D35), comme `WorldView.Maison.cs:102` le fait
pour la maison.

## (e) Maj+F3 : jauges au lieu des chiffres
Mode technique de l'info-bulle (`world/WorldView.InfoBulle.cs:170`, `InfoBulleVivant.cs:98`).
Par valeur : une **jauge d'une ligne de pixels** (barre fine), couleurs de la légende F6
(`visuals/FieldOverlay.cs` `Palettes` — même champ = même couleur), **sens fixe vert = bon /
rouge = mauvais** (le « bon » dépend de la valeur : documenter le sens par clé), un **repère
au seuil de visibilité** du signe, et un mot **léger / marqué / grave**. Les chiffres bruts
restent disponibles en technique (ex. en petit à droite, ou au 2ᵉ appui) — ne pas les
supprimer. Philo #5 : c'est l'affichage technique, déconseillé en découverte (mention gardée).

## (d) Vent en tête du cycle F6 (+ D99)
Registre servi par `cmd_fields` (`data/code/tools/simserver/commands.py:367`) : introspection
des `GridField` d'`EcoFields` → `eco.vent` (paresseux, `fields/ecofields/container.py:455`)
n'y figure **que** s'il a déjà été calculé. Intention : `vent`, `lisiere`, `turbulence`
**toujours** au registre ; si le champ est `None`, répondre une grille neutre (vent 0.0 ;
choisir et documenter le neutre de lisière/turbulence) **sans créer le champ** (neutralité
golden, D99). Côté vue (`world/WorldView.Hud.cs:391` `CycleField`, `_fieldNames`) : `vent`
en **premier** du cycle F6, puis `lisiere`, `turbulence`, puis l'ordre actuel. Palettes à
**bornes fixes** dans `FieldOverlay.Palettes` (leçon D45c). Bump de version du pont
(`tools/simserver/version.py`, entrée commentée comme les précédentes ; côté C# si une
constante de version y est vérifiée). Le « bug » de vent en longue partie zoom/dézoom est
**hors périmètre** (Nico).

## (h) Geste debug : faire pousser un psilocybe
`cmd_debug` (`data/code/tools/simserver/maitrise_cmds.py:115`, ops `palier3` /
`observer_tout` / `reset`, helpers `tools/simserver/debug_pont.py`). Ajouter une op (ex.
`carpophore`) qui fait apparaître un carpophore d'une espèce donnée (défaut `psilocybe`,
`fields/fongique.py:86`) au plot visé — en passant par le **même chemin d'état** que la
fructification normale (lis `fields/fongique.py` et l'export carpophores du snapshot pour
trouver où vit un carpophore), pour que l'info-bulle, la cueillette, la vision et
l'overdose s'exercent comme en jeu. Côté vue : une lettre libre dans la section « DEBUG
voix » de `WorldView.Controls.cs`, au plot sous la souris, étiquetée debug. Op hors golden
(pont opt-in), comme `palier3`.

## Ne PAS faire
Toucher au rendu des plantes (③④) ; corriger le bug de vent en longue partie ; modifier le
moteur hors `tools/simserver/` (sauf lecture).

## Fin de tronçon
Captures avant/après de (b)(n)(e)(d) lues avec Read ; golden vérifié ; `00_etat.md`
§Notes ② ; commit(s). F5 Nico : H, Maj+F3, F6 en tête = vent, touche psilocybe → vision.
