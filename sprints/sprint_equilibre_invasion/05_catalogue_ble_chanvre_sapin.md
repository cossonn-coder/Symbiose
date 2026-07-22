# Tronçon ⑤ — Catalogue paille/BRF : blé, chanvre, sapin + 5 voix chacun

**Prérequis** : `CLAUDE.md`, `00_etat.md`, `docs/faune/trophique/conception_equilibre_invasion.md` §4,
`docs/narration/voix/conception_voix_narratives.md`. Patrons : `plants/species.py`,
`plants/perennials.py` (ligneux, pour le sapin), `plants/catalogue.py`, et les
corpus de voix (`sim/encyclopedie_corpus.py`, `sim/concept_corpus.py`,
`sim/pages_corpus.py`, `sim/magazine.py`, marqueurs d'événements au ledger).

## Objectif
Ajouter **3 espèces** sources de mulch, chacune COMPLÈTE (règle « l'espèce sert
l'idée » + « toute plante = ses 5 voix »).

- **Blé** (*Triticum*) — graminée annuelle, strate moyenne. Récolte → **paille**.
- **Chanvre** (*Cannabis sativa*) — annuelle haute, fibre → **paille durable**.
- **Sapin** (*Abies*) — conifère pérenne ligneux (`perennials.py`), aiguilles
  **acidifiantes** + rameaux → **BRF/aiguilles**. Persistant (non caduc).

## Fichiers à toucher
1. `plants/species.py` (blé, chanvre) / `plants/perennials.py` (sapin) — classes
   avec stades, strate, empreintes, gènes, `ph_opt`/`ph_tol`, marqueur « source de
   mulch » (nature produite à la récolte, lu par ④).
2. `plants/catalogue.py` — enregistrer les 3 espèces.
3. **5 voix par espèce** :
   - **Encyclopédie** (fiche 3 niveaux) — `sim/encyclopedie_corpus.py`.
   - **Carnet / concepts** — `sim/concept_corpus.py` (concepts illustrés : paille/
     BRF, faim d'azote, acidification pour le sapin) via `CONCEPT_DE`.
   - **Pages secrètes** (si lore) — `sim/pages_corpus.py` (ex. chanvre plante-
     service, sapin & sol acide) — optionnel mais souhaité.
   - **Magazine** — `sim/magazine.py` : rattachement famille/offre.
   - **Événements** — marqueurs de cycle de vie au ledger (semis/floraison/récolte).

## Golden
**INTACT**. Espèces ABSENTES du smoke (2 tuiles, catalogue figé du golden) →
aucun effet sur `test_golden`/`test_population`. Vérifier. Ajouter/étendre
`tests/test_catalogue_*` pour les 3 espèces (présence, voix, nature de mulch).

## NE PAS
- Ne pas planter ces espèces dans le monde smoke. Pas de RNG. Une plante sans ses
  voix = interdit (fiche muette).

## Vérif / F5
Encyclopédie/magazine listent les 3 espèces ; récolter du blé/chanvre → stock
paille ; broyer un sapin → BRF. F5 = ⑧.
