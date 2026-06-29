# Sprint SÉNESCENCE × ROSÉE — kickoff autosuffisant

> Sprint **d'investigation + correction** d'une **régression de test** (récidive
> du motif D39). Le DIAGNOSTIC est DÉJÀ FAIT (consigné ci-dessous) ; il reste un
> **arbitrage de design** à trancher avec Nico, puis un correctif petit.
> Repars à froid : tout le contexte est ici.

## Symptôme exact (reproductible)

`tests/test_senescence.py` est ROUGE sur la baseline `ce33bd2` :

```
python3 -m tests.test_senescence
[senescence] FAIL — cause de mort inattendue : autre (âge 19.5 ans)
```

Attendu : le pommier isolé meurt **de sénescence** dans la fenêtre [49 ; 112] ans.
Observé : il meurt **asphyxié à 19.5 ans**.

## Diagnostic (FAIT — ne pas re-chercher)

Trajectoire de l'humidité au plot du pommier (climat labo `_meteo_labo` =
CALME, 15 °C, nébulosité 0.1, AUCUNE pluie) :

| âge | hum(3,3) | asphyxie_memory |
|-----|----------|-----------------|
| 5   | 0.70     | 0.000 |
| 10  | 0.97     | 0.000 |
| 15  | 1.52     | 0.000 |
| 19.5| **2.98** | **0.865** → mort asphyxiée |

**Cause** : le sprint **météo→champs (2026-06-29)** a ajouté la **rosée**
(`fields/ecofields/rosee.py`, appelée en 2c de la boucle). La rosée dépose de
l'humidité **chaque nuit**, pilotée par le refroidissement nocturne
(`t_min_nuit_at`) et la nébulosité — **pas** par les événements de pluie. Or le
climat labo du test choisit **nébulosité 0.1 (ciel clair)**, ce qui **MAXIMISE**
le refroidissement nocturne → **dépôt de rosée maximal**. Sur une terre drainante
mais **sans puits d'évaporation** (D37 vent/évapotranspiration absent), l'humidité
monte de façon **monotone** sur ~19 ans jusqu'à franchir le seuil d'excès, puis
`asphyxie_memory` rampe (`mortalite.py` L73-82) et tue l'arbre **avant** la
sénescence age-based.

**C'est la RÉCIDIVE exacte de D39** : le test isole sa tuile contre une source
d'humidité (la pluie/neige, neutralisée par `_meteo_labo` au 2026-06-20), mais une
**NOUVELLE source** (la rosée) a été ajoutée 1 sprint plus tard sans que le test
soit ré-isolé contre elle. Le test est calibré « au fil du rasoir » (hum confort
1.5, entre sécheresse et asphyxie) → fragile à tout nouvel apport hydrique.

Le moteur n'est **pas** en cause : la rosée se comporte comme conçue (ciel clair =
beaucoup de rosée, §3.6 de `rosee.py`, tension VOULUE). C'est l'**isolation du
test** qui est dépassée.

## Arbitrage de design (→ Nico, AVANT de coder)

Deux pistes, comme pour D39 :

- **(a) Ré-isoler le test contre la rosée** (reco, cohérent avec la résolution
  D39). Surgical, **moteur intact, golden intact**. Variante robuste : neutraliser
  la rosée sur la tuile-double du test, comme la germination est déjà neutralisée
  (`eco.tick_rosee = lambda *a, **k: []` ou équivalent) — ça isole la sénescence
  de **toute** rosée quel que soit le climat, et ne récidivera pas au prochain
  apport hydrique. (Choisir nébulosité élevée = couvert n'est PAS robuste : ça
  rallume l'étiolement/manque de lumière et déplace juste le problème.)
- **(b) Traiter le fond** : sous météo calme et claire PERMANENTE, est-il physique
  qu'une terre drainante se gorge **monotone** depuis la seule rosée, sans aucun
  puits d'évaporation ? Non → il manque l'**évapotranspiration** (D37 vent +
  évaporation diurne). Vrai correctif = **sprint dédié plus gros** (D37), pas ce
  sprint-ci.

**Reco** : (a) en correctif immédiat (rend le test vert + robuste aux futurs
apports), et **consigner explicitement (b)/D37** comme le vrai manque de fond.
Décision = Nico.

> **DÉCISION NICO (2026-06-29)** : **piste (b)** — traiter le fond
> (évapotranspiration). On NE ré-isole PAS le test. Conséquence assumée :
> `test_senescence` **reste rouge** jusqu'à ce que le puits d'évaporation
> atterrisse. Ce sprint devient donc la **conception d'un sprint
> évapotranspiration / vent (D37)** — voir ci-dessous. L'investigation
> elle-même (diagnostic) est CLOSE.

## Critères de succès

- `python3 -m tests.test_senescence` → PASS (pommier mort de **sénescence**,
  âge ∈ [49 ; 112]).
- **Moteur intact, golden INTACT** (piste a ne touche que le double de test).
  Vérifier `python3 -m tests.test_golden` inchangé.
- Lancer aussi `python3 -m tests.test_sim_server` (régression générale) +
  `python3 -m tests.test_rosee` (rosée intacte) + `test_stress_chronique`
  (asphyxie/ombre intacts).

## Clôture

- Rouvrir/mettre à jour **D39** dans `DETTE.md` : il avait été marqué 🟢 ✅ le
  2026-06-20 mais a **récidivé** via la rosée — re-résolu ici (piste a) en
  ré-isolant aussi contre la rosée. Re-marquer ✅ avec la nouvelle date + la cause.
- MAJ `journal.md` (index) + entrée `journal/NN_…`.
- Si Nico choisit (b), ouvrir/lier le sprint D37 (vent/évaporation) — hors
  périmètre de ce sprint.

## Garde-fous projet (rappel)

- Source de vérité = Python `data/code/`, lancement depuis `data/code/`.
- Déterminisme (philo #3) : aucun RNG neuf. Piste (a) = surgical sur le test seul.
- Décision de design → Nico (l'arbitrage a/b ci-dessus).
- Français + commentaires pédagogiques au cœur des fichiers.

## Reprise

« lis `sprints/sprint_senescence_rosee.md` » → l'arbitrage (a/b) est le seul
préalable ; le diagnostic est fait, le correctif (a) est petit et golden-safe.
