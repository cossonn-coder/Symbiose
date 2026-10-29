# Sprint CASSÉ À L'ÉCRAN (D112) — état partagé

**Conception FIGÉE le 2026-10-29** (`/conception D112`, accord Nico « oui »). Doc :
`docs/rendu/pixelart/conception_casse_ecran.md`. **Référence visuelle** (brief de Nico,
gravé tel quel) : `docs/rendu/pixelart/etude_brief_da_16bits.md`. Pure vue + pont
lecture/debug → **golden JAMAIS re-figé** (`fecccded…`, `python3 -m tests.test_golden`
depuis `data/code/`). Filet C# : `dotnet build Symbiose.csproj`. Yeux : `tools/capture_vm.sh`.
Perf : `tools/perf_vm.sh`.

## Décisions clés
- Périmètre = tout D112 (Nico) ; hors : bug de vent en longue partie, nuit (→ D117), sol (D34).
- Une espèce = UNE recette (rampe 3-5 tons à teinte qui dérive, motif, squelette, accent,
  ancrage), **la même à tous les paliers** : palier fin = plus de motifs.
- Masses sans contour ; petits objets = trait de la teinte sombre de LEUR rampe ; jamais `#000`.
- Éclat côté **soleil réel** (`WorldView.SunShadowDir`) ; ombres portées gardées mais teintées.
- **Palette indexée** : atlas = indice de ton + orientation de face ; shader + LUT par matière ;
  F11 post-process retiré ; 0 recuisson au mouvement du soleil.
- Dialectes : SoM = plante seule ; CT forêt = couverts denses / lisière ; nuit = dette D117.
- Iso 2:1 gardée ; bruit/variation = hash, jamais Random. Validation = banc de mesure (①),
  F5 Nico = ressenti seul.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_charte_banc_mesure.md` | à faire |
| ② | `02_defauts.md` — (b)(n)(e)(d)(h) | à faire |
| ③ | `03_palette_indexee_soleil.md` — (f)(l), paliers bas | à faire |
| ④ | `04_paliers_hauts.md` — (i)(m) | à faire |
| ⑤ | `05_faune_icones.md` — (a) | à faire |
| ⑥ | `06_lisiere_decor.md` — (k) + résidus lisière | à faire |
| ⑦ | `07_bilan_ecran.md` — planche, mesures, protocole F5 | à faire |

## Notes de tronçon
(chaque tronçon ajoute ici : ce qui est fait, mesures avant/après, écarts au kickoff)

## §REPRISE
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancement : `/sprint-auto sprint_casse_ecran`.
