# Tronçon ② — PLANTES lot 1 (familles déjà cataloguées)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc de référence FIGÉ : `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`
> (§4 sélection, §7 partage doc/code). Kickoff **autosuffisant** (relançable à froid).

## Objectif

Ajouter **5 espèces** dans des familles **déjà cataloguées** (donc attractivité
florale héritée **gratis**, aucune nouvelle famille à câbler) :

| Espèce | Genre / nom latin | Famille | Cycle | Hiver | Niche débloquée |
|---|---|---|---|---|---|
| **Thym** | *Thymus* | Lamiaceae | perennial | **evergreen** | persistante (gel ⑥) + mellifère abeille |
| **Lavande** | *Lavandula* | Lamiaceae | perennial | **evergreen** | persistante + mellifère abeille/papillon |
| **Bourrache** | *Borago* | Boraginaceae | annual | die | mellifère abeille majeure + comestible |
| **Consoude** | *Symphytum* | Boraginaceae | perennial | dormant | accumulatrice / biomasse-paillis (compost) |
| **Moutarde** | *Sinapis* | Brassicaceae | annual | die | engrais vert pionnier + mellifère syrphe |

> **C'est de la DONNÉE PURE** : on déclare des classes d'espèces + des entrées de
> catalogue. Aucun mécanisme moteur nouveau (voir « point evergreen » ci-dessous).

## Pourquoi attractivité « gratis »

Les 3 familles sont **déjà** dans les tables `_ATTRACT_*` de `fields/population.py`
(abeille/syrphe/papillon) :
- Lamiaceae : abeille 1.0, papillon 1.0, syrphe 0.40 → thym/lavande nourrissent
  fort l'abeille et le papillon.
- Boraginaceae : abeille 1.0, papillon 0.70, syrphe 0.60 → bourrache/consoude
  fortes mellifères abeille.
- Brassicaceae : syrphe 0.90, abeille 0.50 → moutarde nourrit fort le syrphe.

Il suffit que ces espèces aient un effet `floraison` qui pose la rondelle
`pollinisateur` (comme tomate/basilic) **et** que `inst.floraison` monte (le gate
GDD+photopériode du moteur s'en charge) → la `resource_fn` nectar les lit
automatiquement. **Rien à toucher dans `population.py`.**

## ⚠️ Point evergreen — ce tronçon PORTE la vérification

Le doc §7.2 rangeait la vérif `evergreen` en ③ ; on la **rapatrie ici** car les
espèces evergreen (thym, lavande) sont dans CE lot. Bonne nouvelle : le chemin
**existe déjà** et est simple — `sim/engine/mortalite.py:245` :

```python
elif ws == "evergreen":
    plant.stress_memory = min(1.0, plant.stress_memory + 0.05)  # légère réduction métabolique, PAS de mort
```

Donc une vivace `winter_strategy="evergreen"` **survit** à l'hiver (ni mort ni
dormance profonde), juste un léger stress. C'est exactement l'intention (coussin
de thym vert sous le gel). **Mais ce chemin n'est exercé par AUCUNE espèce
aujourd'hui** → l'ajouter sans test laisse un trou. → **livrer un test ciblé** qui
plante un thym, le passe par un hiver, et vérifie qu'il est **encore vivant**
(`is_alive`) et **encore feuillé** (`foliage_density_at > 0` même en hiver — les
evergreen ne sont pas `deciduous`).

`biennial` (carotte/ail) reste en ③ — non concerné ici.

## Données indicatives par espèce (à étudier, calibrage post-test)

Nico n'est pas botaniste : ci-dessous des valeurs **proposées et justifiées**
(allure naturaliste), à reprendre telles quelles ou ajuster. Champs sur le patron
des espèces existantes (cf. `cultivees.py`/`compagnes.py`). `resistance/
stimulation_ecrasement` lus uniquement par le geste « écraser » (défauts neutres
sinon).

**Thym** *(Lamiaceae)* — sous-arbrisseau coussin :
- `life_cycle="perennial"`, `winter_strategy="evergreen"`, `deciduous=False`
- `foliage_density=0.35`, `longevity_years=8`, `reproduction_rate=0.10`
- `resistance_ecrasement=0.8`, `stimulation_ecrasement=0.5` (coussin ligneux, encaisse)
- `keywords=["Aromatique","Mellifère","Médicinale","Couvre-sol"]`
- stades : semis (sol, ~3 cm) → adulte vivace (`duration_weeks=0`, strate basse,
  `canopy_height≈25`, `canopy_radius≈25`) avec effet `floraison` → `add_rondelle
  pollinisateur` ; pas besoin de stade `mature` séparé (vivace).

**Lavande** *(Lamiaceae)* — sous-arbrisseau structurant :
- `perennial`, `evergreen`, `deciduous=False`, `foliage_density=0.45`,
  `longevity_years=12`, `reproduction_rate=0.08`
- `resistance_ecrasement=0.6`, `stimulation_ecrasement=0.4`
- `keywords=["Aromatique","Mellifère","Structurante","Médicinale"]`
- stades : semis → adulte vivace (strate basse-moyenne, `canopy_height≈50`,
  `canopy_radius≈40`), effet `floraison` → `add_rondelle pollinisateur`.

**Bourrache** *(Boraginaceae, sous-classe `PlantBase`)* — annuelle ressemis :
- `annual`, `die`, `foliage_density=0.45`, `reproduction_rate=0.06`
- `keywords=["Mellifère","Comestible","Engrais vert"]`
- stades : semis → adulte (strate basse-moyenne, `canopy_height≈60`), effet
  `floraison` → `add_rondelle pollinisateur` → mature (récolte légère / biodiv).

**Consoude** *(Boraginaceae)* — accumulatrice dynamique vivace :
- `perennial`, `dormant`, `foliage_density=0.55`, `longevity_years=10`,
  `reproduction_rate=0.04`
- `root_radius` LARGE au stade adulte (pivot profond, ≈60 — comme le pissenlit
  `competitor`) → remonte les nutriments
- `keywords=["Accumulatrice","Mellifère","Engrais vert","Biomasse"]`
- effets adulte : `permanent`/`weekly` `inject_field fertilite +0.03 local`
  (remontée nutriments, patron pissenlit) **+** `floraison add_rondelle pollinisateur`.

**Moutarde** *(Brassicaceae, sous-classe `PlantBase`)* — engrais vert pionnier :
- `annual`, `die`, `foliage_density=0.40`, `reproduction_rate=0.07`
- `archetype=None` (NE PAS mettre `pioneer` : `archetype` alimente
  `WEED_CATALOGUE`/la succession spontanée — la moutarde est une cultivée, pas une
  adventice de succession ; garder `None` évite tout télescopage)
- `keywords=["Engrais vert","Mellifère","Pionnière"]`
- effets adulte : `permanent`/`weekly` `inject_field om_fresh +0.02 local`
  (biomasse, patron bourse-à-pasteur) **+** `floraison add_rondelle pollinisateur`.

## Où écrire (garde-fou taille — un fichier = une responsabilité)

`tools/compte_ldc.py` mesure le CODE PUR (commentaires pédagogiques exclus, seuil
~350). Recommandation (à ajuster selon la mesure réelle) :

- **Bourrache + Consoude + Moutarde** → étendre `plants/species/compagnes.py`
  (déjà l'asile des mellifères/engrais-verts compagnons ; Phacélie y est, même
  famille Boraginaceae). Mettre à jour son docstring de tête.
- **Thym + Lavande** → **nouveau** `plants/species/aromatiques.py` (Lamiaceae
  aromatiques persistantes — concept distinct, evergreen) avec docstring dédié.
- Si `compagnes.py` dépasse le seuil après ajout → basculer aussi
  bourrache/consoude vers un fichier `melliferes.py` (décision à la mesure).

Puis **brancher** :
- `plants/species/__init__.py` : importer + ré-exporter les 5 nouvelles classes.
- `plants/catalogue.py` : 5 entrées dans `PLANT_CATALOGUE` (clés `"thym"`,
  `"lavande"`, `"bourrache"`, `"consoude"`, `"moutarde"`). **NE PAS** toucher
  `WEED_CATALOGUE` (succession) ni `PERENNIAL_CATALOGUE` (ligneuses).

## Golden — attendu NEUTRE

Le smoke (`tests/test_golden.py`, 2 tuiles × 4 ans) plante un **jeu fixe**
d'espèces ; il **n'instancie aucune** des 5 nouvelles. Ajouter des classes + des
entrées de catalogue **non plantées** ⇒ **golden NEUTRE** (hash inchangé). Si le
hash bouge, c'est un bug (un import à effet de bord, une famille modifiée) → à
investiguer, pas à re-figer à la légère.

## Validation

1. `python3 -m tests.test_golden` (depuis `data/code/`) → **PASS, hash inchangé**.
2. **Nouveau test ciblé evergreen** (suite `tests/`, patron des autres suites) :
   planter un thym, simuler jusqu'à passer ≥1 hiver, asserter `is_alive` ET
   `foliage_density_at(..., saison="hiver") > 0`. → verrouille le chemin
   `ws=="evergreen"`.
3. **Sanity catalogue** : les 5 clés sont dans `PLANT_CATALOGUE` et instanciables
   (un petit test « chaque espèce du catalogue germe et atteint un stade adulte »
   si une telle suite n'existe pas déjà — sinon vérifier à la main via `main.py`).
4. `tools/compte_ldc.py` : aucun fichier touché ne franchit ~350 sans le signaler.
5. `dotnet build Symbiose.csproj` non requis (zéro C# touché).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (② ✅ + note evergreen vérifié ici, biennial reste ③).
- **Entrée `journal/` + index `journal.md`** (catalogue enrichi ② : +5 plantes
  familles connues, evergreen exercé, golden NEUTRE).
- Commit : `feat(catalogue) : +5 plantes (thym, lavande, bourrache, consoude, moutarde) — familles connues, evergreen exercé, golden NEUTRE`.
- Proposer ③ (familles + cycles neufs) ou ④ (faune parfums) — **pas** d'enchaînement auto.
