# ①d Levée des graines — plus de graines, plus de descendants

> Lire d'abord : `CLAUDE.md`, `00_etat.md` (§Conception FÉCONDATION + bilans ①b, ①c), puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §6.3-6.4.
> Golden attendu : **RE-FIGÉ annoncé** (composition de la levée férale).

## Objectif
Que le stock de graines d'une espèce dans le sol décide de ce qui lève : les annuelles du
jardin se ressèment (S2), et parmi la flore spontanée l'espèce qui a le plus grené a le plus
de chances de lever (S3).

## À faire
1. **S3 — espèce ∝ son pool** (`sim/succession.py::choisir_espece`) : parmi les
   `eligibles` (fenêtre d'azote inchangée), tirage au hash (canal `week × 61` existant)
   pondéré par `ε + eco.seed_bank.species_density(r, c, cls)`. Archétype sans flore → sa
   tête seule, comme avant. Constante `PLUIE_EXTERIEURE = ε` (graines venues de dehors),
   valeur de départ 0,02 [non calibrée] : la consigner comme levier. Si aucun pool n'est
   présent, le tirage reste uniforme (pondérations égales). La fonction devra recevoir
   `eco` ou les densités : adapter l'unique appelant.
2. **S2 — ressemis des annuelles sans archétype** (`succession`, boucle de levée férale,
   `sim/succession.py` ≈ l. 539) : sur un plot libre où **aucun archétype ne lève**, chaque
   espèce dont le pool du plot dépasse `SPECIES_POOL_MIN_DENSITY`, **sans archétype** et
   **sans recrue directe** (annuelle ou bisannuelle : vérifier la règle exacte d'exclusion
   dans `_reproduction`, `sim/engine/mortalite.py`) lève si
   `hash < niche_eff(espèce) × densité de son pool`. `niche_eff` = mêmes portes que la
   levée férale (tolérance à l'ombre, pH, T du sol, allélopathie), calculées pour la
   **classe** et non l'archétype : réutiliser les fonctions d'où sont tirés `arch_tolerance`,
   `arch_ph`, `arch_temp`, `arch_allelo`, sans dupliquer les formules. Une seule levée par
   plot : si plusieurs espèces passent, tirage au hash ∝ densité. Canal de hash **dédié**
   (vérifier au `grep` ; libres au 2026-11-18 : 79, 97, 101, 103, sauf si ①c en a pris un).
   La plante levée suit le même chemin que le féral : `_offset_subplot`, `form_seed_at`,
   `sample_genes` + `_levee_triee`, `sample_F`, `sample_expression`, ligne de log
   `🌿 Germination`.
3. **Ordre** : vérifier au code que le pool lu est celui des graines déjà déposées
   (mise en graine d'automne ou fin de cycle) et que la décroissance du pool
   (`rec["density"] *= perte`, `fields/seedbank.py`) s'applique bien aux graines
   d'annuelles : une banque qui ne s'épuise jamais ferait tout lever chaque année.
4. **Banc population** (`mesures/banc_levee.py`, monde « full », 10 ans [ne pas dépasser
   sans raison]) : nombre de plantes par espèce et par an, avant/après ; temps de tick
   moyen avant/après. **Emballement attendu et assumé** (trèfle ou autre) : le **mesurer
   et le décrire**, ne PAS le corriger (choix de Nico : la correction viendra plus tard,
   par davantage d'espèces en compétition). Si le nombre de plantes dépasse le cap perf
   (`sim/capacite.py`), le consigner.
5. **Banc de sélection** : relancer `mesures/banc_fleurs.py` (a) sur plusieurs
   générations : la descendance des bourraches bleues doit maintenant **lever** et la
   moyenne de `couleur_fleur` de la population doit dériver. C'est le critère
   d'acceptation du trou du ① ; si rien ne bouge, enquêter.
6. **Perf** : la boucle des pools ne lit que les plots libres sans levée d'archétype et
   leur dict d'espèces (creux) ; mesurer le smoke (≤ +2 %) **et** le tick du banc
   population (la hausse due à plus de plantes est à chiffrer, pas à cacher).

## Tests
- Ciblés : `choisir_espece` sans pool = uniforme ; avec un pool dominant, l'espèce
  correspondante sort plus souvent ; une bourrache dont le pool est dense lève sur un
  plot libre favorable, pas sous ombre profonde, pas hors fenêtre de pH ; pool sous le
  seuil → rien.
- Suites succession, banque-sol, trèfle, allélopathie vertes (adapter une valeur attendue
  seulement si elle suppose le tirage uniforme, et le dire).

## Golden
Re-figé : 1ʳᵉ divergence attendue au premier tirage `choisir_espece` sur un plot qui porte
un pool. Diff du digest lu, hash et `population_hash` consignés.

## Ne PAS faire
- Garde-fou anti-emballement, plafond par espèce, retouche de `reproduction_rate`.
- Faire lever depuis le pool les vivaces qui ont déjà leur recrue directe (double voie).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ①d FAIT, hash, composition sur 10 ans, emballement observé (espèce, année,
nombre de pieds), tick. Ouvrir une dette « emballement de <espèce> : plus d'espèces en
compétition » dans `DETTE.md` si l'emballement est constaté. Commit.
