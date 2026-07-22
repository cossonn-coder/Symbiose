# ⑥c Vue Godot — indices visuels du couplage (fond ouvert, nain, substrat)

> Lire `00_etat.md` + `06a`/`06b`. **Option B** (Godot = VUE). Dernier sous-tronçon
> de la vue ⑥ — **clôt le sprint pots/bacs/substrats**. **Golden TRIVIALEMENT
> NEUTRE** : aucun fichier Python touché (tout est déjà dans le snapshot 0.5.7).
> Filet : `dotnet build Symbiose.csproj` (F5 = Nico). Namespace `Symbiose`,
> GDScript INTERDIT. Philo #5 : indices **diégétiques**, pas de chiffres en HUD
> primaire (étiquette au survol tolérée, comme les autres acteurs).

## Objectif
Rendre LISIBLES, sans chiffre imposé, les trois faits écologiques que le moteur
simule déjà sur un conteneur : (1) **fond ouvert vs fermé** (le bac communique
avec le sol, pas le pot fermé), (2) **effet nain** (petit volume → plante
rapetissée), (3) **état du substrat** (humidité/fertilité/pH du mini-sol). Pure
lecture du snapshot, aucun nouveau modèle.

## Ce qui est DÉJÀ là (à lire dans le snapshot `containers`)
- `fond_ouvert` (bool) — le bac couplé à la tuile dessous (⑤). Le pot = fermé.
- `volume` + `rows`/`cols` — petit volume = nain (la plante a déjà un `height_cm`
  réduit côté moteur ; ⑥c ne RECALCULE rien, il SIGNALE la cause).
- `eco_summary` (scalaires plot 0,0) : `humidite`/`n`/`p`/`k`/`ph`/`microbiome`/
  `structure` — l'état du mini-sol, déjà sérialisé.
- `plants[].leaf_symptoms` — symptômes foliaires (chlorose/sécheresse…) déjà
  rendus par `PlantRenderer` sur les plantes du monde : la même sémiologie
  s'applique à la plante en pot (réutiliser, pas réinventer).

## À faire (dans `visuals/ContainerStructure.cs` + le partial Conteneurs)
### A. Indice « fond ouvert / fermé »
Indice diégétique discret sur le placeholder : p.ex. un **fond plein dessiné**
(pot fermé) vs un **fond ajouré / liseré ouvert vers le sol** (bac `fond_ouvert`),
ou de fines **racines qui débordent sous le bac** vers la tuile. À dessiner dans
`_Draw()` selon le flag. Cohérent pixel-art SS² (Palette16).

### B. Indice « effet nain »
La plante rapetissée se VOIT déjà (height_cm). Ajouter un indice de CAUSE si
utile : p.ex. **racines tassées/visibles au bord** d'un petit pot (root-bound),
qui s'estompe sur grand volume / bac couplé (où le nain est levé, ⑤). Discret,
diégétique, sans barre.

### C. Étiquette de survol du conteneur (comme les étiquettes plantes/macro)
Au survol d'un conteneur (réutiliser le picking `FindNearestContainer` de ⑥b et
le système d'étiquettes `world/WorldView.Etiquettes.cs`), afficher une petite
étiquette : substrat, volume, et éventuellement un état QUALITATIF du mini-sol
(« humide / sec », « pauvre / riche ») dérivé d'`eco_summary` — **mots, pas
chiffres** (philo #5 ; les chiffres restent au mode debug/overlay s'il existe).

## Définition de done
- `dotnet build Symbiose.csproj` **vert**.
- Aucun fichier Python touché → golden **trivialement NEUTRE**.
- En F5 (Nico) : un bac fond ouvert se distingue d'un pot fermé d'un coup d'œil ;
  une plante en petit pot montre un indice de confinement ; le survol d'un
  conteneur donne substrat + état qualitatif sans chiffre en HUD primaire.
- MAJ `00_etat.md` : ligne ⑥c FAIT → **ligne ⑥ FAIT, SPRINT pots/bacs CLOS**
  (vue comprise). MAJ `journal.md` + entrée `journal/` (clôture vue). Supprimer
  un éventuel `HANDOFF.md` devenu obsolète. Liste finale des points **F5**.

## Pièges
- Ne RIEN recalculer : l'effet nain, le couplage, la décompo lasagnes sont des
  faits MOTEUR ; la vue ne fait que les MONTRER (sinon divergence Python/C#, D10).
- Garder les indices SOBRES (pixel-art, peu de surcharge) — l'apprentissage est
  diffus (philo #6), l'indice suggère, il n'explique pas.
- Étiquette = au survol, pas un HUD permanent ; les chiffres bruts vont au mode
  debug si présent (`visuals/FieldOverlay.cs`), pas en jeu normal.
- C'est la clôture : vérifier que les 3 sous-tronçons ⑥a/⑥b/⑥c tiennent ensemble
  en F5 avant de déclarer le sprint clos.
