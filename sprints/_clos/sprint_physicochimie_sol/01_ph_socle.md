# Tronçon ① — pH socle (champ hérité + dérive lente, aucun lecteur)

> Sprint physico-chimie du sol. Conception : `docs/champs/sol/conception_sol_ph.md`
> (§2.1, §3, §4, §6). Kickoff **autosuffisant** (relançable à froid).

## Objectif

Introduire le champ `ph` (par plot), **initialisé par héritage du `soil_type`** et
dérivant **très lentement** (lerp à forte inertie, frère de `soil_memory_deep`)
sous l'effet de la matière organique (acidifie) et du lessivage (acidifie). C'est
la fondation physico-chimique du sprint.

**Périmètre strict** : le champ est **posé mais lu par PERSONNE**. Ni l'uptake, ni
la croissance, ni la germination ne le consultent. → golden **NEUTRE** (on ajoute
un champ qui n'influence aucun calcul existant).

## Modèle (ce tronçon)

```
cible_ph[r,c] = PH_PAR_SOL[soil_type]
              − ACIDIF_OM    · om_fresh_norm[r,c]
              − ACIDIF_LEACH · drainage_norm[r,c]

ph[r,c] += (cible_ph − ph[r,c]) · PH_INERTIA / (1 + cec[r,c])
ph[r,c]  = clamp(ph, PH_MIN, PH_MAX)
```

Note : `cec` (volet NPK) n'existe pas encore → `cec = 0` (tampon neutre, dénominateur
= 1). L'amendement (`AMEND_PUSH`) est réservé au tronçon ⑥. `drainage_norm` =
réutiliser la grandeur de drainage déjà calculée par l'hydrologie (ou
`humidite_norm` faute de mieux — à vérifier dans `container.py`).

## Étapes

1. **`fields/ecofields/constants.py`** — ajouter les knobs de ① (conception §3) :
   `PH_MIN=4.0`, `PH_MAX=8.5`, `PH_PAR_SOL={"terre":6.8,"argile":7.0,"sable":5.8,
   "roche":7.6}`, `PH_INERTIA=0.02`, `ACIDIF_OM=0.30`, `ACIDIF_LEACH=0.20`.
   (Ne PAS encore ajouter le bloc lockout `PH_OPT`/`PH_WIDTH`/`CHLOROSE_PH` — ④ ;
   ni `AMEND_PUSH` — ⑥.)

2. **`fields/ecofields/container.py`** :
   - Ajouter le champ `ph: GridField` au dataclass. **Init par héritage** : à la
     construction, remplir chaque plot avec `PH_PAR_SOL[tile.soil_type]` (et non
     une valeur uniforme). Vérifier comment le conteneur accède au `soil_type` de
     la tuile (passé en argument ? attribut ?) — s'aligner sur l'existant.
   - L'exposer dans `get_field` (→ overlay debug gratuit, registre par introspection).
   - Nouvelle méthode `tick_ph(self)` : pour chaque plot, calculer `cible_ph` puis
     lerp. **Pure, aucun log, aucun lecteur.**
   - ⚠️ `container.py` est à 337 ldc (max du dépôt). Si dépassement, sortir le
     calcul dans un helper pur `fields/ecofields/ph.py` (la méthode `tick_ph`
     délègue). Vérifier `python3 tools/compte_ldc.py`.

3. **`sim/engine/boucle.py`** — insérer `eco.tick_ph()` dans la boucle par tuile,
   après la décompo (il lit `om_fresh`) et avant rien de critique (personne ne lit
   `ph`). Position exacte à confirmer en lisant `boucle.py`.

4. **Golden** — lancer `python3 -m tests.test_golden`. **Il doit PASSER INCHANGÉ**
   (aucun lecteur de `ph` → zéro dérive). Si le golden bouge → un lecteur s'est
   glissé par erreur, corriger. **Ne PAS re-figer** (le hash ne doit pas changer).

## Invariant golden

- **NEUTRE** : le hash de référence reste **identique**. C'est tout l'intérêt de la
  tactique neutre-d'abord — on pose l'infrastructure sans rien dériver.
- Si le golden change, c'est un bug : `ph` est consommé quelque part par accident.

## Validation

- `python3 -m tests.test_golden` PASS **sans re-figeage**.
- `python3 main.py` tourne sans crash.
- Vérifier à la main (petit script ou `main.py` instrumenté) que `ph` est bien
  hérité différemment selon `soil_type` (terre ≠ sable) et qu'il dérive lentement
  (pas de saut). Le champ apparaît dans le registre `get_field`.

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ① ✅, golden **inchangé**).
- Commit : `feat(sol) : tronçon ① champ pH hérité du soil_type + dérive lente — golden NEUTRE (aucun lecteur)`.
- Écrire le kickoff `02_npk_socle.md` avant le `/clear` (cf. conception NPK §2.1).
