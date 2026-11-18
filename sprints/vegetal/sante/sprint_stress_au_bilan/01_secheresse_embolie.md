# ① Sécheresse : stomates fermés + défaillance hydraulique (golden RE-FIGÉ annoncé)

Lire : `CLAUDE.md`, `00_etat.md` (ce sprint) + `00_etat.md` du sprint A,
`docs/vegetal/sante/conception_plante_vivante.md` §1, §5.

## Biologie
Quand l'eau manque, la plante ferme ses stomates : la photosynthèse tombe (c'est
déjà `f_eau` dans le bilan) et elle vit sur ses réserves. Si la sécheresse devient
extrême, la colonne d'eau casse dans les vaisseaux : de l'air y entre (**embolie**).
Un vaisseau embolisé ne conduit plus ; il ne se répare pas, la plante doit fabriquer
du bois neuf. Au-delà d'environ 90 % de conduction perdue, elle meurt desséchée.

## À faire
1. État `embolie` ∈ [0,1] sur `PlantInstance` (hors digest du golden, comme le
   sprint A l'a fait pour `feuillage`/`reserves`).
2. Accumulation quand l'eau perçue reste sous un seuil **extrême** propre à
   l'espèce (dérivé de `tolerance_secheresse` × gène exprimé ; la `drought_memory`
   existante peut servir de signal — vérifier ses lecteurs avant de la détourner).
   L'embolie réduit `f_eau` (moins de conduction) ; elle ne baisse qu'avec de la
   croissance nette positive (bois neuf), lentement.
3. Mort par **défaillance hydraulique** à `embolie ≥ SEUIL_EMBOLIE` (≈ 0,9), cause
   consignée `dessèchement` (log + chronique).
4. `drought_stress_damage` (`sim/effects/perturbations.py`) : supplanté (commenté,
   conservé) — la sécheresse agit désormais par `f_eau` (famine) et l'embolie.
5. Test `tests/test_embolie.py` : sécheresse modérée → la plante vit sur ses
   réserves et repart à la pluie ; sécheresse extrême prolongée → mort par
   dessèchement ; une plante tolérante tient plus longtemps.

## Golden
RE-FIGÉ annoncé, dérive prouvée (neutraliser l'embolie et le retrait de
`drought_stress_damage` → retombe sur le hash d'entrée).
