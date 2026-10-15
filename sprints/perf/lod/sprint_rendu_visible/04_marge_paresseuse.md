# T4 — Marge proportionnelle + semaine paresseuse hors champ

> Lire `CLAUDE.md`, `00_etat.md`, `docs/perf/lod/conception_rendu_visible.md` §4 (D2, D6)
> et §5. Vue C# pure. Golden intact.

## Objectif
1. Une **seule** notion de « près de l'écran », proportionnelle au cadre, partagée par
   toutes les couches.
2. Le step hebdomadaire n'applique **que** ce qui est dans la marge ; le reste attend.

## Code concerné (lire avant)
- `world/WorldView.Camera.cs` : `CullPlants` (marge fixe 400 cm × `PxPerCmX`, teste le
  CENTRE du nœud), `VisibleCanvasRect`, appelés au pan/zoom/fin de snapshot.
- `visuals/BakeQueue.cs` : cuit/libère selon `IsVisibleInTree()` (= le culling ci-dessus).
- `world/WorldView.Etalement.cs` : tourniquet 7 familles ; famille 1 plantes en tranches
  de 6 ms, visibles d'abord ; `e.Payloads` = index payload par plante (clic, dossier),
  échangé en fin de famille 1.
- Couches avec leur propre culling (`CullMarginPx`) : `MacroLife`, `ForagerLayer`,
  `MulchLayer`, `LitterLayer`, `LeafLitterLayer`, `CouvertureLayer`, `CarpophoreLayer`,
  `PuddleLayer`, `AllelopathieLayer`, `CoverLayer`, `WeatherLayer` (`grep -n CullMargin`).

## Modèle
- **Rectangle de marge** (un helper unique, statique ou sur `WorldView`) : rectangle
  visible canvas agrandi de **25 % de sa taille de chaque côté pour ENTRER**, **50 % pour
  SORTIR** (hystérésis : un objet déjà « dedans » reste dedans jusqu'à 50 %). Test sur
  l'**emprise** projetée (boîte de l'objet), plus sur son centre. Réévalué au pan/zoom/
  rotation/snapshot, jamais en boucle par frame sans mouvement.
- Les couches qui gardent leur `CullMarginPx` (amplitude d'errance, jitter) l'ajoutent
  à ce rectangle commun au lieu d'un rectangle à elles.
- **Semaine paresseuse (D2)** : en famille 1, une plante HORS marge reçoit seulement sa
  donnée (payload stocké, index `Payloads`/noms à jour — le clic et les butineurs ne
  doivent jamais voir un index faux) et un drapeau « en attente ». Naissances hors champ :
  nœud créé (ou différé, au choix après lecture de `AppliquerPlante`) mais l'application
  coûteuse attend. Morts : retirées immédiatement (pas de fondu hors champ).
  À l'**entrée dans la marge** : les plantes en attente sont appliquées via une file à
  budget (même budget/µs que l'étalement), les plus proches du centre d'abord, AVANT
  leur cuisson. À la **consultation** (dossier F2, clic, taille, survol) : application
  synchrone de la plante concernée d'abord.
  Plusieurs semaines peuvent passer hors champ : seule la DERNIÈRE donnée compte
  (écraser, ne pas empiler).
- Vie macro / couches au sol : appliquer la même règle si leur application hebdo a un
  coût mesurable (mesurer d'abord avec la sonde de F4, ne pas l'imposer à l'aveugle).

## Vérification
- Banc : ×4 ou ×8, pan d'un bord à l'autre du jardin pendant que les semaines passent →
  aucune plante vue dans un état périmé (captures avant/après pan), aucune image vide.
- Mesure du gel hebdomadaire (méthode de `73a3f24` : frames > 250 ms, p95) à ×8 et ×0,5.
  À ×0,5 tout est dans la marge : gain attendu ≈ 0 (normal, le dire).
- Clic sur une plante juste entrée : dossier à jour.

## Ne pas faire
Pas de quadtree. Pas de changement de ce qui est dessiné.

## Fin de tronçon
Maj `00_etat.md`, commit. Point F5 : pan rapide à ×8 pendant que le temps passe — rien ne
« saute », pas de à-coup hebdomadaire.
