# Rapport perf TERRAIN — F5 Nico, 2026-07-08 (avant D67)

> Mesure réelle in-game (émetteur `world/WorldView.Hud.cs`), collée avant le
> lancement de `/sprint-auto sprint_perf_lod_ombre`. Sert de **référence de
> calibrage** au bras fidélité (①) et au choix de `SHADING_POWER_MIN` (②).
> Rappel : `perf_dumps/` est gitignoré (dumps JSON transitoires) → ce rapport
> lisible vit ici, committé.

## Rapport brut

```
=== Rapport perf Symbiose — ete an 2 semaine 11/13 ===
[client] FPS 4 · tick 3770 ms · cadence 4,0 s/sem (1,7 j/s)
  plantes 519 (+0 pousses) · segments 4821 · vie macro 12065 · butineurs 43 · ombres OFF · zoom ×2
[serveur] tick moteur 2929,1 ms · N plantes 519 · RSS —

--- pires ticks (serveur) ---
  s52 (an 1) : 6240,8 ms · 272 pl · 1224 seg · RSS —
    tuiles (pl/seg) : E 52/188  N 19/84  NE 23/121  NO 55/164  O 34/142  S 44/289  SE 22/125  SO 23/111
    espèces : AppleTree×1  Basil×15  Bean×8  BursaPastoris×47  Clover×60  MedicagoLupulina×60  Phacelia×4  PoaAnnua×35  Sunflower×12  Taraxacum×26  Yarrow×4
  s50 (an 1) : 5784,0 ms · 246 pl · 1180 seg · RSS —
  s51 (an 1) : 5713,9 ms · 260 pl · 1201 seg · RSS —
  s49 (an 1) : 4470,8 ms · 243 pl · 1176 seg · RSS —
  s48 (an 1) : 4246,6 ms · 241 pl · 1170 seg · RSS —
--- état courant ---
  s76 (an 2) : 2540,3 ms · 522 pl · 4974 seg · RSS —
    tuiles (pl/seg) : E 112/851  N 30/290  NE 33/379  NO 179/966  O 47/568  S 53/1015  SE 36/514  SO 32/391
    espèces : AppleTree×1  Basil×13  Bean×8  BursaPastoris×76  Clover×220  MedicagoLupulina×80  Phacelia×4  PoaAnnua×67  Sunflower×12  Taraxacum×37  Yarrow×4
```

## Lecture pour D67 (2 signaux)

### Signal 1 — la cible de D67 est CONFIRMÉE par le terrain
La population réelle est massivement dominée par des **semis émetteurs
sous-seuil** : à s76, `Clover×220 + PoaAnnua×67 + BursaPastoris×76 +
MedicagoLupulina×80 + Taraxacum×37` = ~480 des 522 plantes. Ce sont exactement
les petites plantes à `pouvoir = height × canopy_radius × foliage_density`
faible que D67 veut **cesser de faire émettre**. Les grosses canopées (tuiles
**S** 1015 seg, **NO** 966 seg) restent réceptrices ET émettrices. → hypothèse
« coût perf estimé » du `00_etat.md` **validée sur données réelles**, pas
seulement théorique.

### Signal 2 — le pic n'est PAS géométrie-dominé → surveiller D6(e)
Anomalie à intégrer au calibrage : les **pires ticks sont fin an 1**
(s48→s52 : 4246→6240 ms) à **peu de plantes / peu de segments** (272 pl /
1224 seg), alors que l'état courant an 2 est **plus rapide** (2540 ms) avec
**~2× plus de plantes et 4× plus de segments** (522 pl / 4974 seg).

Plus de segments = tick plus court : le pic an 1 n'est donc **pas** dominé par
la géométrie d'ombre (que D67 attaque) mais par autre chose de saisonnier —
très probablement la **vague de germination / reproduction de fin d'été**
(les comptes de semis grimpent sur s48→s52 : BursaPastoris 30→47, Clover
49→60). C'est précisément le **5ᵉ critère du bras fidélité (D6(e))** : « coût
perf de la germination surnuméraire ». Or D67 coupe l'ombre au sol →
**plus de lumière-sol → risque d'AUGMENTER la germination** → risque
d'aggraver ce pic an-1 même si le tick moyen baisse.

**À prendre en compte au ② (calibrage), sans changer la conception** (D5/D6
l'anticipaient déjà) : choisir `SHADING_POWER_MIN` en regardant non seulement
le ms/tick moyen an 6, mais **le pic de fin d'été** et le **comptage
germination/saison** (D6 critères c+e). Cibler an 1 s48-s52 dans le banc
`diag_lod_ombre.py`, pas seulement l'état stabilisé.

> Note secondaire hors D67 : ce pic an-1 de fin d'été à faible N est un
> candidat perf indépendant (germination/reproduction saisonnière) — à verser
> en dette perf si D67 ne le résorbe pas.
