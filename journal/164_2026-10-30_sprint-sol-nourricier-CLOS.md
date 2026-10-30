## 2026-10-30 — Sprint SOL NOURRICIER (D120) — CLOS côté code (①→⑤)

`/sprint-auto sprint_sol_nourricier`. Golden `fecccded…` → `7791bfb8…` (①, annoncé)
→ **`4c696821…`** (②, annoncé), intact ③④⑤. `dotnet build` vert. État et mesures :
`sprints/champs/sol/sprint_sol_nourricier/00_etat.md`.

- ① recharge NPK vers l'équilibre de la roche + lessivage passif lié au drainage.
  **Écart** : demi-vies de la conception (N 1 an, P 5 ans) → sol à 12-17 % de l'équilibre ;
  calibré par mesure à N ≈ 10 sem., K ≈ 13, P ≈ 26 → NPK méd. an 2 ≥ 48 % de l'équilibre
  [seeds 42/1/2, n=3]. Pots/bacs sans recharge (pas de roche dessous).
- ② `sim/nutrition_plante.py` : facteur Liebig [0,4 ; 1] escompte `growth_factor` (après
  l'allélopathie). Haricot carencé −39 % à 26 sem. [1 banc, n=1] ; population 101-103 %
  [n=3] ; perf +0,7 % [n=2, bruit ±2,5 %].
- ③ voix : faim plante = 1 − facteur (seuil 15 %) ; faim bête = déclin imputé au lieu
  (nourriture/habitat) et non au froid/prédateurs. **Écart** : la définition « déficit
  face à la capacité » donnait 0 % ou 89 % d'affamés → imputation par baisse du tick
  (3 grilles de rendu). Bêtes affamées s26 95 % → 0 % [seed 42, n=1].
- ④ `sim/mare_initiale.py` : mare 3×3 en marais (aulnes, sphaignes, rossolis, moustique,
  libellule). **Écarts** : nappe affleurante neuve `fields/ecofields/source.py` (sans elle
  la mare séchait en 4 sem.) ; mare au **sud** de la tuile NE (le coin était vidé par la
  nappe de ceinture, seed 1). Centre en eau 104/104 sem. [n=3].
- ⑤ `visuals/PuddleLayer.Mare.cs` : eau sombre, reflets, rive de vase, berge moussue ;
  pont inchangé, +0 draw call.
- Restes : banc `carence_npk` (oracle `n < 0,3` faux depuis ①) et `test_edaphique`
  IndexError / `test_succession` 4/6 (pré-existants) ; sphaigne quasi invisible ;
  cloporte dit encore « rien à me mettre sous la dent » ; coquille « J'ai senti La
  libellule » ; tournesol/basilic morts à ~4 sem. dans la sonde ② sur les deux sols.
- Attend le **F5 de Nico**.
