# 2026-11-19 — Sprint PLANTE VIVANTE (D140 G, A) CLOS côté code : la plante vit d'un bilan

`/sprint-auto sprint_plante_vivante`, ①→⑥, commits `56d5755` → `7c3bfc1`.

## Ce qui a changé
- ① Bilan carbone en ombre : `plants/physiologie.py` (3 paramètres × 52 espèces),
  `sim/bilan.py`, champs `feuillage`/`reserves`/`bilan_net`. Golden intact.
- ② `vitalite` = lecture (réserves × feuillage), écrire 0 = destruction ; `erode`
  retire du feuillage ; mort par famine ; morts et guérisons au sort neutralisées
  (code conservé). **Golden re-figé annoncé** `699edb51…`.
- ③ Herbivorie par atteinte (`sim/effects/herbivorie.py`) : limace < 40 cm, puceron
  = sucres, doryphore = Solanacées, chenille = feuillage ; perte rapportée à la
  quantité de feuilles ; mutation `PerteTissus`. **Golden re-figé annoncé**
  `8f2dd7ad…` (preuve : les deux herbivories neutralisées → même hash).
- ④ Souches à réserve finie : la souche hérite des réserves, 3 semaines par rejet,
  pas de souche propre avant 3 ans, mort de faim = souche vide. Golden intact.
- ⑤ Critères d'ouverture `full` (seed 42, s10→s30) [n=1] : 0/13 arbres posés morts ;
  19/123 = 15,4 % herbacées (≤ 25 %) ; 0 rejet (aucun arbre mort — critère non
  éprouvé en jeu, fin de cascade prouvée au banc ④). Chronique : âge vrai.
- ⑥ Pont 0.6.21 (`feuillage_bilan`, `reserves`), vue : feuilles clairsemées,
  ternissement suit les réserves, info-bulle à 3 phrases, Maj+F3 jauges ; banc
  `plante_vivante` (4 scènes).

## Chiffres
Avant/après (`full`, seed 42) [n=1] : posées mortes à s21 104 → 10.
Perf tick `full` s10→s30 sur le sprint : +9 % [3 paires].

## Écarts au kickoff (consignés dans `00_etat.md`)
Chaleur en rampe `lim_chaud`→`lim_brul` ; saturation lumière 0,4 ; réserve plantule
≥ 2 semaines ; entretien réduit au froid ; formule d'herbivorie rapportée au
feuillage ; `reserves_detruites` gardées pour la souche ; clé pont `feuillage_bilan`.

## Reste
F5 Nico (recette dans `00_etat.md`). Suite : `/sprint-auto sprint_stress_au_bilan` (B),
puis `sprint_depart_jardin` ④. Hors périmètre vu au ⑥ : étiquette de survol en nom de
classe anglais (« Comfrey · adulte ») → D141.
