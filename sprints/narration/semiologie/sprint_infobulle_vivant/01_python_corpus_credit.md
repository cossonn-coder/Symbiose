# Tronçon ① — Python : corpus, crédit saisonnier, snapshot, légende

> Lire d'abord `CLAUDE.md`, `00_etat.md` et
> `docs/narration/semiologie/conception_infobulle_vivant.md` (§2-§4.1 surtout).
> Golden **INTACT** : référence `22768f33…` (`cd data/code && python3 -m tests.test_golden`).
> Jamais `test_epaisseur_500ans`. Tout est **hors tick**.

## Objectif
Fournir à la vue tout le texte et toutes les données de l'info-bulle du vivant, et rendre
le nom d'une bête / du champignon atteignable en jeu normal (observé en 3 saisons).

## À faire
1. **Corpus** `data/code/sim/signes_corpus.py` (donnée pure, aucun import) :
   - `FAUNE_ROLE` : ≤ 6 mots par espèce de `FAUNE_VU` (mêmes 20 clés ; voix naturaliste,
     cohérente avec les `blurb` de `fields/faune_encyclo.py` et les vraies boucles de
     `fields/population/registry.py` — un rôle ne doit pas affirmer ce que le moteur ne
     fait pas). Test : mêmes clés que `FAUNE_VU`.
   - `CHAMPIGNON_VU` (ce qu'on voit d'un carpophore, sans le nom) et `CHAMPIGNON_ROLE`
     `{bois, racines, humus}` → « décompose le bois mort » / « relie les racines » /
     « lie l'humus ».
   - `VOIX_SAINE` `{franc, automne, terne}` (cf. conception §2.6, §3) ; libellés
     d'abondance (seule / quelques-unes / nombreuses), de nourriture (rare / suffisante /
     abondante), de réseau (clairsemé / dense).
   - Docstring de tête à mettre à jour.
2. **Crédit par observation saisonnière** (faune + `champignon` UNIQUEMENT, jamais les
   plantes) dans le chemin de `observer_espece` (`tools/simserver/maitrise_pont.py`) — ou un
   petit module `sim/` si plus propre (respecter `plants ← fields ← sim ← engine` ; vérifie
   le sens des imports avant de placer) :
   - saison absolue = même calcul que `sim/signes._saison_absolue` (réutilise-le, DRY) sur
     la semaine consignée (`game_state["week"] - 1`, comme `cmd_observer`/`observer_signe`) ;
   - si la saison est **strictement postérieure** à la dernière saison créditée pour cette
     clé ET palier < 3 → `maitrise.enregistrer_preuve(..., n = preuves_requises(palier))`
     (vérifie la signature réelle) pour franchir exactement un palier. Le 1er survol reste
     la découverte (palier 1) et **compte comme la 1ʳᵉ saison**.
   - mémoire « dernière saison créditée » par clé dans la tranche joueur de maîtrise, à
     côté de `_detection` (même convention de clé privée) ; JSON-sérialisable. **Vérifie**
     que le save la conserve (le save sérialise-t-il toute la tranche ?).
   - plafond = `carnet.SEUIL_CARNET` (pas de nombre en dur).
3. `sim/signes.appris` : ajouter `champignon` à la liste `faune` (ou une clé dédiée —
   choisis, documente, la vue ② / ③ s'adapte). `sim/encyclopedie._lire_mono` : corriger le
   commentaire « plafonnée à palier 1 » (la fiche reste mono-niveau).
4. **Snapshot** (`tools/simserver/serialize*.py`) :
   - chaque carpophore porte son **rôle local** (code court `b`/`r`/`h` ou équivalent) :
     bois frais au plot (`eco.bois_fresh_at(r,c) > 0`) → bois ; sinon racines vivantes
     exploitant le plot → racines (trouve la lecture déjà utilisée par le boost
     mycorhizien dans `fields/ecofields/uptake.py` ; ne la recalcule pas autrement) ; sinon
     humus. Lecture pure. Si le calcul des racines par plot est cher, construis l'ensemble
     des plots racinés UNE fois par tuile et par snapshot (jamais par carpophore).
   - **butineurs** : vérifie ce que `ForagerLayer` reçoit ; si aucune ressource locale,
     ajoute l'équivalent de `activite` (ressource florale locale déjà calculée par le
     registre pollinisateurs) — sinon la nourriture des butineurs ne s'affiche pas
     (acceptable si coûteux : le dire dans `00_etat.md`).
5. **Bandes de nourriture mesurées** : script de mesure sous
   `sprints/narration/semiologie/sprint_infobulle_vivant/mesures/` (run témoin ≥ 2 ans,
   seed de démo) → distribution de `activite` des sprites de faune → bornes = tertiles
   (arrondis 2 déc.), constantes nommées dans le corpus avec leur source `[VM, n=…]`.
6. **Légende** (`tools/simserver/maitrise_cmds.cmd_legende`) : ajouter `faune_role`,
   `champignon {vu, roles}`, `voix_saine`, libellés et bornes de nourriture. Rétro-compatible
   (clés ajoutées).
7. Bump `ENGINE_VERSION` (`tools/simserver/version.py`) + son changelog local.
8. Tests : étendre `tests/test_signes.py` / `test_signes_legende.py` / `test_maitrise*` —
   1er survol = palier 1 ; même saison = rien ; 2ᵉ saison = 2 ; 3ᵉ = 3 et `appris` ;
   4ᵉ = reste 3 ; plante survolée = aucun crédit saisonnier ; option anticipée nommée au
   1er survol ; rôle carpophore sur un cas bois / racines / humus. Toutes les suites
   ciblées vertes + golden intact.

## NE PAS
- Toucher au tick, aux champs, à `engine` ; inventer une santé ou une maladie animale.
- Créditer les plantes par ce chemin (leur maîtrise passe par la détection D12).
- Écrire du C# (tronçons ② ③).

## Fin de tronçon
`00_etat.md` : cocher ①, consigner les bornes mesurées, la forme exacte des nouvelles clés
snapshot / légende (la vue en dépend), toute prémisse fausse trouvée. Commit.
