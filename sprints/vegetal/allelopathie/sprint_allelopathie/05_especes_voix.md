# ⑤ Espèces émettrices + voix narratives

> Kickoff autosuffisant. Reprise à froid = `CLAUDE.md` + `00_etat.md` + ce fichier
> + `docs/vegetal/allelopathie/conception_allelopathie.md` §E + `docs/narration/voix/conception_voix_narratives.md`. Prérequis :
> ①②③④ faits. Golden **NEUTRE visé** (à mesurer).

## Objectif

Donner vie aux émetteurs (data pur) : renseigner `allelopathie_emission` et quelques
`allelopathie_sensibilite` marquantes sur des espèces **existantes**, puis **ajouter
2 espèces neuves** — **armoise** et **seigle** — chacune **complète de ses 5 voix
narratives** (règle projet : une plante sans ses voix est une fiche muette).

## Fichiers à toucher

### Traits sur espèces EXISTANTES (data)
- `plants/perennials.py` — **noyer** (`WalnutTree`/Juglans) : `allelopathie_emission`
  **FORT** (juglone), auto-tolérant (`allelopathie_sensibilite` ≈ 0 sur lui-même).
- `plants/species/cultivees.py` — **tournesol** (`Sunflower`) : émission **MODÉRÉE**.
- `plants/base/familles.py:440` — **aulx (Amaryllidaceae)** + aromatiques (Lamiaceae)
  : émission **LÉGÈRE**. **Résout le TODO** (remplace la triche `adjacency_bonus`
  par une vraie injection négative). Migration **surgical** : reformuler l'effet
  répulsif existant en émission allélopathique OU le conserver en doublon léger —
  trancher au plus simple, documenter.
- Sensibilités marquantes : ex. **tomate** très sensible à la juglone
  (`allelopathie_sensibilite` haute) ; graminées tolérantes. Défaut 1.0 ailleurs.

### Espèces NEUVES (moteur + 5 voix chacune)
- **Armoise** (Artemisia, Asteraceae) — vivace inhibitrice **puissante**, fait le
  vide. À ajouter au catalogue (`plants/perennials.py` ou `species/`, patron d'une
  vivace existante). Facette « vivace toxique ».
- **Seigle** (Secale, Poaceae) — annuel, **engrais vert allélopathique**, couvert qui
  étouffe puis se fauche. Facette « couvert stratégique permaculture ».
- Pour **chacune**, les **5 voix** (cf. `docs/narration/voix/conception_voix_narratives.md`) :
  encyclopédie (fiche 3 niveaux §6), carnet (`CONCEPT_DE` → concept `allelopathie`
  / cause, §5), pages secrètes (lore optionnel §7), magazine (rattachement
  famille/offre §2.4), événements (marqueurs de cycle au ledger §1).

## Golden attendu

**NEUTRE visé** — data pur ; armoise/seigle absents du smoke. **MAIS** noyer &
tournesol sont déjà présents au smoke : leur donner `allelopathie_emission > 0`
**peut** charger le champ et, via ②③④, dériver le golden. **Mesurer** : lancer
`python3 -m tests.test_golden`. Si dérive → **isoler** (elle vient des émetteurs
nouvellement dotés), **annoncer** et re-figer le hash dans `00_etat.md`. Si le noyer
n'est pas mature au smoke (maturity > durée du smoke), neutre attendu.

## Ce qu'il NE faut PAS faire

- Ne PAS ajouter une plante **sans ses 5 voix** (règle projet stricte).
- Ne PAS toucher la mécanique moteur (①→④ figés) — ce tronçon est **data + voix**.
- Ne PAS sur-calibrer : `emission`/`sensibilite` restent des placeholders lisibles.
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Vérif

Golden (mesuré, annoncé si dérive) + relecture des 5 voix armoise/seigle (chaque
dispositif renseigné) + vérifier que le TODO `familles.py:440` est levé (plus de
triche `adjacency_bonus` pour l'aulx, ou doublon assumé documenté).
