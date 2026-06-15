## 2026-06-13 — Sprint décompo & compost · sous-sprint ② · **Phase A** : dépôts immédiats — golden NEUTRE

② est **GROS** (kickoff §Ampleur) ; **A|B est un point de coupe valide** → cette
session livre la **Phase A seule** (dépôts immédiats), B (squelette persistant +
ombre, risque #1) et C (abscission, écraser-squelette) suivront après `/clear`.

**Intention Nico réalisée (« toute matière taillée doit être en décomposition »)**
et raffinage de la litière de mort par **constitution** :

**Seam — décision (a) tranchée** : `atteindre_segment` (`sim/growth.py`) retourne
désormais la **liste des segments réellement retirés** (`[]` en DOUX ou sur le
collet protégé). Le bois déposé vient de ce qui a *vraiment* été coupé. Sûr : les
2 appelants (`tailler`, `ecraser_plante`) et les 4 appels de `test_croissance`
ignorent la valeur de retour.

**`tailler`→`bois`** : dépose `Σ length_cm × BOIS_PAR_CM` (nouveau knob
`ecofields.py`, =0.03 aligné sur `NECROMASS_PER_CM`) du sous-arbre retiré, en
litière `bois` au plot-foyer (philo #2 : on dépose, le tick décompose ; le `bois`
humifie fort → humus, §1.2). Gain Vigueur **inchangé** (on récupère ET on rend).
`ecraser_plante` (même seam) dépose **aussi** sur écimage NET — voulu (le coup de
pied qui casse une branche la met au sol).

**Mort → tissus mous typés** : `add_necromass` gagne un param `tissu` (défaut
`herbace` → compat bit-identique ①). Helper `sim/effects.tissu_mort(plant)` =
`feuille` (caducs `deciduous`) / `herbace` (annuelles, tiges molles). Câblé aux
**6 sites de mort** (`engine.py` : alea-santé, sénescence, conflit, bisannuelle,
annuelle-`die`, `_mediated_damage`) + `deraciner` (`actions.py`). Résidus de
récolte restent `herbace` (défaut). **Pas de bois à la mort en phase A** — la
fragmentation lente du squelette est la phase B.

**Golden NEUTRE (non re-figé, h1==h2 implicite)** : hashs **bit-identiques à ①**
— smoke `f75d1c21…`, population `9f351303…`. Raison : le seul caduc du scénario
(`AppleTree`) est **pérenne** → ne meurt pas en 2 ans ; toutes les morts sont des
annuelles **non caduques** → `herbace`, exactement comme ①. Et `tailler`/`ecraser`
/`deraciner` ne sont jamais appelés par le golden (succession pure). La dérive
caduque attendue viendra de l'**abscission (phase C)** : le pommier larguera du
`feuille` chaque automne.

**Tests verts** : golden, population, croissance 67, competition 14, eau 20,
sim_server 113, senescence, génétique 20, vigueur 135, maîtrise 35 ;
`main.py 30` exit 0.

**Suivant** : ② **Phase B** (squelette persistant : mort ne retire plus, nouveau
pass `tick_skeletons` sèche→couchée→fragmentation→retrait final ; **ombre =
silhouette nue = risque #1**, trancher §B.3) puis **Phase C**. Reprise :
`00_etat.md` §REPRISE + `02_depots_vivant_mort.md`.

---
