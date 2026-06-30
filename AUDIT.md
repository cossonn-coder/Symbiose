# AUDIT SYMBIOSE — 2026-06-30

> Audit LECTURE SEULE des trois plans (conception / code / tests). Diagnostic, pas
> de correction. Chaque constat est relié à une dette (Dxx) ou à un sprint ; les
> constats neufs sont marqués **NEUF** et regroupés en fin de doc.
> Référentiel : `CLAUDE.md` (philo #1-#7 + garde-fous).

## Synthèse

| Plan        | 🔴 | 🟡 | 🟢 |
|-------------|----|----|----|
| Conception  | 0  | 2  | 3  |
| Code        | 0  | 4  | 5  |
| Tests       | 1  | 2  | 5  |

**Une seule alerte 🔴 bloquante :**

- 🔴 **`test_population` ROUGE** — le golden de champ interne (`ef5d62aa…`) ne
  correspond plus au calcul (`4928300b…`). La dérive a été introduite au **sprint
  VENT ⑦** (transport éolien de la litière → la litière déplacée nourrit les
  détritivores → le `PopulationField` change), **sans re-figeage ni détection**
  (le journal vent ⑦ liste `test_vent`/`test_sim_server`/`test_senescence` mais
  **pas** `test_population`). Type **D39** (test re-cassé par une source introduite
  plus tard). — (NEUF)

Le **golden moteur** (`test_golden`, smoke 2 tuiles × 4 ans) reste vert et
**conforme** au dernier hash consigné `0d3ca606…` (vent ⑦) : le smoke est trop
grossier pour capter la dérive du champ de population, que `test_population`
(plus sensible) capte — et signale en rouge.

## Points forts

- 🟢 **Déterminisme strict tenu.** Zéro `random.` vivant dans `sim/`/`fields/`
  (seuls des commentaires d'ancien code). Philo #3 respectée à la lettre.
- 🟢 **Bancs d'équilibrage PRÉSENTS** — `bancs/climatique.py`, `bancs/biotique.py`,
  `bancs/edaphique.py` + `tests/bancs/` (oracle + 3 suites, toutes **vertes**).
  C'est l'apport central du plan tests, rarement en place : on peut **mesurer
  l'effet d'un réglage** au lieu de calibrer à l'aveugle. À préserver et étendre.
- 🟢 **Voix narratives complètes et testées.** Les 28 espèces nommées du catalogue
  ont leur fiche encyclopédie ; les 5 dispositifs (`encyclopedie`, `carnet`,
  `pages`, `magazine`, ledger `journal`) existent comme modules `sim/` dédiés,
  chacun couvert par un test vert. Règle « toute plante = ses 5 voix » respectée.
- 🟢 **LightField D32 soldé.** Passage gather→scatter (×6.8 sur la boucle
  lumière-sol, mesuré) ; tick complet ~52 ms (96 plots), LightField redescendu à
  ~40 % du coût, **sous le budget +10 %/tronçon**. Le poste qui était « énorme »
  est borné par élagage bbox + cache d'abri.
- 🟢 **Discipline golden + traçabilité.** Chaque re-figeage est annoncé, localisé
  et justifié au `journal/` (hashes consignés à chaque tronçon). Dette et journal
  exemplaires : chaque sprint laisse une trace lisible et datée.
- 🟢 **Couverture de tests très large** : 44 suites `test_*.py` + 3 bancs, **43/44
  vertes**. `test_senescence` vert (D39 résolu par le fond au vent ②). Build C#
  vert (0 erreur, 0 avertissement).

## Conception

- 🟢 **Vocabulaire roguelike sain.** `grep -ri` des termes bannis dans `docs/` :
  tous les « run » sont légitimes (« run éternel », « run long » = simulation
  longue) ou des docs historiques **expliquant** l'abandon du roguelike. Aucune
  dérive réelle. — (garde-fou CLAUDE.md)
- 🟢 **Cohérence inter-docs.** 29 docs `CONCEPTION_*.md` + `maitrise/` ; le dernier
  gros morceau (D37 vent) est soldé et documenté de bout en bout (conception →
  dette → journal). Pas de contradiction relevée sur un champ partagé.
- 🟢 **Backlog mûr (figé / non encore implémenté)** — conceptions arbitrées dont
  l'implémentation est en attente, c'est du backlog sain, pas un bug : D41 (mort
  par carence édaphique NPK/pH, bloquée par `qi_local` épuisé), D42 (zoochorie,
  invariant plasticité ④ déjà prêt), D43 (Maîtrise → carnet interprétatif),
  D44-D47 (recette/bancs d'observation post-F5), D24/D10 (portage C# différé).
- 🟡 **Repère de taille périmé dans `CLAUDE.md`** — le garde-fou affirme « max
  empirique mesuré = **337**, `container.py` ». Réalité : `population.py` **632**,
  `container.py` **524**. Le repère est faux depuis l'enrichissement faune B /
  physico-chimie. — (NEUF, voir Code)
- 🟡 **Divergence de seuil entre référentiels** — `CLAUDE.md` dit « ~**350**
  lignes de code pur », `tools/compte_ldc.py` (docstring + défaut) dit « ~**500** »,
  la mémoire projet dit « ~500 ». Le seuil chiffré du garde-fou n'est pas tranché
  entre les sources. — (NEUF)

## Code

Mesures : pire fichier **`fields/population.py` = 632 LDC pur** (436 comment.) ;
puis **`fields/ecofields/container.py` = 524** (526 comment.) ; `test_structures.py`
393. Perf tick **~52 ms** (96 plots, 49 plantes), **LightField ~40 %**. Golden
moteur `0d3ca606…` (conforme). Build C# **vert**.

- 🟢 **Zéro RNG vivant** — déterminisme respecté (philo #3). — (garde-fou)
- 🟢 **Voix narratives** — 28/28 espèces nommées avec fiche ; les 4 entrées sans
  fiche (`competitor`/`grass`/`nitrogen_fixer`/`pioneer`) sont des **archétypes de
  guilde de succession**, pas des espèces du catalogue — muettes par nature, pas
  un oubli. — (règle « toute plante = ses 5 voix »)
- 🟢 **Python ↔ C# sans nouvelle divergence** — build C# propre, la divergence
  reste celle tracée par D10 (PathogenPressure) / D24 (portage). Pas de mécanique
  Godot orpheline détectée. — (D10, D24)
- 🟢 **LightField borné** — scatter D32 (×6.8), cache d'abri vent +0 %, passe
  conditionnelle les jours calmes. Le poste ∝ canopée est désormais élagué. — (D32)
- 🟢 **Perf tick sous budget** — ~52 ms sur le smoke, marge gameplay confortable
  (tick ≪ 60 s/semaine). — (sprint vent)
- 🟡 **Deux fichiers au-dessus du seuil, non signalés** — `population.py` (632) et
  `container.py` (524) dépassent **même le seuil indulgent de 500**. `population.py`
  a grossi par accumulation (D31.1+D31.2+D31.3 + faune B `TrophicSpec`). À tracer
  comme candidats au découpage (paquet `population/` ?). — (NEUF, lié D31)
- 🟡 **Seuil de taille flou** — voir Conception : 350 (CLAUDE.md) vs 500 (outil +
  mémoire). Tant que le chiffre n'est pas tranché, le garde-fou ne peut pas
  arbitrer un dépassement. — (NEUF)
- 🟡 **Outil de diagnostic périmé** — `tools/diag_fields_span.py` plante
  (`AttributeError: 'EcoFields' object has no attribute 'om_fresh'` → renommé
  `om_fresh_at`). Outil **offline** (hors tick, n'affecte ni golden ni jeu), mais
  il ne remplit plus son rôle de diagnostic des champs. — (NEUF)
- 🟡 **Pérennité perf à l'échelle cible non profilée** — tout est mesuré sur le
  smoke **96 plots** ; le monde réel est **1600 plots** (20×20 m) et la sim
  accélérée rejoue des siècles. Aucun banc ne vérifie la tenue du tick à l'échelle
  cible ni la dérive du coût quand les canopées mûrissent (LightField ∝ canopée,
  atténué par scatter mais pas annulé). — (NEUF, lié D32)

## Tests

État : **43/44 suites `test_*.py` vertes** + **3 bancs verts**. Golden smoke
`0d3ca606…` **conforme**. Build C# vert.

**Couverture par TYPE :**

- 🟢 **Smoke / golden** — `test_golden` (2 tuiles × 4 ans) PASS, hash `0d3ca606…`
  = dernier consigné (vent ⑦). Pas de re-figeage sauvage. — (sprint vent)
- 🔴 **Non-régression** — **`test_population` ROUGE** (golden de champ interne
  périmé, dérive vent ⑦ non re-figée/non détectée). Toutes les autres suites
  vertes. — (NEUF, type D39)
- 🟢 **Équilibrage / calibrage** — famille **présente** : `bancs/{climatique,
  biotique,edaphique}` + `tests/bancs/` (oracle + 3 suites vertes). On peut régler
  les valeurs de jeu en mesurant l'effet (trajectoire, témoin vs traité). Point
  fort majeur. — (apport central du plan)
- 🟡 **Longue durée** — `main.py` rejoue 500+ ans sans crash (référence
  comportementale), mais **aucun test/banc automatisé** ne verrouille le rejeu
  longue durée : le smoke s'arrête à 4 ans. Famille **absente** en automatisé. — (NEUF)
- 🟢 **Chaînes critiques récentes couvertes** — `test_vent`, `test_mycelium`,
  `test_plasticite`, `test_substrat`, `test_conteneur`, `test_stress_chronique`,
  `test_journal`/`encyclopedie`/`carnet`/`pages`/`magazine` (voix) : toutes vertes.
- 🟡 **Dette de test à rouvrir** — `test_population` est un cas **D39 récidivant
  par une autre source** (litière éolienne) : à re-figer **sciemment** une fois la
  dérive confirmée légitime, ou à investiguer si la dérive est un effet de bord
  non voulu du transport de litière. — (NEUF / D39)
- 🟢 **Build C#** — `dotnet build Symbiose.csproj` vert (0 erreur, 0 avertissement).

## À ouvrir en dette

Constats neufs non encore tracés dans `DETTE.md` (Nico tranche) :

- 🔴 **`test_population` rouge** — golden de champ `population_hash` non re-figé au
  sprint vent ⑦ (transport litière → détritivores). Confirmer si la dérive est
  légitime (alors re-figer le hash de référence du test) ou un effet de bord du
  transport de litière. Détection manquante : la suite n'a pas été lancée à la
  clôture vent ⑦.
- 🟡 **`tools/diag_fields_span.py` cassé** — attribut périmé `om_fresh` →
  `om_fresh_at`. Outil offline, une ligne à corriger.
- 🟡 **Seuil de taille à trancher** — `CLAUDE.md` (350) vs `compte_ldc.py` + mémoire
  (500). Aligner le chiffre, et **rafraîchir** le repère « max empirique 337 »
  (faux : 632 / 524).
- 🟡 **`population.py` (632) et `container.py` (524) > seuil** — non signalés ;
  candidats au découpage en paquet.
- 🟡 **Banc longue-durée absent** — aucun test automatisé ne verrouille le rejeu
  multi-siècles (seul `main.py` le fait, à la main).
- 🟡 **Pérennité perf 1600 plots non profilée** — banc d'échelle (monde réel + sim
  accélérée + dérive ∝ maturité des canopées) manquant.
