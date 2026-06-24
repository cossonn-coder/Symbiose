# ② Conteneur `EcoFields` miniature + boucle

> Lire `00_etat.md` + conception §1, §2, §6. Dépend de ① (registre + override).
> Golden NEUTRE : la liste de conteneurs est VIDE dans le smoke → l'étape neuve
> itère du vide. À PROUVER bit-identique.

## Objectif
Créer l'objet `world/Container` (mini-sol `EcoFields` initialisé par un substrat)
et l'intégrer à la boucle, **sans plante dedans encore** (la plante en pot = ③).
On valide la chimie isolée d'un pot : drainage du substrat, décompo de la litière
pré-chargée (lasagnes/mycélium), pH/structure/soil_memory, lumière à sa position.

## À faire

### A. `world/container.py` (nouveau)
- `@dataclass Container` avec les champs du §1 (`container_id`, `kind`, `substrat`,
  `volume_litres`, `x_cm`, `y_cm`, `mobile`, `fond_ouvert`, `eco: EcoFields`,
  `plants: list`, `rows`, `cols`).
- Fabrique `make_container(kind, substrat, volume_litres, x_cm, y_cm, *,
  rows=1, cols=1, tile_eco=None, tile_rc=None) -> Container` :
  1. construit `eco = EcoFields(tile_id=f"{kind}:{id}", rows, cols)` ;
  2. **applique la recette** `get_substrat(substrat)` : remplit uniformément
     `structure_sol`, `ph`, `n/p/k`, `microbiome` aux valeurs de la recette
     (`GridField.fill` ou boucle `set`) ; dépose `litiere_precharge` via
     `eco.deposer_litiere(r, c, tissu, masse)` sur chaque cellule ;
  3. si `herite_tuile` (terre du jardin) : **copie** les champs du plot
     `tile_rc` de `tile_eco` (humidité, n/p/k, ph, structure, microbiome, om,
     litière) dans la cellule du conteneur — pont tuile→conteneur (§6) ;
  4. `mobile = (kind == "pot")`.
- `Container.tick_chimie(self, saison, house=None, nebulosite=0.0)` — orchestre le
  mini-sol, MÊME ordre que la boucle tuile mais ALLÉGÉ (pas de seed_bank/
  populations) : `tick_light` (avec `tile_origin=(x_cm, y_cm)` pour l'ombre maison),
  `tick_thermique`, `tick_hydrology(drainage_override=recette.drainage)`,
  `tick_decomposition`, `tick_ph`, `tick_structure`, `tick_soil_memory(self.plants)`.
  (En ② `self.plants == []` → soil_memory voit une liste vide, ok.)

### B. Boucle
- Le porteur des conteneurs = une **liste au niveau monde**. Repérer comment la
  boucle (`sim/engine/boucle.py`) reçoit les tuiles/ecos ; ajouter un paramètre
  `containers: list = None` (défaut `None` → `[]`).
- Nouvelle étape « tick conteneurs » : `for ctn in containers: ctn.tick_chimie(...)`.
  **No-op STRICT si `containers` vide** → golden neutre. La placer à un endroit
  cohérent (après le tick des tuiles, avant le snapshot).
- `main.py` : NE PAS poser de conteneur dans le scénario golden. Optionnel : un
  petit banc d'essai conteneur DERRIÈRE un flag, hors du chemin smoke.

## Couches
`world/container.py` importe `fields` (EcoFields, get_field) + `world.substrat` +
`plants`. Vérifier que `fields` n'importe pas `world` (pas de cycle). Si un cycle
apparaît, factoriser l'init substrat→champs dans un helper `fields`-side appelé par
`world`.

## Définition de done
- `Container` + `make_container` + `tick_chimie` opérationnels.
- Boucle tickant `containers` (vide par défaut).
- `tests/test_conteneur.py` : un pot `compost` 5 L tické N semaines isolément →
  NPK/microbiome cohérents avec la recette ; un pot `lasagnes` → la litière
  pré-chargée se décompose (om_fresh décroît, NPK monte dans le temps) ; un pot
  `mycelium_use` → faim d'azote initiale visible (n bas tant que `substrat`
  présent) ; `terre_jardin` → champs == ceux du plot tuile source ; déterminisme
  (h1==h2). Drainage du substrat effectivement appliqué (pot drainant sèche plus
  vite qu'un pot terreau, à apport égal).
- **Golden PROUVÉ NEUTRE** (smoke + population bit-identiques). Suites amont vertes.
- MAJ `00_etat.md` + commit.

## Pièges
- Pas de plante en pot ici (uptake/croissance/confinement = ③).
- `tick_light` du mini-sol : passer la `house` du monde + `tile_origin=(x_cm,y_cm)`
  pour que l'ombre maison s'applique selon la position du conteneur.
- Bien rendre l'étape boucle inerte sur liste vide (le test golden l'exige).
