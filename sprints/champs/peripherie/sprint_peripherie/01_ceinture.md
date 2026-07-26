# ① Ceinture moteur — état, génération déterministe, D92 refermée

> Sprint **PÉRIPHÉRIE** (D73). Lis d'abord `CLAUDE.md` + `00_etat.md` de ce dossier.
> Spec de référence : `docs/champs/peripherie/conception_peripherie.md` §4.1.
>
> **Golden attendu : INCHANGÉ.** Aucun tronçon de ce sprint n'est autorisé à re-figer.
> Si le digest bouge, c'est un bug → annuler, ne jamais figer.

## Objectif

Créer l'**état moteur de la périphérie** : 4 secteurs cardinaux autour du jardin,
générés de façon déterministe depuis le seed. Ce tronçon ne branche **rien** en aval
(personne ne lit la ceinture) → golden neutre **par construction**, exactement comme
`sim/wind.py` au tronçon ① du sprint vent.

Il referme au passage **D92** : la génération C# actuelle (`DecorLayer.BuildProfile`,
hash `decor|{seed}|{cote}`) produit **96,0 % de terrains aux 4 côtés identiques et
0 falaise sur 300 000 seeds**. On repart d'un tirage correct côté Python.

## Fichier à créer

`data/code/fields/peripherie.py` — un fichier, une responsabilité (l'état + sa
génération). Cible ≤ 300 LDC. **Couche `fields`** : n'importe que `constants` et
`fields.noise` ; **jamais** `sim` (la couche basse n'importe pas la haute).

## Modèle

```python
Secteur = {
    "cote":                0..3,        # 0=N, 1=E, 2=S, 3=O
    "type":                "foret" | "riviere" | "falaise" | "prairie" | "friche",
    "essence":             "hetre" | "charme" | "bouleau" | "aulne" | "saule" | None,
    "hauteur_canopee":     float,       # cm
    "densite_ligneuse":    float,       # ∈ [0,1]
    "souche_memory":       None,        # "vivante" | "morte" — posé par ④
    "annees_depuis_coupe": 0.0,         # cinétique — lue par ④
    "ligne_eau":           float,       # cm relatif au bord (riviere)
    "altitude_relative":   float,       # cm (falaise)
}
```

`generer_ceinture(seed: int) -> list[dict]` — 4 secteurs.

**Déterminisme (#3)** : `fields._hash_noise(seed, week, r, c)` avec `week=0` et des
**canaux-sentinelles** décorrélés, sur le patron de `sim/wind.py` (`K_WIND = (90_010, 0)`).
Réserve la tranche `91_00x` :

```
K_TYPE    = (91_000, 0)   # type du secteur   → + cote sur la coordonnée c
K_ESSENCE = (91_001, 0)   # essence dominante
K_HAUTEUR = (91_002, 0)   # hauteur de canopée
K_DENSITE = (91_003, 0)   # densité ligneuse
```

⚠️ **Le bug D92 est là** : ne fais PAS varier seulement une coordonnée d'une unité entre
côtés (c'est exactement ce que faisait le C#). Décale franchement — p. ex.
`_hash_noise(seed, 0, K_TYPE[0] + cote * 7919, K_TYPE[1] + cote * 104729)` (deux grands
premiers). **Vérifie la distribution par le test ci-dessous, ne te fie pas à l'intuition.**

**Distribution des types** : ~35 % forêt, ~25 % rivière, ~30 % prairie, ~10 % friche.
La **falaise n'est pas tirée** : elle DÉRIVE d'un secteur voisin d'une rivière (couplage
hérité de D58 §5.1) — mais contrairement au C#, elle ne doit pas exiger que le voisin
soit resté *prairie*, condition jamais réunie. Règle retenue : **un secteur voisin d'une
rivière, s'il n'est ni rivière ni forêt, devient falaise.**

**Essence dominante** (§4.1, décision D-4) : un secteur `foret` tire son essence parmi
le catalogue **existant** (`hetre`, `charme`, `bouleau`, `aulne`). Un secteur `foret`
**adjacent à un secteur `riviere`** devient **ripisylve** → essence forcée `aulne` ou
`saule`. (Le saule n'entre au catalogue qu'au tronçon ⑥ — ici c'est une chaîne, pas un
import ; aucune dépendance.)

**Plages** : `hauteur_canopee` ∈ [800, 2000] cm pour forêt (0 sinon) ;
`densite_ligneuse` ∈ [0.55, 0.95] pour forêt, [0.05, 0.25] pour friche, 0 sinon ;
`ligne_eau` ∈ [−80, +40] cm (rivière) ; `altitude_relative` ∈ [300, 1200] cm (falaise).

## Test à écrire

`data/code/tests/test_peripherie.py` :

1. **Déterminisme** — `generer_ceinture(42)` deux fois ⇒ identique ; deux seeds
   différents ⇒ profils différents.
2. **D92 refermée** (le test qui compte) — boucle sur **300 000 seeds** (rapide : pas
   de simulation, juste du hash) et vérifie :
   - terrains aux 4 côtés de type identique : **< 15 %** (actuel : 96,0 %) ;
   - terrains portant au moins une falaise : **≥ 5 %** (actuel : 0 %) ;
   - les 4 types non-falaise apparaissent chacun sur ≥ 10 % des terrains.
3. **Ripisylve** — tout secteur `foret` adjacent à une `riviere` a `essence ∈ {aulne, saule}`.
4. **Bornes** — tous les champs dans leurs plages, `densite_ligneuse ∈ [0,1]`.

## Golden

`python3 -m tests.test_golden` depuis `data/code/` → **digest INCHANGÉ**. Personne
n'importe `fields/peripherie.py` à ce stade : la neutralité est structurelle.

## Ce qu'il NE faut PAS faire

- **Ne branche rien** : ni lumière, ni abri, ni seedbank, ni pont, ni C#. C'est ②→⑦.
- **Pas de `PlantInstance`** : la ceinture est un agrégat. Simuler N arbres rouvrirait
  le poste `LightField` (D32) pour rien.
- **Pas de RNG** (#3), pas de `random`, pas de `GetHashCode`.
- **Ne touche pas** `visuals/DecorLayer.cs` (tronçon ⑦).
- **N'exécute JAMAIS** `test_epaisseur_500ans` (long et inutile).
