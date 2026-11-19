# 2026-11-19 — Sprint STRESS AU BILAN CLOS côté code : chaque stress retire ce qu'il retire

`/sprint-auto sprint_stress_au_bilan`, ①②②bis③④⑤ (D140 G, sprint B). Conception :
`docs/vegetal/sante/conception_plante_vivante.md` §4-§5. Suite du sprint A
(`sprint_plante_vivante`) et de `sprint_lisibilite_bilan`.

## Ce qui a changé
- ① Sécheresse : stomates fermés (le bilan) puis **embolie** (`sim/embolie.py`) ; au
  seuil, mort par défaillance hydraulique (« meurt de dessèchement », cause
  `secheresse`). Golden intact.
- ② Froid sans gel et brûlure retirent du feuillage ; le gel retire des feuilles ou
  détruit (bourgeons et collet gelés) ; gel-dégel des ligneux → embolie. Golden
  re-figé `32355a1c…`.
- ③ Mildiou retire du feuillage, oïdium voile la production, fonte des semis détruit,
  asphyxie fait perdre des racines (seulement quand le sol est gorgé), annélation
  consignée. Golden re-figé `bd5e11ab…`.
- ②bis (décision Nico) : la grêle touche toutes les plantes (adulte : moitié exposée
  du feuillage, jamais de destruction). Golden re-figé `f5876f5a…`.
- ④ Vieillesse au bilan (production rabotée, entretien majoré → famine de vieillesse,
  cause `sénescence`) ; fin de cycle qui remplit les graines de ses réserves ; exsudats
  ∝ part racinaire du bilan. Golden re-figé `bce813af…`.
- ⑤ Vue et voix (golden **intact**, pont 0.6.24) : `sim/causes_bilan.py` — la mort de
  famine est consignée au carnet et à la chronique sous la cause qui a miné la plante
  (marques de tissus, racines, embolie, facteur limitant du bilan), le log du moteur
  inchangé ; info-bulle « desséchée », « gelée au cœur », « racines pourries », « à bout
  d'âge » ; signe NEUF oïdium (blanc) ; signe sécheresse qui lit l'embolie (reste flétri
  après la pluie) ; banc `stress_au_bilan` (une plante par cause, morts s12-s19
  [seed 42, n=1]) + oracle à la demande ; tests `test_causes_bilan` (20/20).

## Écarts au kickoff (⑤)
- Le limitant du bilan passe AVANT les signes chroniques pour nommer la cause d'une
  famine (sinon le poivron mort à l'ombre sortait « herbivorie », collet rongé).
- Pas de clé neuve `embolie` rendue : elle passe par l'intensité du signe `secheresse`
  (dessin existant) ; exportée seulement au dossier debug.
- Gel noirci : déjà rendu par le palier thermique `gel` (teinte `ThNoirci`).

## Reste
F5 Nico (recette dans `00_etat.md`) → D140 (G) close. Puis reprise de
`sprint_depart_jardin` ④. Reliquats en D142 (réseau fongique qui ne lit pas les
exsudats, longévités raccourcies — ortie −21 % [n=1] —, seuils de voix non mesurés).
