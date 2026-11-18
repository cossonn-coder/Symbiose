# ④ Vieillesse, fin de cycle, paiement aux champignons (golden RE-FIGÉ annoncé)

Lire : `CLAUDE.md`, `00_etat.md` (ce sprint + sprint A), conception §1, §5.

## Biologie
- **Vieillesse** : avec l'âge, la photosynthèse rapporte moins et l'entretien
  coûte plus (bois, tissus à maintenir) → l'arbre s'épuise et meurt de famine.
- **Fin de cycle** : l'annuelle ou la bisannuelle remobilise tout vers ses graines
  (ses réserves partent dans les graines), puis meurt.
- **Mycorhize** : la plante paie le champignon en sucres (jusqu'à 10-20 % de sa
  production) et reçoit phosphore et azote. Le paiement est déjà la part `X` du
  bilan ; ici il devient un vrai échange lu par le champ fongique.

## Existant
`sim/engine/mortalite.py` `_tick_senescence_health` (sénescence au sort,
`SEN_RATE`, `onset_senescence` de `sim/tempo.py`) ; `sim/engine/fin_de_cycle.py`
(`fin_de_cycle`, `semer_fin_de_cycle`) ; exsudats `_apply_exudates`
(`sim/engine/croissance.py`) ; champ fongique (`fields/fongique.py`), gène
`mycorhization`.

## À faire
1. Sénescence : après l'onset (`onset_senescence`, inchangé), `photo_max`
   effectif décline et l'entretien croît → famine émergente ; supprimer le tirage
   `SEN_RATE` (commenté, conservé). Cause consignée `vieillesse` quand la famine
   survient après l'onset.
2. Fin de cycle : les réserves sont transférées aux graines (le nombre/la vigueur
   des graines peut en dépendre si un lecteur existe — sinon simple vidage), puis
   mort (cause `fin de cycle`, inchangée).
3. Paiement mycorhizien : `X` du bilan alimente le dépôt d'exsudats existant
   (remplace `lumière × surface × santé` par la vraie part carbone) ; vérifier au
   code qui lit les exsudats avant de changer leur forme.
4. Tests : longévités des espèces conservées à ±20 % (banc sur arbres isolés) ;
   une annuelle meurt après grenaison ; exsudats ∝ photosynthèse.

## Golden
RE-FIGÉ annoncé, dérive prouvée par neutralisation des chemins du tronçon.
