## 2026-06-04 — Sprint conception Hormones de croissance : D29 auxine / dominance apicale (conception seule)

**Conception SEULE** (cadrage Nico) — aucun code moteur. Livrable :
`docs/conception/CONCEPTION_HORMONES.md` (volets A–I). Surface la réponse architecturale
à la taille que `CONCEPTION_VIGUEUR.md` §3.3 avait renvoyée à D29 : couper l'apex
lève la **dominance apicale**, l'auxine cesse d'inhiber → les bourgeons latéraux
**débourrent** → ramification, port buissonnant, **mise à fruit**.

**Constat structurant.** Une plante = **un point + des stades/courbe d'âge +
des disques** (canopée/racines). **Aucune topologie de branches/bourgeons.** C'est
la matière dont on dispose pour faire ÉMERGER la réponse.

**Décision #1 — faisabilité topologique (point ouvert n°1) → SCALAIRE.** La règle
posée par Nico (topologie réelle *seulement si* calcul **et** RAM **et** affichage
suivent) tranche mécaniquement : calcul ✅ (×339 de marge) et RAM ✅ (27 Mo) suivent,
mais le **rendu ne peut pas** — les plantes sont des **PNG par stade**, il n'existe
**aucun moteur de rendu végétal procédural** (squelette/L-system/variantes), et le
construire est hors périmètre. → repli sur l'**option (ii) scalaire émergent**.
Cohérent avec les patrons Vigueur (façade) / Maîtrise (couche au-dessus). Porte
laissée ouverte vers l'hybride (iii) le jour d'un sprint frontend de rendu.

**Décision #2 — 2 scalaires hormonaux** sur `PlantInstance` (repos NEUTRE) :
- `dominance_apicale: float = 1.0` — signal **transitoire** (1.0 = apex intact,
  auxine inhibe à fond) ; chute à 0 à la coupe, **se rétablit** vers 1.0 en N
  semaines (cinétique du débourrement).
- `ramification: float = 0.0` — état architectural **cumulatif persistant** (la
  buissonnité réalisée), reste acquis après rétablissement de la dominance.

Un seul scalaire ne peut porter les deux temporalités (un signal qui passe + une
structure qui reste). **Repos = identité** : `dominance=1.0` & `ramification=0.0`
donnent ×1/+0 sur tous les mappings → tick no-op → golden `c950f06c…`/`b005d9ba…`
intacts (le golden = succession sans joueur, personne ne taille). **Critère #1**
posé : si un mapping impose une lecture non neutre au repos, c'est un bug de design.

**Mapping coupe → émergence** (sur variables EXISTANTES, jamais un `+=`) :
`canopy_radius ×(1+K_R·ramif)`, `canopy_height ×(1−K_H·ramif)`, `foliage_density ↑`,
**mise à fruit** = `reproduction_rate` modulé par `ramif` via un modèle,
`growth_factor` redirigé. Cinétique déterministe (variabilité par `_hash_noise`,
pas de RNG) ; bornes anti-emballement (`dominance∈[0,1]`, `ramif∈[0,RAMIF_MAX]`).

**Action `tailler`** (dans `sim/actions.py`, modèle des 6 gestes) : deux gestes
(couper l'**apex** → `dominance→0` + hook géométrique immédiat = lumière aux strates
basses ; couper une **branche** → réduction locale, dominance ~inchangée). Coût
`MODÉRÉ` via `cout_action`, binaire tout-ou-rien, objets touchés `("taille",
"sécateur")` + cible vivante (déjà prévus §10.3/§10.4). Gain Vigueur faible si organe
mûr récupéré. **`tailler` v1 (effet géométrique) conservé comme socle**, la réponse
hormonale se branche par-dessus.

**Maîtrise.** `tailler` = **technique** (§10.3) ; succès §9.5 (« action payée ET
effet visé observé »). Branchement futur dans `maitrise_detection.py` (i4) :
nouveau marqueur **`🌿` (débourrement)** lu post-tick, imputé au geste dans la
fenêtre d'imputation — décrit, **non codé**.

**Décision #3 — démonstrateur** : trait **`reponse_taille`** sur `PlantBase`,
**défaut `insensible` = neutre golden** (une graminée a son méristème à la base, elle
ne rebourgeonne pas ainsi). `Tomato` → `"buissonnante"` (écimage/égourmandage →
mise à fruit) ; **fruitier = pommier** (`AppleTree`, `"fructification_laterale"`),
choisi pour le **thème normand** (verger à cidre) et parce que la taille de
fructification du pommier est l'exemple canonique tempéré (figuier = candidat
trivial ultérieur).

**Placeholders → calibrage post-test** : `DEBOURR_RATE`, `DOMINANCE_RECOVERY`,
`RAMIF_MAX`, `K_R`, `K_H`, seuils mise à fruit / marqueur `🌿`, coût exact.

**Statut.** D29 **conçu** → `docs/conception/CONCEPTION_HORMONES.md`. Prochain = sprint
d'implémentation Python des hormones (état + cinétique + `tailler` + démonstrateur ;
golden écolo préservé sans re-figeage). Aucun golden touché (conception pure).

---
