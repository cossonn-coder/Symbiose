# 2026-10-26 — Sprint FLUIDITÉ PC LEVIERS (2ᵉ temps D116) — CLOS (`/sprint-auto`, ①→⑤)

Conception : `docs/perf/fluidite/conception_fluidite_pc_leviers.md` · état :
`sprints/perf/fluidite/sprint_fluidite_pc_leviers/00_etat.md` (bilan + §F5 détaillés).
Ordre décidé par Nico : vue d'abord, re-mesure PC, moteur Python ensuite (hors sprint).

## Tronçons
- **①** `07c703b` — journal des changements de palier (`WorldView.ZoomJournal.cs`), rapport
  copiable **touche Z** (F8 réservée par l'éditeur), balayage `tools/perf_vm.sh -Z`.
  Chiffres « avant » : pire image au cran 233-442 ms, 590 plantes invalidées par cran.
- **②** `b25718f` — butineurs + pollen en un lot `LotTriangles.Grain()` (losange/octogone
  pixel-art au lieu de `DrawCircle`). Draw calls phase C 1 037 → 608, butineurs
  2,16 → 0,32 ms/image ; rendu CPU VM inchangé (llvmpipe) [n=1 run, VM].
- **③** `837b7e0` — décor : une maille prête par palier (`DecorLayer.Mailles.cs`), construite
  en fond par tranches → décor au cran 27-37 → 0 ms ; plantes non cuites gardent leur dessin
  mis à l'échelle jusqu'à cuisson. Pire image au cran 292 → 279 ms : la **cuisson** domine
  désormais [1 balayage, VM]. Une tranche de fond atteint 21 ms au démarrage (budget 8 ms).
- **④** `efff211` — pont en **delta opt-in**, protocole **0.6.0** (`pont_delta.py` /
  `PontDelta.cs`) : segments nouveaux/changés + semaine de naissance, gènes une fois, liste
  des disparues ; équivalence delta ≡ complet testée (36 réponses). Réponse 2 383 → 915 Ko,
  lecture plantes 247 → 63 ms [n=1 run, VM chargée].
- **⑤** `cf0fb59` — lisière côté caméra **devant** le jardin (`DecorLayer.Devant.cs`, +1 draw
  call, recalculée à la rotation, boussole au-dessus) ; bilan VM ; protocole PC ; D112 (n)
  ouverte (la forêt avant masque une bande du jardin à ×1).

## Bilan VM du sprint [n=1 run par mesure, « avant » à des charges VM différentes]
Rendu actif 1 s/sem demandée : 2,80 → 2,10 s/sem · rendu suspendu 1,67 → 1,32 s/sem ·
pire image au cran (12 crans) 292 → 249 ms. Aucune image < 100 ms sur VM : le run PC tranche.

Golden jamais re-figé `fecccded…`, build C# vert partout, pont 300/300. Refactor auto-léger
no-op (aucun fichier du sprint > 400 LDC).

## Suite
1 run PC de Nico (protocole `00_etat.md` §F5) → 3ᵉ temps D116 (levier moteur si 2 s/sem
non tenu ; cuisson au cran = prochain goulot vue).
