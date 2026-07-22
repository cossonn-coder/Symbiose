# Tronçon ④a — SCAFFOLDING « catégorie » (filet, golden NEUTRE)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc de référence FIGÉ : `docs/faune/vie_macro/conception_faune_dediee.md`
> (modèle B ; ce tronçon = §1.2 + §4 + §7 ligne ④a).
> Kickoff **autosuffisant**. Lancement Python depuis `data/code/`.
> Filet C# : `dotnet build Symbiose.csproj` (**zéro C# attendu ici**).

## Pourquoi ce tronçon EN PREMIER

Le modèle B remplace les 3 champs de guilde (`ravageur`/`auxiliaire`/
`vers_de_terre`) par 10 champs d'espèce. Mais **6 consommateurs lisent
`populations[guilde]` en dur** — dont la **santé des plantes**. Si on scinde les
champs sans filet, tout casse d'un coup et le golden saute de façon opaque.

④a pose le **filet** : on introduit la notion de **catégorie** et un helper
d'agrégation, et on **recâble les consommateurs dessus — SANS scinder aucun
champ encore**. Tant qu'une catégorie ne contient qu'un seul champ (l'actuel),
`category_density(cat) == populations[cat]` plot par plot → **golden NEUTRE**.
C'est l'invariant de contrôle du sprint.

## Périmètre EXACT

**DANS ④a** :
1. `TrophicSpec` (`fields/population.py`) gagne `category: str` (cf. doc §1.1).
   Tagger les 3 specs actuelles : `ravageur`→`"ravageur"`,
   `auxiliaire`→`"auxiliaire"`, `vers_de_terre`→`"detritivore"` (la catégorie est
   renommée, **mais le `name`/clé du champ reste `vers_de_terre` en ④a** — on ne
   touche aux noms de champ qu'à la scission ④d). Pollinisateurs (`PollinatorSpec`)
   **non concernés** (couche isolée) — leur donner `category="pollinisateur"` si
   `category_density` doit les voir, sinon les ignorer (cf. C12, ils ne sont lus
   que par `pollinator_density`).
2. Helper `EcoFields.category_density(category, r, c)` (`fields/ecofields/container.py`)
   = somme des `populations.values()` dont `spec.category == category` (doc §1.2).
3. **Recâbler les 6 consommateurs** (doc §4) vers `category_density` :
   - C1 `sim/effects/perturbations.py:213` `ravageur` → `category_density("ravageur")`
   - C2 `sim/effects/perturbations.py:249` `auxiliaire` → `category_density("auxiliaire")`
   - C3 `sim/vigueur_macro.py:59` `ravageur` → idem
   - C4 `sim/vigueur_macro.py:65` `auxiliaire` → idem
   - C5 `sim/vigueur_macro.py:80` `vers_de_terre` → `category_density("detritivore")`
   - C6 `fields/ecofields/container.py:383,408` `vers_de_terre` (decomp) → **garder
     `populations["vers_de_terre"]` tel quel** (en ④d ça deviendra `["lombric"]` ;
     pas de catégorie ici car decomp = le ver précis, pas la catégorie). Le noter.
   - C8 `sim/actions/gestes.py:420` `vers_de_terre` → inchangé en ④a (un seul champ).

**HORS ④a** : aucune scission d'espèce (④b–④d), aucune métadonnée encyclo (④e),
aucun protocole pont (⑥). `_ravageur_grid` (ressource auxiliaire) **inchangé**.

## Conception technique

- `category_density` est une **lecture pure** (somme), zéro effet de bord. À
  `populations` = {ravageur, auxiliaire, vers_de_terre, abeille, syrphe, papillon},
  la somme par catégorie d'un seul membre == ce membre → neutralité exacte.
- Ne PAS changer l'ordre de tick, les salts, les pondérations.
- Garde-fou : `population.py` est **déjà ≈369 LDC > ~350** (signalé en ③) — ④a
  n'y ajoute qu'un champ de dataclass (~1 ligne) ; le helper va dans `container.py`.
  Ne rien gonfler d'autre.

## Validation

1. `python3 -m tests.test_golden` → **PASS, hash `5fddfe54…` INCHANGÉ**. C'est LE
   critère : si le hash bouge dès ④a, c'est un **BUG d'agrégation** (la somme ne
   reproduit pas le champ unique), pas un re-figeage légitime.
2. `python3 -m tests.test_population`, `test_attraction`, `tests/vigueur/*` → PASS
   (les consommateurs recâblés lisent la même valeur qu'avant).
3. Filet C# `dotnet build Symbiose.csproj` (zéro C# touché, mais vérifier).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (④a ✅ : catégorie + helper + 6 consommateurs
  recâblés, golden NEUTRE confirmé, scission à venir ④b).
- Entrée `journal/` + index `journal.md`.
- Commit : `refactor(catalogue) : faune ④a — couche catégorie + category_density, golden NEUTRE`.
- Enchaîner ④b (scinder ravageur) — **pas** d'auto-enchaînement, attendre Nico.
