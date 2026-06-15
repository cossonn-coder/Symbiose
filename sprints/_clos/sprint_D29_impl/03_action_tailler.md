# Sprint D29·i3 — Action `tailler` + démonstrateur tomate/pommier (Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico vient du C/Python embarqué,
> expert simulation ; débutant Godot/C# en frontend). **Pré-requis : i1+i2 faits.**

## Ce que c'est, en une phrase

Dernier tronçon : on **surface** le geste `tailler` qui **écrit** l'état hormonal
(que i2 sait déjà lire), et on **active le démonstrateur** en migrant 2 espèces.
C'est une **action directe sur le vivant** (philo #1 : permise mais coûteuse) dont
la **réponse est émergente** (philo #2 : `tailler` écrit `dominance_apicale`, le
tick produit l'architecture). Sans ce tronçon, le modèle est complet mais
**inerte** (tout le catalogue est `"insensible"` et rien n'écrit les scalaires) :
i3 le rend démontrable de bout en bout.

**Le golden écolo NE bouge PAS** (`c950f06c…` / `b005d9ba…`) : `tailler` n'est
**jamais appelée** par le golden (succession sans joueur). Migrer Tomato/AppleTree
ne change rien tant que personne ne taille (defaults hormonaux neutres, mapping
identité au repos vérifié en i2). Si un hash bouge → fuite, bug.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_HORMONES.md` — **§D** (l'action : 2 gestes apex/branche, ce
   que le geste écrit, esquisse de contrat, coût MODÉRÉ binaire, objets touchés),
   **§E** (liens Vigueur : coût via `cout_action`, gain ∝ maturité ; et §E.2 maîtrise
   = **référence seulement**, marqueur `🌿` **hors périmètre**), **§F** (le tableau
   démonstrateur : Tomato `"buissonnante"`, AppleTree `"fructification_laterale"`).
2. `sprints/sprint_D29_impl/00_etat.md` — découpage + **point ouvert i3** (effet
   hormonal exact de `cible="branche"`).
3. Code — **le patron à copier, à la lettre** (les 6 gestes existants) :
   - `data/code/sim/actions.py` — `COUTS` (ligne ~75, ajoute `"tailler": MODERE`),
     `OBJETS_TOUCHES` (ligne ~92, ajoute `"tailler"`), `_objets_action`
     (ligne ~123), le seam `cout_action` (ligne ~160). **Reproduis `deraciner`
     (binaire tout-ou-rien, ligne ~246) et `recolter` (gain ∝ maturité, ligne
     ~230)** — `tailler` = mélange des deux.
   - `data/code/plants/species.py` — la classe `Tomato` (Solanaceae, annuelle).
   - `data/code/plants/perennials.py` — la classe `AppleTree` (Rosaceae, `maturity_years=5`).

## Périmètre

### A. `tailler` dans `actions.py`
Signature sur le modèle des gestes existants (cf. esquisse §D.2) :
```python
def tailler(game_state, player, plant, eco, *, cible="apex") -> bool:
```
- **Coût** : `COUTS["tailler"] = MODERE` ; `cost = cout_action(game_state, player,
  "tailler", _objets_action("tailler", plant))`. **Binaire** : `if spend(...) < cost:
  return False` (rien écrit, comme `deraciner`) — pas de taille « à moitié ».
- **Objets touchés** : `OBJETS_TOUCHES["tailler"] = ("taille", "sécateur")` (statiques
  §10.4) ∪ cible vivante (clé d'espèce via `_objets_action`/`_cle_espece`).
- **Gate espèce** : si `plant.plant_class.reponse_taille == "insensible"` → **hook
  géométrique seulement** (réduction d'empreinte, la « v1 » de §3.3 : baisser
  `canopy_height` immédiatement → lumière livrée aux strates basses dès le tick
  suivant), **aucune** écriture hormonale, `return True`.
- **Sinon, selon `cible`** :
  - `"apex"` (écimage/pincement) : `plant.dominance_apicale = 0.0` (lève la dominance
    → débourrement géré par le tick i2) **+ hook géométrique immédiat** (empreinte
    réduite — on conserve la v1, on ne jette rien).
  - `"branche"` (éclaircir/égourmander) : **point ouvert i3** — défaut sobre =
    réduction d'empreinte **locale** (canopée/`foliage_density`), dominance
    **~inchangée** (l'apex reste). Signale ce choix dans `00_etat.md`.
- **Gain Vigueur** : `+` faible **si un organe mûr est récupéré à la coupe** (∝
  maturité, même logique que `recolter`/`manger`) ; **nul** sur du bois vert. Net :
  `tailler` reste coûteuse. **Ne pas** rouvrir D19 — comptabilité ∝ maturité, point.
- **Sans RNG** (philo #3). Le geste mute **au-dessus du tick**, jamais dedans.

### B. Démonstrateur (2 espèces)
- `Tomato` : `reponse_taille = "buissonnante"`.
- `AppleTree` : `reponse_taille = "fructification_laterale"`.
- Le reste du catalogue **reste `"insensible"`** (défaut). Si les 2 archétypes
  demandent des overrides de coefficients (cf. §F « overrides »), garde-les **minimes
  et nommés**, calibrage post-test.

### C. Test — `tests/test_hormones.py` (étendre i2) : golden joueur dédié
1. **Coût/binaire** : Vigueur insuffisante → `tailler` renvoie `False`, **rien écrit**
   (dom/ramif inchangés). Suffisante → `True`, Vigueur décrémentée du coût.
2. **Séquence apex sur Tomato** : `tailler(cible="apex")` → `dom==0` ; après N ticks
   → `ramification` monte, `height` ↓, `canopy_radius` ↑, `dom` se rétablit ;
   au-delà du seuil → mise à fruit (repro effectif ↑). **Trajectoire attendue
   capturée** (golden joueur).
3. **Pommier `fructification_laterale`** : la séquence favorise le bois latéral →
   `reproduction_rate` effectif ↑ via `ramification`.
4. **Espèce insensible** (ex. une graminée du catalogue) : `tailler` → hook
   géométrique seulement, **aucune** écriture hormonale, scalaires au repos.
5. **Gain ∝ maturité** : couper une branche à organe mûr → petit gain Vigueur ;
   bois vert → gain nul.
6. **Objets touchés / coût atténuable** : `cout_action("tailler", …)` passe bien par
   `f_globale`/`f_objets` (maîtrise atténue, comme les autres gestes).

## Hors périmètre (NE PAS faire ici)
Marqueur `🌿` dans `maitrise_detection.py` (§E.2 — **plus tard**, ligne BACKLOG :
1 preuve = `tailler` payée + `🌿`/mise à fruit dans la fenêtre d'imputation §9.5).
Généralisation du trait au reste du catalogue (espèce par espèce, calibrage). Rendu
végétal Godot, organes fins (D19), bouture (D22), portage C# (D24).

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_hormones      # golden joueur complet, doit passer
python3 -m tests.test_golden        # DOIT rester c950f06c… / b005d9ba…  (INTACT — critère dur)
python3 -m tests.test_genetique && python3 -m tests.test_auxiliaires
python3 -m tests.test_vigueur && python3 -m tests.test_maitrise   # non-régression actions/coût
python3 main.py                     # tourne sans crash
```
Quand tout passe : mets à jour `00_etat.md` (i3 ✅ → impl. D29 COMPLÈTE), puis
`journal.md` + `DETTE.md` (D29 → implémenté) + `BACKLOG.md` (sprint ✅ + ligne
**marqueur `🌿` à venir**) + mémoire (`project_status.md`). Commit. Fin du sprint.
