# ⑤ — Catalogue : Lierre + Jasmin (+ 5 voix chacun)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_GRIMPANTES.md` §7 + `CONCEPTION_VOIX_NARRATIVES.md`.
> **Golden NEUTRE** (espèces non semées dans le golden). Lancement depuis `data/code/`.

## Objectif
Ajouter les 2 espèces neuves qui complètent la démonstration des 3 modes de
grimpe, chacune AVEC ses 5 voix narratives (règle projet : « toute plante = ses
5 voix »). Le haricot (`vrille_volubile`) est déjà couvert par ①.

## Espèces
- **Lierre** (`Ivy`, `Hedera`), famille **Araliaceae** (NEUVE) :
  `mode_grimpe = "crampon"`, `hauteur_autoportante` faible (rampe puis grimpe),
  pérenne sempervirent, **sciaphile** (`shade_tolerance` > 1), `procedural_growth`.
  Monte au **mur nu** (crampon). Placeholders calibrage (hauteurs/rayons/gènes).
- **Jasmin** (`Jasmine`, `Jasminum`), famille **Oleaceae** (NEUVE) :
  `mode_grimpe = "sarmenteux"`, ne s'accroche que par `palisser` (④). Floraison
  mellifère (rattache aux pollinisateurs si le trait existe). Placeholders.

## Fichiers
- `plants/species/` : ajouter les classes dans le fichier thématique adéquat
  (grimpantes/pérennes — suivre le rangement existant : `cultivees.py`,
  `sauvages.py`…) + les exporter dans `plants/species/__init__.py` et
  `plants/__init__.py` (API publique).
- Nouvelles **familles** botaniques Araliaceae/Oleaceae : si le moteur porte une
  notion de famille (spillover maîtrise, `SOIL_SIGNATURE`), les déclarer au même
  endroit que les familles existantes.
- `SOIL_SIGNATURE` : étendre pour les 2 familles neuves (patron D26 — chercher
  `SOIL_SIGNATURE` et copier une signature de famille voisine, ajuster).
- **5 voix** (cf. `CONCEPTION_VOIX_NARRATIVES.md`, corpus §5/§6/§7 + §1/§2.4) :
  - **Encyclopédie** (fiche 3 niveaux) : ajouter lierre + jasmin au corpus
    (`sim/encyclopedie_corpus.py`).
  - **Carnet** : concept(s) que l'espèce illustre via `CONCEPT_DE` (le port
    grimpant/l'accroche) — `sim/concept_corpus.py` / `sim/carnet.py`.
  - **Pages secrètes** : une page de lore SI l'espèce en porte (lierre =
    symbolique ; jasmin = parfum) — `sim/pages_corpus.py` (optionnel mais
    recommandé).
  - **Magazine** : rattachement famille/offre — `sim/magazine.py`.
  - **Événements** : marqueurs de cycle de vie consignés au ledger (`sim/evenements.py`).

## Golden
**NEUTRE** — hash inchangé vs ①. Les 2 espèces ne sont PAS semées dans le golden
(`tests/test_golden.py`). Ajouter des classes au catalogue + du corpus narratif
ne touche aucune grandeur du digest.
1. `python3 -m tests.test_golden` → **inchangé** vs hash ①.
2. Si ça bouge : une des espèces est référencée par la succession spontanée
   (`niche_index`/`SeedBank`) et lève dans le golden → vérifier ; sinon corriger.
3. `python3 main.py 30` doit tourner sans crash (le catalogue élargi est chargé).

## Ce qu'il NE faut PAS faire
- Pas glycine/courge/kiwi/vigne/akébia (→ D26).
- Pas de fiche muette : les 5 voix sont OBLIGATOIRES (garde-fou projet).
- Ne pas semer ces espèces dans le golden.

## F5
- (au banc ⑥) lierre qui tapisse le mur sud ; jasmin palissé qui fleurit.
