# ④ Encyclopédie — `encyclopedie_index` / `encyclopedie_lire` (fiche 3 niveaux)

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` (§2.2, §6).
> Tronçon **deuxième voix** : wiki ingame read-only, voix « naturaliste ». Niveau de
> fiche = `min(palier, 3)`, **aucun état neuf**. Dépend de ② (présence joueur/maîtrise),
> indépendant de ③. Premier geste : RE-MESURER les hashs golden.

## Objectif
Écrire `encyclopedie_index(gs, player) -> list[espèce]` (espèces dont
`maitrise.palier >= 1`) et `encyclopedie_lire(gs, player, espèce) -> Fiche` tronquée à
`min(palier, 3)` (doc §2.2). Le corpus = **28 fiches × 3 niveaux** (doc §6), recopié
dans un module de données. Pas d'état neuf : la fiche existe ssi `palier >= 1`.

## À faire

### A. Corpus de données (recopier du doc §6)
- Module de données `FICHES[espèce] = {1: "…N1…", 2: "…N2…", 3: "…N3…"}` — **recopier
  les 28 fiches × 3 niveaux** (N1 basique / N2 bio / N3 écosystémique) du doc §6.
- **Clés espèces = clés catalogue** (`plants.catalogue` / `plants/catalogue.py`).
  Vérifier que chaque clé du corpus existe au catalogue (sinon TODO nommé).

### B. `encyclopedie_index(gs, player)` (`sim/encyclopedie.py` ou module voix)
- Sans `gs["maitrise"][player]` → `[]`.
- Renvoyer la liste des espèces avec `maitrise.palier(gs, player, espèce) >= 1`
  (espèces « découvertes »). Tri stable (ordre catalogue ou alpha).

### C. `encyclopedie_lire(gs, player, espèce)`
- `p = maitrise.palier(gs, player, espèce)` ; si `p < 1` → `None` (non découverte).
- Renvoyer la fiche **tronquée à `min(p, 3)`** : niveaux 1..min(p,3) de `FICHES[espèce]`.
- Structure de retour : dict/namedtuple `{espèce, niveau_max, niveaux: {1:…, …}}`.

## Couches
Lecteur read-only au niveau `sim`. Lit `maitrise.palier` (D12) + `plants.catalogue`
(clés). N'écrit RIEN, hors tick, aucun RNG.

## Définition de done
- Corpus `FICHES` recopié du doc §6 (28 × 3), `encyclopedie_index` + `encyclopedie_lire`.
- `tests/test_encyclopedie.py` (NOUVEAU) : palier 1/2/3 → fiche au **bon niveau** (et
  palier 4/5 → toujours plafonné à 3) ; espèce `palier 0` → **absente de l'index** et
  `encyclopedie_lire` → `None` ; clés du corpus toutes présentes au catalogue.
- **Golden INTACT** (lecture pure) : smoke + population bit-identiques.
- MAJ `00_etat.md` (④ → FAIT) puis commit.

## Pièges
- **Corpus éditorial** : recopier les fiches **fidèlement** du doc (sujet bio hors
  expertise Nico — ne pas réinventer le contenu). C'est de la donnée.
- `min(palier, 3)` : paliers 4 et 5 ne débloquent PAS de niveau 4 (décision A figée).
- Clé espèce ≠ clé catalogue = bug silencieux → tester l'alignement des clés.
- Pas d'état neuf : ne stocke rien dans `gs`, tout dérive de `maitrise` + corpus.
