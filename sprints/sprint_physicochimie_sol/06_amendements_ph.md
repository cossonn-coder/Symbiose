# Tronçon ⑥ — Amendements pH (rondelles `chaux` / `soufre`)

> Sprint physico-chimie du sol. Conception : `docs/conception/CONCEPTION_SOL_PH.md`
> §2.4 (amendements), §2.1 (formule de dérive `cible_ph` où s'injecte `AMEND_PUSH`),
> §3 (constantes). Kickoff **autosuffisant** (relançable à froid). Python depuis
> `data/code/`.
> Tronçons ① (champ `ph` hérité + dérive), ② (n/p/k posés), ③ (Liebig), ④ (lockout
> cloches), ⑤ (fenêtres pH par espèce + chlorose + indicatrices) **déjà CLOS**.
> Golden figé `d8856261bbe49787…` (inchangé depuis ④ : ⑤ a été NEUTRE).

## Objectif

Le pH dérive aujourd'hui de façon SUBIE (héritage roche-mère − litière − lessivage,
tronçon ①). Le ⑥ donne au joueur le **levier d'action** : deux nouvelles
`RONDELLE_TYPES` posables — **`chaux`** (remonte le pH, corrige un sol acide) et
**`soufre`** (descend le pH, acidifie pour les calcifuges type myrtille). C'est le
geste permacole « j'amende mon sol », **lent et progressif sur les saisons** (jamais
instantané — philo #2 : on pousse une cible, le sol répond avec inertie).

## Le modèle (CONCEPTION §2.4 + §2.1)

L'amendement injecte un terme `AMEND_PUSH` dans la **cible** de dérive du pH (le
`tick_ph` de `fields/ecofields/ph.py`), **tant que la rondelle est présente** sur un
`StakeSlot` du plot (ou de la tuile) :

```
cible[r,c] = ph_roche[soil_type] − ACIDIF_OM·om − ACIDIF_LEACH·leach
           + AMEND_PUSH        si rondelle `chaux`  présente   (signe +)
           − AMEND_PUSH        si rondelle `soufre` présente   (signe −)
ph += (cible − ph) · PH_INERTIA / (1 + cec)
```

- **Progressif** : la poussée est sur la CIBLE, pas sur `ph` directement. Avec
  `PH_INERTIA` faible (0.02), il faut plusieurs saisons pour que le pH rejoigne la
  nouvelle cible — exactement l'effet d'un amendement réel (la chaux met un an).
- **Réversible** : retirer la rondelle ⇒ la cible repart vers son héritage, le pH
  redérive lentement. Pas d'effet « cliquet ».
- **Event-driven** : poser/retirer une rondelle = geste joueur HORS tick (comme les
  autres rondelles), coûtant de la **Vigueur**. Le tick écolo ne fait que LIRE la
  présence → **golden NEUTRE** (aucune rondelle `chaux`/`soufre` dans le smoke).

## Constante (CONCEPTION §3 — à ajouter dans `fields/ecofields/constants.py`)

```python
AMEND_PUSH = 0.15   # poussée pH/saison d'un amendement présent (signe selon chaux/soufre)
```
(placeholder, calibrage post-test — déjà annoncée dans la conception, pas encore posée).

## Greffes exactes (repères, à re-vérifier au grep)

1. **`RONDELLE_TYPES`** — `world/tile.py:16` : ajouter `"chaux"`, `"soufre"` au
   `frozenset`. Vérifier `StakeSlot.add_rondelle` (validation par appartenance au set,
   ~ligne 42) : rien d'autre à toucher pour la POSE.

2. **`tick_ph`** — `fields/ecofields/ph.py` : le calcul de `cible` doit voir la
   présence d'amendement PAR PLOT. La couche `fields` n'importe pas `world`/`sim` →
   passer l'info en ARGUMENT depuis le conteneur. Deux options à trancher :
   - (a) un `amend_push_at(r,c)` scalaire signé (map ou GridField léger) construit par
     `container.tick_ph` à partir de la tuile, ajouté à `cible` ;
   - (b) `tick_ph(eco, cec, amend_map=None)` où `amend_map[(r,c)] = +1|−1|0`.
   Recommandé : (a) signé `∈ {−AMEND_PUSH, 0, +AMEND_PUSH}`, ajouté tel quel à `cible`.

3. **Pont conteneur** — `container.py` `tick_ph` (la fine méthode déléguante du ①) :
   collecter les `StakeSlot` portant `chaux`/`soufre` (via `tile`), construire le
   push signé par plot, le passer à `ph.tick_ph`. **Vérifier la couche** : le
   conteneur a-t-il accès à la tuile/aux slots au moment du tick ? (sinon passer la
   map depuis l'engine, comme la nébulosité du thermique). Lire `boucle.py` étape 4c
   (où `tick_ph` est appelé) avant de câbler.

4. **Coût Vigueur + geste** — si une action joueur `amender`/`add_rondelle` existe
   déjà côté `sim/actions.py`, réutiliser le chemin (poser une rondelle coûte déjà de
   la Vigueur). Sinon, la pose passe par le même mécanisme que les autres rondelles
   (event-driven) — ne PAS créer d'action neuve si la pose générique suffit.

## Golden attendu

**NEUTRE** (CONCEPTION §4) : aucune rondelle `chaux`/`soufre` n'est posée dans le
smoke (2 tuiles, aucun amendement). Le set `RONDELLE_TYPES` grossit mais aucun
lecteur ne déclenche → `tick_ph` reçoit un push nul partout → dérive ① inchangée.
**Vérifier** : hash golden = `d8856261…` inchangé. Si dérive ⇒ bug (un push non nul
fuite dans le smoke), corriger plutôt que re-figer.

## À faire en fin de tronçon
- Ajouter `AMEND_PUSH` + `"chaux"`/`"soufre"` au `RONDELLE_TYPES`.
- Brancher le push signé dans `tick_ph` (cible) via le pont conteneur/engine.
- Vérifier golden NEUTRE (hash inchangé) + suites (structures, vigueur…).
  `test_senescence` reste rouge = D39 pré-existante (pas ⑥).
- Tester À LA MAIN (hors golden) : poser `chaux` sur tuile sable (5.8) → pH remonte
  sur plusieurs saisons ; retirer → redérive. Idéalement un mini-test dédié.
- MàJ `00_etat.md` (⑥ ✅, hash, note taille) ; `main.py` 50+ ans OK.
- Commit : `feat(sol) : tronçon ⑥ amendements pH (rondelles chaux/soufre) — golden NEUTRE`.
- Écrire `07_faim_azote.md` avant le `/clear` (volet NPK §2.7 : bois/BRF + substrat
  usé de culture de champignons immobilisent l'azote → re-figé maîtrisé).
