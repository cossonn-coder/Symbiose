# Tronçon ④b — SCINDER la catégorie `ravageur` (puceron / limace / doryphore)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc FIGÉ : `docs/conception/CONCEPTION_FAUNE_DEDIEE.md` (§2 ravageur, §4 C11/C13/C14).
> **Pré-requis : ④a CLOS** (catégorie + `category_density` + consommateurs recâblés).
> Kickoff autosuffisant. Python depuis `data/code/`. Filet `dotnet build`.

## Objectif

Remplacer le champ unique `ravageur` par **3 champs d'espèce** (même catégorie
`"ravageur"`), chacun avec SA triade (doc §2). La pression herbivore subie par les
plantes (`category_density("ravageur")`, posé en ④a) devient la **somme** des trois
→ le golden bouge de façon **attribuable à cette seule scission**.

| Espèce | Nourriture (resource_fn) | Prédateurs | Habitat (habitat_fn) | Fenêtre |
|---|---|---|---|---|
| **puceron** | `_foliage_grid` *(existe)* | coccinelle, chrysope, **syrphe_larve** | `_monoculture_grid` *(existe)* | estivale (daylen 10/13) |
| **limace** | `_foliage_grid` *(réutilisé)* | carabe, hérisson | `_humide_litiere_grid` *(neuf)* | humide/frais |
| **doryphore** | `_foliage_solanaceae_grid` *(neuf, filtré famille)* | carabe | `_solanaceae_grid` *(neuf, réduit par ail)* | estivale |

> ⚠️ En ④b, coccinelle/chrysope/carabe/hérisson **n'existent pas encore** (ce sont
> des auxiliaires, scindés en ④c). Donc leurs noms dans `predators` ne résoudront
> PAS encore (sauf `syrphe_larve`, pont existant). C'est **voulu** : `_predator_field`
> renvoie `None` pour un nom inconnu → prédation 0 pour ce prédateur (pas d'erreur,
> cf. `EcoFields._predator_field`). La régulation auxiliaire se branchera en ④c.
> En attendant, garder le prédateur **`auxiliaire` agrégé** transitoire ? **NON** :
> on liste les vrais prédateurs nommés dès ④b (ils s'activeront en ④c) → re-figeage
> en deux temps mais lisible. (Si Nico préfère un golden ④b plus proche de l'actuel,
> option : laisser `syrphe_larve` seul en ④b, ajouter les nommés en ④c — à décider
> au lancement, défaut = noms dès ④b.)

## Périmètre EXACT

**Specs** (`fields/population.py`, `build_population_specs`) : retirer la spec
`ravageur`, ajouter `puceron`/`limace`/`doryphore` (`category="ravageur"`). Salts
DÉDIÉS neufs (`_SALT_PUCERON`… décorrélés). Signal fruit pourri (`_rav_fruit_signal`)
→ **retiré du ravageur** ici, **reposé sur cloporte en ④d** (en ④b : aucun porteur
du signal pourri → petit re-figeage du fruit pourri, à noter ; alternative : le
laisser sur `limace` transitoirement → à décider, défaut = retiré, reposé ④d).

**Ressources neuves** (`population.py`) :
- `_foliage_solanaceae_grid` : comme `_foliage_grid` mais ne somme que les plantes
  dont `plant_class.family == "Solanaceae"`.
- `_solanaceae_grid` : habitat doryphore = présence Solanaceae locale, **réduite**
  par la rondelle `maladie`-répulsive de l'ail (Amaryllidaceae `adjacency_bonus`
  posé en ③) — relire comment l'ail dépose son effet pour le soustraire ici.
- `_humide_litiere_grid` : habitat limace = `eco.humidite` (existe) + présence de
  litière (`eco.litiere[r][c]` masse). **Partagé avec cloporte en ④d**.

**Recâblage** (doc §4) :
- C11 `_ravageur_grid` (ressource auxiliaire) → bientôt scindé en
  `_espece_grid("puceron")`/`("limace")` ; mais l'auxiliaire est encore un champ
  unique en ④b → **garder `_ravageur_grid` = `category_density("ravageur")`**
  (l'auxiliaire mange « tous les ravageurs » tant qu'il n'est pas scindé). Le
  recâblage fin par espèce arrive en ④c.
- C14 `syrphe_larve` ∈ `predators` du **puceron** (plus du champ ravageur disparu).

## Validation

1. `python3 -m tests.test_golden` → re-figé MAÎTRISÉ. **Capturer le nouveau hash**,
   l'inscrire dans `00_etat.md` + journal, expliquer la dérive (3 espèces aux
   ressources/habitats distincts vs 1 champ ; doryphore filtré Solanaceae →
   pression nulle là où il n'y a pas de Solanaceae, etc.).
2. `tests/test_population`, `test_attraction`, `tests/vigueur/*` → adapter si elles
   référencent `populations["ravageur"]` (utiliser `category_density` ou un nom
   d'espèce). NE PAS casser leur intention.
3. **Nouveau** `tests/test_faune_dediee.py` (ou l'amorcer) : les 3 ravageurs
   existent, `category="ravageur"`, fenêtres ouvertes/fermées correctes, doryphore
   nul sans Solanaceae.
4. Filet `dotnet build`.

## À faire en fin de tronçon

- `00_etat.md` (④b ✅ : ravageur scindé en 3, **nouveau hash golden = …**, signal
  pourri reposé ④d, prédateurs auxiliaires inactifs jusqu'à ④c).
- Entrée `journal/` + index.
- Commit : `feat(catalogue) : faune ④b — ravageur scindé (puceron/limace/doryphore), golden re-figé maîtrisé`.
- Proposer ④c (scinder auxiliaire) — pas d'auto-enchaînement.
