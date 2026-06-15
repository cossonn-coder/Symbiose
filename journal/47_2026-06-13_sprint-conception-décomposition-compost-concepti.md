## 2026-06-13 — Sprint conception : décomposition & compost — CONCEPTION SEULE (FIGÉE)

Spec figée → [`docs/conception/CONCEPTION_DECOMPOSITION_COMPOST.md`](docs/conception/CONCEPTION_DECOMPOSITION_COMPOST.md).
Conception en conversation (4 rounds de questions, Nico tranche), **aucun code
moteur écrit**. Seul changement code de la session : `world/WorldView.cs`
`DebugSecondsPerWeek` 0 → **3** (Nico : la simu doit tourner vite pour tester
chaque itération).

**Cadre** : Nico ne veut PAS reprendre l'intégration Godot ni le save/jardin
éternel pour le moment — d'abord développer/débugger les features existantes.
Prochain sprint choisi = **décomposition & compost** (gravé au backlog 2026-06-11).

**Décisions structurantes (tranchées round par round) :**
- **Parcelles discrètes** (`{tissu, masse, age_sem}` par plot) **remplacent le
  champ scalaire `om_fresh`** ; `om_fresh` survit en **lecture dérivée** = Σ
  masses (les lecteurs — famine microbienne, vers, vitalité, snapshot — restent
  branchés). Fusion par tissu = bornage (≤ 6 classes/plot). Cascade
  `om_active`/`om_stable` **conservée**.
- **Taxonomie tissus** : `diffus` (exsudats, parcelle permanente) / `feuille` /
  `fleur` / `herbacé` / `fruit` / `bois`. `bois` **humifie fort** (→ humus,
  décompo très lente) ; tendres **minéralisent fort**. Table §1.2.
- **Mort → squelette persistant** : structure SURVIT (`sèche` debout →
  `couchée` → fragmentation en parcelles `bois` sur des semaines). Tissus mous
  déposés tout de suite ; **n'occupe pas le plot** (germination dessous OK,
  ombre = silhouette bois nu).
- **Abscission d'automne** (événement) : caducs larguent → parcelle `feuille`.
- **`tailler` dépose** enfin (`bois`) ; **écraser un squelette le met au sol**.
- **Organes-fruits traçables** (absorbe **D19**) : maturité par fruit, exposée
  au snapshot (vue l'affiche) ; `manger` cible UN fruit (gain ∝ sa maturité, le
  fruit **disparaît**) ; non-cueilli sur-mûr → tombe (fermentation).
- **Attraction animale** (succession sur le fruit) : frais → `auxiliaire` ;
  avancé → `ravageur` dominant **+ fraction `auxiliaire`** (auxiliaires de
  décomposition — pas de 5ᵉ guilde, modélisation tranchée Nico).
- **2 structures posables** : **bac à compost** (tendre, refuse le bois,
  maturation **hybride** : passive + `retourner` accélère) ; **pile à bois**
  (BRF/hügel, lente, **habitat `auxiliaire`** « hôtels à insectes »). Les deux
  produisent un **amendement**. `poser` = action de **planification**.
- **épandre** borné par une **jauge `compost_mur`** mesurée → **trio humus**
  (`+om_stable`, ensemence `microbiome`, `+fertilite`).

**Golden** : l'impl re-figera **largement** golden écolo + population (vers
lisent `om_fresh`) — annoncé. **On en profite pour RACCOURCIR le smoke test**
(trop long ; proposé 2 tuiles × 2 ans).

**Découpage impl** = **6 sous-sprints indépendants** (§7) : ① parcelles+cascade
(+raccourci golden) → ② dépôts vivant/mort → ③ organes-fruits → ④ attraction →
⑤ structures+gestes → ⑥ vue (quand Godot reprend).

**Suivant** : implémentation, sous-sprint ① (kickoff `sprints/` à écrire au
démarrage). Nico : « si tu penses à une feature/question de design, interromps
et propose ».

---
