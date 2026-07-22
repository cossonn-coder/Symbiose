# Tronçon ④e — MÉTADONNÉE encyclopédie + tests + stub pont (golden NEUTRE)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc FIGÉ : `docs/faune/vie_macro/conception_faune_dediee.md` (§1.1 blurb/interconnexions, §4 C9/C10, §7 ④e).
> **Pré-requis : ④d CLOS** (les 10 espèces existent, toutes les interconnexions
> dynamiques bouclées). Kickoff autosuffisant. Python depuis `data/code/`.

## Objectif

Clore la partie **Python** : remplir la **métadonnée d'encyclopédie** (donnée pure,
rendu = ⑥), poser la **suite de tests complète**, et préparer la **sérialisation
par espèce** pour le pont (consommée par la vue ⑥). **Aucune dynamique nouvelle**
→ golden **NEUTRE** (la métadonnée n'est jamais lue par le tick).

## Périmètre EXACT

1. **Métadonnée** (`fields/population.py`, sur chaque `TrophicSpec` des 10) :
   - `blurb` : texte d'encyclopédie (voix naturaliste, cf. CLAUDE.md philo #5).
   - `interconnexions: tuple[str, ...]` : noms liés (graphe doc §3 / catalogue §5.3),
     ex. puceron → `("coccinelle","chrysope","syrphe_larve")`. **Donnée pure**, pas
     de mécanique (les vraies boucles sont déjà dans `predators`/`resource_fn`).
   - **Honnêteté** (docstring) : `nocturne`/`humide` — rappeler ce qui est une vraie
     porte (humide = ressource réelle via `eco.humidite`) vs un simple tag
     (nocturne = fenêtre élargie, pas de cycle jour/nuit).

2. **Suite `tests/test_faune_dediee.py`** (consolider les amorces ④b–④d) :
   - **Couverture** : 10 espèces présentes ; catégories ∈ {ravageur, auxiliaire,
     detritivore} ; chaque catégorie a ≥1 membre.
   - **Triade** : chaque espèce a resource_fn, habitat_fn ; les `predators` nommés
     existent dans le registre (ou sont des champs larvaires connus).
   - **Boucles** : coccinelle/chrysope ne montent que si puceron présent ; carabe/
     hérisson que si limace ; merle suit fruit frais + lombric ; cloporte suit litière.
   - **Déterminisme** : deux runs identiques → mêmes champs ; salts distincts (pas de
     corrélation triviale entre espèces au même (week,r,c)).
   - **Fenêtres** : doryphore/puceron nuls en plein hiver ; lombric quasi annuel.
   - **Catégorie** : `category_density("ravageur")` == somme(puceron,limace,doryphore).

3. **Stub sérialisation pont** (`tools/simserver/serialize.py`, C10) : préparer
   l'émission des sprites **par espèce** (10 clés) au lieu de par guilde — soit
   activé ici si non-cassant pour le client actuel, soit laissé en TODO documenté
   pointant ⑥. **Ne pas casser** le snapshot existant (le client Godot actuel lit
   l'ancien format → bascule coordonnée en ⑥). Idem `target.espece` (C9) = ⑥.

## Validation

1. `python3 -m tests.test_golden` → **PASS, hash INCHANGÉ depuis ④d** (métadonnée
   + tests + stub sérialisation ne touchent pas le tick).
2. `python3 -m tests.test_faune_dediee` → PASS (suite complète).
3. Suites existantes → PASS. Filet `dotnet build`.
4. Garde-fou taille : si `population.py` (déjà ≈369 > ~350) gonfle trop avec les
   blurbs, **éclater** la métadonnée dans un module données dédié (ex.
   `fields/faune_encyclo.py`) ré-exporté — le signaler.

## À faire en fin de tronçon

- `00_etat.md` (④ COMPLET : a→e, refonte faune B close côté Python, golden final
  = hash ④d, frontière ⑥ rappelée).
- Entrée `journal/` + index — **bilan de la refonte B** (3 re-figeages localisés,
  pourquoi, hashs successifs).
- Commit : `feat(catalogue) : faune ④e — encyclopédie + tests + stub pont, refonte B close (Python), golden NEUTRE`.
- Proposer ⑤ (pollinisateurs B : bourdon/osmie) ou ⑥ (vue Godot) — pas d'auto-enchaînement.
