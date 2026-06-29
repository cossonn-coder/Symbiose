# ③ Carnet auto — `carnet_lire` + `CONCEPT_DE` + gabarits 2 registres (D14 + D43)

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` (§2.1, §5).
> Tronçon **première voix** : lecteur read-only du ledger ②, voix « je » qui bascule
> **descriptif → interprétatif** au palier 3 du CONCEPT. Dépend de ②. Premier geste :
> RE-MESURER les hashs golden.

## Objectif
Écrire `carnet_lire(gs, player, filtre=None) -> list[EntréeFormatée]` (doc §2.1) :
pour chaque entrée du ledger, choisir le **concept** via la table `CONCEPT_DE`, choisir
le **registre** selon le palier de maîtrise du concept, et produire le **texte** via le
gabarit `(kind, cause, registre)`. **Aucun état neuf, aucun câblage** : pure lecture.
Inclut **D43** (acclimatation → concept `adaptation`).

## À faire

### A. Tables de données (recopier VERBATIM du doc, module de données)
- `CONCEPT_DE[(kind, cause)] = concept` — **recopier la table doc §5.0** telle quelle
  (ex. stagnation/sec→`eau`, mort/sénescence→`sénescence`, …).
- Gabarits `GABARIT[(kind, cause, registre)] = "texte avec slots {e}/{l}/{s}"` —
  **recopier VERBATIM les 2 colonnes du doc §5.1** (descriptif + interprétatif).
  Slots : `{e}` = espèce, `{l}` = lieu/zone, `{s}` = semaine/saison.
- **D43** (doc §5.1 dernière ligne) : `CONCEPT_DE[("acclimatation", None)] = "adaptation"`
  + le gabarit acclimatation (2 registres). **Aucun câblage neuf.**

### B. `carnet_lire(gs, player, filtre=None)` (`sim/carnet.py` ou module voix)
- Si pas de `gs["journal"][player]` → renvoyer `[]` (golden-safe).
- Pour chaque entrée du ledger : `concept = CONCEPT_DE[(kind, cause)]` (fallback nommé
  si paire absente — TODO, ne pas crasher) ;
- `registre = "interprétatif" si maitrise.palier(gs, player, concept) >= SEUIL_CARNET
  or reglage_anticipé(gs, player) else "descriptif"` ;
- `texte = GABARIT[(kind, cause, registre)].format(e=…, l=…, s=…)`.
- `filtre` (optionnel) : par **concept**, par **zone**, par **saison**.

### C. Seuil + réglage d'aide
- `SEUIL_CARNET = 3` (placeholder D12.4, knob en tête).
- Réglage « interprétatif anticipé » (Options, **défaut NON**, cf. CLAUDE.md) → seuil
  ramené à **1** pour ce joueur. Lire le flag via le réglage joueur (helper local si
  pas encore exposé ; sinon `# TODO(options): brancher le flag réel`).

## Couches
Lecteur read-only au niveau `sim`. Lit `gs["journal"]` (②) + `maitrise.palier` (D12,
`sim/maitrise.py`). N'écrit RIEN, n'avance aucun tick, aucun RNG.

## Définition de done
- Tables `CONCEPT_DE` + `GABARIT` recopiées du doc (§5.0/§5.1), `carnet_lire` + `SEUIL_CARNET`.
- `tests/test_carnet.py` (NOUVEAU) : même événement → **palier<3 = descriptif**,
  **palier≥3 = interprétatif** ; réglage anticipé force interprétatif dès palier 1 ;
  **acclimatation → concept `adaptation`** (D43) ; `filtre` par concept/zone/saison ;
  sans joueur → `[]`.
- **Golden INTACT** (lecture pure, hors tick) : smoke + population bit-identiques.
- MAJ `00_etat.md` (③ → FAIT) puis commit.

## Pièges
- **Corpus = livrable éditorial** : recopier le texte du doc **fidèlement**, ne pas
  réécrire les gabarits. C'est de la donnée, pas de la logique.
- Le registre dépend du palier du **CONCEPT** (pas de l'espèce) — décision B figée.
- Paire `(kind, cause)` absente de `CONCEPT_DE` → fallback nommé + TODO, jamais un crash.
- Read-only : si tu touches un champ écologique, le golden bouge → tu as un bug.
