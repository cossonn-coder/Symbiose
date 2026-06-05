# Sprint Croissance·3 — Seam de perturbation `atteindre_segment` + action `tailler`

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico vient du C/Python embarqué,
> expert simulation ; débutant Godot/C# en frontend).
>
> Tronçon **moyen** : 2 fichiers de prod couplés (`sim/growth.py` pour le seam,
> `sim/actions.py` pour `tailler`) + 2 fichiers de test. Synchro cohérente assumée
> (l'exception « un fichier à la fois » est levée pour ce tronçon).

## Ce que c'est, en une phrase

Troisième des 6 tronçons. On crée le **point d'entrée unique de perturbation de
la structure** — `atteindre_segment(plant, segment_id, intensite)` (§F) — et son
**premier appelant**, l'action joueur `tailler`. Le mécanisme ne sait **pas qui**
abîme la plante (découplage acté §F) : `tailler` aujourd'hui, la grêle / un
ravageur / le vent plus tard appelleront **le même seam**. La **réponse est
émergente** (philo #2) : on baisse l'auxine / on retire du bois, et c'est le tick
de croissance suivant (`grow_plant`, tronçon 1) qui **produit** le débourrement —
on ne code aucun « +X latéraux » en dur.

## Décisions déjà tranchées (avec Nico, 2026-06-05) — NE PAS re-débattre

1. **Périmètre = seam + `tailler` SEUL.** Démontré sur la **tomate** (déjà
   procédurale, `procedural_growth=True`, tronçon 2). La **migration procédurale
   du pommier** (port étalé, fructification latérale) est **HORS périmètre** →
   tronçon **3bis** dédié (elle re-figerait le golden + exige de résoudre l'override
   `PerennialWoody` + calibrer `age_curve` sur des décennies). Ici **golden INTACT**.
2. **Coupe nette = `kill = subtree(seg)`** (le segment ciblé **inclus** + tout son
   sous-arbre). **Collet protégé** (jamais retiré : `seg.parent is None` → on démote
   sans tuer). Coupe franche, rabat la plante.
3. **Gain en Vigueur de `tailler` = proxy `∝ maturité`** (`maturite(plant)`, faible),
   en attendant les organes mûrs réels (tronçon 5) qui le raffineront. Levier de
   calibrage.

## Le découplage à garder en tête

```
        ┌─ tailler (joueur, CE tronçon) ──┐
grêle ──┤  ravageur (D31)  │  vent ────────┼──► atteindre_segment(plant, seg, intensité)
        └─ (tous PLUS TARD, hors périmètre)┘            │ baisse auxine / retire bois
                                                        ▼
                                          grow_plant (tronçon 1) → débourrement ÉMERGENT
```

Le seam est **pur structurel** (couche `sim`, déterministe, zéro RNG, zéro Vigueur).
`tailler` est **orchestration** (lit le coût, dépense la Vigueur, PUIS appelle le
seam) — exactement le patron des 6 gestes existants.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_CROISSANCE.md` — **§F** (le seam : signature, `intensite`
   continue [0,1], `COUPE_NETTE` = seuil d'écimage, `tailler` = premier appelant,
   nature → apex « plus tard »). Relis **§E.2** (archétypes : `graminee`/`rosette`
   = méristème basal → **insensibles à l'écimage par construction**, rien de spécial
   à coder). Survole §G/§H (empreinte/rendu = déjà fait / tronçons suivants).
2. `data/code/CONCEPTION_HORMONES.md` (**ARCHIVÉ**) — **§D** (l'action `tailler` :
   deux gestes apex/branche, binaire tout-ou-rien, `cout_action`/`spend`, mutation
   au-dessus du tick) et **§E** (Vigueur : coût `MODÉRÉ`, gain ∝ maturité ; Maîtrise :
   objets `("taille","sécateur")`). ⚠️ **ATTENTION** : ce doc écrit pour le modèle
   scalaire MORT (`plant.dominance_apicale = 0`, trait `reponse_taille`). Tu
   **n'utilises NI `dominance_apicale` NI `reponse_taille`** : tu appelles le seam
   structurel. Garde de ce doc le **contrat Vigueur/Maîtrise** (coût/gain/objets/
   binaire/golden-safe), **jette** la mécanique scalaire.
3. `sprints/sprint_croissance/00_etat.md` — état + tronçons 1/2 faits.
4. Code — **les ancrages** :
   - `data/code/plants/base.py:130-141` — le `dataclass Segment` (`parent`, `base`,
     `dir`, `length_cm`, `is_apex`, `has_bud`, `auxin`). Le seam **mute `is_apex`/
     `auxin`** et retire des segments.
   - `data/code/sim/growth.py:129-164` — les **helpers topologiques DÉJÀ ÉCRITS** que
     le seam **réutilise** : `_children(segs)`, `_subtree(root, ch)` (inclut `root`),
     `_rebuild(plant, kill)` (retire + réindexe les `parent`). **Ne les redéveloppe
     pas.** Le seam = ~10 lignes par-dessus.
   - `data/code/sim/growth.py:42-61` — bloc des **constantes de module**. Ajoute
     `COUPE_NETTE` ici (seuil au-delà duquel `intensite` retire l'apex + le sous-arbre).
   - `data/code/sim/actions.py:75-100` — tables `COUTS` et `OBJETS_TOUCHES` : tu y
     **ajoutes `"tailler"`**.
   - `data/code/sim/actions.py:246-260` (`deraciner`) — **le modèle exact** d'un geste
     binaire tout-ou-rien (`cout_action` → `spend` → si `ratio < 1.0: return False`).
     `tailler` le calque, mais appelle le **seam** au lieu de tuer la plante.
   - `data/code/sim/actions.py:27` — `maturite` est déjà importé (`from
     sim.vigueur_plante import maturite, vigueur_plante`). `HARVEST_GAIN_FULL`
     (`actions.py:52`) pour le gain.
   - `data/code/tests/test_croissance.py` — golden de STRUCTURE (tronçon 1) ; tu
     l'étends (effet structurel du seam). `data/code/tests/test_vigueur.py` — tests
     des ACTIONS ; tu y ajoutes le contrat Vigueur de `tailler`.

## Périmètre

### A. Le seam `atteindre_segment` — `sim/growth.py`
Ajoute une constante `COUPE_NETTE` (seuil ∈ ]0,1], défaut sobre **0.8** — au-delà,
l'`intensite` est « franche », on écime) et la fonction :

```python
def atteindre_segment(plant, segment_id: int, intensite: float) -> None:
    """Seam de perturbation §F — point d'entrée UNIQUE. Ne sait pas QUI abîme.
    intensite ∈ [0,1] continue : baisse l'auxine locale (lève l'inhibition aval) ;
    au-delà de COUPE_NETTE → écimage (retrait du segment + son sous-arbre)."""
    segs = plant.segments
    seg = segs[segment_id]
    seg.auxin = max(0.0, seg.auxin - intensite)        # douce : lève l'inhibition
    if intensite >= COUPE_NETTE and seg.parent is not None:  # collet protégé
        ch = _children(segs)
        _rebuild(plant, set(_subtree(segment_id, ch)))      # seg INCLUS (décision #2)
```

- **Doux** (`intensite < COUPE_NETTE`) : seule l'auxine baisse, structure intacte
  (modélise notching/courbure ; le débourrement local peut suivre si l'auxine passe
  sous `AUXIN_INHIB_THRESHOLD`).
- **Net** (`≥ COUPE_NETTE`) : `kill = subtree(seg)` (décision #2), `_rebuild`.
  **Collet protégé** : si `seg.parent is None`, on ne retire rien (la baisse d'auxine
  suffit ; `grow_plant` a déjà le **rejet de souche** si plus aucun apex).
- **Déterministe**, zéro RNG, zéro Vigueur. Le débourrement n'est PAS écrit ici : il
  **émerge** au prochain `grow_plant` (moins d'apex → `_update_auxin` retombe →
  bourgeons survivants sous le seuil → `_debourrement`). C'est tout l'intérêt du
  découplage : le seam écrit l'**état**, le tick produit l'**architecture**.

### B. L'action `tailler` — `sim/actions.py`
1. `COUTS["tailler"] = MODERE` ; `OBJETS_TOUCHES["tailler"] = ("taille", "sécateur")`
   (la cible vivante = clé d'espèce est ajoutée par `_objets_action`, comme les autres).
2. La fonction, calquée sur `deraciner` (binaire tout-ou-rien) :

```python
def tailler(game_state, player, plant, eco, *, cible: str = "apex") -> bool:
    """Tailler (écimage si cible='apex', égourmandage si 'branche') — geste DIRECT
    sur le vivant (philo #1 : permis mais coûteux), réponse ÉMERGENTE (philo #2 :
    on appelle le seam, le tick produit le débourrement). Binaire tout-ou-rien."""
    cost = cout_action(game_state, player, "tailler", _objets_action("tailler", plant))
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → rien n'est écrit
    seg_id = _segment_cible(plant, cible)
    if seg_id is not None:
        atteindre_segment(plant, seg_id, intensite=1.0)   # ≥ COUPE_NETTE → écimage
    gain(game_state, player, HARVEST_GAIN_FULL * maturite(plant) * GAIN_TAILLE_RATIO)
    return True
```

- **`_segment_cible(plant, cible)`** — sélecteur déterministe (point ouvert, défaut
  sobre + signale) : `"apex"` → l'**apex meneur** = segment `is_apex` au `tip[2]`
  (hauteur) max ; `"branche"` → un **sous-arbre latéral** = racine du sous-arbre du
  segment `is_apex` non-collet le plus profond (s'il n'y en a pas, repli sur l'apex
  meneur). Renvoie `None` si la plante n'a qu'un collet sans rien à couper (no-op
  géométrique, mais le coût/gain restent — on a quand même « taillé »). Depuis Godot
  (tronçon 4+) le `segment_id` viendra du clic ; ici l'engine/test le sélectionne.
- **`GAIN_TAILLE_RATIO`** — constante locale (défaut sobre **0.3**) : tailler rend
  un **peu** de Vigueur (organe récupéré à la coupe), mais reste **net coûteux** (∝
  maturité, raffiné au tronçon 5 avec les organes réels — décision #3).
- **Import** : `from sim.growth import atteindre_segment` en tête d'`actions.py`
  (couche `sim` → `sim`, pas de cycle : `growth` n'importe pas `actions`).
- **`graminee`/`rosette`** : aucun cas spécial. Leur profil ne débourre pas le long
  d'une tige (`port_archetype`, §E.2) → après écimage, pas de réveil latéral : elles
  sont insensibles **par construction** (vérifie-le en test, ne le code pas).

### C. Tests
**Étends `tests/test_croissance.py`** (effet STRUCTUREL du seam, sans Vigueur) :
- **écimage** : sur une tomate poussée N ticks (structure ramifiée), `atteindre_segment`
  sur l'apex meneur avec `intensite=1.0` **réduit `len(segments)`** (sous-arbre retiré)
  et la **hauteur max** baisse ; puis sur **quelques ticks `grow_plant`**, des latéraux
  **naissent** (le `len` remonte, l'apex meneur n'est plus le même) → débourrement
  émergent.
- **doux** : `intensite=0.3` (< `COUPE_NETTE`) ne retire **aucun** segment, baisse
  juste l'auxine ciblée.
- **collet protégé** : `atteindre_segment(plant, 0, 1.0)` sur une plante réduite au
  collet ne retire rien (et `grow_plant` la fait repartir — rejet de souche).
- **déterminisme** : même seed/pos/séquence d'appels → structures identiques.

**Étends `tests/test_vigueur.py`** (contrat ACTION de `tailler`) :
- **coût** : `tailler` débite `MODERE` (atténué par le seam `cout_action` si maîtrise) ;
- **binaire** : Vigueur < coût → `return False`, **structure inchangée** + Vigueur non
  consommée au-delà (cf. comportement `deraciner` : `spend` drague, mais rien d'écrit) ;
- **gain** : sur une plante mûre, gain > 0 (∝ maturité) ; net peut rester < coût ;
- **objets** : `_objets_action("tailler", plant)` contient `"taille"`, `"sécateur"` et
  la clé d'espèce.

## D. Golden — il doit rester INTACT (critère dur)
`tailler` n'est **jamais appelée** par le golden (pas de joueur dans le scénario
déterministe), et `atteindre_segment` n'est appelé que **par `tailler`** → aucun
chemin du tick ne change. **Donc :**
```
python3 -m tests.test_golden     # DOIT redonner 6369c30b… (engine) — INCHANGÉ
```
Le golden **population** (`b005d9ba…`) et `vigueur_hash.txt` ne doivent **pas**
bouger non plus. **Si un hash bouge, c'est une FUITE** (tu as touché le tick) → à
corriger, **PAS** à re-capturer. Aucun `--capture` ce tronçon.

## Hors périmètre (NE PAS faire ici)
Migration procédurale du **pommier** (tronçon 3bis). Déclencheurs **naturels** du
seam (grêle/ravageur/vent → `atteindre_segment` : §F « plus tard »). Détection de
succès de maîtrise / marqueur `🌿` (`maitrise_detection.py`, i4 — `actions.py`
n'importe **pas** la détection, sens de dépendance acté). Branchement du `tailler`
au **clic Godot** (tronçons rendu 4-5). Organes / `foliage_density` (tronçon 5).
N'utilise **ni** `plant.dominance_apicale` **ni** `reponse_taille` (modèle mort).

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_croissance     # étendu (seam structurel), doit passer
python3 -m tests.test_vigueur        # étendu (action tailler), doit passer
python3 -m tests.test_golden         # INCHANGÉ (6369c30b…) — golden-safe
python3 -m tests.test_genetique && python3 -m tests.test_auxiliaires
python3 -m tests.test_maitrise && python3 -m tests.test_signes
python3 main.py                      # tourne sans crash
```
Critère dur **de ce tronçon** : le seam + `tailler` existent et sont testés
(structure ET Vigueur), l'écimage déclenche un débourrement **émergent** au tick
suivant, et le **golden ne bouge pas** (3 hashs identiques). Mets à jour
`00_etat.md` (tronçon 3 ✅ : seam posé, `tailler` branchée, golden intact, points
tranchés : `COUPE_NETTE`, `_segment_cible`, `GAIN_TAILLE_RATIO` ; tronçon 3bis
pommier à venir), commit, `/clear`, lance `04_*.md`.

## Points ouverts (défaut sobre + signaler)
- **`COUPE_NETTE`** : seuil 0.8 (défaut) — au-delà, écimage ; en deçà, perturbation
  douce. Calibrable.
- **`_segment_cible`** : apex meneur = tip z max ; branche = sous-arbre latéral le
  plus profond, repli apex (défaut). Autre heuristique possible.
- **`GAIN_TAILLE_RATIO`** : 0.3 (défaut) — fraction de `HARVEST_GAIN_FULL·maturité`.
  Raffiné au tronçon 5 (organes mûrs réels récupérés à la coupe).
- **`cible="branche"` vs `"apex"`** : même seam, même `intensite=1.0`, seule la
  sélection diffère (la « dominance ~inchangée » de l'égourmandage émerge du fait
  qu'on retire un latéral, pas l'apex meneur). Point ouvert §00 n°3.
