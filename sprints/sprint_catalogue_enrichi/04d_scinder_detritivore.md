# Tronçon ④d — SCINDER la catégorie `detritivore` (lombric / cloporte)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc FIGÉ : `docs/conception/CONCEPTION_FAUNE_DEDIEE.md` (§2 detritivore, §4 C6/C8/C13, §5.3).
> **Pré-requis : ④c CLOS** (auxiliaire scindé, merle/hérisson lisent `detritivore` agrégé).
> Kickoff autosuffisant. Python depuis `data/code/`. Filet `dotnet build`.

## Objectif

Remplacer le champ `vers_de_terre` par **2 champs d'espèce** (catégorie
`"detritivore"`) : le **lombric** (ver du sol, moteur de l'humus) et le **cloporte**
(détritivore de litière). Boucler les interconnexions restantes : lombric/cloporte
**proies** de merle/hérisson/carabe ; fruit pourri → cloporte ; `decomp_speed`
piloté par le lombric.

| Espèce | Nourriture (resource_fn) | Prédateurs | Habitat (habitat_fn) | Fenêtre |
|---|---|---|---|---|
| **lombric** | `_soil_food_grid` *(existe : MO+microbiome)* | merle, hérisson | `_undisturbed_grid` *(existe)* | quasi annuelle (daylen 8.5/10) |
| **cloporte** | `_litter_grid` *(neuf : masse litière en décompo)* | carabe, hérisson | `_humide_litiere_grid` *(④b, partagé limace)* | humide |

## Périmètre EXACT

**Specs** : retirer `vers_de_terre`, ajouter `lombric`/`cloporte`
(`category="detritivore"`), salts dédiés. Le **lombric hérite du salt
`_SALT_VERS`** (continuité du champ historique) si utile, sinon salt neuf.

**Ressource neuve** `_litter_grid` (`population.py`) : somme de la masse de litière
en décomposition du plot (`eco.litiere[r][c]`, hors parcelle `fruit` déjà gérée par
le signal), normalisée. Distincte de `_soil_food_grid` (qui lit MO+microbiome du
sol, pas la litière de surface).

**Recâblage** (doc §4) :
- **C6 `decomp_speed`** (`container.py:383,408`) : `populations["vers_de_terre"]`
  → `populations["lombric"]`. Le cloporte n'accélère PAS l'humus du sol ici
  (décision §5.3 : cloporte→litière = dette si littéral). **Re-figeage decomp** à
  attendre (le lombric a sa propre dynamique distincte de l'ancien champ agrégé).
- **C8 `gestes.py:420`** : `populations["vers_de_terre"].add(...)` →
  `populations["lombric"]`.
- **C13 signal fruit pourri** `_rav_fruit_signal` (retiré en ④b) → reposé sur
  **cloporte** (signal_fn), + petite part `limace` si souhaité (défaut : cloporte
  seul, plus simple).
- **Merle/hérisson** (④c) : leur lecture `category_density("detritivore")` → bascule
  vers `_espece_grid("lombric")` (le merle/hérisson mangent le ver, pas le cloporte
  prioritairement) ; carabe/hérisson prédatent le cloporte (predators de cloporte).
- **C5 vigueur macro** `category_density("detritivore")` : déjà bon (④a) — vérifier
  qu'il somme bien lombric+cloporte maintenant.

> ⚠️ La catégorie s'appelle `detritivore` mais la clé du champ historique était
> `vers_de_terre`. Après ④d il n'y a PLUS de champ `vers_de_terre` (→ lombric +
> cloporte). Vérifier qu'aucun lecteur résiduel ne référence `"vers_de_terre"` en
> dur (grep ; cf. tests, simserver).

## Validation

1. `python3 -m tests.test_golden` → re-figé MAÎTRISÉ #3. Nouveau hash → `00_etat.md`
   + journal, dérive expliquée (lombric ≠ ancien champ agrégé ; decomp_speed sur le
   seul lombric ; cloporte+litière+prédation neufs).
2. `tests/test_faune_dediee.py` complété : lombric/cloporte existent, cloporte nul
   sans litière, decomp_speed suit le lombric, prédation merle→lombric active.
3. `test_population`/`test_attraction`/décompo (`tests/test_structures` etc.) :
   adapter les références `vers_de_terre` → `lombric` ou `category_density`.
4. Filet `dotnet build`.

## À faire en fin de tronçon

- `00_etat.md` (④d ✅ : detritivore scindé, **nouveau hash**, decomp→lombric,
  cloporte+litière, toutes interconnexions §3 bouclées côté dynamique).
- Entrée `journal/` + index.
- Commit : `feat(catalogue) : faune ④d — detritivore scindé (lombric/cloporte), decomp→lombric, fruit pourri→cloporte, golden re-figé`.
- Proposer ④e (encyclo + tests + stub pont) — pas d'auto-enchaînement.
