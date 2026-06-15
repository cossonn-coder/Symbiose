# Sprint D12·i1 — Cœur de la maîtrise : objet + progression intra-objet (Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico apprend Godot/C# en frontend,
> vient du C/Python embarqué ; expert Python/simulation).

## Ce que c'est, en une phrase

Premier des 4 tronçons de l'implémentation D12. On pose le **cœur** de la maîtrise :
l'**état par avatar** (`game_state["maitrise"][player]`), la **découverte** d'un
objet (palier 0→1, gratuite) et la **progression de palier par preuves** (courbe
de difficulté logarithmique, monotone). **Aucun agrégat, aucun pont Vigueur, aucun
seam de coût, aucune détection automatique de succès** — tout ça vient aux
tronçons i2/i3/i4. Ici les preuves sont **injectées par API** (un test appelle
`enregistrer_preuve(...)`), exactement comme le sous-sprint 1 de la Vigueur posait
l'état + le cycle avant de brancher les actions.

**Le golden écolo NE bouge PAS** (`c950f06c…` engine / `b005d9ba…` champ) : la
maîtrise est une couche gameplay **au-dessus du tick**, et le tick ne l'appelle
jamais (le golden est une succession spontanée **sans joueur**). Si un hash bouge,
c'est un **bug** (fuite dans le tick), pas un re-figeage.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_MAITRISE.md` — **§1** (l'objet de maîtrise = unité
   atomique, paliers `0..5`, catégories ouvertes data-driven), **§2** (progression :
   §2.1 découverte gratuite par observation, §2.2 paliers = succès **répétés**,
   **§2.3 courbe log `preuves(k) ≈ ceil(BASE·R**(k-1))`**, §2.4 **monotone**),
   **§6** (méta-état par avatar, golden intact — la décision structurante de ce
   tronçon). Survole §3/§4 (agrégats/ponts = i2/i3, **hors périmètre ici**) et §9
   (détection = i4, **hors périmètre**).
2. `sprints/sprint_D12_impl/00_etat.md` — le découpage des 4 tronçons + les points
   ouverts (dont celui d'i2 sur `palier_bonus`, **pas le tien**).
3. Code — **le patron à copier, à la lettre** :
   - `data/code/sim/vigueur.py` — **LE modèle de couche joueur** : `ensure_player`
     (geste d'OPT-IN : tant qu'aucun joueur n'est enregistré, `game_state` n'a pas
     la clé → le tick reste un no-op strict → golden intact), état par joueur dans
     `game_state["vigueur"][player]`, `palier_bonus` stubbé à 1.0 (que TU ne
     remplis PAS — c'est i2). Reproduis EXACTEMENT ce style pour `maitrise`.
   - `data/code/tests/test_vigueur.py` — **le patron de golden joueur** : section A
     (contrats déterministes sans RNG, `check(name, cond, detail)`), le test
     **no-op golden** `test_noop_sans_joueur` (à cloner pour la maîtrise), capture
     de hash optionnelle. Reproduis la structure dans `tests/test_maitrise.py`.

## Périmètre — `sim/maitrise.py` (nouveau) + `tests/test_maitrise.py` (nouveau)

### A. Le module `sim/maitrise.py`

Couche `sim` pure (n'importe rien d'autre que la lib standard `math` ; **ne touche
ni `vigueur.py` ni le tick**). État miroir de la Vigueur :

```
game_state["maitrise"][player] = {
    "objets": {                       # clé = nom d'objet (string, catalogue-agnostique)
        "<objet>": {"palier": int 0..5, "preuves": int},
        ...
    }
}
```

Fonctions (toutes pures-ish : mutent uniquement `game_state["maitrise"]`, jamais
l'écolo) :

- **`ensure_player_maitrise(game_state, player) -> dict`** — crée si besoin et
  renvoie la tranche du joueur. C'est l'**opt-in** : pas de joueur → pas de clé
  `maitrise` (cf. `vigueur.ensure_player`). Patron identique.
- **`palier(game_state, player, objet) -> int`** — lecture ; `0` si l'objet est
  inconnu (jamais découvert). Ne crée PAS l'objet (lecture pure d'un inconnu = 0).
- **`decouvrir(game_state, player, objet) -> bool`** — passage `0 → 1` par simple
  observation (§2.1, gratuit, aucun succès requis). Idempotent : ne fait rien si
  l'objet est déjà au palier ≥ 1. Renvoie `True` si une **nouvelle** découverte a
  eu lieu (utile à i2 pour le gain ponctuel ; ici on renvoie juste le booléen).
- **`preuves_requises(k) -> int`** — `ceil(BASE * R**(k-1))` pour franchir `k→k+1`
  (§2.3). `k` ∈ {1,2,3,4} (on ne franchit pas au-delà de 5). `BASE`/`R` =
  **placeholders nommés** (calibrage D12.4) ; choisis des valeurs qui rendent la
  courbe **visible et croissante** dans les tests (p.ex. `BASE=2`, `R=2` →
  2,4,8,16 preuves), documentées « à calibrer post-test ».
- **`enregistrer_preuve(game_state, player, objet) -> int`** — le cœur. Incrémente
  le compteur de preuves de l'objet ; tant que `preuves >= preuves_requises(palier)`
  **et** `palier < 5`, **consomme** le quota et **franchit** un palier (boucle :
  une grosse fournée de preuves peut faire monter de plusieurs paliers d'un coup —
  décide et documente : je propose **consommation cumulative**, le reliquat reste
  au crédit du palier suivant). **Pré-condition** : un objet non découvert
  (`palier 0`) ne peut pas accumuler de preuves « utiles » — décide sobrement :
  enregistrer une preuve sur un inconnu le **découvre d'abord** (0→1) puis crédite,
  OU exige `decouvrir` avant (lève/ignore). **Défaut proposé : auto-découverte**
  (une preuve implique qu'on a observé l'objet). Renvoie le palier courant après
  mise à jour. **Monotone** (§2.4) : un palier ne redescend jamais ; il n'existe
  aucune fonction de décrément.

Pas d'agrégats (complétude/accumulation), pas de famille/spillover, pas de
`palier_bonus`, pas de `cout_action`, pas de hook tick. **Si tu es tenté d'en
ajouter, arrête — c'est i2/i3/i4.**

### B. Le golden joueur `tests/test_maitrise.py`

Déterministe sans RNG (preuves injectées). Patron `test_vigueur.py` section A.
Couvre au minimum :
1. **No-op golden** : un `game_state` SANS joueur enregistré n'a JAMAIS de clé
   `maitrise` (le contrat qui garde le golden écolo intact — clone de
   `test_noop_sans_joueur`, en faisant tourner quelques `Engine.tick_semaine` sur
   un monde minimal et en vérifiant `"maitrise" not in gs`).
2. **Découverte** : `palier == 0` avant, `decouvrir` → `1`, idempotence (re-`decouvrir`
   ne dépasse pas 1, renvoie `False` la 2ᵉ fois), lecture d'un inconnu = 0.
3. **Progression par preuves** : injecter `preuves_requises(1)` preuves → palier
   passe à 2 ; vérifier la **courbe croissante** (`preuves_requises(1) <
   requises(2) < … < requises(4)`).
4. **Plafond** : on ne dépasse jamais 5, même en sur-injectant des preuves.
5. **Monotonie** : aucune séquence d'appels ne fait baisser un palier.
6. **Déterminisme** : même séquence d'injections → même état (et, si tu juges utile,
   un hash de trajectoire de paliers façon `test_vigueur` golden B — **optionnel**,
   les asserts ci-dessus suffisent souvent ; n'étends JAMAIS le golden écolo).

Pour le no-op golden, réutilise le `_minimal_state()` de `test_vigueur.py`
(copie locale ou import) — un monde 1 tuile / 3 plantes suffit.

## Hors périmètre (gated — NE PAS faire ici)

- **Remplir `palier_bonus`**, complétude-ratio, accumulation-log, spillover
  famille → **i2**.
- **`cout_action` + table objets-touchés** (§10.4) → **i3**.
- **Détection automatique de succès** (lire les signaux du tick §9, fenêtre
  d'imputation, tag féral, gate d'observation) → **i4**. Ici, **zéro hook** dans
  `engine`/`actions` : les preuves arrivent uniquement par appel direct d'API.
- **Calibrage** `BASE`/`R` (placeholders nommés, D12.4).
- **Portage C#** (D24).

## Garde-fous (non négociables)

- **GOLDEN ÉCOLO INTACT — c'est le test du tronçon.** Avant *et* après :
  `python3 -m tests.test_golden` → **`c950f06c…`** et `python3 -m tests.test_population`
  → **`b005d9ba…`**. **Aucun des deux ne bouge.** La maîtrise ne doit avoir AUCUN
  point d'entrée depuis le tick (pas de hook `engine`, pas d'appel depuis `actions`).
  Si un hash bouge → fuite → corrige, **ne re-fige pas**.
- **`tests/test_vigueur.py` reste 87/87** (tu ne touches pas la Vigueur).
- **Ne touche pas `sim/vigueur.py`** : `palier_bonus` reste stubbé à 1.0 (c'est i2
  qui le remplira, sans casser le découplage §4.1).
- **Couche `sim` pure** : `sim/maitrise.py` n'importe que la lib standard. Règle de
  couches `plants ← fields ← sim ← engine ← main`. Imports absolus, lancement
  depuis `data/code/`.
- **Déterminisme** : aucun RNG, aucun tirage. La progression est une fonction
  déterministe des preuves injectées.
- **`main.py` doit toujours tourner.**
- **Ne jamais jeter/supprimer de code.** Tronçon purement additif (un module neuf,
  un test neuf).

## Ampleur

**Petit/moyen** — un module neuf court + son golden joueur, zéro couplage avec
l'existant (purement additif, pas de re-figeage). Le tronçon le plus simple des 4 :
il pose la fondation que i2/i3/i4 viendront lire et brancher.

## À la fin

- MAJ `sprints/sprint_D12_impl/00_etat.md` (i1 ✅, ce qui reste i2/i3/i4, golden
  vérifiés inchangés).
- MAJ `journal.md` (entrée : cœur maîtrise, **golden écolo `c950f06c…`/`b005d9ba…`
  VÉRIFIÉS INCHANGÉS**, golden joueur maîtrise neuf).
- MAJ `DETTE.md` (D12 → cœur i1 implémenté) + `BACKLOG.md` (ligne sprint impl. D12·i1).
- Mémoire `project_status` : prochain = D12·i2 (agrégats + ponts Vigueur).
- Puis commit. Puis `/clear` avant i2.
