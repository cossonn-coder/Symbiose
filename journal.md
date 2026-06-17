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

---

> Tout le contenu détaillé est dans les fichiers liés ci-dessus
> (`journal/` et `journal_archive/`). La dette est dans [`DETTE.md`](DETTE.md),
> le backlog dans [`BACKLOG.md`](BACKLOG.md) (source unique, plus de duplication).
