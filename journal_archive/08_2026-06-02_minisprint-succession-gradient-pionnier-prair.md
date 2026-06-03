<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-06-02 — Mini-sprint succession : gradient pionnier → prairie ∝ maturité du sol

### Contexte

Traite la dette **D25** diagnostiquée le matin même (Consolidation sol vivant,
axe 2). Sprint **Python pur** sur le moteur de vérité. Objectif : faire **mûrir**
la végétation spontanée — un sol redevenu riche restait bloqué 100 % en
pionnières annuelles ; on veut une succession qui progresse vers un couvert de
**prairie vivace** à mesure que le sol mûrit.

### Décisions actées (avec Nico, Partie 3 du kickoff)

1. **Proxy de maturité = `soil_memory_deep`**. Argument décisif : ce champ
   *est déjà* la combinaison composite `micro*0.4 + fert*0.2 + om*0.2 + sig*0.2`
   (cf. `tick_soil_memory`), mais passée dans un **filtre passe-bas décennal**
   (lerp 0.02). Le prendre brut aurait fait osciller la succession ; filtré, il
   donne la bascule lente recherchée. Pas de champ ad hoc.
2. **Gradient 3 paliers** : pioneer → nitrogen_fixer → grass → competitor, par
   rang ∝ maturité (continu, pas de seuil dur).
3. **Trickle de propagules vivaces** ∝ maturité : OUI, faible (dispersion
   lente, diégétique).
4. **Ampleur** : pionnier → prairie seulement. Le climax ligneux relève des
   pérennes (D21, Sprint éclairement).

### Étape 1 — choix d'archétype ∝ maturité (`engine.py`)

Nouvelle fonction module `choisir_archetype(candidates, soil_deep, fertilite)`,
**factorisée** entre `_succession` et `_spring_flush` (supprime la duplication
de la logique `chosen`). Rang de succession = index dans `SEED_ARCHETYPES` ;
`rang_cible = soil_deep * 3` ; on choisit le candidat dont le rang est le plus
proche (tie-break : le plus avancé). **Filet conservé** : `fertilite < 0.3` +
fixatrice candidate → on force la fixatrice (azote limitant). Orphelin `micro`
retiré de `_succession`.

### Étape 2 — amorçage de la banque en propagules vivaces (`fields.py`)

`SeedBank.tick_late_succession_enrichment(soil_deep_field)`, symétrique de
`tick_disturbance_enrichment` (qui n'amorce que `pioneer`). Trickle ∝ maturité :
`SEED_LATE_GAIN` 0.0008, seuil `SEED_LATE_MIN_MATURITY` 0.2 (rien sur sol jeune),
`competitor` gaté à `SEED_COMPETITOR_MATURITY` 0.4 (le plus tardif). Branché dans
`EcoFields.tick_seed_bank`. **C'est l'étape qui débloque tout** : sans graines
vivaces dans la banque, le choix corrigé n'a rien à choisir.

### Étape 3 — reflux + observabilité

Le **frein explicite n'a pas été nécessaire** : une fois les vivaces installées,
`niche_index` réduit la niche libre (root_density + soil_deep) → les pionnières
refluent d'elles-mêmes. `main.py` : ajout d'un **log de composition du couvert
installé par archétype**, échantillonné en **plein été (S26)** pour ne pas
sous-compter les annuelles (mortes à l'hiver).

### Résultats (déterministes, `main.py` 500 ans, exit 0)

- **Flux de germination** : vivaces 0,1 % → **~37 %** en plateau, montée monotone.
- **Couvert installé** (le test clé) : an 10 **17 %** vivace (flush pionnier,
  24 pionnières) → an 30 **84 %** → plateau **~75-90 %** stable jusqu'à l'an 500,
  sans oscillation ni blocage. La fixatrice (Minette) domine le couvert mûr.
- Le couvert (~80 %) est bien plus vivace que le flux (~37 %) : une vivace
  pérenne persiste des années, une pionnière annuelle doit re-germiner — le flux
  sous-estime le couvert. C'est cohérent.

### Aussi

- `main.py` : `N_YEARS` rendu **ajustable via argument CLI** (`python3 main.py 60`),
  défaut 500 — lancer des simus courtes pour gagner du temps. Dernière année
  toujours échantillonnée.
- **Dette de portage** : cette logique de succession n'est pas portée en C# →
  s'ajoute à **D24 / Sprint 3**.
- **Futur sprint diversification écologique** (question de Nico) : le moteur
  accepte facilement de nouvelles espèces (classe + 1 ligne `PLANT_CATALOGUE` ;
  `SOIL_SIGNATURE` indexée par famille). Mais à séquencer **après** le Sprint
  éclairement (D21 apporte les strates/ligneux = nouveaux archétypes) et **après**
  une décision *class-based vs data-driven*, en coordination avec la génétique
  (D22). Noté au backlog (**D26**).

### Ce qui a été produit

- `data/code/engine.py` — `choisir_archetype` + branchement `_succession`/`_spring_flush`
- `data/code/fields.py` — `tick_late_succession_enrichment` + constantes + branchement
- `data/code/main.py` — log composition couvert (S26) + `N_YEARS` ajustable CLI
- `journal.md`, `CLAUDE.md` (backlog), mémoire ; commit

---
