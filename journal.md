# Journal Symbiose

Trace écrite vivante du développement. Une entrée par sprint, par décision
structurante, ou par incident notable.

**Schéma (depuis le SS② du sprint refactor global, 2026-06-15)** : ce fichier
est un **index de pointeurs**. Chaque entrée vit dans son propre fichier sous
`journal/` (entrées récentes) ou `journal_archive/` (entrées d'avant le refactor
structurel du 2026-06-03), nommé `NN_AAAA-MM-JJ_slug.md` et numéroté
chronologiquement. Pour ajouter une entrée : créer
`journal/NN_<date>_<slug>.md` (NN = numéro suivant) et ajouter sa ligne de
pointeur ci-dessous. Ne plus écrire le contenu des entrées ici.

**Conventions des entrées** :
- Dates en `YYYY-MM-DD`.
- Une entrée commence par un titre `## YYYY-MM-DD — Titre court`.
- Les décisions sont préfixées `**Décision :**`, les questions ouvertes `**Question :**`.
- Dette et backlog ne sont pas dans le journal : voir `DETTE.md` et `BACKLOG.md`.

---

## Index

**Dette technique** → [`DETTE.md`](DETTE.md) · **Backlog des sprints** → [`BACKLOG.md`](BACKLOG.md)

### Entrées archivées (`journal_archive/`)

- [2026-05-29 — Sprint 0 : reprise et infrastructure documentaire](journal_archive/01_2026-05-29_sprint-0-reprise-et-infrastructure-documentai.md)
- [2026-05-29 — Sprint conception : redéfinition de la vision du jeu](journal_archive/02_2026-05-29_sprint-conception-redéfinition-de-la-vision-d.md)
- [2026-05-29 — Sprint conception bis : zones blanches refermées](journal_archive/03_2026-05-29_sprint-conception-bis-zones-blanches-refermée.md)
- [2026-05-29 — Zone Z7 : éclairement spatial pixel-exact](journal_archive/04_2026-05-29_zone-z7-éclairement-spatial-pixelexact.md)
- [2026-05-29 — Sprint conception éclairement & reproduction (recadrage Z7)](journal_archive/05_2026-05-29_sprint-conception-éclairement-reproduction-re.md)
- [2026-06-02 — Sprint sol vivant : le sol devient organisme (Python)](journal_archive/06_2026-06-02_sprint-sol-vivant-le-sol-devient-organisme-py.md)
- [2026-06-02 — Consolidation sol vivant : puits microbien (Python)](journal_archive/07_2026-06-02_consolidation-sol-vivant-puits-microbien-pyth.md)
- [2026-06-02 — Mini-sprint succession : gradient pionnier → prairie ∝ maturité du sol](journal_archive/08_2026-06-02_minisprint-succession-gradient-pionnier-prair.md)
- [2026-06-02 — Sprint éclairement : ombres-capsules astronomiques + pérennes (Python)](journal_archive/09_2026-06-02_sprint-éclairement-ombrescapsules-astronomiqu.md)
- [2026-06-02 — Conception mini-sprint mortalité réaliste (sénescence)](journal_archive/10_2026-06-02_conception-minisprint-mortalité-réaliste-séne.md)
- [2026-06-02 — Mortalité réaliste passe 1 : santé dynamique + sénescence (Python)](journal_archive/11_2026-06-02_mortalité-réaliste-passe-1-santé-dynamique-sé.md)
- [2026-06-02 — Mortalité réaliste passe 2 : fonte, fongique, ravageurs régulés, renouvellement (Python)](journal_archive/12_2026-06-02_mortalité-réaliste-passe-2-fonte-fongique-rav.md)

### Entrées récentes (`journal/`)

- [2026-06-02 — Attire-auxiliaires + monde 9 tuiles (Python)](journal/13_2026-06-02_attire-auxiliaires-monde-9-tuiles-python.md)
- [2026-06-03 — Sprint génétique / reproduction : banques + héritage biparental (Python)](journal/14_2026-06-03_sprint-génétique-reproduction-banques-héritage-b.md)
- [2026-06-03 — Sprint refactor structurel : paquets + golden + assainissement docs (Python)](journal/15_2026-06-03_sprint-refactor-structurel-paquets-golden-assain.md)
- [2026-06-03 — Sprint conception météo / climat + signes diégétiques](journal/16_2026-06-03_sprint-conception-météo-climat-signes-diégétique.md)
- [2026-06-03 — Sprint implémentation météo : déterminisation → température → réponses médiées → forecast/signes (Python)](journal/17_2026-06-03_sprint-implémentation-météo-déterminisation-temp.md)
- [2026-06-03 — Sprint gènes du vecteur : vigueur + résistance pathogène + tolérance sécheresse (Python)](journal/18_2026-06-03_sprint-gènes-du-vecteur-vigueur-résistance-patho.md)
- [2026-06-04 — Sprint conception Vigueur : couche transversale D11 (conception seule)](journal/19_2026-06-04_sprint-conception-vigueur-couche-transversale-d1.md)
- [2026-06-04 — Sprint conception paliers de maîtrise : D12 (conception seule)](journal/20_2026-06-04_sprint-conception-paliers-de-maîtrise-d12-concep.md)
- [2026-06-04 — Sprint D12.1 : succès par axe (conception seule)](journal/21_2026-06-04_sprint-d121-succès-par-axe-conception-seule.md)
- [2026-06-04 — Sprint D12.3 : taxonomie des objets de maîtrise (conception seule)](journal/22_2026-06-04_sprint-d123-taxonomie-des-objets-de-maîtrise-con.md)
- [2026-06-04 — Sprint conception Vie macroscopique : D31 (conception seule)](journal/23_2026-06-04_sprint-conception-vie-macroscopique-d31-concepti.md)
- [2026-06-04 — Sprint impl. D31.1 : champs de population + perception (Python)](journal/24_2026-06-04_sprint-impl-d311-champs-de-population-perception.md)
- [2026-06-04 — Sprint impl. D31.2 : câblage écologique de la vie macroscopique (Python)](journal/25_2026-06-04_sprint-impl-d312-câblage-écologique-de-la-vie-ma.md)
- [2026-06-04 — Sprint impl. D31.3 : façades `vigueur_*` + gestes joueur (Python)](journal/26_2026-06-04_sprint-impl-d313-façades-vigueur_-gestes-joueur.md)
- [2026-06-04 — Sprint impl. maîtrise D12·i1 : cœur + progression intra-objet (Python)](journal/27_2026-06-04_sprint-impl-maîtrise-d12-i1-cœur-progression-int.md)
- [2026-06-04 — Sprint impl. maîtrise D12·i2 : agrégats + ponts Vigueur (Python)](journal/28_2026-06-04_sprint-impl-maîtrise-d12-i2-agrégats-ponts-vigue.md)
- [2026-06-04 — Sprint impl. maîtrise D12·i3 : seam `cout_action` + table objets-touchés (Python)](journal/29_2026-06-04_sprint-impl-maîtrise-d12-i3-seam-cout_action-tab.md)
- [2026-06-04 — Sprint impl. maîtrise D12·i4 : détection de succès branchée (Python) — impl. D12 COMPLÈTE](journal/30_2026-06-04_sprint-impl-maîtrise-d12-i4-détection-de-succès.md)
- [2026-06-04 — Sprint conception Hormones de croissance : D29 auxine / dominance apicale (conception seule)](journal/31_2026-06-04_sprint-conception-hormones-de-croissance-d29-aux.md)
- [2026-06-05 — Sprint conception Croissance procédurale : pivot rendu + morphogénèse (conception seule)](journal/32_2026-06-05_sprint-conception-croissance-procédurale-pivot-r.md)
- [2026-06-06 — Sprint Croissance·4 : premier rendu pixel des branches (Godot/C#)](journal/33_2026-06-06_sprint-croissance-4-premier-rendu-pixel-des-bran.md)
- [2026-06-07 — Sprint Maison & ombre déterministe : conception + tronçons 1-4 (Python) — CLOS](journal/34_2026-06-07_sprint-maison-ombre-déterministe-conception-tron.md)
- [2026-06-07 — Sprint Croissance·5 + ·6 : organes procéduraux + sérialisation — sprint CLOS (Python)](journal/35_2026-06-07_sprint-croissance-5-6-organes-procéduraux-sérial.md)
- [2026-06-07 — Kickoff Sprint Intégration Godot ↔ Python : Option B actée](journal/36_2026-06-07_kickoff-sprint-intégration-godot-python-option-b.md)
- [2026-06-10 — Sprint Intégration·1 : pont vivant minimal `sim_server.py` ↔ `SimBridge.cs`](journal/37_2026-06-10_sprint-intégration-1-pont-vivant-minimal-sim_ser.md)
- [2026-06-10 — Sprint Intégration·2 : monde statique rendu (`WorldView`)](journal/38_2026-06-10_sprint-intégration-2-monde-statique-rendu-worldv.md)
- [2026-06-10 — Sprint Intégration·3 : saison animée (boucle hybride côté vue)](journal/39_2026-06-10_sprint-intégration-3-saison-animée-boucle-hybrid.md)
- [2026-06-11 → 2026-06-12 — Sprints Intégration·4, ·5 et ·6 : le jardin devient JOUABLE et LISIBLE — tranches CLOSES](journal/40_2026-06-11_sprints-intégration-4-5-et-6-le-jardin-devient-j.md)
- [2026-06-12 — Sprint « écraser » : volet 1 (guildes) + volet 2 (plantes) CLOS](journal/41_2026-06-12_sprint-écraser-volet-1-guildes-volet-2-plantes-c.md)
- [2026-06-13 — Sprint planter/arroser · Session A : `planter` (germination différée) — golden INTACT](journal/42_2026-06-13_sprint-planter-arroser-session-a-planter-germina.md)
- [2026-06-13 — Sprint planter/arroser · Session B : `arroser` + modèle « eau » (asphyxie) — golden RE-FIGÉ T0+T1 (maîtrisé)](journal/43_2026-06-13_sprint-planter-arroser-session-b-arroser-modèle.md)
- [2026-06-13 — Sprint planter/arroser · Session C : pont `sim_server.py` (protocole 0.3.3) — sprint CLOS](journal/44_2026-06-13_sprint-planter-arroser-session-c-pont-sim_server.md)
- [2026-06-13 — Sprint conception : compétition intra-plot (cohabitation, stratification, éclaircissage) — CONCEPTION SEULE](journal/45_2026-06-13_sprint-conception-compétition-intra-plot-cohabit.md)
- [2026-06-13 — Sprint compétition intra-plot · IMPLÉMENTATION CLOSE — golden RE-FIGÉ maîtrisé (3 causes)](journal/46_2026-06-13_sprint-compétition-intra-plot-implémentation-clo.md)
- [2026-06-13 — Sprint conception : décomposition & compost — CONCEPTION SEULE (FIGÉE)](journal/47_2026-06-13_sprint-conception-décomposition-compost-concepti.md)
- [2026-06-13 — Sprint décompo & compost · sous-sprint ① : parcelles de litière — golden RE-FIGÉ + RACCOURCI (maîtrisé)](journal/48_2026-06-13_sprint-décompo-compost-sous-sprint-①-parcelles-d.md)
- [2026-06-13 — Sprint décompo & compost · sous-sprint ② · **Phase A** : dépôts immédiats — golden NEUTRE](journal/49_2026-06-13_sprint-décompo-compost-sous-sprint-②-phase-a-dép.md)
- [2026-06-14 — Sprint décompo & compost · sous-sprint ② · **Phases B & C** : squelette persistant + abscission — golden RE-FIGÉ LARGE (maîtrisé) — ② CLOS](journal/50_2026-06-14_sprint-décompo-compost-sous-sprint-②-phases-b-c.md)
- [2026-06-14 — Sprint décompo & compost · sous-sprint ③ : organes-fruits traçables — golden NEUTRE — absorbe D19](journal/51_2026-06-14_sprint-décompo-compost-sous-sprint-③-organes-fru.md)
- [2026-06-14 — Sprint décompo & compost · sous-sprint ④ : attraction animale (fruit→guildes) — golden NEUTRE](journal/52_2026-06-14_sprint-décompo-compost-sous-sprint-④-attraction.md)
- [2026-06-15 — Sprint décompo & compost · sous-sprint ⑤ : structures posables (bac/pile) — golden NEUTRE — ⑤ CLOS](journal/53_2026-06-15_sprint-décompo-compost-sous-sprint-⑤-structures.md)
- [2026-06-16 — Sprint REFACTOR GLOBAL · SS①–⑦ TOUS CLOS — golden inchangé, dépôt rangé (un fichier = une responsabilité), seuil taille recalibré ~350](journal/54_2026-06-16_sprint-refactor-global-SS1-7-CLOS.md)
- [2026-06-16 — Sprint saisonnalité vie macro CLOS — photopériode + inertie asymétrique (dormance/réveil par guilde), golden RE-FIGÉ maîtrisé (herbivorie saisonnière)](journal/55_2026-06-16_sprint-saisonnalité-vie-macro-CLOS.md)
- [2026-06-16 — Arc Pollinisation & cycle de vie CONCEPTION FIGÉE (A–E) — floraison réelle (GDD+photopériode), nouaison pollinisée, ressource mellifère, chenille→papillon bouclé ; impl ①→④ à venir](journal/56_2026-06-16_conception-pollinisation-cycle-vie-FIGEE.md)
- [2026-06-18 — Sprint Pollinisation & cycle de vie · implémentation ①→⑦ MOTEUR CLOS — floraison/nectar/butineurs/nouaison/ponts larvaires + ruche/miel + piqûre-alarme émergente (pont 0.4.1) ; golden `4f9fad91…1260` ; reste vue Godot (F5)](journal/57_2026-06-18_sprint-pollinisation-implémentation-①-⑦-CLOS-moteur.md)
- [2026-06-18 — Sprint Pollinisation & cycle de vie · vue Godot — SPRINT TERMINÉ (butineurs fleur-en-fleur + dépôt pollen, piqûre temps réel vue pure, ruche/miel dessinés) ; golden INTACT, 0 ligne Python](journal/58_2026-06-18_sprint-pollinisation-vue-godot-CLOS-sprint-terminé.md)
- [2026-06-18 — Sprint THERMIQUE & MICROCLIMAT CLOS (10 tronçons) — T sol spatialisée couplée au LightField (surchauffe/évapo/isolation/nébulosité/gel localisé/neige), croissance spatialisée, pont 0.5.0, rendu météo + manteau + heatmap F7 ; goldens maîtrisés ①→⑦, ⑧⑨⑩ NEUTRES](journal/59_2026-06-18_sprint-thermique-microclimat-CLOS.md)
- [2026-06-18 — Sprint CATALOGUE ENRICHI · tronçon ① : conception FIGÉE (audit + 2 matrices espèce×feature + ~10 plantes par niche + faune nommée « parfum »/types, découpage ②→⑥) — golden INTACT (doc seul)](journal/60_2026-06-18_conception-catalogue-enrichi-FIGEE.md)
- [2026-06-18 — Sprint CATALOGUE ENRICHI · tronçon ② : +5 plantes (thym, lavande, bourrache, consoude, moutarde) familles connues — attractivité héritée gratis, chemin `evergreen` enfin exercé (test_evergreen.py), golden NEUTRE — ② CLOS](journal/61_2026-06-18_sprint-catalogue-enrichi-tronçon-②-plantes-lot1.md)
- [2026-06-18 — Sprint CATALOGUE ENRICHI · tronçon ③ : +5 plantes (carotte, ortie, courgette, mâche, ail), 5 familles NEUVES + `_ATTRACT_*`, gate `biennial` comblé (rosette an 1 / montaison an 2, `croissance.py`), tests biennial+lot2, golden NEUTRE — ③ CLOS](journal/62_2026-06-18_sprint-catalogue-enrichi-tronçon-③-plantes-lot2.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④a : faune modèle B, filet « catégorie » (`TrophicSpec.category` + `category_density`/`category_fields`), 6 consommateurs recâblés (santé plantes incluse), `_vigueur_categorie`, golden NEUTRE — ④a CLOS](journal/63_2026-06-19_sprint-catalogue-enrichi-tronçon-④a-scaffolding-categorie.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④b : scinder `ravageur` → puceron / limace / doryphore (triades propres, limace détritivore litière-dominante, doryphore spécialiste Solanaceae réduit par l'ail), régression prédation transitoire assumée, golden re-figé MAÎTRISÉ #1 (`63d50eeb`/`1f7dcda8`, vigueur inchangé) — ④b CLOS](journal/64_2026-06-19_sprint-catalogue-enrichi-tronçon-④b-scinder-ravageur.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④c : scinder `auxiliaire` → coccinelle / chrysope / carabe / merle / hérisson (triades propres via `_espece_grid`, merle omnivore fruit+vers, habitats `pile` duck-typés), boucles proie↔prédateur ACTIVES (résorbe la régression ④b), golden re-figé MAÎTRISÉ #2 (`53327632`/`e707002f`, vigueur inchangé) — ④c CLOS](journal/65_2026-06-19_sprint-catalogue-enrichi-tronçon-④c-scinder-auxiliaire.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④d : scinder `detritivore` → lombric / cloporte (lombric héritier humus pilote `decomp_speed` proie merle/hérisson, cloporte litière+fruit pourri proie carabe/hérisson, limace perd le signal pourri), détritivores en position proie, golden re-figé MAÎTRISÉ #3 (`9be1c05a`/`58ecf6d8`, vigueur inchangé) — ④d CLOS](journal/66_2026-06-19_sprint-catalogue-enrichi-tronçon-④d-scinder-detritivore.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④e : encyclopédie (blurb + graphe d'interconnexions sur 10 espèces, module dédié `faune_encyclo.py`) + 5 tests d'invariants (couverture, salts distincts, phénologie hivernale, graphe symétrique) + stub pont par espèce — golden NEUTRE, refonte faune B close côté Python — ④e CLOS](journal/67_2026-06-19_sprint-catalogue-enrichi-tronçon-④e-encyclopedie-tests.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ⑤ : pollinisateurs B (bourdon buzz-pollination Solanaceae / osmie maçonne Rosaceae nichant dans les piles de bois), registre data-driven `PollinatorSpec`, golden re-figé MAÎTRISÉ pollen→nouaison (`f7e1a9b4`), pop-golden dérive purement additive (`a39834df`), vigueur inchangé — ⑤ CLOS, reste ⑥ vue Godot](journal/68_2026-06-19_sprint-catalogue-enrichi-tronçon-⑤-pollinisateurs-B.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ⑥a (Python) : encyclopédie des 5 pollinisateurs (abeille/syrphe/papillon/bourdon/osmie dans `faune_encyclo.py`, splat dans `PollinatorSpec`) + protocole pont `target.espece` (clé canonique, `guilde` en repli) — 3 goldens INCHANGÉS (golden NEUTRE), `dotnet build` OK — ⑥a CLOS, reste ⑥b vue Godot/sprites](journal/69_2026-06-19_sprint-catalogue-enrichi-tronçon-⑥a-encyclo-pollinisateurs-protocole-espece.md)
- [2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ⑥b (vue Godot, C#) — SPRINT TERMINÉ : table sprite par espèce (`MacroLife` 10 placeholders procéduraux, bourdon/osmie exclus → butineurs), butineurs B (`ForagerLayer`), heatmaps PAR ESPÈCE (`FieldOverlay` 15 palettes, registre `fields` déjà par espèce), bascule client `target.espece` (`WorldView.Actions` via `SpeciesNear`) ; golden NEUTRE (`f7e1a9b4…`), `dotnet build` OK, F5 validé — ⑥b CLOS, sprint ①→⑥ TERMINÉ (17→27 plantes, 3 guildes→15 espèces nommées)](journal/70_2026-06-19_sprint-catalogue-enrichi-tronçon-⑥b-vue-godot-CLOS-sprint-terminé.md)
- [2026-06-20 — Sprint PHYSICO-CHIMIE DU SOL · tronçon ⑨ (vue Godot, C#) — SPRINT TERMINÉ : 5 overlays debug F6 (pH/N/P/K/structure_sol, `fertilite` mort retiré) + indice diégétique de chlorose alcaline (Option 1 flag moteur dans le snapshot, `Chlorotic()` lerp vert→jaune sur apex/silhouette/feuilles) ; golden NEUTRE (`e209e8d8…`), `dotnet build` OK, F5 validé — ⑨ CLOS, sprint ①→⑨ TERMINÉ (pH maître + NPK Liebig + structure_sol D30 + faim d'azote + chlorose)](journal/71_2026-06-20_sprint-physicochimie-sol-tronçon-⑨-vue-overlays-chlorose-CLOS-sprint-terminé.md)
- [2026-06-20 — Sprint SÉMIOLOGIE FOLIAIRE (D33) — ①②③ TOUS CLOS, SPRINT TERMINÉ : `leaf_symptoms` (liste triée `{cause, intensity}`) généralise la chlorose à tout le vocabulaire — ① détecteurs chroniques purs (rampe sur le SEUIL de chaque mécanique), ② marques événementielles gel/grêle/maladie décroissantes (`cause` typé + `symptom_marks`), ③ vue C# 2 canaux (COULEUR colorant dominant `SymptomTint` + TEXTURE criblage/gel/affaissement), bool `chlorose` retiré ; golden NEUTRE (`e209e8d8…`), pont 0.5.1, `dotnet build` OK — D33 clôturée](journal/72_2026-06-20_sprint-semiologie-foliaire-CLOS-sprint-terminé.md)

- [2026-06-20 — Fix dette D39 : régression `test_senescence` (asphyxie chronique par précipitations) — ré-isolation du test via climat de laboratoire (`_meteo_labo` : beau temps constant doux, pas de pluie ni gel), AUCUN fichier moteur touché, golden INTACT `e209e8d8…`, pommier mort de sénescence à 59.8 ans ∈ [49 ; 112] — D39 CLOSE](journal/73_2026-06-20_fix-D39-senescence-asphyxie.md)
- [2026-06-22 — Sprint PLASTICITÉ & EXPRESSION DE GÈNES ADAPTOGÈNES · tronçon ⑤ (signe d'acclimatation) — SPRINT TERMINÉ : nouvelle cause `acclimatation` (signe GÉNÉRIQUE tranché, feuillage glauque/coriace) dans `leaf_symptoms` — intensité = plus forte sur-expression des gènes adaptogènes en rampe `[EXPR_MIN, EXPR_MAX]`, priorité 9 (un dégât d'égale intensité passe devant), détecteur lecture pure ; teinte glauque `#9db8b0` côté `PlantRenderer` ; golden NEUTRE (`2ab026ad…`), pont 0.5.3, `dotnet build` OK ; dette D43 (Maîtrise → carnet interprétatif, P4) — sprint plasticité ①→⑤ TERMINÉ (génotype + expression plastique + priming + coût défense + signe)](journal/74_2026-06-22_sprint-plasticite-tronçon-⑤-signe-acclimatation-CLOS-sprint-terminé.md)

---

> Tout le contenu détaillé est dans les fichiers liés ci-dessus
> (`journal/` et `journal_archive/`). La dette est dans [`DETTE.md`](DETTE.md),
> le backlog dans [`BACKLOG.md`](BACKLOG.md) (source unique, plus de duplication).
