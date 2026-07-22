# Tronçon ⑧ — Structure / compaction du sol (`structure_sol`, dette D30)

> Sprint physico-chimie du sol. Conception : `docs/champs/sol/conception_sol_structure.md`
> (volet C/3, §2 le modèle, §3 les constantes). Kickoff **autosuffisant** (relançable
> à froid). Python depuis `data/code/`.
> Tronçons ① (champ `ph`), ② (n/p/k posés), ③ (Liebig + lessivage diff. + CEC),
> ④ (lockout cloches dispo), ⑤ (fenêtres pH espèce + chlorose), ⑥ (amendements
> chaux/soufre), ⑦ (faim d'azote bois/substrat) **déjà CLOS**. Golden figé
> `d8856261bbe49787…`. **⑧ = dernier tronçon MOTEUR** (⑨ = vue Godot, overlays).

## Objectif

Donner un champ à la **structure du sol** (agrégation en grumeaux poreux). Un sol
compacté (piétiné, battu par la pluie sur sol nu, semelle de bêchage) asphyxie :
l'eau ruisselle/s'engorge, les racines ne pénètrent plus. Aujourd'hui `becher` tape
le sol mais `grelinette` est un **no-op** — le bénéfice d'aération n'a nulle part où
s'inscrire. On crée le champ `structure_sol` (dette **D30** absorbée), **Option B**
(champ dédié, mutualise l'infra « champ lent hérité du `soil_type` + dérive par
gestes » bâtie pour le pH — décision Nico 2026-06-19, PAS l'Option A sobre par vers).

## Le modèle (CONCEPTION STRUCTURE §2)

### Champ `structure_sol ∈ [0,1]` (1 = grumeleux/aéré, 0 = compacté/battant)
`GridField` par plot, init hérité du `soil_type` (`STRUCTURE_INIT_PAR_SOL`), **lent**
(inertie comme le pH/soil_memory_deep). Dérive sous forces ± :

```
d_struct[r,c] = + BIOTURB      · lombric_norm[r,c]              ⟵ vers (constructeur lent)
              + RACINE_PIVOT · presence_pivot[r,c]              ⟵ racines décompactantes (catalogue)
              + GRELINETTE_GAIN (si geste grelinette ce tick)   ⟵ aère sans retourner
              − BATTANCE     · pluie_norm · (1 − couvert_norm)  ⟵ pluie battante sur sol NU
              − BECHAGE_MALUS (si geste becher ce tick)         ⟵ semelle de tassement
structure_sol += d_struct · STRUCT_INERTIA   ;   clamp [0,1]
```

`couvert_norm` = litière protectrice (paillage amortit la battance) — réutilise
`om_fresh_at` comme le thermique. `lombric_norm` = `populations["lombric"].at_plot/3`
(cf. `decomp_speed`). `presence_pivot` = présence d'une plante à racine pivot
décompactante sur le plot (ex. `MedicagoLupulina` ; marqueur catalogue à repérer/poser).

### Bêchage : leurre (§2.2) — **VERSION SOBRE PAR DÉFAUT**
`becher` = malus net `structure_sol`, `grelinette` = gain net. NE PAS coder le pic
transitoire « ameublit puis re-tasse » sauf si le gain pédagogique le justifie en main
(décision à l'implémentation, défaut = sobre, §6).

### Trois couplages lecteurs (branchés EN MÊME TEMPS, §2.3)
```
infiltration : une part de la pluie RUISSELLE (perdue) quand structure basse
asphyxie_factor ×= (2 − structure_sol)                # compacté+saturé → anoxie aggravée
uptake_factor   ×= mix(STRUCT_UPTAKE_MIN, 1, structure_sol)  # racines pénètrent moins
```
L'asphyxie & l'uptake se branchent dans `plant_uptake` (le `asphyxie_factor` existe
déjà). L'infiltration nourrit `tick_hydrology` : à structure basse, une fraction de
`BASE_RAIN` (ou de la pluie événementielle) est perdue au ruissellement.

## Constantes (§3 — à ajouter dans `fields/ecofields/constants.py`)
```python
STRUCTURE_INIT_PAR_SOL = {"terre": 0.7, "argile": 0.45, "sable": 0.6, "roche": 0.4}
STRUCT_INERTIA    = 0.05     # champ lent (saisons)
BIOTURB           = 0.30     # construction par les vers (× lombric_norm)
RACINE_PIVOT      = 0.10     # décompactage par racines pivots
GRELINETTE_GAIN   = 0.15     # gain durable d'un passage de grelinette
BECHAGE_MALUS     = 0.20     # tassement net (version sobre)
BATTANCE          = 0.15     # dégradation par pluie battante sur sol nu
STRUCT_UPTAKE_MIN = 0.5      # uptake résiduel en sol totalement compacté
```

## Greffes (repères, à re-vérifier au grep)
1. **Champ** : ajouter `structure_sol: GridField` au dataclass `EcoFields`
   (`container.py`), init hérité dans `__post_init__` (façon `ph`), exposer dans
   `get_field` (overlay debug ⑨ gratuit).
2. **Dérive** : `tick_structure(self, grelinette=False, becher=False, pluie_norm=0.0)`
   délègue à un helper PUR `fields/ecofields/structure.py` (façon `ph.py`/`nutriments.py`
   — NE PAS gonfler `container.py`, déjà **429 ldc**). Câblé dans `boucle.py` près du
   `tick_ph` (étape 4c), gestes du tick passés en argument (couche `fields` n'importe
   pas `sim`/`world`).
3. **Couplages** : `plant_uptake` → multiplier `asphyxie_factor` par `(2−structure)` et
   appliquer le `mix` uptake ; `tick_hydrology` → ruissellement ∝ `(1−structure)`.
4. **Gestes** : `sim/actions.py` — compléter `grelinette` (no-op → ↑structure +↑lombric),
   `becher` garde son malus vers/microbiome + ajoute ↓structure. Repérer comment les
   gestes remontent à la boucle (l'event du tick).
5. **Racine pivot** : repérer le marqueur catalogue (`MedicagoLupulina`) — attribut de
   classe `decompactante` (ou liste). Si absent, le poser (défaut False, NEUTRE).

## Golden attendu
**RE-FIGÉ MAÎTRISÉ** (un seul tronçon, re-figé assumé en une fois — la structure n'a
pas de phase neutre séparée, §4). La dérive vient de l'infiltration (hydrologie) +
uptake + asphyxie modulés par `structure_sol` hérité ≠ 1.0 sur les tuiles du smoke.
**Inspecter au `git stash` diff** : vérifier que la dérive vient BIEN de ces trois
couplages et de rien d'autre. Si elle surprend, **scinder ⑧a (champ neutre, aucun
lecteur) / ⑧b (couplages)** au moment de l'implémentation (filet §4).

## À faire en fin de tronçon
- Champ `structure_sol` + dérive (helper pur `structure.py`) + 3 couplages + gestes
  `grelinette`/`becher`.
- Vérifier golden (re-figé MAÎTRISÉ inspecté `git stash`, ou NEUTRE si héritage=1.0
  partout — improbable) + suites (structures, vigueur, planter, eau, population, ombre…).
  `test_senescence` reste rouge = **D39 pré-existante** (asphyxie pommier, pas ⑧ — mais
  ⑧ touche l'asphyxie : VÉRIFIER que ⑧ n'aggrave pas D39 au point de casser d'AUTRES
  suites ; si oui, isoler).
- Tester À LA MAIN : un sol compacté (`structure` basse) ruisselle plus / asphyxie
  plus vite ; un passage de `grelinette` remonte `structure` ; `becher` la baisse.
- MàJ `00_etat.md` (⑧ ✅, hash, note taille) ; `main.py` 1 an OK (50 ans sauté, cf. ⑤⑥).
- Commit : `feat(sol) : tronçon ⑧ structure_sol (compaction/infiltration/asphyxie/uptake) — dette D30`.
- **Sprint moteur CLOS après ⑧.** Écrire `09_vue_overlays.md` avant le `/clear` (volet
  vue : overlays Godot des nouveaux champs ph/n/p/k/structure + indice visuel chlorose).
