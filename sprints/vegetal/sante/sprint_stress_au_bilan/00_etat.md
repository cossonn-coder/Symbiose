# Sprint STRESS AU BILAN (D140 G, sprint B) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/sante/conception_plante_vivante.md`
> (§4-§5). **Prérequis : `sprints/vegetal/sante/sprint_plante_vivante/` (A) CLOS** —
> ce sprint suppose le bilan carbone, `feuillage`, `reserves`, `vitalite` dérivée et
> l'adaptateur `erode` = perte de tissus en place. Lire l'`00_etat.md` du sprint A
> (acquis, noms réels des fonctions et constantes) AVANT tout tronçon.

## But
Remplacer l'adaptateur universel du sprint A par le **vrai mécanisme de chaque
stress** : ce qu'il retire (feuilles, sucres, eau, racines, vaisseaux, bourgeons).

## Décisions clés (Nico, 2026-11-18)
- Tout le vivant végétal passe au bilan ; plus de mort au sort.
- Causes de mort : famine, destruction, défaillance hydraulique, racines perdues,
  fin de cycle, vieillesse. Code supplanté commenté et conservé, jamais supprimé.

## Golden
Départ = `e24a23d8cb09…` (fin de `sprint_lisibilite_bilan`). ① **INTACT** (vérifié, voir Acquis) · ② **RE-FIGÉ → `32355a1c8649…`** (preuve par neutralisation) · ③ **RE-FIGÉ → `bd5e11abf44f…`** (preuve par neutralisation) · ④ **RE-FIGÉ annoncé** (dérive
prouvée localisée par neutralisation du seul mécanisme du tronçon) · ⑤ **INTACT**.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_secheresse_embolie.md` — stomates + défaillance hydraulique | **FAIT** (golden INTACT `e24a23d8…`, non commité) |
| ② | `02_froid_gel_brulure.md` — feuilles détruites vs bourgeons/sève gelés | **FAIT** (golden RE-FIGÉ `32355a1c…`, non commité) |
| ③ | `03_maladies_racines.md` — mildiou, oïdium, fonte, asphyxie, pourriture, campagnol | **FAIT** (golden RE-FIGÉ `bd5e11ab…`, non commité) |
| ④ | `04_vieillesse_cycle_mycorhize.md` — vieillesse, fin de cycle, paiement fongique | à faire |
| ⑤ | `05_vue.md` — signes, info-bulle, banc, clôture D140 G | à faire |

## Contrôle commun à chaque tronçon
Critères d'ouverture du sprint A toujours tenus (`tests/test_ouverture_vivante.py`) ;
perf tick `full` ≤ +10 % ; suites `tests/` vertes ; jamais `test_epaisseur_500ans`.

## Acquis du ① (2026-11-19)
- Départ réel = golden de `sprint_lisibilite_bilan` (`e24a23d8cb09…`, hauteur acquise),
  pas celui du sprint A.
- `sim/embolie.py` (neuf, pur) : `seuil_extreme(plant)` = `PART_EXTREME` 0,5 ×
  `SEUIL_SEC` 0,15 / gène `tolerance_secheresse` EXPRIMÉ ; `maj_embolie(plant,
  hum_percue, presence, surplus) -> bool` (accumule `TAUX_EMBOLIE` 0,20 × sévérité ×
  présence ; dilue `× (1 − RENOUV_BOIS 0,05 × min(1, surplus))` ; True à
  `SEUIL_EMBOLIE` 0,9) ; `conduction(plant)` = 1 − embolie.
- `PlantInstance.embolie` (hors `_PLANT_ATTRS`). `sim/bilan.f_eau` : rampe sèche sur
  `hum_percue × conduction` (la plante « voit » un sol plus sec ; sur sol arrosé une
  embolie partielle ne coûte rien). **Écart au kickoff (mesuré)** : un rabot direct
  `f_eau × conduction` mettait un chêne à 50 % d'embolie en déficit l'été sur sol humide
  → jamais de bois neuf → spirale de famine.
- `_update_physiology` : `presence` calculée une fois, puis après la famine
  `elif maj_embolie(…)` → `MortaliteMixin._mort_dessechee` (setter `vitalite = 0` =
  destruction, la souche garde ses réserves ; log « 🪦 X@pos meurt de dessèchement
  (embolie …) » + nécromasse). `sim/evenements._raison_mort` : « meurt de dessèchement »
  → cause **`secheresse`** (voix carnet/aide/concept `eau` EXISTANTES, pas de clé neuve
  `dessechement` — écart assumé au kickoff).
- `drought_stress_damage` SUPPLANTÉ (appel commenté dans `perturbations.py`, fonction
  conservée ; `DROUGHT_DAMAGE_THRESHOLD` reste lu par `souche_vivante`, `semiologie`,
  bancs). `drought_memory` NON détournée (5 lecteurs : plasticité, voix soif, signe,
  souche, pont) : l'embolie lit `eau_percue` du tick, l'accumulation fait l'intégration.
- Gène de tolérance sécheresse : aucune espèce ne le surcharge (neutre 1,0 partout) —
  pas de « tolérance d'espèce » comme le kickoff le supposait ; le seuil suit le gène
  individuel × plasticité seulement.
- Golden **INTACT** `e24a23d8…` (re-figeage annoncé inutile) : smoke ne descend jamais
  sous 2× le seuil sec (eau perçue / seuil ≥ 2 sur 5005 plante-semaines), `drought_memory`
  max 0,035 → ni l'ancien dégât ni l'embolie ne s'y exercent [seed 42, n=1].
- Effet en jeu (`full` seed 42 s10→s62, n=1) : `drought_memory` max 0,39 → l'ancien
  dégât ne tirait JAMAIS non plus ; embolie sur 51 plante-semaines, toutes des trèfles
  (max 0,63), aucune mort desséchée — le monde normand n'a pas de sécheresse extrême ;
  le mécanisme est prouvé par banc (`tests/test_embolie.py`).
- Banc `tests/test_embolie.py` : modérée (10 sem stomates fermés, réserves 0,79,
  embolie 0, pluie → remonte) ; extrême (chêne mort hydraulique en 5 sem, réserves 0,90) ;
  tolérante (sol 0,03 : neutre 8 sem, gène 1,5 → 12 sem) ; bois neuf (0,50 → 0,41 en
  4 sem, figé en dormance) ; tick réel → ligne 🪦 lue `secheresse`.

- `tests/test_ouverture_vivante` : 3 critères TENUS (arbres 0/13 ; herbacées 18/123 =
  14,6 % ; 0 rejet). Suites : vertes sauf `test_peripherie`, `test_population` et 6
  `tests/bancs/*` (climatique, biotique, edaphique, bancs_grimpe, liane_relais,
  verger_mur) — tous **rouges aussi sur HEAD** (worktree, vérifié), sans lien.
- Perf tick `full` s10→s30 [3 paires alternées, charge 5-8, bruitée] : HEAD 13,2 s →
  13,3 s (+0,8 %, dans le bruit).
- LDC : `croissance.py` 273, `mortalite.py` 250, `perturbations.py` 309, `instance.py`
  296, `embolie.py` 19, `bilan.py` 78.
- Pour ②③ : `_mort_dessechee` est le patron d'une mort par destruction consignée au
  log 🪦 (ajouter la phrase à `_raison_mort`) ; l'embolie de GEL-DÉGEL des ligneux
  (conception §5) n'est PAS faite — ② peut réutiliser `plant.embolie` (accumuler depuis
  le gel) et la même mort.

## Acquis du ② (2026-11-19)
- `sim/engine/reponse_thermique.py` : froid sans gel et brûlure → `PerteTissus` de
  feuillage (`FROID_FEUILLE_K` = `FROID_LESION_K`×⅓ = 1/12 /°C·sem, `BRULURE_FEUILLE_K` = 1/6
  /°C), sans `resilience_base` (la tolérance est déjà dans `lim_*`). `FROID_LESION_K`/
  `BRULURE_K` gardés (lus par `posture_thermique`). Anciens `ReduceHealth` commentés.
- Gel : `_gel_tissus(plant, effectif)` passé à `_mediated_damage(reponse=…)` (paramètre
  NEUF, `mortalite.py` ; None = ancien chemin `ReduceHealth`). Écart effectif (°C, après
  paillage) = effectif × `FROST_SEVERITY_REF` ; feuillage gelé = écart / marge ;
  écart ≥ marge → destruction (`PerteTissus(destruction=True)`, raison « gel (bourgeons
  et collet gelés) » → cause `gel`). `MARGE_BOURGEONS` 4 °C (herbacées),
  `MARGE_BOURGEONS_LIGNEUX` 8 °C (`plant_class.ligneux`). **Calibrage mesuré** : à 3 °C,
  carotte/bourrache semées en janvier (bancs catalogue, nuit −8,2 °C s4) et chênes du
  banc nucléation mouraient ; 4 °C tient tout sauf le chanvre (gel −3 °C, mort à −8 :
  biologique) → `test_catalogue_mulch` sème le chanvre en avril, `test_evergreen` sème
  ses 5 espèces en avril (bourrache).
- `PerteTissus` (`sim/effects/mutations.py`) : champs NEUFS `cause` (marque foliaire,
  gain = feuillage/VITALITE_STEP × `SYMPTOM_MARK_GAIN`, même échelle que `ReduceHealth`)
  et `destruction` (→ `vitalite = 0`, la souche garde ses réserves) ; `resolution.py`.
- Gel-dégel : `sim/embolie.maj_gel_degel(plant, nuit, t_air)` (ligneux ; nuit <
  `T_CONGELATION_SEVE` et t_air > 0 → `TAUX_GEL_DEGEL` 0,03 × min(1, écart/6)), appelé
  dans `_tick_nuit_froide` ; la mort passe par `maj_embolie` (physiologie, log
  « dessèchement » → cause `secheresse` : une mort par gel-dégel serait mal nommée —
  jamais observée). Inerte au golden (embolie hors digest, sol humide).
- Grêle : INCHANGÉE volontairement. Elle passe par `erode` (feuilles hachées ÷
  constitution) et ne frappe que les semis → « pas de mort directe sauf plantule » est
  déjà vrai. **Question Nico** : étendre la grêle aux adultes (perte de feuillage seule) ?
- Golden RE-FIGÉ `32355a1c86497409…` ; anciennes méthodes `_tick_nuit_froide`/`_tick_brulure`
  de HEAD réinjectées en mémoire → `e24a23d8…` exact. Smoke [seed 42, n=1] : morts
  thermiques froid 8 → 0, remplacées par famine (basilic 2, tomate 2, haricot 1) et gel
  (haricot 1, tournesol 2) ; vivantes s104 [44, 13] → [44, 14].
- Effet `full` s10→s62 [seed 42, n=1] : morts froid 40 → 0 ; famine 90 → 109, fin de
  cycle 39 → 61 (les tendres d'automne perdent leurs feuilles et meurent par le bilan) ;
  embolie de gel-dégel max 0,05 (bouleau). **À traiter en ⑤ (voix)** : la chronique dit
  « faim » là où le joueur voit le froid — la famine ne dit pas ce qui a retiré les feuilles.
- `test_ouverture_vivante` tenu (0 arbre, 18/123 = 14,6 %, 0 rejet). Perf tick `full`
  s10→s30 [1 paire, charge ~2] : 0,55 → 0,55 s. Suites : `test_reponse_thermique` étendue
  (22/22 : tomate gel léger vit / profond meurt, chêne endurci à −10 °C ne perd rien,
  gelée d'avril dégarnit sans tuer, gel-dégel) ; rouges = les mêmes que HEAD seulement.
- Le kickoff citait `test_niche_thermique` : il ne teste aucun dégât (limites seules) ;
  les tests de dégât vivent dans `test_reponse_thermique`.
- LDC : `reponse_thermique.py` 78, `mortalite.py` 254, `embolie.py` 26, `resolution.py` 235.

## Acquis du ③ (2026-11-19)
- **Mildiou** (`fungal_disease` ET l'effet familial Solanacées `reduce_health` de
  `resolution.resolve`) → `PerteTissus(feuillage = VITALITE_STEP / resilience_base)`,
  jamais de destruction (l'ancien `erode` détruisait si le coup dépassait la vitalité).
  Mildiou et oïdium passent dans `tissus_muts` (hors `_cap_chronique`, fonction conservée).
- **Oïdium** : mutation NEUVE `Oidium(plant, couverture, reason, cause)` (`mutations.py`,
  résolue dans `resolution.py`, marque « maladie » à la même échelle) ; champ NEUF
  `PlantInstance.oidium` ∈ [0,1] (hors `_PLANT_ATTRS`) ; un coup = +1/3. `sim/bilan.py` :
  P × (1 − `OIDIUM_RENDEMENT` 0,5 × oidium) ; `OIDIUM_EFFACE` 0,10/sem, remis à 0 si
  presence = 0 (feuilles tombées). Feuillage jamais touché.
- **Fonte** → `PerteTissus(0, destruction=True)` : tue désormais aussi une plantule de
  constitution > 1 (trèfle 1,25 n'était pas tué par l'ancien `erode`).
- **Asphyxie** : voie santé au sort de `_tick_senescence_health` SUPPLANTÉE (commentée).
  `racines.pression_asphyxie(plant, gorge)` = (asphyxie_memory − SEUIL)/tolérance (même
  médiation), **nulle si le sol n'est pas gorgé cette semaine** (`exces_stress > 0`) —
  écart au kickoff, mesuré : sans cette porte, la mémoire (lerp 0,05) continuait de tuer
  des racines ~30 sem après le ressuyage. `maj_pourriture(plant, pression, asphyxie=0)` :
  asphyxie → mêmes racines perdues que le pourridié (`pourriture_memory` → `eau_percue`),
  `ASPHYXIE_TAUX` = `POURRI_TAUX` 0,10, le chevelu repousse pendant l'engorgement
  (équilibre pommier ~0,8 / aulne ~0,6, constante ~1 an). Labo (sol 2,95, été, n=1) :
  pommier 0,26 en 16 sem, mort de faim ~44 sem (bord noyé du bilan) ; aulne 0,09, réserves
  pleines. ASPHYXIE_* retirés de l'import de `mortalite.py`.
- **Écart au kickoff (nécessaire)** : `f_eau(plant, hum_percue, hum_sol=None)` et
  `semaine_bilan(…, hum_sol=None)` — le bord NOYÉ (et le nom « noyé » du limitant) lit
  l'humidité du SOL : sinon des racines pourries « sortaient » la plante de l'excès d'eau
  (eau ressentie < HUM_NOYE → production remontée). Appel moteur `hum_sol=hum`.
- **Annélation** : `root_herbivory` renvoie désormais une ligne de log
  « 🪦 X@pos meurt annelé (écorce rongée au collet, sève coupée) » (`list[str]`), appelée EN
  PREMIER dans `apply_disturbances` (+ `continue` : plus de 2ᵉ mort au carnet par une perte
  de feuilles le même tick) ; `_raison_mort` « meurt annelé » → cause `herbivorie`.
- Pourriture/campagnol : déjà au flux (`eau_percue`, `plant_uptake`) — inchangés. Les
  nutriments PERÇUS (`facteur_nutrition`) ne lisent pas les racines perdues (seul
  l'uptake du sol le fait) — non fait, hors kickoff.
- Golden RE-FIGÉ `bd5e11abf44f20df…` ; HEAD de `perturbations.py`/`resolution.py`/
  `mortalite._tick_senescence_health` réinjectés en mémoire + `pression_asphyxie` → 0 +
  `semaine_bilan` sans `hum_sol` → `32355a1c…` exact. Neutraliser les SEULES maladies
  (perturbations + resolution) suffit → asphyxie/hum_sol inertes au smoke. Smoke [seed 42,
  n=1] : maladie/poivron 2 → famine/poivron 2 (mildiou défolie, le bilan tue) ; fonte tue
  2 semis de trèfle (avant : survivaient) ; vivantes s104 [44, 14] → [46, 14].
- Effet `full` s10→s62 [seed 42, n=1] : 24 coups de mildiou familial, 1 fongique, 1 fonte,
  0 oïdium (seule la courgette y est sensible), asphyxie max 0,38 → pourriture max 0,03 ;
  morts : maladie 0 → 1 (fonte), herbivorie 11 → 12, le reste identique. Mécanismes
  prouvés par banc `tests/test_maladies_racines.py` (5 cas, < 5 s).
- Tests : `test_parasite` I adapté (« sans réseau » : pourriture < 0,1 au lieu de == 0 —
  ce sol se gorge par épisodes, l'asphyxie y tue quelques radicelles, max 0,08 mesuré) ;
  `test_inoculum`/`test_automate_determinisme` relisent `golden_hash.txt` (mis à jour).
  Rouges = ceux de HEAD seulement. `test_ouverture_vivante` tenu (0/13, 18/123 = 14,6 %, 0).
- Perf `full` s10→s30 [3 paires alternées, charge 1,2 → 7,6, bruitée] : HEAD 10,8/15,1/12,1 s
  → 12,0/13,5/12,0 s (médianes égales).
- LDC : `perturbations.py` 316 (🟡, était 309), `resolution.py` 243, `racines.py` 59,
  `bilan.py` 88, `instance.py` 297, `mortalite.py` 242.
- **Pour ⑤ (voix)** : plus aucune mort « asphyxie » ni « maladie » par mildiou — elles
  sortent en `famine` (ou `secheresse` par embolie) ; la chronique ne dit pas que la
  maladie ou l'eau stagnante ont retiré feuilles/racines. La voix « parasite »
  (`voix_etres`, rampe sur `pourriture_memory`) parlera aussi pour des racines asphyxiées
  (aulne en marais ~0,3-0,6 à long terme). Oïdium : pas exporté au pont (rendu ⑤).

## REPRISE
①②③ faits (③ non commité). Lire `CLAUDE.md`, ce fichier, l'`00_etat.md` du sprint A et de
`sprint_lisibilite_bilan` (hauteur acquise), la conception, puis le kickoff du premier
tronçon « à faire » (④). Golden courant `bd5e11abf44f…`. Lancer : `/sprint-auto sprint_stress_au_bilan`.
