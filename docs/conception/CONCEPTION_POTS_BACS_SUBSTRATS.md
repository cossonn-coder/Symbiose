# CONCEPTION — Pots, bacs & substrats composables

> **Conception FIGÉE le 2026-06-24** (conversation Nico ↔ Claude). Source de
> vérité du sprint `sprint_pots_bacs/`. Implémentation en 5 sous-sprints
> golden-neutres. Aucun code écrit avant cette conception. Pré-conception
> antérieure (2026-06-20) consolidée et détaillée ici.

## 0. Intention

Le joueur peut **mettre en pot** une graine / un semis / une plante, le **remplir
d'un substrat au choix** (terreau, compost, billes d'argile, lasagnes…), et
**déplacer** les pots dans le jardin. Les **bacs** sont plus grands et
**immobiles** (carré potager surélevé). Un petit pot **rapetisse** la plante
(effet nain/bonsaï) ; un grand bac la **libère**.

C'est un nouveau **terrain de jeu écologique** : un conteneur est un **mini-sol
autonome** que le joueur compose et déplace, avec sa propre chimie, son propre
drainage, sa propre décomposition. Il respecte les 7 garde-fous de design — en
particulier **#2** (jamais de bonus/malus direct sur la plante : tout passe par
un flux → contrainte → réponse) et la **règle d'interconnexion des acteurs** (le
conteneur communique avec le jardin : drainage, racines, microbiome).

## 1. Le conteneur = un `EcoFields` miniature

**Décision tranchée (1/6) : on RÉUTILISE `EcoFields`.** Un conteneur porte un
`EcoFields` de petite taille, donc **zéro nouveau modèle chimique** — tous les
ticks existants (`tick_hydrology`, `tick_decomposition`, `tick_ph`,
`tick_structure`, `tick_soil_memory`, `tick_thermique`) marchent tels quels.

```
pot  → EcoFields(rows=1, cols=1)
bac  → EcoFields(rows=2, cols=2)   (taille paramétrable)
```

Nouvel objet **`world/Container`** (couche `world`, peut importer `fields` et
`plants` ; `fields` n'importe jamais `world` → pas de cycle) :

| Champ            | Type           | Rôle |
|------------------|----------------|------|
| `container_id`   | `str`          | identifiant stable |
| `kind`           | `str`          | `"pot"` (mobile) / `"bac"` (immobile) |
| `substrat`       | `str`          | clé du registre `SUBSTRATS` (§2) |
| `volume_litres`  | `float`        | pilote le confinement (§3) |
| `x_cm, y_cm`     | `float`        | position monde (lumière, déplacement) |
| `mobile`         | `bool`         | pot `True`, bac `False` |
| `fond_ouvert`    | `bool`         | bac couplé à la tuile dessous (§5) |
| `eco`            | `EcoFields`    | le mini-sol |
| `plants`         | `list[PlantInstance]` | la/les plante(s) dedans |

**Golden-neutre par construction.** Les conteneurs vivent dans une **liste au
niveau monde, VIDE au repos**. La boucle ajoute une étape « tick conteneurs » qui
itère cette liste vide → **zéro écriture** → smoke test inchangé. Le smoke ne pose
jamais de conteneur.

**Tick allégé au 1er sprint** : le mini-sol ne ticke QUE la chimie (hydrologie,
décompo, ph, structure, soil_memory, thermique, lumière) + l'uptake/croissance de
ses plantes. La `seed_bank` et les `populations` du conteneur **ne sont pas
tickées** (un pot n'a ni succession spontanée ni vie macro propre) → dette
ultérieure si on veut des adventices/faune en pot.

## 2. Le substrat data-driven (registre, 6 recettes)

**Décision tranchée (3/6) : 6 substrats de départ.** Un substrat = une **recette**
qui (a) **initialise** les champs du mini-sol et (b) **fixe ses coefficients**
(drainage notamment). Registre `world/substrat.py`, patron identique au registre
d'espèces/faune (data-driven).

```python
@dataclass(frozen=True)
class SubstratRecette:
    nom:             str
    drainage:        float            # remplace DRAINAGE_PAR_SOL[soil_type]
    structure_init:  float            # structure_sol initiale [0,1]
    ph_init:         float
    npk_init:        tuple            # (n, p, k)
    microbiome_init: float
    litiere_precharge: tuple = ()     # ((tissu, masse), …) — lasagnes/mycélium
    herite_tuile:    bool = False     # "terre du jardin" : copie les champs locaux
```

**Valeurs de DÉPART (calibrage post-test, philo #3 — knobs explicites) :**

| Clé               | drainage | struct | pH  | (N,P,K)        | micro | litière pré-chargée |
|-------------------|---------:|-------:|----:|----------------|------:|---------------------|
| `terreau`         | 0.990    | 0.85   | 6.5 | (1.2, 1.0, 1.0)| 0.6   | — |
| `compost`         | 0.992    | 0.90   | 7.0 | (2.2, 1.5, 1.8)| 1.5   | — |
| `drainant_mineral`| 0.975    | 0.95   | 6.8 | (0.2, 0.2, 0.2)| 0.1   | — |
| `lasagnes`        | 0.988    | 0.70   | 6.5 | (0.5, 0.4, 0.4)| 0.8   | feuille 2.0 · herbace 1.0 · bois 0.8 |
| `terre_jardin`    | hérité   | hérité | hér.| hérité         | hérité| copie de la tuile au point de remplissage |
| `mycelium_use`    | 0.985    | 0.80   | 6.5 | (0.3, 0.3, 0.3)| 0.5   | substrat 2.0 |

- **Drainant minéral** (billes d'argile / perlite / sable) : ne se décompose pas →
  pur modificateur de drainage/structure, NPK pauvre. Pour plantes qui craignent
  l'excès d'eau.
- **Lasagnes** : la `litiere_precharge` est libérée dans le temps par la décompo
  confinée du mini-sol (cascade `om_fresh→active→stable→NPK` **déjà existante**) —
  zéro nouveau modèle. Le `bois` initial crée une **faim d'azote** de départ
  (réaliste pour une lasagne fraîche, tissu ∈ `FAIM_N_TISSUS`) puis se libère.
- **Substrat usé de mycélium** : pré-charge du tissu `substrat` (∈ `FAIM_N_TISSUS`,
  déjà au moteur) → faim d'azote initiale forte puis libération. **Pont vers les
  champignons** (acteurs futurs) — respecte l'interconnexion.
- **Terre du jardin** : `herite_tuile=True` copie les champs du plot de tuile au
  point de remplissage → le pont le plus direct conteneur↔jardin.

`tick_hydrology` est généralisé pour accepter un **`drainage_override`** optionnel
(défaut `None` → comportement actuel, tuiles **bit-identiques**) ; le conteneur
passe le drainage de son substrat.

## 3. Confinement racinaire — effet nain HYBRIDE

**Décisions tranchées (2/6 échelle, 1/6 canal) :** un pot = **1 cellule, volume
libre** ; l'effet nain émerge par un **mécanisme hybride** (émergent + léger
signal root-bound). Philo #2 : on ne pose **jamais** un malus direct sur la plante.

Référence : `VOLUME_REF` ≈ volume racinaire d'un plot de pleine terre
(50×50 cm × ~30 cm ≈ **75 L**). `volume_norm = volume_litres / VOLUME_REF`. Un pot
de 75 L ≈ pleine terre (pas de confinement) ; un pot de 5 L → `volume_norm ≈ 0.07`
→ fort confinement.

**Trois leviers cumulés :**
1. **Réservoir réduit (émergent).** Les flux d'uptake/évaporation du conteneur
   sont rapportés au volume : un petit pot voit sa **concentration** chuter vite
   (assèchement, carence rapides). On passe un `volume_factor` à `plant_uptake`
   (défaut `1.0` → tuiles bit-identiques). La plante stresse via les mécanismes de
   **sécheresse/carence DÉJÀ existants**.
2. **Plafond physique d'expansion racinaire (émergent).** L'uptake n'itère que sur
   les cellules du mini-sol (1 pour un pot) → `root_plots` bornés à la géométrie du
   conteneur. Les racines ne peuvent pas s'étendre au-delà du pot.
3. **Signal root-bound léger (explicite, garantit le bonsaï visible).**
   `occupation = biomasse_racinaire / volume_litres`. Au-delà de
   `ROOTBOUND_SEUIL`, un facteur `confinement ∈ [CONF_MIN, 1]` **bride la
   croissance segmentaire** (multiplie le gain dans `growth.py`). Activé seulement
   quand le pot est saturé de racines → la contrainte reste édaphique, mais l'effet
   nain est garanti.

Knobs de départ (calibrage post-test) : `VOLUME_REF=75`, `ROOTBOUND_SEUIL` et
`CONF_MIN` à fixer au tronçon ③.

## 4. Mobilité & bacs

**Décision tranchée (2/6 transplantation) : déplacer coûte de la Vigueur AU
JOUEUR seul, la plante ne souffre pas** (le mini-sol voyage intact avec elle ;
encourage le réagencement libre du jardin).

- Geste **`deplacer_pot(container, x_cm, y_cm)`** — coût Vigueur `MODERE` (effort,
  calibrage post-test). Change la position → la **lumière reçue est recalculée**
  au prochain tick (`eco.tick_light(..., tile_origin=(x_cm, y_cm))` : ombre maison
  selon la nouvelle position). Réservé aux `kind="pot"` (`mobile`).
- **Bacs** : `kind="bac"`, `rows×cols > 1` (ex. 2×2), `mobile=False`, volume grand
  → confinement faible/nul. Pas de geste déplacer.
- Gestes de pose (planification) : **`poser_pot`** / **`poser_bac`** (kind,
  substrat, volume, position) créent un conteneur rempli ; puis `planter` dans le
  conteneur. Le substrat est fixé à la pose (rempotage = dette ultérieure).
- **Pas de choc de transplantation** au 1er sprint (rempoter ≠ déplacer ; le choc
  éventuel du rempotage = dette).

## 5. Couplage fond ouvert & lasagnes

**Décision tranchée (3/6 bac↔sol) : bac à fond ouvert = COUPLÉ à la tuile
dessous.** Respecte l'interconnexion des acteurs.

**Bac `fond_ouvert=True`** posé sur une tuile à `(x, y)` :
- **drainage → tuile** : l'eau évacuée par `tick_hydrology` (part `1-drainage`)
  est **injectée** dans l'humidité du plot de tuile sous le bac (au lieu d'être
  perdue). Pont matière.
- **racines → tuile** : une fois `ROOTBOUND_SEUIL` atteint, les `root_plots`
  s'étendent dans la tuile sous le bac → uptake aussi dans la tuile → **lève
  l'effet nain** (la plante puise enfin dans le sol profond).
- **microbiome/om → tuile** : diffusion lente entre la cellule du bac et le plot
  de tuile (colonisation par le bas).

**Pot** (fond fermé / trou de drainage) : seul le drainage s'écoule vers la tuile
dessous (l'eau du trou) ; racines confinées ; pas de diffusion microbiome.

**Lasagnes (arc complet validé ici)** : la `litiere_precharge` (§2) → décompo
confinée → NPK disponible dans le temps → plante nourrie progressivement. C'est le
test de bout en bout de l'astuce « lasagne = litière pré-chargée ». Dépend de ②
(mini-sol qui ticke la décompo) et ③ (plante en pot).

## 6. Ponts d'interconnexion (récap, règle des acteurs)

| Pont | Sens | Tronçon |
|------|------|---------|
| Substrat → drainage/structure/NPK/pH | substrat → mini-sol | ① |
| Lumière de la position | tuile/maison → conteneur | ② |
| Terre du jardin (hérite_tuile) | tuile → conteneur | ① |
| Drainage du fond | conteneur → tuile dessous | ⑤ |
| Racines qui descendent (bac ouvert) | conteneur ↔ tuile | ⑤ |
| Microbiome/om colonisation | tuile ↔ conteneur | ⑤ |
| Faim d'azote bois/substrat | litière → plante | ②/⑤ |
| Mycélium usé | substrat → champignons (futurs) | ① |

## 7. Découpage en sous-sprints (5, golden-neutres)

| # | Sujet | Kickoff | Golden |
|---|-------|---------|--------|
| ① | Substrat data-driven (registre + 6 recettes, `drainage_override`) | `01_substrat.md` | NEUTRE (data pure) |
| ② | Conteneur `EcoFields` miniature + tick chimique isolé (pot confiné) + boucle | `02_conteneur.md` | NEUTRE (liste vide) |
| ③ | Plante en pot + confinement racinaire hybride (effet nain) | `03_confinement.md` | NEUTRE |
| ④ | Mobilité (déplacer, lumière, Vigueur) + bacs N×M immobiles + pont snapshot | `04_mobilite_bacs.md` | NEUTRE |
| ⑤ | Couplage fond ouvert (drainage/racines/microbiome) + lasagnes (arc complet) | `05_couplage_lasagnes.md` | NEUTRE |

**Invariant golden GLOBAL** : aucun conteneur dans le smoke → toute étape neuve
itère une liste vide ou une signature rétrocompatible (`drainage_override=None`,
`volume_factor=1.0`) → **golden jamais re-figé** sur tout le sprint. À PROUVER
empiriquement (hash bit-identique) à chaque tronçon, comme décompo·compost.

**Vue Godot** = tronçon ⑥ **différé** (Option B, intégration en pause), comme la
vue de décompo·compost rattrapée plus tard. Les hooks moteur (snapshot conteneurs,
gestes routés) sont posés côté Python au fil des tronçons ; le rendu C# viendra
quand la vue reprendra.

## 8. Décisions tranchées (récap AskUserQuestion, 2026-06-24)

1. **Mini-sol** = `EcoFields` réutilisé (vs classe légère).
2. **Échelle pot** = 1 cellule, volume libre (vs sous-grille fine).
3. **Bac↔sol** = fond ouvert couplé (vs confiné d'abord).
4. **Effet nain** = hybride (émergent réservoir+plafond + léger root-bound).
5. **Transplantation** = Vigueur joueur seule, pas de choc plante.
6. **Substrats** = terreau, compost, drainants minéraux, lasagnes, terre du
   jardin, **substrat usé de mycélium** (ajout Nico).

Antérieures (2026-06-20, conservées) : mini-sol autonome, confinement OUI, moteur
Python d'abord / vue Godot ensuite.
