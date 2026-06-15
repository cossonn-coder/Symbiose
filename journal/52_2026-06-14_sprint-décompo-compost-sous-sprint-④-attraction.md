## 2026-06-14 — Sprint décompo & compost · sous-sprint ④ : attraction animale (fruit→guildes) — golden NEUTRE

**Intention** (conception §4 FIGÉE) : le fruit tombé (parcelle `fruit` déposée
par `_tick_fruits` de ③) **appelle la faune** selon son `age_sem` — **frais** →
`auxiliaire` (frugivores, oiseaux : le verger nourrit la faune utile) ; **pourri**
→ `ravageur` DOMINANT (charognards, mouches : pénalité de fermentation qui incite
à cueillir, philo #6) **+ une petite fraction `auxiliaire`** (auxiliaires de
décomposition). **Aucune 5ᵉ guilde** (tranché Nico), et le fruit ne touche
**jamais** la plante (philo #2 : il modifie un champ de population, la réponse
est émergente au tick suivant).

**Modèle** (carte blanche, tout dans `fields/population.py`, couche `fields`
intacte — aucun import `sim`/`tools`) :
- 3ᵉ terme additif **optionnel** `signal_fn` sur `TrophicSpec` (défaut `None` →
  terme 0 → capacité strictement inchangée : pollinisateur/vers **bit-identiques**).
  Branché dans `PopulationField.tick` : `capacite = clamp(resource_w·res +
  habitat_w·hab + signal)`.
- Helpers purs : `_fruit_litter(eco,r,c)` lit la parcelle `fruit` du plot
  (**unique/plot** par fusion de tissu ① → lecture déterministe, aucun ordre) ;
  `_fruit_weights(age)` = `(frais, pourri)` (rampes : frais↓, pourri↑) ;
  `_aux_fruit_signal` = `FRUIT_AUX_GAIN·sig·(frais + FRAC_AUX_POURRI·pourri)` ;
  `_rav_fruit_signal` = `FRUIT_RAV_GAIN·sig·pourri` ; `sig = min(1, masse/
  FRUIT_SIGNAL_REF)`.
- Knobs CONSERVATIFS (un tas ne sature pas la guilde), calibrage post-test :
  `FRUIT_FRAIS_SEM`=3, `FRUIT_POURRI_SEM`=6, `FRUIT_SIGNAL_REF`=0.45,
  `FRUIT_AUX_GAIN`=0.50, `FRUIT_RAV_GAIN`=0.60, `FRAC_AUX_POURRI`=0.25.

**Décision — golden NEUTRE (non re-figé), vérifié** : comme ③, le scénario golden
ne produit **aucune** litière `fruit` (seule espèce `fruitier` = AppleTree,
`maturity_years`=5 > fenêtre 2 ans → nouaison jamais déclenchée). À zéro fruit, le
terme `signal` vaut **exactement 0** partout → champs de population inchangés.
Hashs **bit-identiques à ③** : smoke `908f591b…`, population `435e6f72…` (h1==h2).
La consigne §7 (« re-figé population ») était écrite avant le constat empirique de
③ ; ④ confirme la neutralité. La vraie dérive n'apparaîtra qu'avec un fruitier
précoce / un horizon ≥ 5 ans (hors golden).

**Décision #0 — pile à bois → habitat (§4.1) DIFFÉRÉE à ⑤** : la structure
n'existe pas avant ⑤, rien à câbler. ④ = couplage fruit→guildes seul ; l'habitat
réutilisera le patron rondelle/`_stability_grid` quand la pile sera posable.

**Tests** : nouveau `tests/test_attraction.py` (**17 checks**, 2 niveaux) —
A. MODÈLE PUR (grilles de signal exactes) : frais→aux seul, pourri→rav dominant +
fraction aux, monotonie âge (rav↑/aux↓), échelle masse, **neutralité** (0 fruit →
0 partout) ; B. INTÉGRÉ (après 15 ticks) : frais↑auxiliaire vs témoin, pourri↑
ravageur + un peu d'aux vs témoin, rav(pourri)>rav(frais), déterminisme h1==h2,
neutralité (eco sans fruit → champ uniforme). Suites vertes : golden, population,
fruits 21, vigueur 135, croissance 67, competition 14, eau 20, génétique 20,
maîtrise 35, maîtrise_detection, auxiliaires, signes 8, ombre_maison 4,
phototropisme 11, planter 18, sim_server 113, senescence, **attraction 17** ;
`main.py 5` exit 0.

**Sous-sprint ④ CLOS.** **Suivant** : ⑤ structures posables (bac à compost / pile
à bois + gestes composter/empiler/retourner/epandre + jauge `compost_mur` +
amendements + **pile→habitat reporté ici**), ⑥ vue Godot (différé). Écrire
`05_*.md` avant ⑤. Reprise : `00_etat.md` §REPRISE.

---
