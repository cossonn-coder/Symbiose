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
| ① | `01_charte_banc_mesure.md` | **fait** (2026-10-29, non commité) |
| ② | `02_defauts.md` — (b)(n)(e)(d)(h) | à faire |
| ③ | `03_palette_indexee_soleil.md` — (f)(l), paliers bas | à faire |
| ④ | `04_paliers_hauts.md` — (i)(m) | à faire |
| ⑤ | `05_faune_icones.md` — (a) | à faire |
| ⑥ | `06_lisiere_decor.md` — (k) + résidus lisière | à faire |
| ⑦ | `07_bilan_ecran.md` — planche, mesures, protocole F5 | à faire |

## Notes de tronçon
(chaque tronçon ajoute ici : ce qui est fait, mesures avant/après, écarts au kickoff)

### ① Charte + banc de mesure — fait
- **Table des rampes** `visuals/RampesDa.cs` (NON branchée au rendu, c'est ③) : 12 matières
  hex du brief (canopée jour, tronc, buisson vif, couvert olive, touffe claire, gazon, feuille
  de fleur, fleur jaune, fleur magenta, terre cuite, pierre, crème) ; `Deriver(base)` OKLab →
  5 tons (base = ton 2 inchangé ; ombre vers 230° froid, clair vers 105° jaune, 6°/cran ;
  ombre des jaunes → orangé ; anti-noir sous L 0,33) ; recettes `Plante/Faune/Carpophore`
  mémoïsées ; `Contour(rampe)` = ton le plus sombre. Accesseurs lecture seule ajoutés :
  `PlantRenderer.TeintesEspece` (Organs.cs), `MacroLife.CouleurEspece`. Valeurs NON mesurées
  du brief (ombre de fleur jaune, magenta, gris crème, pierre) = dérivées puis figées, signalées.
- **Banc** `tools/mesure_da.py` (+ `tools/da_image.py` : PNG et OKLab en stdlib pure — ni PIL
  ni numpy sur la VM). Mode monde = paire test/réf : même capture avec `-x …,Objects` → masque
  par différence (ombres = assombrissement uniforme retiré) ; mode planche = fond uni.
  `--charte visuals/RampesDa.cs` contrôle la table (0 défaut). Chaque seuil a sa ligne de
  rationale en tête du fichier. ~12 s par image [VM].
- **`capture_vm.sh`** : `-F` (palette F11 au montage) et `-O` (ombres portées coupées).
- **Écart au kickoff** : la planche L ne pose PAS les espèces séparément (elle zoome sur UNE
  plante du monde) → isolation par la paire test/réf. Protocole retenu :
  `capture_vm.sh -b BANC -c X,Y -w W -O -x Weather,MacroLife,House [-F] -l 2 -n 190` puis la
  même avec `,Objects` ; `mesure_da.py planche_xN_t.png --ref planche_xN_r.png`. La planche
  nomme ×0,5 `planche_x0,5.png` (virgule).
- **Ligne de base AVANT** (médianes par sprite, pixels logiques, soleil de référence 135° ;
  chaque cellule [n=1 capture]) :

| scène | palier | sprites | tons lus | qnoir % | dérive ° | aplat px (> 24) | éclat côté soleil | voisins identiques |
|---|---|---|---|---|---|---|---|---|
| luxuriance F11 off | ×1 | 5 | 4 | 0 | 25,8 | 1 (0/5) | 0/5 | 1/2 paires |
| | ×2 | 10 | 6 | 0 | 43,0 | 1 (0/10) | 3/10 | 0/14 |
| | ×4 | 15 | 5 | 0 | 2,2 (7/15 > 3°) | 94 (13/15) | 7/15 | 0/9 |
| | ×16 | 6 | 2 | 0 | 10,7 (3/6) | 190 (6/6) | 2/6 | — |
| luxuriance F11 on | ×1 | 4 | 5 | 0 | 48,6 | 2 (0/4) | 0/4 | 0/1 |
| | ×2 | 10 | 6 | 0 | 15,5 | 2 (0/10) | 3/10 | 0/17 |
| | ×4 | 26 | 5 | 0 | 41,7 | 82 (21/26) | 11/26 | 0/106 |
| | ×16 | 9 | 3 | 0 | 32,5 | 86 (7/9) | 2/9 | 0/2 |
| forêt (automne, nus) | ×1 | 11 | 5 | 0 | 39,4 | 2 (1/11) | 4/11 | 0/3 |
| | ×2 | 13 | 4 | 0 | 20,2 | 3 (3/13) | 5/13 | 0/2 |
| | ×4 | 4 | 1 | 0 | 0,0 (0/4) | 20 (1/4) | 0/4 | — |
| diversité (tournesols) | ×2 | 18 | 4 | 0 | 40,1 | 3 (0/18) | **0/18** | **10/138** |
| faune (luxuriance) | ×4 | 8 | 1 | **3/8 sprites à 100 %** | 0,0 | 17 (3/8) | 3/8 | 1/3 |

  Lecture : (1) **paliers hauts = aplats** (×4/×16 : 13/15 et 6/6 sprites > 24 px d'un seul
  ton) et dérive qui s'effondre (×4 : 2,2°) — cible ④ ; (2) **éclat jamais côté soleil** aux
  bas paliers (0/5, 0/18 : l'éclat est en BAS du sprite, cf. `Kit.cs` `Eclairement`) — cible
  ③ (l) ; (3) **voisins identiques** à ×1/×2 (10 paires de tournesols) — cible hash ③/④ ;
  (4) **faune quasi-noire** (merle/carabe : 3 sprites 100 % quasi-noirs) — cible ⑤ ; (5) aucun
  quasi-noir sur les plantes (le contour ×1 actuel est vert sombre, pas neutre) ; (6) couleurs
  brutes 24-43 par sprite de 50 px à ×1 = fondu non indexé (attendu jusqu'à ③).
  **Trouvaille hors mesure** : à ×16 la planche sur le cerisier (forêt) n'affiche AUCUN pixel
  de l'arbre (0 sprite, image vérifiée) → à regarder en ④.
- Captures de la ligne de base (hors dépôt, effacées au reboot) : `/tmp/claude-1000/da/base2/`.

## §REPRISE
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire » (② `02_defauts.md`).
Lancement : `/sprint-auto sprint_casse_ecran`. Valider chaque tronçon visuel au banc :
protocole et ligne de base en §Notes ① (`tools/mesure_da.py`, `capture_vm.sh -O -F`).
