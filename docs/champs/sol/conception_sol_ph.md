# CONCEPTION — SOL · pH

> Conception figée le 2026-06-19 (Sprint physico-chimie du sol, volet A/3).
> Étude de fond et pédagogie agronomique complète : `sprints/etude_physicochimie_sol.md`.
> Volets frères : `CONCEPTION_SOL_NUTRIMENTS_NPK.md`, `CONCEPTION_SOL_STRUCTURE.md`.
> Ce doc porte l'**ordre global du sprint** (§6) car le pH en est le socle.

## 0. Objectif & intuition

Le pH **n'existe pas** aujourd'hui dans le moteur. C'est pourtant le
maître-régulateur de la chimie du sol : il décide *quelle plante pousse où*
(calcifuges acidophiles vs calciphiles) et **combien** un nutriment présent est
réellement disponible (« lockout », le phosphore en tête). On introduit un champ
`ph` lent, hérité de la roche-mère, qui pilote ensuite trois lecteurs :
disponibilité des nutriments, activité microbienne, et fenêtre d'espèce.

Philosophie : **#2 flux → contrainte → réponse** (le pH module un *flux* de
disponibilité, jamais un bonus direct sur la plante) ; **#3 déterminisme** (champ
tamponné, zéro RNG) ; **#5 pas de chiffre HUD** (le joueur lit le pH via les
indices : chlorose, quelles plantes prospèrent, indicatrices d'acidité).

## 1. État de départ

| Brique | Où | Statut |
|---|---|---|
| `soil_type ∈ {terre, argile, sable, roche}` | `world/tile.py` | OK — vecteur d'héritage du pH |
| Champs lents tamponnés (`soil_memory_deep`, `temperature_sol`) | `fields/ecofields` | modèle de référence du champ à forte inertie |
| `RONDELLE_TYPES` (amendements posables) | `world/tile.py` | OK — on y ajoute `chaux`/`soufre` |
| Mécanique indicatrices (`UnlockCondition`) | catalogue | OK — on la nourrit d'indicatrices d'acidité |
| **Champ `ph`** | — | **néant, à créer** |
| **Fenêtre pH par espèce** | — | **néant, à créer** |

## 2. Le modèle

### 2.1 Champ `ph` (tronçon ①)

`GridField` par plot, plage **[4.0, 8.5]**, **initialisé par héritage** du
`soil_type` (table §3). Dérive **décennale** (lerp à très forte inertie, frère de
`soil_memory_deep`) vers une cible composée de quatre forces :

```
cible_ph[r,c] = ph_roche[soil_type]                          (état hérité, dominant)
              − ACIDIF_OM    · om_fresh_norm[r,c]            ⟵ acides humiques (③ NPK)
              − ACIDIF_LEACH · drainage_norm[r,c]            ⟵ lessivage du calcium (climat humide)
              + AMEND_PUSH(chaux/soufre présents)            ⟵ amendements (⑥)

ph += (cible_ph − ph) · PH_INERTIA / (1 + cec[r,c])          ⟵ tampon CEC (volet B)
ph  = clamp(ph, PH_MIN, PH_MAX)
```

**Couplage CEC** : un sol argilo-humique (CEC élevée) tamponne → dérive plus
lente. C'est `cec[r,c]` du volet NPK qui amortit ici (dépendance douce, le pH
fonctionne sans, `cec=0` par défaut tant que B n'est pas posé).

### 2.2 Lockout — disponibilité en cloche (tronçon ④)

Le couplage qui **donne du sens** au pH. Facteur multiplicatif gaussien appliqué à
l'uptake de chaque nutriment (et à l'activité microbienne) :

```
dispo_i(ph) = exp( −((ph − PH_OPT_i) / PH_WIDTH_i)² )        i ∈ {N, P, K, micro}
```

- **P** centré 6.5, **étroit** (width 1.0) : bloqué en acide (fer/alu) ET en
  alcalin (calcium) — le cas pédagogique roi.
- **N** centré 6.8, **large** (2.2) : peu sensible.
- **K** centré 6.5, intermédiaire (1.8).
- **micro** centré 6.8 (1.6) : l'activité bactérienne en cloche → `ph → microbiome
  → décompo` (couplage indirect, sans champ neuf).

**Chlorose alcaline** : quand `ph > CHLOROSE_PH` (≈ 7.6) sur une espèce
acidophile, lockout du fer → malus de vigueur + **indice visuel jaunissement**
(rendu volet vue). C'est le « pourquoi ma myrtille jaunit sur calcaire ».

### 2.3 Fenêtre d'espèce (tronçon ⑤)

Deux champs catalogue neufs par espèce : `ph_opt` et `ph_tol` (demi-largeur).
Facteur en cloche `bell(ph ; ph_opt, ph_tol)` lu à **deux endroits** :
- **germination/succession** : porte (une espèce ne s'installe pas hors fenêtre) ;
- **croissance** : facteur de vigueur (dépérit doucement en bord de fenêtre).

Noyau démonstrateur (le reste du catalogue = `ph_tol` large ⇒ neutre) :

| Espèce | type | `ph_opt` | `ph_tol` |
|---|---|---|---|
| Myrtille (à ajouter) | acidophile/calcifuge | 4.8 | 0.8 |
| Lavande / thym | calciphile | 7.4 | 1.1 |
| Oseille, prêle | **indicatrices acidité** | 5.0 | — (UnlockCondition `ph < 5.5`) |

### 2.4 Amendements (tronçon ⑥)

Deux nouvelles `RONDELLE_TYPES` : **`chaux`** (remonte le pH) et **`soufre`**
(descend). Posées sur `StakeSlot`, **event-driven** (pas dans le tick écolo →
golden NEUTRE), elles injectent un `AMEND_PUSH` local tant qu'elles sont présentes,
**progressif sur saisons** (jamais instantané), coûtant de la Vigueur. Le paillage
acide (aiguilles de pin) tombe naturellement du système litière (volet NPK).

## 3. Constantes (placeholders — calibrage post-test)

À placer dans `fields/ecofields/constants.py` (valeurs PURES) :

```python
PH_MIN, PH_MAX = 4.0, 8.5
PH_PAR_SOL   = {"terre": 6.8, "argile": 7.0, "sable": 5.8, "roche": 7.6}  # héritage roche-mère
PH_INERTIA   = 0.02          # dérive décennale (avant amortissement CEC)
ACIDIF_OM    = 0.30          # acidification par matière organique fraîche
ACIDIF_LEACH = 0.20          # acidification par lessivage (climat humide)
AMEND_PUSH   = 0.15          # poussée pH par saison d'un amendement présent (signe selon chaux/soufre)

# Lockout — cloches de disponibilité
PH_OPT   = {"N": 6.8, "P": 6.5, "K": 6.5, "micro": 6.8}
PH_WIDTH = {"N": 2.2, "P": 1.0, "K": 1.8, "micro": 1.6}
CHLOROSE_PH = 7.6            # au-dessus, chlorose ferrique des acidophiles
```

## 4. Tronçons & golden (volet pH)

- **①** Champ `ph` + dérive (héritage + OM + lessivage), **aucun lecteur**. Golden
  **NEUTRE** (champ posé, personne ne le lit) + overlay debug gratuit.
- **④** Lockout : cloches sur l'uptake N/P/K + activité microbienne + chlorose.
  Golden **RE-FIGÉ MAÎTRISÉ** (un seul levier branché).
- **⑤** Fenêtres pH par espèce (noyau) + indicatrices acidité. Germination +
  croissance. Golden **~neutre** (espèces neuves, le cœur ne bouge pas).
- **⑥** Amendements `chaux`/`soufre` (rondelles, event-driven). Golden **NEUTRE**.

## 5. Interconnexions

`ph` ← `soil_type` (héritage) · ← OM/litière (acidifie) · ← lessivage (`humidite`/
climat) · ← amendements joueur · ← **CEC** (tampon, volet B).
`ph` → **disponibilité N/P/K** (lockout, volet B) · → **microbiome** (cloche) →
**décompo/minéralisation** · → **catalogue** (fenêtres + chlorose + indicatrices).
Variable la **plus connectée** du sprint.

## 6. Ordre global du sprint (les 3 volets)

Tactique **neutre-d'abord** (validée au thermique) ; le gros re-figé est isolé au
tronçon 3. Numérotation globale :

1. **pH socle** (ce doc ①) — neutre.
2. **N/P/K socle** (NPK ①) — champs posés, uptake lit encore `fertilite`. Neutre.
3. **Bascule uptake loi-du-minimum** (NPK ②) — retrait `fertilite`, Liebig,
   lessivage différencié, CEC, `SOIL_SIGNATURE` explicite. **LE gros re-figé.**
4. **pH → lockout** (ce doc ④) — re-figé maîtrisé.
5. **Fenêtres pH espèces** (ce doc ⑤) — ~neutre.
6. **Amendements pH** (ce doc ⑥) — neutre.
7. **Faim d'azote** (NPK ④ — bois/BRF + substrat usé champignons) — re-figé maîtrisé.
8. **Structure `structure_sol`** (volet C) — re-figé maîtrisé.
9. **Vue** — overlays nouveaux champs + indices visuels (chlorose). Neutre.

## 7. Garde-fous

- **Golden** : re-figeage **annoncé** par tronçon, dérive vérifiée localisée.
- **Couches** : `fields` n'importe jamais `sim` ; l'événement amendement est passé
  en argument depuis l'engine.
- **Taille** : si le bloc pH grossit, l'isoler dans `fields/ecofields/ph.py`
  (helper pur), `container.py` ne portant que l'orchestration (comme pour le
  thermique).
- **Philo #5** : aucun chiffre de pH en HUD — uniquement chlorose, vigueur,
  indicatrices.
