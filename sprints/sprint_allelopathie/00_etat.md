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

## §REPRISE

Phase B **FIGÉE** (OK Nico 2026-07-13). Doc de référence :
`docs/conception/CONCEPTION_ALLELOPATHIE.md`. Kickoffs autosuffisants écrits :
`01_champ_injection.md` … `06_vue_godot.md`. **Prêt pour `/sprint-auto`.**

Découpe = **6 tronçons** (chacun son kickoff) :
- **① champ `allelopathie` + injection (`inject_field`) + décroissance modulée
  microbiome** (`01_champ_injection.md`) — lu par personne → golden **NEUTRE visé**.
- **② lecture GERMINATION** (`02_lecture_germination.md` — `seedbank.niche_index`,
  rampe douce Monod, trait `allelopathie_sensibilite`, auto-tolérance = sensibilité
  propre basse) — golden **probable neutre** (invariant champ=0 ⇒ inchangé).
- **③ escompte CROISSANCE/vigueur** (`03_escompte_croissance.md`, `sim/growth.py`,
  facteur borné sur le gain, empreinte racinaire) — golden **re-figeage à évaluer**,
  isolé (probable neutre tant que ⑤ pas fait).
- **④ AUTOTOXICITÉ / fatigue du sol** (`04_autotoxicite.md` — champ `autotox` +
  traceur d'espèce récurrente, alimente l'inhibition de la même espèce) — golden
  **RE-FIGÉ MAÎTRISÉ ANNONCÉ** (invariant : autotox=0 ⇒ identique au pré-④).
- **⑤ espèces émettrices + voix** (`05_especes_voix.md` — traits noyer(fort)/
  tournesol(modéré)/aulx-aromatiques(léger, lève TODO `familles.py:440`) + AJOUT
  armoise & seigle avec leurs **5 voix**) — golden **neutre visé**, mesuré/annoncé
  si noyer|tournesol chargent le champ au smoke.
- **⑥ vue Godot** (`06_vue_godot.md` — overlay F6 + indices diégétiques sol nu +
  pont snapshot liste creuse) — golden **intact**, F5 = Nico.

Ordre ①→⑥ (neutre d'abord, re-figeage isolé au ④). Reprise à froid = lire CLAUDE.md
+ ce fichier + le kickoff `0N`. Prochaine action Nico : `/clear` puis
`/sprint-auto sprint_allelopathie`.
