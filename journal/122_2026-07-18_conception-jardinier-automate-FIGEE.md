# 2026-07-18 — Conception JARDINIER AUTOMATE (D78) — FIGÉE (`/conception`)

## Origine
Amorce de Nico (`docs/amorce/amorce_conception_automate.md`) après ses sessions F5 :
à 2,5 J/s (phase de test), le testeur ne peut pas tenir 50-600 plantes → **toutes
nos mesures récentes (D69, D66/67/70/71, D74) portent sur un jardin ABANDONNÉ**.
Besoin : un agent qui tient le jardin pendant qu'on observe.

## Nature de l'outil
Agent **déterministe** (pas d'IA, pas de RNG — philo #3), **instrument de dev**
(pas de PNJ, pas de tutoriel — philo #6, statut overlay F6). Comportement =
**loi du minimum de Liebig** : identifier le facteur limitant dominant et lever
celui-là. Nom : `jardinier_automate` (« IA » proscrit).

## Invariant central (H2)
Module **au-dessus du moteur**, invoqué **entre deux ticks** côté appelant → le
moteur ne change pas d'une ligne → **golden INTACT par construction**. Vérifié au
tronçon ① (verrou « automate OFF → golden bit-identique »).

## Préalable résolu — inventaire réel des gestes (Q1)
Lecture de `sim/actions/` (paquet). La table §2.3 de l'amorce corrigée :
- **`pailler` consomme un stock de mulch** (`mulch_stock`) → refus si stock
  insuffisant, MÊME en libre → chaînage `broyer`/`recolter_paille` requis.
- **`drainer`/`creuser` n'existent pas** (hydrologie conçue non implémentée) →
  retirés ; ce sprint **ne crée aucun geste**.
- `pailler`/`broyer`/`tailler` sont GATED par la maîtrise → en mode payé,
  impasse si non débloqué.

## Arbitrages Nico (2026-07-18)
- **Q3 tutelle** = cultivées ; **désherbage commutable** (défaut `curatif` =
  déraciner une férale seulement si facteur limitant d'une cultivée).
- **Q5 récolte** = dès mûr, avec **`part_recoltee ∈ [0,1]` slider** (défaut 1.0).
- **Q4 comptabilité** = **`paie_vigueur` ET `credite_maitrise` commutables** par
  profil (flags orthogonaux ; `bride`/`libre` deviennent des presets).

## Deux exigences neuves structurantes
- **Trace structurée** (livrable central) : journal des gestes + **conséquences**
  (déverrouillages de maîtrise, paliers, morts).
- **Détecteur d'impasses** (objectif important) : facteur limitant sans
  geste-réponse applicable = **trou de gameplay** consigné → l'automate devient un
  instrument de découverte des problèmes insolubles dans l'état actuel du jeu.

## Objectifs — germe du système de quêtes
`Objectif(geste, quantité, cible)` injectable au début / en planification ; biaise
la priorisation + compte la progression ; **onglet** = trace scopée + événements
monde ; cible inatteignable → impasse. **Cœur mécanique seulement** — le système de
quêtes complet (courrier voisin/oncle/enfant, objectifs à condition d'état « kiwi
5 m »/« trèfles fleuris », panneau Godot, voix) part en **D79**.

## Profil configurable
`perception` (omniscient/semiologique) · `paie_vigueur` · `credite_maitrise` ·
`desherbage` (curatif/aucun/systematique) · `part_recoltee` · `ecrit_carnet`.

## Perf (Q9) — le vrai risque, à mesurer
Coût propre négligeable (O(N×k) local). Risque INDIRECT : un jardin tenu porte plus
de biomasse → plus d'émetteurs d'ombre (D67) → **LightField plus cher** → peut
rouvrir D66/D67/D70. Mesuré explicitement au banc ⑤ (peut-être le résultat le plus
intéressant du sprint) ; si avéré, D67/D71 à relire (calibrés sur le mauvais régime).

## Découpage — 7 tronçons, golden intact partout
① socle (boucle 5 étapes + profil + arroser/recolter + journal + verrous
déterminisme) → ② table complète + budget + chaînage broyer→pailler +
tailler/deraciner + slider + détecteur d'impasses → ③ comptabilité commutable +
trace des conséquences → ④ objectifs + onglet → ⑤ banc « jardin tenu » vs abandonné
+ rapport d'impasses → ⑥ vue Godot (sim_server + retour visuel + onglet) →
⑦ semiologique (optionnel, chiffre la qualité de la sémiologie).

## Livrables
`docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md` + `sprints/sprint_jardinier_auto/`
(00_etat + 01→07). DETTE **D78** (ce sprint) + **D79** (quêtes). Prêt pour
`/sprint-auto sprint_jardinier_auto`.
