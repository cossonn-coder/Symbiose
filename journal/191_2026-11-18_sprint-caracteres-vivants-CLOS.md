# 2026-11-18 — Sprint CARACTÈRES VIVANTS (D139, sprint ③ sur 3) — CLOS côté code

Tronçons ①, ①b, ①c, ①d, ②→⑥ faits (`sprints/vegetal/genetique/sprint_caracteres_vivants/`),
exécutés par `/sprint-auto`. D139 close côté code sur ses trois sprints ; F5 attendu.

## Ce qui change
- ① Fleurs : taille, nectar, pollen, couleur (axe par espèce, préférence par butineur),
  guides à nectar, parfum ; `cout_genetique`. Golden `d05997a4…` (`968704c`).
- ①b Fécondation à la fanaison `a + (1−a)·g(pollen_recu)`, lue partout où le taux de
  graines l'est ; part autofécondée ; pommier mûr dans le smoke. Golden `db941814…` (`b157ee6`).
- ①c Compteur `pollen_donne`, père tiré au hash ∝ pollen exporté. Golden INTACT (`96505f5`).
- ①d Annuelles qui se ressèment depuis leur pool ; espèce spontanée ∝ ε + densité du pool.
  Golden `5d26af06…` (`9fdcbe9`).
- ② Taille des fruits, appétence feuille/fruit, bouchée toxique (Vigueur négative),
  `sim/gout.py`. Golden `c6fd8275…` (`0134bd5`).
- ③ Coriacité, repousse, bouture au hash, dormance, dominance apicale. Golden `5bfbd8a3…` (`bc22825`).
- ④ Clonalité, portée des graines, fixation, allélopathie, mycorhization. Golden `db4d6b75…` (`dac1231`).
- ⑤ 7 signes dérivés des gènes, « fané sans graines », 20 libellés au survol G, voix.
  Pont 0.6.20. Golden INTACT (`5b17796`).
- ⑥ Vue : pétales en dégradé, guides, taille, matité, port, rejets, têtes fanées ; banc
  `caracteres_vivants`. Golden INTACT (`df5a57f`).

## Constats
- Sélection réelle de la couleur : pool des bourraches +0,016 → −0,047 vers le bleu
  [n=16 pieds, 1 seed] après ①d ; la lignée s'éteint vers l'an 4.
- Trèfle fondateur très clonal (gène 1,185) : pic de population 598 → 751 en hiver an 2,
  même plateau en an 5-6 [n=1 seed, 5 ans] ; emballement assumé (décision Nico).
- Run F5 PC (monde full, code du ① seul) : cultivées du SE mortes s0-1 cause
  `non_consignee`, cerisier 3 → 52 en an 3 ; à verser en dette après F5.
- Refactor auto-léger : rien > 400 LDC ; 🟡 `cultivees.py` 384, `sauvages.py` 379.

## Suite
F5 de Nico (recette 12 points dans `00_etat.md`) ; arbitrages listés en §REPRISE.
