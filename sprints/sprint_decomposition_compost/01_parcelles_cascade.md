# Sous-sprint ① — Parcelles de litière + cascade + `om_fresh` dérivé + raccourci golden

> **Kickoff autosuffisant (démarrage à froid).** Lire d'abord `00_etat.md` et
> `data/code/CONCEPTION_DECOMPOSITION_COMPOST.md` (§1 surtout). Ce sous-sprint
> pose **l'infrastructure** des parcelles. Il ne crée **aucun geste joueur**,
> **aucun squelette**, **aucun organe-fruit** (ce sont ②③④⑤). Objectif : que le
> moteur stocke la matière fraîche en **parcelles** au lieu du scalaire
> `om_fresh`, **à comportement écologique équivalent** (le re-figeage golden doit
> être attribuable aux SEULES causes listées au §Golden), et **raccourcir** le
> smoke test.

## But mesurable
1. `om_fresh` (GridField) n'est plus l'unité de stockage du frais → remplacé par
   une **liste de parcelles par plot** ; `om_fresh_at(r,c)` = Σ masses est lu par
   tous les anciens lecteurs.
2. `tick_decomposition` itère les parcelles (décompo ∝ tissu × microbiome × vers),
   reverse humification → `om_active`, minéralisation → `fertilite`, respiration
   perdue ; la cascade `om_active → om_stable → fertilite` est **inchangée**.
3. Les exsudats alimentent une parcelle **`diffus`** permanente ; la nécromasse
   et les `inject_field om_fresh` déposent des parcelles.
4. Smoke test **raccourci** (`N_YEARS 4 → 2`) et **re-figé**, population re-figée,
   déterminisme (`h1 == h2`) intact. Dérive attribuable aux seules causes du
   §Golden.

## Modèle de données (proposé — ajuster à l'écriture)
Dans `fields/ecofields.py` :
```python
# Constitution → cinétique (placeholders §1.2 du doc conception, calibrage post-test)
TISSU = {
    # tissu      decay   humif  miner   (le reste = respiré)
    "diffus":  (0.50,  0.15,  0.55),
    "feuille": (0.25,  0.30,  0.45),
    "fleur":   (0.30,  0.20,  0.50),
    "herbace": (0.15,  0.35,  0.35),
    "fruit":   (0.28,  0.20,  0.50),
    "bois":    (0.02,  0.55,  0.10),
}

@dataclass
class Parcelle:
    tissu: str
    masse: float
    age_sem: float = 0.0
```
Stockage : un champ `EcoFields.litiere : list[list[list[Parcelle]]]` (grille de
listes, comme les autres champs) **ou** `dict[(r,c), list[Parcelle]]`. Préférer la
grille de listes (cohérent avec `GridField.data`, itération déterministe par
`(r,c)` puis tri par tissu).

**Fusion par tissu (bornage, obligatoire)** : à chaque dépôt, si une parcelle de
même `tissu` existe au plot → `masse += masse` et `age_sem` = moyenne pondérée
par la masse ; sinon append. → ≤ 6 parcelles/plot.

**Parcelle `diffus` permanente** : présente à chaque plot dès `__post_init__`
(masse 0). Reçoit les exsudats. Ne disparaît jamais (peut tomber à 0).

## API à exposer sur `EcoFields`
- `om_fresh_at(r, c) -> float` = Σ `masse` des parcelles du plot. **C'est le
  remplaçant** de `om_fresh.at_plot(r,c)`.
- `om_fresh_average() -> float` = Σ toutes parcelles / (rows·cols). Remplace
  `om_fresh.average()` dans `summary()`.
- `deposer_litiere(r, c, tissu, masse)` : dépôt + fusion. **Point d'entrée unique**
  pour tous les écrivains.

## Réécriture de `tick_decomposition` (`ecofields.py:355`)
Aujourd'hui (à remplacer) : lit `fresh = om_fresh.data[r][c]`, calcule
`d_fresh = fresh × OM_FRESH_DECAY × speed`, route humif→`om_active`,
miner→`fertilite`. Le `speed` (microbiome + vers) et la suite (`active`→`stable`,
famine microbienne, lessivage) **restent**.

Nouveau, pour chaque plot :
1. `speed = 0.5 + micro*0.5 (+ WORM_DECOMP_BONUS*worms)` — **inchangé**.
2. Pour chaque parcelle du plot (ordre trié par tissu) :
   `d = masse × TISSU[tissu].decay × speed` ; `masse -= d` ; `age_sem += 1` ;
   `om_active.add(r,c, d × humif)` ; `fertilite.add(r,c, d × miner)` ;
   (reste respiré). Retirer les parcelles de masse ≈ 0 **sauf `diffus`**.
3. Famine microbienne : `fresh = om_fresh_at(r,c)` (Σ parcelles **APRÈS** ou
   **AVANT** décompo — choisir et figer ; l'ancien code la calculait sur le
   `fresh` d'avant. **Garder « avant »** pour limiter la dérive). Formule
   `famine = 1 − min(1, fresh / MICROBE_FOOD_REF)` **inchangée** (§1.4 doc).
4. `active`→`stable` + lessivage : **copier tels quels** depuis l'ancien code.

> `OM_FRESH_DECAY/HUMIF/MINER` deviennent les colonnes de `TISSU` (le `diffus`
> reprend ≈ les anciennes valeurs fresh pour amortir la dérive ; le reste = §1.2).

## Recâblage exhaustif (faire `grep -rn "om_fresh" data/code` au démarrage)
**Écrivains → `deposer_litiere`** :
- `sim/engine.py:_tick_exudates` (~ligne 288 `eco.om_fresh.add(r,c, om_share)`)
  → `deposer_litiere(r, c, "diffus", om_share)`.
- `fields/ecofields.py:add_necromass` (~425 `self.om_fresh.add(r,c, deposited)`)
  → `deposer_litiere(r, c, "herbace", deposited)` (tissu générique en ① ; ②
  raffinera feuille/bois selon la source et le squelette). Garder la signature
  `(r,c,biomass,harvested)` et le `BIOMASS_EXPORT`.
- `sim/effects.py:134` resolver `inject_field` : si `variable == "om_fresh"`
  (paillage/engrais vert de `plants/species.py:47,152`) → `deposer_litiere(r,c,
  "herbace", amount)` au lieu de `field.add`. **Piège** : ce resolver fait
  `getattr(eco, variable).add(...)` génériquement — intercepter le cas `om_fresh`
  AVANT le `getattr` (sinon AttributeError, le champ n'existe plus).

**Lecteurs → `om_fresh_at` / `om_fresh_average`** :
- `fields/population.py:_soil_food_grid` (~261) `om_fresh.at_plot + om_active.at_plot`
  → `om_fresh_at(r,c) + om_active.at_plot(r,c)`.
- `fields/ecofields.py:summary()` (~551) `om_fresh.average()` → `om_fresh_average()`.
- `tick_decomposition` (famine, ci-dessus).
- **Vérifier** : `vitalite()` ne lit PAS `om_fresh` (confirmé — lit om_active/
  fertilite/om_stable/microbiome). `sim_server.py` expose l'OM via `summary()`
  (couvert). Re-grep pour être sûr de l'exhaustivité.

**Suppression** : retirer le champ `om_fresh: GridField` de `EcoFields` (dataclass
field + `__post_init__` + `get_field`/dict `"om_fresh"`). **Attention** :
`get_field("om_fresh")` / l'introspection `fields` du pont (sim_server 0.3.0,
registre des `GridField`) — `om_fresh` disparaîtra de l'overlay F6 (acceptable ;
ou exposer une grille dérivée si on veut le garder visible — défaut : retirer,
noter dans 00_etat).

## Raccourcir le golden
`tests/test_golden.py:38` `N_YEARS = 4` → `2`. (Le digest = log complet + état
final ; moins d'années = log plus court = test plus rapide.) Re-générer la
référence : `python3 -m tests.test_golden --update` (ou le flag équivalent — voir
`__main__` du fichier, ligne ~127 : écrit `golden_hash.txt`).

## Procédure de re-figeage (maîtrisé, annoncé)
1. Coder à comportement équivalent (diffus ≈ ancien fresh).
2. Lancer `python3 -m tests.test_golden` → il FAIL (attendu). Noter l'ancien hash
   `6bf71ee5…` → nouveau.
3. Lancer `python3 -m tests.test_population` (re-fige aussi : les vers lisent le
   frais) → noter l'ancien hash de champ → nouveau.
4. **Vérifier le déterminisme** : deux runs donnent le MÊME nouveau hash
   (`h1 == h2`). Sinon → bug d'ordre (parcelles non triées, dict non ordonné).
5. Mettre à jour les fichiers de référence, `00_etat.md` (hashes), le commit.

## Critères de fin (DoD)
- [ ] `om_fresh` n'est plus un `GridField` ; parcelles + `diffus` permanente en place.
- [ ] `tick_decomposition` itère les parcelles ; cascade active/stable + lessivage intacts.
- [ ] Exsudats → `diffus` ; nécromasse + `inject_field om_fresh` → `deposer_litiere`.
- [ ] Tous les lecteurs re-câblés (grep `om_fresh` propre).
- [ ] `N_YEARS = 2`. Golden + population **re-figés**, `h1 == h2`, dérive expliquée.
- [ ] Suites vertes : `test_golden`, `test_population`, `test_vigueur`,
      `test_croissance`, `test_competition`, `test_eau`, `test_sim_server`,
      `test_senescence`, `genetique`, `maitrise`. `main.py 30` exit 0.
- [ ] `00_etat.md` + `journal.md` à jour (hashes, dérive). Commit.

## Pièges identifiés
- **Cap** : `om_fresh` avait `max_val=10.0`. Les parcelles n'ont pas de cap dur
  → **défaut : pas de cap** (l'écologie borne ; vigilance perf = D32). Le noter.
- **Famine timing** : figer « fresh d'avant décompo » (comme l'ancien) pour ne
  pas ajouter une cause de dérive.
- **Ordre déterministe** : itérer `(r,c)` puis parcelles **triées par tissu**.
  Jamais de `dict` non ordonné dans le chemin du tick.
- **`inject_field`** : intercepter `variable=="om_fresh"` AVANT le `getattr`
  générique dans `effects.py` (le champ n'existe plus).
- **Périmètre** : NE PAS introduire ici les vitesses différenciées par SOURCE
  (feuille/bois selon la plante) ni le squelette — c'est ②. En ①, la nécromasse
  est un tissu générique (`herbace`). Les 6 tissus EXISTENT dans la table mais
  seuls `diffus` (exsudats) et `herbace` (nécromasse/inject) sont alimentés.

## Ce que ① NE fait pas (rappel)
Pas de geste joueur, pas de squelette persistant, pas d'abscission, pas d'organe-
fruit, pas d'attraction animale, pas de structure posable. → ②③④⑤.
