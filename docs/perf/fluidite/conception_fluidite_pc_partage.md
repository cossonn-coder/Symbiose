# Conception — Fluidité PC, partage du CPU (3ᵉ `/conception D116`)

> Figée le 2026-10-28 avec Nico. Sprint : `sprints/perf/fluidite/sprint_fluidite_pc_partage/`.
> Précédents : `conception_fluidite_pc.md` (diagnostic, banc 3 phases),
> `conception_fluidite_pc_leviers.md` (leviers vue + pont delta 0.6.0).
> Golden `fecccded…` **jamais re-figé** dans ce sprint.

## 1. Cible (inchangée)

PC de Nico — i5-4200H (2 cœurs / 4 threads), **Intel HD 4600 seule** (pas de carte
dédiée, confirmé 2026-10-28) — an 2, 1 s/sem demandée → **≤ 2 s/sem effectives en
phase A**, aucune image > 100 ms. Validation par mesure ; le F5 sert au ressenti seul.

## 2. Ce que dit le run PC du 2026-10-27 (s90 ×4) [n=1 run, PC]

| Phase | s/sem | tick | images |
|---|---|---|---|
| A normal | 2,78 | 1 819 ms | 59,6 ms moy., 56/420 > 100 ms |
| B rendu suspendu | 1,19 | 842 ms | — |
| C moteur en pause | — | — | 30,9 ms moy., 32 FPS |

- Le moteur **seul** tient la cible (B). La cadence se perd quand vue et moteur tournent
  **ensemble** : le tick est multiplié par ~2,2. Il manque 0,78 s en A.
- **Hypothèse retenue (NON mesurée)** : sur un Haswell mobile, CPU et iGPU partagent le
  budget de puissance (TDP) et le cache L3. Une vue qui rend en continu (pas de plafond
  de FPS, la synchro verticale ne bride jamais à 17 FPS) fait baisser la fréquence des
  cœurs et vide le cache du moteur Python. C'est ce que le banc de partage (§4 ②) doit
  confirmer ou réfuter.
- Hauts paliers ×4 ↔ ×32 : pire image jusqu'à 453 ms (×8→×4), dont 10 ms attribués
  [n=1 aller-retour, PC] — l'envoi au GPU au cran est soupçonné, rien n'est mesuré.

## 3. Mesure d'ouverture côté Python (VM, 2026-10-28) [n=1 run, VM, charge 0,3→5, `full` graine 1521550718, s85-100, mode delta]

- Tick 881-1 686 ms ; `_snapshot` 201-508 ms (≈ 20-30 % du temps Python d'une semaine,
  premier poste hors tick) ; `json.dumps` 54-123 ms.
- Ramasse-miettes Python : 25-47 ms par semaine, plus une collecte génération 2 toutes les
  ~7 semaines (s86, s93, s100) à 151-224 ms ; ~190-205 k objets suivis ; seuils
  par défaut (2000, 10, 10).

## 4. Leviers retenus

### ① Moteur, résultat bit-identique
- **Ramasse-miettes** : `gc.freeze()` après le montage du monde (les objets de l'init ne
  sont plus jamais parcourus) + seuil de génération 0 relevé. Ne change aucun résultat
  **sauf** si du code dépend des adresses mémoire : `sim/grimpe.py:87-101` départage par
  `id(other)` — une adresse différente peut changer un ordre. D'où la vérification
  obligatoire « deux runs serveur, avec / sans réglage, même état » (kickoff ①).
  Gain attendu : ~3 % par semaine, **pics gen2 de 150-220 ms supprimés** [estimation VM].
- **`_snapshot` mémoïsé par plante** : profiler d'abord DANS `_snapshot`
  (`tools/simserver/serialize.py:108`), puis ne recalculer l'entrée d'une plante que si sa
  clé d'état a changé (clé auto-invalidante, règle « pas de recalcul dans un tick »).
  Cible −40 % du `_snapshot` [hypothèse].

### ② Régulateur de cadence + banc de partage (vue)
- **Régulateur** : en **Saison**, tant qu'une semaine est **due mais pas encore revenue**
  du moteur, `Engine.MaxFps = 15` (**plancher accepté par Nico**). Plein régime
  (plafond d'origine) en Planification, en pause, quand la semaine est à l'heure, et
  pendant ~1 s après toute interaction caméra (molette, glisser, touches de caméra).
  Pas d'option de menu (comportement automatique). Le banc E C (moteur en pause) n'est
  pas régulé (aucune semaine due).
- **Banc de partage** : la phase A du banc 3 phases se découpe en **4 sous-phases** —
  régulateur off/on × priorité moteur BelowNormal/Normal — rapportées côte à côte
  (s/sem, tick, images moy., > 100 ms, FPS). C'est la courbe « cadence ↔ images » qui
  tranche l'hypothèse §2 et le réglage final (priorité).

### ③ Hauts paliers (vue)
Mesurer d'abord ce qui part vers le GPU à chaque cran (mémoire vidéo / textures /
tampons via `Performance`, nombre de textures créées ou mises à jour par image, taille
des cuissons à ×8+), ajouter ces colonnes au rapport Z, puis agir sur ce que la mesure
montre (ex. étaler les envois, plafonner la taille des cuissons aux hauts paliers).

### ④ Bilan VM + protocole d'un run PC + clôture.

## 5. Écartés

- **Carte graphique dédiée** : absente.
- **Enchaînement anticipé du step** (le moteur repart pendant que la vue lit la semaine) :
  gain ~200-300 ms en A [estimation], mais un geste cliqué attendrait jusqu'à ~2 s de
  plus — **jugé trop long par Nico**. En dette (note D116), à rouvrir seulement si ①-③
  ne suffisent pas.
- Brider la population, re-figer le golden : interdits (comme aux sprints précédents).

## 6. Coût / risques

- ① : aucun coût de tick ; risque = ordre par `id()` (vérifié par comparaison d'état).
- ② : quelques lignes par image ; risque = régulateur inutile si l'hypothèse §2 est
  fausse — le banc le dira, le régulateur reste alors inoffensif (15 FPS seulement en
  retard).
- ③ : instrumentation à coût nul hors rapport ; le levier dépend de la mesure.
