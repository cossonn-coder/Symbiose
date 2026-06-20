# Tronçon ④ — pH → lockout (cloches `dispo_i(ph)` + chlorose alcaline)

> Sprint physico-chimie du sol. Conception : `docs/conception/CONCEPTION_SOL_PH.md`
> §2.2 (lockout), §3 (constantes), §5 (interconnexions). Kickoff **autosuffisant**
> (relançable à froid).
> Tronçons ① (champ `ph` hérité + dérive, inerte), ② (champs `n`/`p`/`k` posés),
> ③ (bascule Liebig : `fertilite` supprimé net, uptake N/P/K plafonné par le champ,
> minéralisation splittée, lessivage/CEC) **déjà CLOS**. Golden figé `87ed27ae…`.
> ⚠️ **Re-figé MAÎTRISÉ** (un seul levier branché) — annoncer la dérive à Nico.

## Objectif

Donner enfin **du sens au champ `ph`** (posé inerte au ①) : il devient le
maître-régulateur de la **disponibilité** des nutriments. Le pH ne gate PAS la
croissance directement (philo #2) — il module un **flux de disponibilité** en
cloche gaussienne appliqué à l'uptake N/P/K et à l'activité microbienne. Plus le
**phosphore** : étroitement bloqué en acide ET en alcalin (le cas pédagogique
roi). Plus la **chlorose alcaline** : une espèce acidophile sur sol calcaire
jaunit (lockout du fer) → malus de vigueur + futur indice visuel.

## Le modèle (CONCEPTION §2.2)

### Cloche de disponibilité
```
dispo_i(ph) = exp( −((ph − PH_OPT_i) / PH_WIDTH_i)² )     i ∈ {N, P, K, micro}
```
- **P** centré 6.5, **étroit** (width 1.0) : bloqué des deux côtés.
- **N** centré 6.8, **large** (2.2) : peu sensible.
- **K** centré 6.5, intermédiaire (1.8).
- **micro** centré 6.8 (1.6) : `ph → microbiome → décompo` (couplage indirect,
  **sans champ neuf**).

### Chlorose alcaline
Quand `ph > CHLOROSE_PH` (≈ 7.6) **sur une espèce acidophile** : lockout du fer →
malus de vigueur. L'**indice visuel jaunissement** est du ressort de la vue
(tronçon ⑨) — ici on pose juste le **facteur de vigueur** côté moteur.

## Constantes (déjà spécifiées CONCEPTION §3 — à ajouter dans `constants.py`)

```python
PH_OPT   = {"N": 6.8, "P": 6.5, "K": 6.5, "micro": 6.8}
PH_WIDTH = {"N": 2.2, "P": 1.0, "K": 1.8, "micro": 1.6}
CHLOROSE_PH = 7.6            # au-dessus, chlorose ferrique des acidophiles
```

## Greffes exactes (repères actuels, à re-vérifier au grep)

1. **Helper pur** — ajouter dans `fields/ecofields/nutriments.py` (ou un `ph.py`
   déjà existant pour la dérive ①) une fonction PURE `dispo(ph, nut)` =
   `exp(−((ph − PH_OPT[nut])/PH_WIDTH[nut])²)`. Garder `container.py` mince.

2. **Uptake N/P/K** — `container.plant_uptake`, bloc BESOIN (actuellement
   `container.py:683-691`). Le commentaire `# pH lockout = 1.0 ici (④)` marque le
   point. Multiplier `besoin` par `dispo(self.ph.at_plot(r,c), nut)` :
   ```python
   ph_local = self.ph.at_plot(r, c)
   for nut, fld in (("N", self.n), ("P", self.p), ("K", self.k)):
       besoin = (BESOIN[nut].get(stage_index, 0.0) * share * asphyxie_factor
                 * (1.0 + micro_norm * UPTAKE_MICRO_BONUS)
                 * dispo(ph_local, nut))          # ⟵ cloche pH
   ```

3. **Activité microbienne** — repérer où `microbiome` alimente la décompo
   (`tick_decomposition` / `tick_soil_memory`, ~`container.py:411`) et y appliquer
   `dispo(ph, "micro")` comme facteur multiplicatif (cloche → décompo plus lente
   hors zone neutre). Vérifier que ça ne double-compte pas un facteur microbiome
   déjà présent.

4. **Chlorose (vigueur)** — côté `sim/vigueur_plante.py` (là où `qi_local` lit déjà
   `min(n,p,k)` depuis ③). Ajouter un facteur de chlorose : si l'espèce est
   acidophile (`ph_opt` bas, cf. fenêtre d'espèce — mais ⑤ pose `ph_opt`/`ph_tol`,
   **pas encore là**) ET `ph_local > CHLOROSE_PH` → malus. ⚠️ **Dépendance ⑤** : la
   notion « acidophile » par espèce arrive au ⑤. **Décider avec Nico** : soit poser
   la chlorose ici avec un proxy minimal (ex. seuil dur sans fenêtre d'espèce, peu
   d'effet golden car le smoke n'a pas d'acidophile), soit **reporter la chlorose
   au ⑤** (où `ph_opt` existe) et ne livrer au ④ que les **cloches de dispo**.
   Pencher pour : **cloches au ④, chlorose au ⑤** (évite un proxy jetable).

## Golden attendu

**RE-FIGÉ MAÎTRISÉ** : un seul levier (cloche pH sur uptake + micro). Sur les sols
du smoke (`terre` ph≈6.8, `argile` ph≈7.0), `dispo` est proche de 1.0 (proche des
optima) → **dérive faible et localisée**. Vérifier : tracer `dispo(ph, "P")` sur
terre/argile (doit être ~0.9+), confirmer que la dérive du hash s'explique par la
légère réduction d'uptake. Annoncer à Nico, re-figer.

## À faire en fin de tronçon
- Ajouter `PH_OPT`/`PH_WIDTH`/`CHLOROSE_PH` dans `constants.py` + helper pur `dispo`.
- Brancher cloche sur uptake N/P/K + activité microbienne.
- Trancher chlorose ④ vs ⑤ avec Nico (reco : reporter au ⑤).
- Vérifier suites ciblées (vigueur surtout) + golden re-figé maîtrisé (nouveau hash).
- MàJ `00_etat.md` (④ ✅, hash, dérive, note taille) ; `main.py` 50+ ans OK.
- Commit : `feat(sol) : tronçon ④ pH lockout — cloches dispo_i(ph) sur uptake N/P/K + microbiome — golden re-figé maîtrisé`.
- Écrire `05_fenetres_ph_espece.md` avant le `/clear` (volet pH §2.3 : `ph_opt`/
  `ph_tol` par espèce, germination + croissance, indicatrices acidité ; + chlorose
  si reportée ici).
