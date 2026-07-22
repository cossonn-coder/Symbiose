# CONCEPTION — Scatter de la boucle lumière-REÇUE (perf run éternel, suite)

> Figé le 2026-07-09 après audit du coût du tick. Sprint `sprint_perf_tick_on2`.
> Continuation directe de `CONCEPTION_PERF_RUN_ETERNEL.md` (D66) et de la dette
> D32 (LightField). **Optimisation PURE : bit-identité obligatoire, golden
> INCHANGÉ.**

## 1. Constat (audit 2026-07-09)

Profil cProfile sur le monde complet (`build_world_full` grandi 80 sem → 595
plantes vivantes ≈ pic an 2 du rapport terrain, cf. `tools/profile_monde.py`) :

| Poste | Part du tick |
|---|---:|
| **LightField** (`fields/light.py:compute`) | **62 %** |
| — dont `ObstacleIndex.covering` | **40 % à lui seul** |
| Maladie fongique (déjà corrigée, commit `7c5344e`) | 17 % → nul |
| Reste (vie macro, uptake, croissance, conflits…) | ~O(N) linéaire |

Le tick est piloté par la **densité de plantes** (an 64 / 5 plantes = 330 ms
vs an 2 / 405-625 plantes = 8 s).

## 2. Diagnostic — la boucle REÇUE est restée en gather

D32 a converti la boucle **lumière-sol** de `compute` en **scatter** (chaque
ombre ne visite que la bounding-box de sa capsule). Mais la boucle **lumière-
reçue par plante** (`light.py`, la boucle `for p … receivers` avec 5 échantillons
× 3 tranches) est restée en **gather** : chaque échantillon appelle
`ObstacleIndex.covering(sx, sy, max_len)` avec

```
reach = max_length + max_radius      (light_index.py:58)
max_length = index.max_height × inv_tan
```

`max_height` est le **maximum GLOBAL de la tuile** (tournesol 250 cm, au soleil
bas `inv_tan` grand) → le carré de buckets scanné à **chaque** échantillon fait
~500 cellules, **indépendamment** des obstacles réellement proches. Coût ≈ 15·N
requêtes × ~500 `dict.get` → **10,7 M `dict.get` + 35 k tris** par bloc de 4 ticks.

Le `reach` global est géométriquement *nécessaire* tant qu'on demande « qui
m'ombre ? » **par échantillon** (gather). Le renverser en **scatter** — « quels
échantillons j'ombre ? » **par émetteur** — borne le coût par l'ombre de
**chaque** émetteur (et le LOD `SHADING_POWER_MIN=37,5` limite déjà les émetteurs
aux plantes structurantes).

## 3. Solution — scatter émetteur→échantillons (miroir de D32 sol)

Pour chaque tranche solaire (boucle externe, comme le scatter sol) :

1. Marquer les échantillons **sous la maison** (`_point_in_swept_rect`) → att = 0,
   **exclus** de la moyenne (réplique exacte du `continue` du gather).
2. Indexer les échantillons NON masqués par cellule-plot (`ReceiverIndex`, miroir
   de `ObstacleIndex`, hébergé dans `light_index.py`). Chaque échantillon porte
   `(hauteur_du_récepteur ph, réf récepteur, sx, sy)`.
3. Itérer les émetteurs **dans `order`** (hauteur décroissante — déjà trié). Pour
   chaque émetteur `(q, qx, qy, qh, qr, qd)` avec `qd > 0` : calculer la bbox de
   sa capsule (longueur `qh × inv_tan`), récupérer les échantillons candidats de
   la bbox, et pour chacun tel que `qh > ph` (plus haut → auto-ombrage exclu) et
   `_point_in_capsule(...)` : `att[échantillon] *= (1 − qd)`.
4. Par récepteur : `light_slice = max(LIGHT_FLOOR, Σ att non masqués / 5)` ;
   `acc += light_slice × w`. Après les tranches : `received[id(p)] = acc / total_w`.

### 3.1 Preuve de bit-identité (invariant critique)

- **Même ENSEMBLE de facteurs** : gather multiplie l'émetteur `q` dans
  l'échantillon `s` ssi `q ∈ covering(s)` ET `qh > ph` ET `qd > 0` ET
  `_point_in_capsule(s, capsule_q)`. Scatter le multiplie ssi `s ∈ bbox(q)` ET
  mêmes trois tests. `covering`/`bbox` ne sont que des **pré-filtres sur-ensemble**
  (ils n'écartent que des cas où `_point_in_capsule` renvoie déjà False). Le test
  réel `_point_in_capsule` étant **identique**, l'ensemble des facteurs appliqués
  est le même.
- **Même ORDRE de produit** : gather trie les candidats par `rank` (= index dans
  `order` = hauteur décroissante) ; scatter itère les émetteurs dans `order`. Pour
  un échantillon donné, le sous-ensemble retenu est multiplié dans le **même
  ordre** dans les deux → produit flottant `(1−qd)` bit-à-bit identique.
- **Maison / plancher / moyenne / pondération** : termes par récepteur inchangés.

→ `self.received` **bit-identique** → **golden INCHANGÉ** (`24ec11e7`).

Verrou dédié : `tests/test_scatter_lumiere_recue.py`, calqué sur le verrou D32
`tests/test_scatter_lumiere_sol.py` (reconstruit l'ANCIENNE boucle gather ligne à
ligne, compare `received` en égalité `==` sur tous les scénarios : monde smoke
grandi, 4 saisons, avec/sans maison).

## 4. Coût & gain attendu

- Nouveau coût boucle reçue ≈ Σ (aires de capsule des émetteurs en espace-
  échantillon) — quelques émetteurs structurants, chacun borné par SA propre
  ombre. Élimine l'essentiel des 40 % de `covering`.
- Gain attendu : tick lourd **~−35 %** (à confirmer `tools/profile_monde.py
  --week 104`). Aucune régression fonctionnelle (bit-identique).
- Le tick redevient ~**O(N)** linéaire en nombre de plantes → le tapis clonal
  (Clover×369) n'est plus une catastrophe perf (cf. §5).

## 5. Hors périmètre — cap démographique clonal (dette D71)

L'explosion pop vient des **ramets clonaux** (`sim/clonal.py`,
`COUVERTURE_SATURATION=0,85` borne la colonie tardivement). **② désamorce le
motif PERF** (tick linéaire). Un cap ne se justifierait plus que par un motif
**design/réalisme** (auto-limitation de colonie), au risque de trahir la
densification émergente voulue par LUXURIANCE (philo #4/#7). → **versé en dette
design D71**, à rouvrir seulement si le gameplay le demande, **jamais pour la
perf**.

## 6. Découpage (2 tronçons)

- **01 — Scatter de la boucle reçue** : `fields/light_index.py` (`ReceiverIndex`),
  `fields/light.py` (récriture de la boucle reçue), `tests/test_scatter_lumiere_recue.py`
  (verrou d'équivalence). Golden INCHANGÉ, bit-identique.
- **02 — Validation perf + F5** : mesure `profile_monde.py` avant/après (via git
  stash du diff, ou comparaison au chiffre de référence), confirme la table
  cProfile (`covering` sort du top), aucun rebuild C# (zéro delta visuel/protocole),
  et pose la **checklist F5** pour Nico (rendu inchangé + tick client à forte
  population vs rapport terrain).
