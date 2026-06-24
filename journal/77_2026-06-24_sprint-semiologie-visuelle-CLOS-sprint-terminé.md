# 2026-06-24 — Sprint SÉMIOLOGIE VISUELLE (T1→T3) — SPRINT TERMINÉ

> Conception figée : `docs/conception/CONCEPTION_SEMIOLOGIE_VISUELLE.md` (dette D48).
> Modèle moteur sous-jacent NON retouché : `CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (D33, clos).
> État partagé : `sprints/sprint_semiologie_visuelle/00_etat.md` (bandeau 🏁 CLOS + mémo C2/C3).

## Objectif

Compléter et unifier la **traduction en pixels** des signes de souffrance/réponse
émis par le moteur. Couche **B pure** (`visuals/PlantRenderer.*`, C#) : le modèle
moteur (détecteurs, champ `leaf_symptoms`, intensités) est déjà figé par D33 et
n'est PAS touché — on consomme `leaf_symptoms` (déjà au snapshot), on le rend mieux.

## Tronçons

- **T1 `ombre` / étiolement** (`a07702c`, lève la **dette 0.5.2**) — canal COULEUR
  `ColorantTints["ombre"]` (vert pâle délavé) + canal TEXTURE `_ombre` (limbe
  chétif : calotte éclairée réduite via le toggle `_litFactor`, plancher E4 →
  jamais d'aplat). `ombre` était le seul vrai TROU : émis par le moteur mais sans
  entrée de mapping → ignoré silencieusement.
- **T2 `maladie` / taches cryptogamiques** (`213c97b`) — canal TEXTURE `_maladie`
  (semis de petites taches brun foncé par hash, salt neuf 37/41 ≠ criblage 23/29,
  rayon `r*0.12` < criblage `r*0.22`) → distingue le **ponctué** cryptogamique de
  l'**aplat uniforme** de l'asphyxie. La teinte brune (canal COULEUR) coexiste (D33).
- **T3 cohérence palette SS² + diagnostic C2/C3** (ce commit, CLÔT le sprint) :
  - **(A) Repli palette §5** : depuis SS² les feuilles passent par un **hue-shift**
    (volume) dont la composante FROIDE (vers le bleu) pouvait faire **reverdir/
    bleuir** un symptôme JAUNE (chlorose/sénescence) côté nord. On borne désormais
    l'amplitude du shift FROID ∝ `_colorAmount` : `HueShift` (rendu **instance**)
    multiplie `Mathf.Abs(lum)` par `_coolShiftScale` quand `lum < 0`. Toggle posé
    à l'entrée de la boucle feuilles (`Organs.cs`) à
    `Mathf.Lerp(1f, ColorCoolShiftFloor, _colorAmount)` (**K = 0.5**, réglable F5),
    **remis à 1 après** → branches/fruits/fleurs/silhouette gardent le froid plein.
    Seule la TEINTE est bornée — VALEUR et SATURATION inchangées (volume lisible).
    **Tissu sain** (`_colorAmount = 0` → facteur 1) = hue-shift SS² PLEIN, **zéro
    régression**.
  - **(B) Chaleur `ombre`** : `b8c8a0` → `c2c8a0` (un poil plus chaud) pour rester
    DISTINCT du froid du hue-shift côté nord — risque noté à la clôture T1.
  - **(B-doc) Mémo de protocole F5 C2/C3** (instrumente D47, PAS de mécanique) :
    tableau cause moteur → banc → attendu écran → verdict pour C2 (asphyxie
    `asphyxie_argile`, intensité brun-vert graduée vs muet) et C3 (ravageurs
    `infestation_ravageur` vs témoin, criblage plus dense côté infesté vs criblage
    fantôme). Consigné dans `00_etat.md` §Mémo C2/C3.

## Décisions techniques

- **`HueShift` rendue méthode d'INSTANCE** (était `static`) pour lire le champ
  `_coolShiftScale`. Tous ses appelants (`DrawVolumeEllipse/Circle`, `DrawBranch`,
  `DrawCanopySilhouette`, `DrawLeafVeins`) sont déjà des méthodes d'instance → zéro
  changement de signature côté appelants, compilation propre.
- **Toggle `_coolShiftScale`** calqué sur `_litFactor` (même fenêtre boucle
  feuilles) plutôt que de propager un paramètre à travers les 6 archétypes de
  feuille — cohérent avec l'option (a) actée en T1 (lisibilité).
- **K = 0.5** retenu (suggestion kickoff) : la moitié du froid au pic de
  coloration — assez de volume pour ne pas aplatir, pas assez pour noyer un jaune.

## Vérifications

- **Golden** : INCHANGÉ sur les 3 tronçons —
  `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646` (aucun fichier
  Python touché, vue passive).
- **`dotnet build Symbiose.csproj`** : VERT — 0 erreur, 0 warning.
- **Pont** : ENGINE_VERSION inchangé (0.5.6) — `ombre`/`maladie` étaient déjà dans
  `leaf_symptoms` côté moteur, on ne fait que mieux les peindre.

## Dette

- **Dette 0.5.2 LEVÉE** (mapping `ombre`, T1).
- **D48 LEVÉE** (sprint terminé).
- **D47** : C2/C3 désormais INSTRUMENTÉS (mémo de protocole) ; suspect `ombre`
  rendu C# LEVÉ ; reste à EXÉCUTER le protocole au F5 (Nico) — statut 🟡 maintenu.

## Reste (F5 = Nico)

Parcourir `ombre_dense`, `asphyxie_argile`, `infestation_ravageur` : symptômes
lisibles côté nord, délavé `ombre` distinct du froid, plante saine inchangée vs
SS². Régler K si besoin. Appliquer le mémo C2/C3 pour trancher les suspects rendu
résiduels (tout bug confirmé → dette ciblée `PlantRenderer`).
