# 2026-06-24 — Sprint RENDU FEUILLAGE (T1→T6) — SPRINT TERMINÉ

> Conception figée : `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md`.
> État partagé : `sprints/sprint_rendu_feuillage/00_etat.md` (bandeau CLOS).
> Exécuté en autonomie via `/sprint-auto` (un sous-agent par tronçon, /clear
> implicite à froid ; l'orchestrateur vérifie golden + build et commite chacun).

## Objectif

Combler les trous du **rendu des feuilles par espèce** dans la continuité du
pixel-art 16-bit (SS④) : forme, couleur, nervures, croissance, insertion, chute
+ litière. Couche **B** (`visuals/PlantRenderer.*`) sauf T5/T6 qui **transportent**
une donnée déjà calculée par le moteur via le pont. **Golden trivialement préservé
sur TOUS les tronçons** (vue passive ; T5/T6 = transport pur, pas calcul).

## 6 exigences Nico

- **E1** croissance progressive (1-2 sem) · **E2** nervures couleur ≠ limbe ·
  **E3** forme **et** couleur par espèce · **E4** jamais d'aplat (≥ 2 valeurs) ·
  **E5** feuille émerge d'une branche verte (+ **E5bis** chute au pétiole, reste
  au sol) · **E6** vrilles grimpantes → **DIFFÉRÉ, dette D49** (sprint moteur séparé).

## Tronçons (commits sur `main`)

- **T1** `d2cedd1` — Couleur du limbe par espèce (table `Palettes` étendue à
  **23 espèces**, `Organs.cs`). E3-couleur.
- **T2** `ff1a52f` — Forme par espèce : `enum LeafShape` (**6 archétypes**
  Elliptique/Lanceolee/Cordee/Lobee/Composee/Aciculaire), `LeafProfile`, tracé
  déterministe (jitter par hash), partial dédié `PlantRenderer.Leaf.cs`. E3-forme.
- **T3** `f3a1a85` — Nervures = **3ᵉ valeur** : topologie par archétype
  (penninerve/palmée/rachis), teinte `HueShift(limbe, ±VeinShift)`, 1 px non
  antialiasé. E2.
- **T4** `2724bf8` — Insertion : verrou **« feuille ⟹ segment vert »**
  (`LeafMaxThickCm = LignifyFullCm·0.5 = 1.5`, ré-alignement des deux seuils) +
  **pétiole vert** (`DrawPetiole`, teinte du rameau local, jamais brun = point de
  rupture de l'abscission). E5.
- **T5** `57f0f8f` — Croissance progressive (E1) — **pont 0.5.5**. `age_weeks` du
  segment (déjà émis par `Segment.to_dict()`, transport pur) lu côté C#
  (`record struct Segment` + `ParseSegment` tolérant). Facteur `LeafGrowthFactor =
  clamp(AgeWeeks/1.5, 0,1)` ease-out → rayon × leafGrowth + limbe interpolé
  vers le rameau à l'émergence. Synergie plancher §1, pas de pop-in.
- **T6** `3525fc1` — Chute + litière (E5bis) — **pont 0.5.6, SPRINT CLOS**.
  `age_sem` ajouté au bloc `litiere` (5ᵉ champ, proxy d'état de décompo, transport
  pur). Primitive `DrawLitterLeaf` + nouveau calque monde **`LeafLitterLayer.cs`**
  (hérite `PlantRenderer` comme « stylo », semis déterministe djb2, feuilles
  mortes à plat brun-roux dérivant vers l'humus ∝ `age_sem`, quantité bornée ∝
  masse). Cassure au pétiole = émergente (rien à coder : la feuille disparue
  emporte son pétiole vert). Câblage `WorldView.Compost.cs`.

## Vérifications (constantes sur tout le sprint)

- **Golden** : inchangé `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`
  sur les 6 tronçons (couche B = vue passive ; ⑤⑥ = transport pont pur).
- **Pont** : `ENGINE_VERSION` 0.5.4 → **0.5.6** (deux entorses transport : ⑤ 0.5.5,
  ⑥ 0.5.6).
- **Smoke pont** : 185/186 — seule rouge = « pommier pré-âgé noue des fruits @ S52 »
  (`tests/simserver/morts.py`), **PRÉEXISTANTE** (datée du re-figeage thermique) et
  **hors périmètre**.
- **Build C#** : `dotnet build Symbiose.csproj` vert (0 avertissement, 0 erreur).

## Décisions notables

- **Dérogation D10 assumée** : la forme de feuille est codée **directement en C#**
  (pas de maquette SVG Python préalable) — tranché par Nico au cadrage (verrou ③).
  Justifié : une silhouette de limbe est un pur fait de rendu, sans contrepartie
  écologique à valider côté moteur.
- **Litière en repli `Elliptique`** : l'espèce d'origine de la nécromasse **n'est
  pas traçable côté moteur** (la `Parcelle` de litière est typée par TISSU, pas par
  espèce) → toutes les feuilles mortes au sol sont elliptiques. Reporté en dette
  **D50** (si on veut des silhouettes d'espèce au sol, le moteur doit tracer
  l'espèce de la nécromasse).

## Dette créée / rappelée

- **D50** (neuve) — litière de feuilles non traçable par espèce (repli Elliptique).
- **D49** (rappel) — vrille grimpante E6, différée (sprint moteur séparé).

## Points F5 en attente (validation visuelle Nico, non bloquants)

Teintes des 23 espèces · silhouettes lobées/composées · nervures 1 px · pétiole
vert (émergence pas « posée dans le vide ») · croissance sans pop-in · litière
brun-roux dérivant vers l'humus. Knobs ajustables listés dans `00_etat.md`.
