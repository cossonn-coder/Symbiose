# État — Sprint ALLÉLOPATHIE (conception FIGÉE, prêt /sprint-auto)

> Carnet de bord vivant (skill /conception §0bis). Reconstructible à froid :
> lire `CLAUDE.md` + ce fichier suffit à reprendre sans le fil de conversation.
> **Phase A (challenge/design) — rien de figé.** Le doc `CONCEPTION_ALLELOPATHIE.md`
> et les kickoffs ne seront écrits qu'après OK explicite de Nico (phase B).

## Sujet

Allélopathie racinaire : chimie plante↔plante. Une plante libère par ses racines
(exsudats) des composés qui **inhibent** (ou parfois favorisent) la germination et
la croissance des voisines. Trou mécanique NET (aujourd'hui seulement narratif dans
l'encyclopédie). Choisi par Nico le 2026-07-13 (parmi allélopathie / zoochorie /
climat pluriannuel / épidémie spatiale).

## Ce que l'existant offre (audité 2026-07-13)

- **`family_effects` data-driven** (`plants/base/familles.py`) avec actions
  `inject_field` / `adjacency_bonus` / `companion_bonus`. L'ortie fait DÉJÀ
  `inject_field variable="n" amount=+0.03 cible="local"` → **le mécanisme
  d'injection dans un champ de sol au voisinage EXISTE**.
- **TODO explicite** `familles.py:440` (Amaryllidaceae/aulx) : « faute d'action
  moteur qui injecte du NÉGATIF dans le champ, on triche avec un adjacency_bonus ».
  L'allélopathie comble exactement ce manque.
- **Champs de sol nombreux** (`fields/ecofields/container.py`) : microbiome, om_*,
  soil_memory(_fast/_deep), ph, n/p/k, structure_sol, mycelium, marais_memory…
  → un champ NEUF `allelopathie` s'insère naturellement, ou réutilise soil_memory.
- **Germination** : `fields/seedbank.py` `niche_index` / `germination_candidates`
  + `sim/succession.py` (portes de levée). Point d'insertion NATUREL de l'inhibition
  (l'allélopathie bloque surtout la GERMINATION).
- **Empreinte racinaire** : rayon racinaire → plots exploités (déjà dérivé).
- **Croissance/santé** des plantes établies : escompte possible (2ᵉ cible).
- **Mycélium** (mycorhize) : interaction connue (le réseau peut dégrader/transporter
  les allélochimiques) → piste d'interconnexion.

## Décisions arrêtées (lot 1, Nico 2026-07-13)

- **D1 — Cible = germination ET croissance.** L'inhibition ferme la niche de
  germination des voisines (effet principal, réaliste/lisible) ET escompte la
  croissance/vigueur des plantes établies au voisinage d'un émetteur. Rationale :
  Nico veut le modèle riche (une plante peut dépérir sous un noyer), pas seulement
  le blocage de levée. → surface de re-figeage + calibrage plus larges, à isoler.
- **D2 — Inhibition SÉLECTIVE.** L'émetteur est auto-tolérant (ne s'inhibe pas
  lui-même) ; chaque espèce a sa **sensibilité** propre (nouveau trait, patron des
  tolérances de niche existantes). Réaliste + stratégique (compagnonnage chimique).
- **D3 — Autotoxicité / fatigue du sol INCLUSE, en tronçon isolé.** L'allélochimique
  s'accumule si la même espèce revient sans rotation → la monoculture se punit
  elle-même (pépite pédagogique permaculture). Touche le golden (monoculture) →
  **tronçon dédié, re-figeage annoncé**, placé en DERNIER.

## Orientation technique retenue (à durcir)

- Champ de sol NEUF `allelopathie` (GridField, comme microbiome/ph), alimenté par
  `inject_field` (données par espèce émettrice) — résout le TODO `familles.py:440`.
- Décroissance par tick **modulée par le microbiome/mycélium** (sol vivant détoxifie)
  = interconnexion. Régime labile par défaut ; l'accumulation (D3) est le mode
  autotoxique, réglable.
- Lecture : (a) germination via `seedbank.niche_index`/`succession` (niche se referme) ;
  (b) croissance via escompte de vigueur/croissance au voisinage. Philo #2 : jamais
  de malus direct sur la plante, tout passe par le champ.
- Sensibilité (D2) = trait par espèce ; auto-tolérance = l'émetteur s'exclut de sa
  propre lecture (ou sensibilité ~0 sur sa propre molécule).

## Décisions arrêtées (lot 2, Nico 2026-07-13)

- **D4 — Champ UNIQUE `allelopathie`** (1 GridField, concentration totale/plot).
  Auto-tolérance = l'émetteur s'exclut de sa propre lecture + sensibilité par espèce
  (D2). Léger, suffit pour D1/D2. **L'autotoxicité (D3) trace l'identité d'espèce à
  part au tronçon ④** — soil_memory NE trace PAS l'espèce (mémoire fertilité
  fast/deep, vérifié `sol.py`) → prévoir un traceur léger d'espèce récurrente au ④.
- **D5 — Émetteurs = existants + neuves.** Existants (déjà au catalogue, trait à
  poser) : **noyer** (`WalnutTree`/Juglans, juglone fort), **tournesol** (modéré),
  aromatiques/aulx (léger, résout TODO `familles.py:440`). NEUVES à ajouter avec
  leurs **5 voix narratives** (règle projet) : **armoise** (Artemisia, inhibitrice
  vivace puissante) ET **seigle** (engrais vert allélopathique annuel, geste
  permaculture du couvert). Deux facettes : vivace toxique vs couvert stratégique.
- **D6 (tranché par Claude, défaut) — courbes en RAMPE DOUCE continue** (pas de
  seuil dur), cohérent avec `niche_index` continu ; escompte croissance = facteur
  multiplicatif borné. Amounts/décroissance = placeholders calibrage post-test.

## Coût perf (estimation préliminaire)

Un champ de sol de plus = O(plots)/tick (injection scatter local bornée par rayon
racinaire + décroissance), négligeable vs les ~20 champs existants. Pas de O(N²).
À confirmer au chiffrage du doc.

## Coût perf (estimation préliminaire)

Un champ de sol de plus = O(plots) par tick (injection + décroissance), négligeable
(cf. les ~20 champs existants). L'injection réutilise le pattern `inject_field`
(scatter local borné par le rayon racinaire), pas de balayage O(N²). À confirmer.

## Avancement

- **① champ `allelopathie` + injection + décroissance — FAIT (2026-07-14).**
  Golden **INCHANGÉ** (`ebe04b44…`, neutre comme visé). Champ de sol UNIQUE (D4)
  déclaré/init dans `container.py`, exposé dans `get_field` (→ `inject_field
  variable="allelopathie"` route générique, aucune modif de `resolution.py`) ;
  décroissance labile (perte spontanée + détox ∝ microbiome) dans un helper PUR
  `allelopathie.py`, wrappé par `ticks.tick_allelopathie`, appelé en `boucle.py`
  (§4f, après mycélium, avant diffusion) ; trait `allelopathie_emission=0.0`
  DÉCLARÉ sur `PlantBase` (non renseigné → tronçon ⑤). Test ad hoc : décroissance
  monotone vers 0, plus rapide à microbiome élevé, voisins intacts. Aucun C#
  (pont/overlay = ⑥). NON committé (Nico commit).

- **② lecture GERMINATION — FAIT (2026-07-14).** Golden **INCHANGÉ**
  (`ebe04b445054…`, neutre comme visé — invariant `allelopathie=0 ⇒ rampe(0)=0 ⇒
  f_allelo=1`). Ajouts : trait `allelopathie_sensibilite: float = 1.0` sur
  `PlantBase` (défaut neutre partout, calibrage ⑤) ; constante `ALLELO_GERM_K=1.0`
  (demi-saturation de la rampe Monod, `constants.py`, réexportée via `import *`) ;
  helper PUR `_f_allelo(allelo, sensibilite) = 1 − sens·(x/(x+K))` dans
  `succession.py` (rampe douce D6, court-circuit à 1.0 si plot propre). Lecture
  branchée aux DEUX chemins de levée : (a) grains PLANTÉS (`_lever_grains_en_attente`,
  escompte niche après la porte thermique) ; (b) adventices férales (`arch_allelo`
  dict par plot passé à `germination_candidates`, patron symétrique à
  `arch_ph`/`arch_temp` — nouveau paramètre optionnel `arch_allelo` dans
  `seedbank.germination_candidates`, défaut absent = rétro-compatible).
  Auto-tolérance (D2) approximée par sensibilité basse de l'émetteur (posée au ⑤),
  PAS d'auto-exclusion du champ (choix surgical du kickoff). Tests ad hoc :
  invariant f=1 à champ nul ; sensible→niche effondrée à forte charge ;
  tolérant(0)→intacte ; rampe monotone continue ; demi-saturation à x=K ;
  intégration `germination_candidates` (f=0 coupe la levée, f=1 identique au
  baseline). Aucun C# (pont/overlay = ⑥). NON committé (Nico commit).

- **③ escompte CROISSANCE/vigueur — FAIT (2026-07-14).** Golden **INCHANGÉ**
  (`ebe04b445054…`, neutre comme visé — invariant `allelopathie=0 ⇒ moyenne 0 ⇒
  f_croissance=1 ⇒ target_g inchangé`). Ajouts : constante `ALLELO_GROWTH_ESC_MAX
  =0.6` (escompte MAX borné <1, `constants.py` près d'`ALLELO_GERM_K`, réexportée
  via `import *`) ; helper PUR module `_f_croissance_allelo(allelo, sensibilite) =
  1 − ESC_MAX·sens·rampe(x)` dans `sim/engine/croissance.py` (MÊME rampe Monod
  `x/(x+ALLELO_GERM_K)` qu'au ②, court-circuit à 1.0 sur sol propre). Application
  dans `_update_physiology` : lecture de la concentration MOYENNE de `allelopathie`
  sur l'empreinte RACINAIRE déjà dérivée (`plant.root_plots`, RÉUTILISÉE — pas
  recalculée, règle projet) → rabotage MULTIPLICATIF de `target_g` (la cible du
  `growth_factor` lissé, donc pas de compounding) par `f_croissance`, borné par le
  clamp existant [0.3,1.0]. Escompte le GAIN, JAMAIS `vitalite` (philo #2 :
  dépérissement ÉMERGENT via ombre/ravageurs). Traits `allelopathie_emission` encore
  0 partout (⑤) → champ nul au smoke → golden neutre. Tests ad hoc : invariant f=1 à
  champ nul (toute sensibilité) ; tolérant(sens=0)→1.0 même saturé ; monotone
  décroissant ; demi-saturation à x=K ; jamais annulé ; intégration engine (sol
  saturé → growth_factor tombe à ~0.56 vs 1.0 sur sol propre, espèce sensible).
  Aucun C# (pont/overlay = ⑥). LDC croissance.py = 189 pur (🟢). NON committé.

- **④ AUTOTOXICITÉ / fatigue du sol — FAIT (2026-07-14).** Golden **INCHANGÉ**
  (`ebe04b445054…`). ⚠️ Le kickoff PRÉVOYAIT un « RE-FIGÉ MAÎTRISÉ ANNONCÉ », mais
  la dérive s'est révélée **NULLE** : l'invariant du kickoff (autotox=0 ⇒ identique
  au pré-④) est SATISFAIT dans le cas fort, car la montée d'`autotox` est
  CONDITIONNÉE à un occupant ÉMETTEUR (`allelopathie_emission > 0`) — or AUCUNE
  espèce n'émet avant le ⑤ → le traceur `autotox_espece` ne s'arme jamais → `autotox`
  reste nul partout → `allelo_effectif == allelopathie` → ②/③ bit-identiques. C'est
  la meilleure issue possible (dérive isolée à 0, prouvée par le hash). Le re-figeage
  ANNONCÉ interviendra au ⑤ quand noyer/armoise/tournesol chargeront le champ.
  Ajouts : champ `autotox` (GridField [0, AUTOTOX_MAX]) + traceur léger d'identité
  `autotox_espece` (grille de `plant_class` ou None, une réf/plot — garde-fou RAM)
  déclarés/init dans `container.py`, exposés `get_field` (overlay ⑥) ; méthode
  `allelo_effectif(r,c,plant_class) = allelopathie + autotox SI cette espèce est
  l'émetteur récurrent traceé du plot` (spécificité de la fatigue, D3) ; helper PUR
  `autotoxicite.py` (`emetteur_du_plot` + `tick_autotoxicite` : montée `+AUTOTOX_MONTEE`
  par saison de ré-occupation par la MÊME espèce émettrice, redescente
  `*(1−AUTOTOX_REPOS−détox)` à la rotation/sol nu, détox ∝ microbiome) wrappé par
  `ticks.tick_autotoxicite`, appelé EN FIN DE SAISON dans `boucle.py` §17a (cadence
  pluriannuelle, avec `tick_soil_memory`) ; constantes `AUTOTOX_MAX/MONTEE/REPOS/MICROBE`
  (`constants.py`, réexportées via `import *`). Les DEUX lecteurs ②/③ lisent désormais
  `eco.allelo_effectif(...)` au lieu du raw `allelopathie.at_plot` (succession :
  grain planté + dict `arch_allelo` féral par candidat ; croissance : moyenne sur
  l'empreinte racinaire). Tests ad hoc : monoculture → autotox monte monotone ;
  spécifique à l'espèce (autre espèce voit 0) ; rotation vers culture de repos / sol
  nu → autotox retombe (détox) ; bascule vers un AUTRE émetteur → repos 1 tick puis
  fatigue DE cette espèce ; invariant émetteur-nul (emission=0 → autotox jamais armé) ;
  intégration ②/③ (autotox=1.75 → f_germ 0.36 / f_crois 0.62 pour l'espèce fatiguée,
  1.0 pour toute autre). Aucun C# (pont/overlay = ⑥). LDC pur : autotoxicite.py 27
  (🟢), container.py 315 (🟡 vigilance, +5 code pré-④, single-responsibility état),
  succession.py 179, croissance.py 190 (🟢). NON committé (Nico commit).

## §REPRISE

Phase B **FIGÉE** (OK Nico 2026-07-13). Doc de référence :
`docs/conception/CONCEPTION_ALLELOPATHIE.md`. Kickoffs autosuffisants écrits :
`01_champ_injection.md` … `06_vue_godot.md`. **①②③④ FAITS ; prochain = ⑤**
(espèces émettrices + voix, `05_especes_voix.md` — traits noyer/tournesol/aulx +
AJOUT armoise & seigle avec leurs 5 voix ; golden NEUTRE visé, re-figeage MESURÉ/
ANNONCÉ si noyer|tournesol chargent le champ au smoke). NOTE : c'est au ⑤ que le
re-figeage ANNONCÉ du ④ se matérialise réellement (émetteurs enfin actifs →
`autotox`/`allelopathie` non nuls → ②/③ mordent).

Découpe = **6 tronçons** (chacun son kickoff) :
- **① champ `allelopathie` + injection (`inject_field`) + décroissance modulée
  microbiome** (`01_champ_injection.md`) — **FAIT, golden inchangé `ebe04b44…`**.
- **② lecture GERMINATION** (`02_lecture_germination.md` — `seedbank.niche_index`,
  rampe douce Monod, trait `allelopathie_sensibilite`, auto-tolérance = sensibilité
  propre basse) — **FAIT, golden inchangé `ebe04b44…`** (invariant champ=0 ⇒ inchangé).
- **③ escompte CROISSANCE/vigueur** (`03_escompte_croissance.md`, escompte borné du
  gain via `growth_factor` dans `sim/engine/croissance.py`, empreinte racinaire
  réutilisée) — **FAIT, golden inchangé `ebe04b44…`** (neutre tant que ⑤ pas fait).
- **④ AUTOTOXICITÉ / fatigue du sol** (`04_autotoxicite.md` — champ `autotox` +
  traceur d'espèce récurrente `autotox_espece`, lu par ②/③ via `allelo_effectif`) —
  **FAIT, golden INCHANGÉ `ebe04b44…`** (re-figeage ANNONCÉ resté NUL : montée
  conditionnée à un émetteur, aucun avant le ⑤ → autotox jamais armé → invariant
  autotox=0 satisfait de fait ; re-figeage réel décalé au ⑤).
- **⑤ espèces émettrices + voix** (`05_especes_voix.md` — traits noyer(fort)/
  tournesol(modéré)/aulx-aromatiques(léger, lève TODO `familles.py:440`) + AJOUT
  armoise & seigle avec leurs **5 voix**) — golden **neutre visé**, mesuré/annoncé
  si noyer|tournesol chargent le champ au smoke.
- **⑥ vue Godot** (`06_vue_godot.md` — overlay F6 + indices diégétiques sol nu +
  pont snapshot liste creuse) — golden **intact**, F5 = Nico.

Ordre ①→⑥ (neutre d'abord, re-figeage isolé au ④). Reprise à froid = lire CLAUDE.md
+ ce fichier + le kickoff `0N`. Prochaine action Nico : `/clear` puis
`/sprint-auto sprint_allelopathie`.
