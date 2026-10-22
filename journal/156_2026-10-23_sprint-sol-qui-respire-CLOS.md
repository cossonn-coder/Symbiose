## 2026-10-23 — Sprint LE SOL QUI RESPIRE (D111) — CLOS

`/sprint-auto sprint_sol_qui_respire` (`sprints/champs/sol/sprint_sol_qui_respire/`).
8 tronçons figés + **3 ajoutés en cours de route** avec Nico (②bis, ②ter, ⑦bis), parce que
deux tronçons livraient une mécanique codée mais **inerte** en jeu. Golden final
`fecccded8cd146368623372919f4bdc6c61fb8bb997c75fdc59806f08dc3898b`, pont 0.5.56.

### Tronçons
- **① bilan hydrique** (`a9c1b82`) — rosée calculée sur une humidité de l'AIR océanique
  saisonnière (casse la boucle « sol sec ⇒ pas de rosée »), pluie dans toutes les saisons,
  transpiration portée par les feuilles (constante `feuillage` par espèce, ≈ 0 en dormance).
  Humidité médiane annuelle dans [1 ; 2] sauf graine 7 en années sèches [n=1 run/graine].
  Golden re-figé annoncé `22768f33…` → `1ce02bce…`.
- **② bois tombé** (`a5b572a`) — plomberie branche élaguée → litière `bois`. Inerte : aucune
  branche ne mourait (bois sans apex : ~77 ans).
- **②bis mort des branches** (`a5b94e0`) — cladoptose par l'ombre, casse tempête/neige
  (fragilité du bois par espèce), donnée `ligneux` (arbustes inclus), bois mort initial.
- **②ter arbres adultes** (`1b7753c`) — pré-croissance des ligneux pré-vieillis (**ferme
  D105**), tolérance à l'ombre par espèce (bouleau 0,75 … hêtre 1,30), cladoptose bornée.
  Golden re-figé annoncé `1ce02bce…` → `df6ebf04…` (seule cause : ombre du pommier).
- **③ règne fongique** (`9a95109`) — 13 espèces en données ; l'espèce émerge de l'offre du
  plot ; fructification la semaine qui suit la pluie.
- **④ parasite de faiblesse** (`52fe44e`) — attaque racinaire des hôtes déjà affaiblis ;
  `eau_percue` : une racine abîmée se fait enfin sentir (campagnol compris).
- **⑤ voix des champignons** (`2641604`) — une fiche par espèce (renverse Q2 vie macro),
  carnet, pages P43-P47, magazine.
- **⑥ manger / vision** (`8625b6c`) — comestible/vénéneux/mortel/psychédélique ; vision
  d'une semaine, `parler` (phrases générées depuis les vrais besoins), overdose.
- **⑦ nectar par espèce** (`b30806d`) — golden re-figé prévu `df6ebf04…` → `fecccded…`.
- **⑦bis bois continu** (`31ba317`) — la ceinture forestière lâche du bois en lisière,
  décompo selon le diamètre (demi-vie 0,7 an à 0,3 cm → 14 ans à 30 cm), le parasite peut
  tuer (`pourriture_memory`). Bois au sol `full` 18 → 68 en 3 ans (base 1,7) [n=1 run].
- **⑧ vue Godot** (`6e54142`) — bois mort à stades, 13 portraits de champignons, manger,
  shader de vision, murmures d'overdose. Build vert.

**Décision :** perf +33 % en an 2 acceptée (la population survit enfin à la soif, coût par
plante inchangé) → **D114 URGENTE**, F5 suspendu par Nico jusqu'à sa résolution.
**Décision :** banc `test_succession` (4/6) conservé tel quel : la bascule pionnière reposait
sur la soif → trou de mécanique → **D115**.
**Décision (Nico) :** le bois mort continu vient de la ceinture forestière ; le gros bois se
décompose lentement ; le parasite peut tuer.

### Constats
- D110 (h) résolu ; (g) et (i) NON résolus (acclimatation surtout d'ombre ; butineurs sous
  0,1 de nourriture à 54-59 %).
- Leçon : deux prémisses de kickoff fausses (élagage supposé actif ; pommier pré-vieilli
  supposé adulte) — un tronçon doit mesurer son **effet en jeu**, pas seulement passer ses tests.
- Zone jaune (300-400 LDC) : `perennials.py` 397, `WorldView.ActionDispatch.cs` 393,
  `serialize.py` 387. Aucun fichier rouge → `/refactor` sans scission.
