# 2026-07-04 — Sprint USURE, PAS PUNITION (D64 reframé, ①→③) — SPRINT TERMINÉ (`/sprint-auto`)

Le conflit spatial cesse de **tuer d'un verdict** ; la mort du dominé ÉMERGE du
stress continu (ombrage, sénescence). Aligne le code sur une conception DÉJÀ figée
(`CONCEPTION_COMPETITION_INTRAPLOT` Q3 : « mort émergente, jamais verdict ») —
n'invente pas de modèle neuf. Golden final **`15073be1…`**.

## ① Conflit spatial NON-LÉTAL — `sim/engine/mortalite.py::_resoudre_conflits`
Suppression de `loser.regress()` (au stade 0 mettait `health = 0` = mort sèche
d'une plante saine), du `resolved`-verdict et du `deposer_mort(loser,…)` de ce
chemin. Corrige d'un coup le **double-comptage** foliar+root (2 conflits par paire
résolus le même tick), le **regress-kill** brutal et la rétroaction **« le plus
jeune perd »**. Le conflit redevient une NOTIFICATION diégétique pure
(`detect_conflicts` + log `⚠ Conflit`). `resolved` ne sert plus qu'à ÉLAGUER un
conflit périmé (plante morte OU chevauchement disparu) via la statique
`_conflit_perime` (lecture seule). `regress()` désormais INUTILISÉ (conservé,
règle « ne jamais jeter de code »).

**Golden RE-FIGÉ `a6c2f651…` → `007be139…`** — PAS `a1c9c51f…` comme pré-mesuré au
kickoff. Divergence **tranchée par preuve par l'orchestrateur** : reconstruire le
variant de l'auteur du kickoff (garder la ligne de log `↓ … (conflit)` sans le
`regress()`) redonne **exactement `a1c9c51f…`** → le digest d'état des plantes est
IDENTIQUE entre les deux, la seule différence est **une ligne de log fantôme**
(le golden hashe log+digest). `a1c9c51f…` laissait un log annonçant une régression
qui n'a plus lieu (mensonger, contre la prose du kickoff) ; `007be139…` est la
version honnête et fidèle → figée. La condition STOP du kickoff (« hash différent
⇒ effet de bord sur l'état ») est FALSIFIÉE : aucun effet de bord, log seul.
`test_competition` 14/14, `test_senescence` PASS.

## ② Cap de létalité chronique −1 santé/tick — `sim/effects/perturbations.py`
Sur l'échelle santé entière 0-3, plusieurs `ReduceHealth` empilés dans un tick
pouvaient passer 3→0 (mort-éclair). `apply_disturbances` ventile désormais les
mutations en DEUX flux : **AIGU** (fonte des semis) passe INTACT ; **CHRONIQUE**
(herbivorie, fongique, sécheresse, ombre, mortalité de fond) borné à −1/tick/plante
par la statique `_cap_chronique` (garde un seul `ReduceHealth` amount=1, en
privilégiant un coup à `cause` non vide → marque foliaire préservée). Une plante
saine tient ≥ 3 ticks de fond avant de mourir = usure (philo #6). Ordre d'appel des
fonctions INCHANGÉ (tirages `_hash_noise` corrélés, zéro RNG neuf).

**Golden RE-FIGÉ (localisé, pré-autorisé) `007be139…` → `15073be1…`** : divergence
prouvée localisée par diff baseline↔capé — uniquement des coups chroniques >−1/tick
ramenés à −1 (bites herbivorie létale −2→−1, cumuls −1+−1→−1) + cascade aval sur
adventices annuelles (survie prolongée puis mort ailleurs). Cœur du jardin et
pérennes inchangés.

## ③ Vue Godot & F5 — vérification pure, zéro C#
Le rendu du signe `ombre` est DÉJÀ en place (`PlantRenderer.Organs.cs` mappe
`ombre`/`senescence`/`secheresse`). Chaîne de données vérifiée de bout en bout sur
le banc `grimpantes` via le serializer réel du pont : tournesol-hôte@(2,2) reste
vivant toute l'année (225 cm, plus de mort-éclair w12) ; haricot dominé@(2,3) porte
un `leaf_symptoms` cause=`ombre` croissant (0.04→0.17) → dépérissement progressif
visible. Volet (b) D64 (lisibilité auxiliaires) subsumé par D60 (noté DETTE).
Golden **INTACT**.

## Clôture
Refactor auto-léger **no-op** (fichiers touchés : `mortalite.py` 228 LDC,
`perturbations.py` 219 LDC — 🟢 ≤300). D64 → ✅ FAIT (DETTE mise à jour). **Reste
F5 = Nico** sur le banc `grimpantes` : (a) tournesol reste vivant et coiffe le
haricot (non-régression clé) ; (b) haricot jaunit/délave lentement sous l'ombre en
fin de saison (signe subtil ~0.17 — si jugé trop faible au F5, calibrage à verser
en dette). Suite séparée : `/conception` pour **D65 luxuriance/stratification**.
