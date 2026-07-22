# Tronçon ⑦ — Voix narratives (encyclopédie + carnet), OBLIGATOIRE

> Kickoff **autosuffisant** (lis CLAUDE.md + 00_etat.md + ce fichier).
> Conception : `docs/vegetal/floraison/conception_germination_thermique.md` §6 +
> `docs/narration/voix/conception_voix_narratives.md`. Lancement depuis `data/code/`.
> Golden : **NEUTRE** (corpus read-only, hors tick).

## Objectif
Rendre la germination thermique **lisible par le joueur** via les voix diégétiques.
La mécanique est muette sans ses voix (garde-fou projet « toute plante = ses
voix »). Ici, pas d'espèce neuve, mais on enrichit les voix des espèces typées.

## Contexte voix (read-only, hors tick)
- **Encyclopédie** : `sim/encyclopedie_corpus.py` (fiche 3 niveaux, §6 de
  `docs/narration/voix/conception_voix_narratives.md` : niveau 1 « vu », niveau 2 « cycle complet/bio »,
  niveau 3 « cycles répétés/effets écosystémiques »).
- **Carnet** : `sim/carnet.py` + `CONCEPT_DE` (§5) — descriptif au début,
  **interprétatif au palier de maîtrise** du concept.
- Ledger d'événements `sim/journal.py` (hors tick), `sim/evenements.py`.

## À faire
1. **Encyclopédie** — pour les espèces typées (③), enrichir la fiche :
   - niveau 2 (bio) : la **fenêtre thermique de levée** (« germe dès que le sol
     atteint ~X °C », sans chiffre en HUD primaire — texte naturaliste) +
     l'environnement préférentiel ;
   - niveau 3 (éco) : la **succession temporelle émergente** (« les pionnières
     ouvrent la saison sur sol encore frais, les frileuses suivent à la chaleur »).
2. **Carnet** — concept « germination / chaleur du sol » (ajouter au `CONCEPT_DE`
   si absent) :
   - **descriptif** (avant maîtrise) : « les semis tardent », « rien ne lève
     encore », « le froid retient les graines » ;
   - **interprétatif** (au palier de maîtrise météo/sol) : « le sol n'a pas atteint
     la chaleur de réveil de cette espèce » ; « mes lignées lèvent plus tôt chaque
     année » (rend visible la sélection darwinienne émergente).
3. **Voix première personne**, méthode scientifique préservée (descriptif tant que
   non maîtrisé). Pas de narrateur omniscient, pas de chiffre en HUD.
4. **Pages secrètes** (`sim/pages_corpus.py`) : OPTIONNEL — une page de lore paysan
   sur « semer à la lune / au sol tiède » si elle s'incarne bien ; ne pas forcer.

## Golden
**NEUTRE.** Corpus et ledger sont read-only, hors tick → `tests/test_golden.py`
**inchangé**. Vérifier le hash.

## Ce qu'il NE faut PAS faire
- Ne PAS faire dépendre la simulation des voix (read-only strict).
- Ne PAS mettre de chiffres/barres en HUD primaire (philo #5 — texte diégétique).
- Ne PAS livrer le carnet interprétatif avant le palier (préserve la méthode #6).
