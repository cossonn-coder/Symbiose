# 2026-07-23 — Conception RETOURS UI/HUD POST-FENÊTRAGE (D89) — FIGÉE

`/conception` sur repo, cinq retours F5 de Nico après le sprint fenêtrage, tous de
la **vue** (C#/Godot). Amorce recadrée par la lecture du code : les deux « vraies
inconnues » de l'amorce (quel texte du bas ? un journal par plante existe-t-il ?) ont
été levées au `grep`.

## Constats de terrain (vérité, pas hypothèses)
- **Palette** (`WorldView.Palette.cs`) lit **déjà** `gestes_debloques` et **grise** les
  verrouillés (choix « plus pédagogique » assumé, ligne 109) ; `Gestes[]` ≈ 28 ;
  accélérateurs 1..9 (pas 0-9).
- **« Texte du bas »** = le `Label legend` (`WorldView.Hud.cs:155`, `PROVISOIRE`),
  pleine largeur à `y=1080-96`, **recouvre le bas du champ** ; déjà dans le HUD → « le
  mettre dans le HUD » = **le sortir du champ**.
- **Launcher** = `CanvasLayer` **détruit** au « Lancer », `_ExitTree` ferme proprement
  le pont → `ReloadCurrentScene` redémarre tout sans démontage manuel.
- **Aucun historique chronologique par plante.** L'état par instance = **mémoires
  scalaires intégrées** (shade/drought/asphyxie/cold/infection/wind/root_herbivory/
  stress ∈ [0,1]) + vitalité/état + expression plastique + symptômes + stade/âge/gènes.
  Le seul chrono = `sim/journal.py`, mais **spatial** (zone tuile), par joueur, opt-in.
  Snapshot expose déjà état/gènes/symptômes ; picking `FindPlant()` existe.

## Arbitrages Nico (D1-D5)
- **item 4 = FORK A, dossier INSTANTANÉ** (pas de log moteur : coût mémoire run éternel
  + recoupe `journal.py`). Le clic lit l'ÉTAT courant ; les mémoires SONT l'histoire
  compressée (honnête).
- **item 1** : **masquer** (renverse le grisé), modèle **slot cap 10** touches **1-9+0**,
  auto-remplissage + **débordement invisible** (pas de FIFO), **édition clic droit**,
  persistance **globale** `user://`.
- **item 2** : légende → overlay **F1 masqué par défaut** (= premier geste de D54(a)).
- **item 3** : launcher pleine hauteur (plafond scroll 360→écran).
- **item 5** : **Échap → `ReloadCurrentScene` immédiat**, sans confirmation ; précédence :
  ferme un panneau ouvert d'abord.

## Découpage — 3 tronçons (dernier = vue+pont)
- **T1** palette gérable (pure vue, golden INCHANGÉ) ·
- **T2** chrome & navigation = items 2+3+5 (pure vue, golden INCHANGÉ) ·
- **T3** dossier de plante au clic = ajout snapshot `serialize.py` (mémoires+expression+
  âge, hors `_PLANT_ATTRS`) + panneau debug C# (golden **NEUTRE** annoncé, bump pont).

## Croisements
- **item 2** = premier geste concret de **D54(a)** (HUD diégétique, sans le compléter).
- **item 1** **résout autrement le débordement de palette** signalé par **D80(d)**
  (cap+masquage+édition au lieu de grille multi-colonnes).

Doc `docs/joueur/interface/conception_retours_ui_fenetrage.md` + sprint
`sprints/joueur/interface/sprint_ui_retours_fenetrage/` (00_etat + 01_palette ·
02_chrome_navigation · 03_dossier_plante). DETTE **D89 → 🟢** (conçu, prêt). Prêt pour
`/sprint-auto sprint_ui_retours_fenetrage`.
