# Conception — Migration des 9 arbres en croissance procédurale (D91)

**Figée le 2026-07-24** (`/conception`, code lu et vérifié au `grep`).
**Lignée :** D29 (croissance procédurale, doc mère `conception_croissance.md`) ·
D90 (taper, CLOS) · amorce rev 2 fournie par Nico.

Ce document fige la migration des **9 arbres restants** — Figuier, Cerisier,
Noyer, Chêne, Hêtre, Bouleau, Charme, Sapin, Aulne — de l'empreinte-couronne
tabulée (`age_curve`) vers la **croissance procédurale en segments**
(`procedural_growth=True`), comme le pommier. Ils se dessineront alors en branches
et porteront le taper D90 (`girth_max_cm` déjà posé par espèce, aujourd'hui sans
effet faute de migration).

Ce n'est **pas** un ajout d'espèces : les 9 sont déjà au catalogue avec leurs 5
voix. C'est une **bascule de modèle de croissance/rendu** espèce par espèce, avec
un **calibrage** de leviers et une **validation à l'œil (F5)** par port.

---

## 1. Trois faits établis par lecture du code (corrigent l'amorce)

L'amorce rev 2 posait des hypothèses ; la lecture du moteur les tranche.

### 1.1 Le golden est STRICTEMENT NEUTRE — aucun re-figeage, aucun tronçon

`tests/test_golden.py` n'instancie parmi les ligneux **que le pommier**
(`AppleTree`, ligne 94). Les 9 arbres à migrer ne sont ni semés dans le scénario
(espèces plantées : Tomate, Basilic, Haricot, Tournesol, Poivron, Achillée,
Phacélie, Trèfle, Pommier), ni tirés par la succession spontanée (`archetype=None`
→ hors `WEED_CATALOGUE`). **Conséquence : aucun tronçon de D91 ne touche le
golden.** L'amorce §3 hedgeait un « re-figeage conditionnel » ; la réalité est plus
simple — golden-neutre de bout en bout, comme les sprints décompo ③④⑤.

### 1.2 `port_archetype` n'est jamais lu par le moteur

Grep vide dans `sim/` et `fields/` : `port_archetype` est une **étiquette
descriptive**. Le comportement `fleche`↔`etale` **émerge** de
`apical_dominance_base` + le relâchement d'auxine avec l'âge (`_update_auxin`,
phases.py). **Conséquence directe sur le pleureur** : « ajouter un 8ᵉ archétype
pleureur » comme chaîne de caractères **ne produit rien**. Le pleureur exige un
**vrai levier mécanique neuf** (§3). Le trou de modèle n'est pas un mot manquant,
c'est une force manquante.

### 1.3 Le vrai risque n'est PAS le golden — c'est la mort hydrique au F5

`update_footprint` (instance.py:259) dérive `root_r = canopy_r =
max_horiz + foliage_halfwidth`, avec `PROC_ROOT_RATIO = 1.0` global. Le
commentaire de calibrage du pommier (perennials.py:178-186) est explicite : une
**jeune flèche étroite** a une couronne minuscule → des racines minuscules → tout
le prélèvement d'eau (`_apply_uptake`, `share = 1/nplots`) se concentre sur le
plot-foyer qui s'assèche → `drought_memory > 0.6` → **mort par stress hydrique vers
l'an 3**. Le pommier ne survit qu'en réglant `foliage_halfwidth = 50` (racines
étalées sur plusieurs plots).

> **Poste de calibrage n°1, par espèce.** Chaque arbre migré doit régler
> `foliage_halfwidth` pour que son empreinte racinaire jeune couvre assez de plots.
> Les espèces **hautes-grêles** (sapin en flèche, bouleau élancé) y sont **les plus
> exposées** (couronne étroite → racines étroites). Invisible au golden, révélé
> seulement au F5 (jardin réel avec eau simulée). Chaque kickoff le traite en
> première classe.

---

## 2. Le levier d'ontogénie par espèce (`auxin_release_scale`) — DÉCISION D2

L'amorce (Q4) demandait si l'ontogénie « déjà modélisée » suffit aux ligneux
centenaires. Vérification : `_update_auxin` lit la constante **globale**
`AUXIN_RELEASE_SCALE = 400.0` semaines (~7,7 ans) :

```python
f_age = max(AUXIN_PROD_FLOOR, 1.0 - plant_age / AUXIN_RELEASE_SCALE)
```

Donc **tout arbre s'étale entièrement dès ~l'an 8**, quelle que soit sa longévité —
un chêne de 500 ans dérive aussi vite qu'un cerisier. Retoucher la constante
toucherait le pommier (dans le golden). **Décision (Nico)** : lever ce paramètre
**par espèce**.

- Nouvel attribut de classe `auxin_release_scale: float = 400.0` sur `PlantBase`
  (défaut = la constante actuelle → **pommier / Tomate / grimpantes bit-identiques,
  golden intact**).
- `_update_auxin(segs, dominance, release_scale)` lit désormais
  `cls.auxin_release_scale` (passé par `grow_plant`).
- Calibrage par espèce : ligneux longévifs (chêne, hêtre) → échelle **plus grande**
  (dressé plus longtemps avant de s'étaler) ; pionniers (bouleau, aulne) → plus
  petite (s'étalent vite). Golden-safe (les 9 sont hors golden).

La constante de module `AUXIN_RELEASE_SCALE` **reste** comme valeur-défaut miroir
(cohérent avec le patron déjà en place pour `growth_speed`/`emit_length`…).

---

## 3. Le levier gravitropique (`gravitropism_gain`) — DÉCISION D1 (pleureur)

Le port pleureur du bouleau (*Betula pendula*) **ne relève pas de l'auxine** mais
de la **mécanique du rameau** : les brindilles fines **retombent sous leur propre
poids**. Aucun archétype existant ne le décrit (§1.2), et le nom seul ne fait rien.
**Décision (Nico)** : ajouter un vrai levier.

- Nouvel attribut `gravitropism_gain: float = 0.0` sur `PlantBase` (**défaut
  neutre = aucune retombée → golden intact**, personne ne le règle sauf le bouleau).
- **Greffe** : dans `_elongate_emit`, le segment émis reçoit sa direction via
  `_phototropic_bias` (biais vers la lumière). On applique **ensuite** un biais
  gravitropique — helper neuf `_gravitropic_droop(dir, depth, gain)` dans
  `geometrie.py` — qui incline `dir` vers le bas.
- **Échelonné par la profondeur** (`_depths`, déjà calculé) : le tronc et la flèche
  (faible profondeur) restent **dressés** ; seuls les **rameaux distaux** (forte
  profondeur) retombent. Résultat : leader droit + brindilles pendantes = le port
  pleureur émerge de la structure, pas d'une silhouette peinte (philo #2).
- **Déterministe** : biais géométrique pur, zéro RNG (philo #3).
- **Réutilisable** : prépare le saule (D23), même mécanique.

**Ordre des biais dans `_elongate_emit`** : direction axiale → biais phototropique
→ retombée gravitropique. La retombée ne doit pas **écraser** le phototropisme (le
rameau pousse d'abord vers la lumière, puis ploie) — d'où l'échelonnage par
profondeur et un `gain` modéré, calibré au F5.

---

## 4. Cartographie des 9 espèces (leviers à régler)

Rappel : `port_archetype` est descriptif (documentation) ; le **comportement**
vient de `apical_dominance_base` + `auxin_release_scale` (+ `gravitropism_gain`
pour le seul bouleau). Le gabarit (`max_height_cm`/`max_extent_cm`) et la vitesse
(`growth_speed`/`emit_length_cm`) se calibrent sur l'`age_curve` de chaque espèce
(cible = reproduire l'allure dans la fenêtre d'observation, §E.3 du doc mère).
`girth_max_cm` est **déjà posé** par espèce (D90).

| Espèce | `port_archetype` | Leviers spécifiques | Tronçon |
|---|---|---|---|
| **Cerisier** | `etale` | patron pommier direct | T1 |
| **Charme** | `etale` | ovoïde dense, dressé jeune | T1 |
| **Hêtre** | `etale` | grand ample, `release_scale` **long** (dressé longtemps), `foliage_density` haute | T1 |
| **Noyer** | `etale` | grand ouvert, charpentières hautes | T1 |
| **Chêne** | `etale` | très étalé, `release_scale` **long** (dressé jeune puis s'ouvre) | T1 |
| **Aulne** | `etale` | élancé, rôle hydro D61 **intact** (empreinte racinaire dérivée cohérente) | T2 |
| **Figuier** | `buissonnant` | dominance modérée, bas & large ; multi-tronc = **option F5** | T2 |
| **Sapin** | `fleche` | dominance **haute** + `release_scale` **long**, `deciduous=False` (déjà), `foliage_halfwidth` **critique** (flèche étroite) ; aiguilles/verticille = T4 (rendu) | T2 |
| **Bouleau** | `fleche` | élancé + `gravitropism_gain > 0` (pleureur), pionnier `release_scale` court | T3 |

**Structure de code (mutualisation).** Pour éviter 9 blocs isolés, on pose sur la
base `PerennialWoody` des **défauts procéduraux d'arbre** (echelle de segment,
`emit_length_cm`, `max_segments`, `wood_persistence`, `branch_angle`,
`foliage_halfwidth` de départ) que chaque espèce **surcharge par delta** (gabarit,
release_scale, dominance). `procedural_growth` **reste flippé par espèce** (pas sur
la base) → migration **incrémentale et sûre** : une espèce non encore calibrée
garde l'ancien chemin `age_curve` (§I du doc mère). Le pommier garde son profil
complet inchangé.

---

## 5. Interconnexions (cohérence à préserver)

- **D90 (taper)** — amont direct : `girth_max_cm` déjà posé par espèce s'active dès
  la migration. Rien à changer côté taper.
- **LightField / ombrage** — la canopée dérivée des segments **modifie l'ombre
  projetée** (un chêne étalé ombre autrement qu'un disque). Émergent et souhaité,
  mais chaque arbre migré = émetteur d'ombre plus riche → **couplage perf** (D66
  O(N·k), D67 LOD). À profiler au F5 sur monde réel, pas à l'estime. La croissance
  elle-même est O(segments) bornée par `max_segments` → linéaire, non critique.
- **D21 (pérennes)** — `age_curve` devient **cible de calibration** (garde son rôle
  carnet/encyclopédie « semis/jeune/adulte »), ne pilote plus l'empreinte des
  migrées. `foliage_density_at` (caduc nu l'hiver) reste inchangé.
- **D61 (aulne, marécage)** / **D69 (sapin, aiguilles acidifiantes)** — rôles
  écologiques (fixation N₂, mulch aiguilles) portés par des `family_effects` /
  attributs **indépendants** de la morphologie → la migration n'y touche pas ;
  vérification de non-régression au calibrage.
- **D58 (décor cosmétique `TreePort`)** — à **ne pas confondre** : le décor de
  pourtour dessine des silhouettes peintes ; D91 concerne les arbres **simulés** du
  jardin. Aucun couplage.
- **D26 / D23 (extension catalogue)** — bénéficiaires collatéraux : une fois le
  patron rodé, poirier/prunier/châtaignier/saule/érable… deviennent un coût
  marginal. Le levier gravitropique **prépare le saule** (D23).

---

## 6. Voix narratives

Les 9 espèces sont **déjà au catalogue avec leurs 5 voix** — D91 **n'ajoute pas
d'espèce**, donc **pas de nouvelles voix à créer**. La migration **surface** le
**port** comme fait observable. Enrichissement **léger et optionnel** (T4, non
bloquant) : compléter la fiche **encyclopédie** (niveau descriptif) de ces espèces
avec leur architecture (« le chêne étale une couronne large et basse », « le sapin
monte en flèche unique », « le bouleau laisse pendre ses rameaux »). Aucune page
secrète / magazine / événement nouveau requis.

---

## 7. Découpage — 4 tronçons, golden INTACT partout

Regroupement **par famille de calibrage** (mutualise le F5) :

1. **T1 — feuillus etale + levier `auxin_release_scale`.** Moteur : ajout de
   l'attribut `auxin_release_scale` (défaut 400 → golden intact) et passage en
   paramètre de `_update_auxin`. Défauts procéduraux d'arbre sur `PerennialWoody`.
   Migration de **cerisier, charme, hêtre, noyer, chêne** (patron pommier).
   Calibrage `foliage_halfwidth` (**survie hydrique**) + gabarit sur `age_curve`.
   *Golden intact* (5 espèces hors golden ; défaut release_scale = pommier inchangé).
2. **T2 — cas atypiques.** Migration d'**aulne** (etale, rôle hydro D61 préservé),
   **figuier** (`buissonnant` mono-collet ; multi-tronc = option F5 différée),
   **sapin** (`fleche`, persistant, dominance haute + release long, `foliage_halfwidth`
   critique). Aiguilles/verticille = notés pour T4. *Golden intact.*
3. **T3 — bouleau + levier gravitropique.** Moteur : ajout `gravitropism_gain`
   (défaut 0 → golden intact) + helper `_gravitropic_droop` dans `geometrie.py`,
   greffé après `_phototropic_bias`. Migration du **bouleau** (`fleche` élancé +
   retombée distale). *Golden intact.* Prépare le saule (D23).
4. **T4 — vue Godot + banc F5.** Vérifie les 9 nouveaux ports rendus en branches
   (`PlantRenderer` fait déjà les segments), **mode aiguilles** du sapin
   (`PlantRenderer.Organs.cs`), LOD silhouette aux zooms faibles, **banc
   d'observation** des 10 arbres côte à côte pour valider chaque port. Enrichissement
   encyclopédie optionnel (§6). Pont si un champ manque au snapshot. *Golden intact.*

**Réserves portées explicitement (non bloquantes) :** le **multi-tronc du figuier**
reste une option F5 (pas de sur-ingénierie #2 : la structure initiale est un seul
collet, un vrai multi-collet demanderait une émission basale — à ne faire que si le
port mono-collet lit mal) ; la **phyllotaxie verticillée du sapin** est laissée en
polish différé (une flèche dense lit déjà « conifère »).

---

## 8. Respect de la philosophie #1-#7

- **#2 (flux → réponse émergente, jamais silhouette peinte)** — respecté : le port
  émerge des leviers mécaniques (auxine, gravitropisme, gabarit), pas d'un `port =
  "colonnaire"` sélectionné. `port_archetype` reste descriptif.
- **#3 (déterminisme, zéro RNG)** — les deux nouveaux leviers sont des biais
  géométriques purs ; la ramification reste hash-based (`form_seed`).
- **#4 (run éternel borné)** — `max_segments` + gabarit plafonnent chaque arbre ;
  le taper D90 est saturant. Coût croissance O(segments) borné.
- **#5 (pas de HUD chiffré)** — le port devient un **indice visuel** riche (lire
  l'espèce à sa silhouette) ; les leviers restent en coulisse.
- **#1 / #6 / #7** — neutres à positifs : `tailler` inchangé ; apprentissage par
  observation enrichi (voir un sapin filer vs un chêne s'ouvrir) ; hétérogénéité
  préservée (phototropisme par segment → deux arbres diffèrent selon la lumière).
