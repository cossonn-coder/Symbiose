# ① Champ `mycelium` + dynamique (effets DÉBRANCHÉS)

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md`
> (§1). Tronçon **fondation** : on AJOUTE le champ et sa dynamique propre, **aucun
> effet §2 branché** (décompo/uptake/faune intacts). Premier geste : RE-MESURER les
> hashs golden (déjà notés dans `00_etat.md`) pour partir d'une base sûre.

## Objectif
Créer le champ scalaire `mycelium` dans `EcoFields`, sa **croissance/déclin** par
tick (§1.2), à l'état de **repos NEUTRE** (nul partout au lancement → idéalement
golden bit-identique). Aucun rôle §2 encore — c'est la couche de base.

## À faire

### A. Champ `mycelium` (`fields/ecofields/container.py`)
- Déclarer `mycelium: GridField = field(default=None)` (à côté de `structure_sol`,
  ~L118), init dans `__post_init__` (~L196) : `GridField(rows, cols, max_val=1.0)`
  → **nul partout au départ** (`initial=0.0` par défaut).
- Exposé AUTO au pont/F6 par introspection (registre `fields`) → palette overlay à
  ajouter côté vue en ⑥, rien à faire ici côté pont.

### B. Dynamique `tick_mycelium` (méthode de `EcoFields`)
- `croissance = K_G × substrat × humidite_norm × fenetre_temp` ;
  `declin = K_D × mycelium × (secheresse + epuisement_substrat)` ;
  `mycelium += croissance − declin` (clampé [0,1] par le `GridField`).
- **`substrat`** = carbone pondéré BOIS : lire la litière `bois` du plot
  (`bois_fresh_at(r,c)` existe, cf. container.py:782) + `om_active`, normalisés ;
  `epuisement_substrat = 1 − min(1, substrat/REF)`. (Bonus proximité pile = ⑤,
  PAS ici.)
- **`humidite_norm`** = `humidite` normalisée ; `secheresse = 1 − humidite_norm`.
- **`fenetre_temp`** = cloche douce sur `temperature_sol` (`bell(...)` dispo) ;
  repli neutre 1.0 si non calibré.
- Knobs `const` en tête de fichier (placeholders) : `MYCEL_K_G`, `MYCEL_K_D`,
  `MYCEL_SUBSTRAT_REF`, fenêtre temp (centre/largeur). Zéro RNG.

### C. Brancher dans la boucle (`sim/engine/boucle.py`)
- Nouvelle étape **4e** `eco.tick_mycelium()` APRÈS `tick_structure` (~L205), AVANT
  `tick_diffusion` (~L208) : le champ lit une litière/humidité/T_sol déjà à jour ce
  tick. (Les rôles §2 liront le mycélium de CE tick aux étapes suivantes, ②③④.)

## Couches
`tick_mycelium` est une méthode de `EcoFields` (`fields/`) — ne remonte vers aucune
couche haute. La boucle (`sim/engine`) l'appelle, comme les autres ticks.

## Définition de done
- Champ `mycelium` déclaré + init nul + `tick_mycelium` + appel boucle 4e.
- `tests/test_mycelium.py` (NOUVEAU) : champ nul à l'init ; croissance sur un plot
  jouet (bois + humide + T tempérée → `mycelium` MONTE sur quelques ticks) ;
  déclin (sec + sans bois → REDESCEND) ; bornage [0,1] ; déterminisme h1==h2.
- **Golden** : RE-MESURER smoke + population. Le smoke ne pose pas de bois colonisable
  notable → **viser bit-identique**. Si dérive : l'ANALYSER (le champ ne doit avoir
  AUCUN effet en retour ce tronçon) — probable lecture parasite à corriger, PAS à
  re-figer à l'aveugle. Documenter le verdict dans `00_etat.md`.
- MAJ `00_etat.md` (① → FAIT + acquis + hash) puis commit.

## Pièges
- **N'EFFET RIEN** ce tronçon : `mycelium` ne doit modifier ni décompo, ni uptake,
  ni population, ni structure. Si le golden bouge, c'est un branchement accidentel.
- `disturbance` n'est PAS le travail du sol (cf. §1.2) — ne PAS le lire pour le
  déclin. Le bêchage event-driven est en ⑤ (ou ici si trivial — à trancher).
- Ne PAS dépendre de la proximité d'une pile (⑤) — `substrat` = litière+om locaux.
- Garder les valeurs en knobs lisibles (calibrage post-test annoncé).
