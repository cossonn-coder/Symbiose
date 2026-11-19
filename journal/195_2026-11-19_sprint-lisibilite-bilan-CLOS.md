# 2026-11-19 — Sprint LISIBILITÉ DU BILAN CLOS côté code : la plante garde sa taille, parle français, laisse sa paille

`/sprint-auto sprint_lisibilite_bilan`, ①→③, commits `9e304cd` → `b7004be`.
Retours F5 de `sprint_plante_vivante` (A) + D141. Conception :
`docs/vegetal/sante/conception_lisibilite_bilan.md`.

## Ce qui a changé
- ① Hauteur acquise (moteur) : `hauteur_acquise` = max atteint pour les plantes
  sans segments ; la hauteur n'y redescend plus (le stress ralentit, ne rapetisse
  pas). Relâchée à la régression de stade et au repli hivernal des vivaces
  herbacées. Poivron à l'ombre : 60 cm jusqu'à la mort (avant 60 → 47).
  **Golden re-figé annoncé** `8f2dd7ad…` → `e24a23d8…` (mémoire neutralisée →
  ancien hash) : tiges restées hautes captent plus de lumière, morts de faim
  65 → 50 lignes, vivantes à w104 42 → 57 [smoke seed 42, n=1].
- ② Noms français (D141) : nom affiché = `cls.name` via la clé de pont `name`
  existante ; étiquette « nom · stade », dossier plante, planche, gènes, rapport
  F4, texte de chronique. Pont 0.6.22, test 52 espèces. Golden intact, snapshot
  du pont identique octet pour octet.
- ③ Vue + banc : pont 0.6.23 (masse/âge de la litière `herbace` par plot),
  `visuals/StrawLitterLayer.cs` (tiges paille → humus) ; `composter` les ramasse
  (bac requis). Banc `plante_vivante` ouvert sans semaine pré-simulée (consoudes
  broutées à 0,2), 3 consoudes. Info-bulles du bilan vérifiées par capture VM
  (`captures/`, 5 PNG). Golden intact, build C# vert.

## Écarts au kickoff
- ① Mémoire mise à jour AVANT le mouvement du growth_factor (sinon −2 cm au 1er
  tick). Pas de repli aérien « à ras » dans le moteur : la consoude descend à
  ~42 cm l'hiver ; un vrai repli à ras serait une mécanique neuve (non faite).
- ③ Consoudes broutées NON mises toutes deux à réserves basses (« épuisé » masque
  « refait ») : témoin / broutée pleine (refait en 6 sem) / broutée « à bout »
  (réserves 0,10 — proche du seuil de mort ~0,08, surveillé par l'oracle du banc).

## Reste
F5 Nico (recette dans `00_etat.md`) puis fermer D141. Suite :
`/sprint-auto sprint_stress_au_bilan` (B).
