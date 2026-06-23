# Sprint « bancs d'essai / environnements de test dédiés » — état partagé

> **Origine** : verdict F5 du 2026-06-22 (post-plasticité). Conclusion Nico :
> « il faudra créer des environnements de test dédiés, la carte actuelle ne
> permet pas d'observer tous les phénomènes ». La carte `full` est un jardin de
> démo, pas un instrument d'observation : un signe muet à l'écran ne dit pas si
> c'est un **bug** ou un **artefact de la carte** (c'est exactement la dette D47).
>
> **But** : une bibliothèque de **mondes paramétrés** qui FORCENT chaque
> condition observable, chacun avec un **oracle** (mini-test Python qui asserte
> que le signe apparaît bien). Sert aussi d'**outil de tri pour D47** : oracle
> qui passe + écran muet ⇒ bug **rendu C#**, pas la carte.

## Principe directeur — AUCUNE mécanique nouvelle
Le moteur sait DÉJÀ produire tous les signes (cf. `sim/semiologie.py`). Un banc
ne fait que **composer des conditions** (sol, champs éco, plantes, ombre maison)
au-delà du seuil d'une cause. Conséquence forte : **golden NEUTRE à chaque
tronçon** — les fabriques de bancs ne sont branchées que pour `config ∉
{smoke, full}`. Le golden (`config="smoke"`) et la démo (`config="full"`) ne les
voient jamais. Si un tronçon fait dériver le golden → STOP, une fabrique a touché
une couche partagée.

## Vocabulaire sémiologique forçable (source : `sim/semiologie.py:174-192`)
| Signe | Levier du banc |
|---|---|
| `chlorose` | espèce acidophile (`myrtille`, `ph_opt=4.8`) sur sol au pH alcalin (`eco.ph`) |
| `secheresse` | déficit hydrique soutenu (sable + humidité basse, pas d'arrosage) |
| `asphyxie` | excès d'eau soutenu (argile + humidité haute / arrosage répété) |
| `ravageurs` | densité `ravageur`/`chenille` au plot (criblage) |
| `ombre` | ombre INSTALLÉE (maison haute/proche) — ⚠️ rendu C# manquant (dette 0.5.2) |
| `senescence` | vivace en fin de longévité |
| `acclimatation` | sur-expression plastique soutenue (stress doux prolongé) — teinte glauque |

## Décisions figées (Nico, 2026-06-22)
- **Granularité MIXTE** : bancs thématiques par famille de stress, mais phénomène
  ISOLÉ quand il interfère (ombre dense étouffe tout ; semis tempéré).
- **Oracle par banc** (mini-test Python, signe attendu au plot/semaine) — le
  levier de diagnostic D47.
- **Sélecteur Godot** dans le scope (tronçon ⑤) : menu C# pour choisir le banc à
  l'`init` sans éditer d'argument.
- **Accélération assumée** côté serveur : un banc force le phénomène VITE
  (pré-vieillissement, champs pré-chargés au seuil), comme `full` pré-vieillit
  déjà les fruitiers (`commands.py:70-73`). Déterministe, golden jamais touché.

## Architecture cible
- **Fabriques** : nouveau paquet `data/code/bancs/` (niveau `main.py` — peut tout
  importer). `bancs/__init__.py` expose `BANCS: dict[str, fabrique]` où une
  fabrique `() -> (tiles, ecos, house, banque)`. Un module par famille
  (`edaphique.py`, `climatique.py`, `biotique.py`) + `base.py` (helpers communs :
  tuile paramétrable, forçage de champ/mémoire, accélération).
- **Branchement** : `cmd_init` (`tools/simserver/commands.py:45`) — après les
  cas `smoke`/`full`, `if config in BANCS: ... = BANCS[config]()`.
- **Oracles** : `data/code/tests/bancs/` (paquet) — un test par banc + un helper
  `assert_signe(plant, cause, semaine)` réutilisable.

## Liste des bancs (mixte)
- *Édaphique* (②) : `chlorose_acidophile`, `asphyxie_argile`, `carence_npk`
- *Climatique* (③) : `secheresse_sable` (livré au ①), `acclimatation`, `ombre_dense`
- *Biotique* (④) : `infestation_ravageur`, `verger_floraison`, `semis_tempere`

## Tronçons
| # | Titre | Golden | Statut |
|---|---|---|---|
| ① | infra — paquet `bancs/` + registre + branchement `cmd_init` + `secheresse_sable` bout-en-bout + cadre d'oracle | NEUTRE ✅ | **CLOS** |
| ② | banc édaphique (chlorose/asphyxie/NPK) + oracles → tri D47-C2/C6 | NEUTRE ✅ | **CLOS** |
| ③ | banc climatique (acclimatation/ombre dense) + oracles + note rendu `ombre` C# | NEUTRE ✅ | **CLOS** |
| ④ | banc biotique (ravageur/floraison→fruits/semis tempéré) + oracles → tri D47-C3/C4/C5 | NEUTRE ✅ | **CLOS** |
| ⑤ | sélecteur Godot (menu C#) + F5 + bilan D47 (trancher, verser bugs en dette) | NEUTRE | À FAIRE |

## Golden
- Départ (post-plasticité) : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`.
- **Attendu INCHANGÉ à tous les tronçons** (bancs branchés hors smoke/full).
- Pont : **0.5.3** (inchangé ① à ④ ; bump éventuel au ⑤ uniquement si un champ de
  protocole est ajouté pour le sélecteur — sinon `init config=<banc>` suffit).

## REPRISE
④  CLOS. Prochain : `05_selecteur_godot.md` (sélecteur Godot menu C# + F5 + **bilan
D47** : trancher chaque anomalie, verser les vrais bugs en dette). Au F5, exhiber
chaque banc et confronter oracle (vert) vs écran :
- ⚠️ Dette **0.5.2** (rendu `ombre` C# manquant) toujours à lever — `ombre_dense` =
  oracle vert / écran muet (cas-école du tri D47, bug RENDU confirmé).
- **D47-C2** (`asphyxie_argile`) : oracle vert → si muet à l'écran = bug RENDU C#.
- **D47-C3** (`infestation_ravageur` vs témoin) : si le témoin montre AUSSI du criblé
  = bug RENDU ; sinon le criblage est sincère (floor TRÈS bas, 0.025).
- **D47-C4/C5** : tranchés MOTEUR (chaîne floraison OK, Solanaceae lèvent) → ce sont
  des conditions de la carte `full`, pas des bugs. Cf. journal ④.

## API de lecture des signes (NOTÉE pour ②③④)
Source UNIQUE = `sim.semiologie.leaf_symptoms(plant, eco, saison)` → liste triée
`[{cause, intensity}]`. C'est CE que `serialize._snapshot` met dans
`plant["leaf_symptoms"]` (serialize.py:117) — donc l'oracle lit au même endroit
que la vue. `tests/bancs/oracle.py:signes_du_plot` enveloppe l'appel (retrouve
l'`eco` de la tuile + saison courante). Détecteurs purs, miroirs des seuils des
mécaniques qui blessent (DRY) — un signe ne ment jamais.

## Piège de calibration découvert au ① (à retenir)
La route « stress purement naturel » NE FRANCHIT PAS toujours le seuil : avec le
seed serveur (`0x5AB1057E`), une pluie de fond ramène l'humidité vers la sem. 16 et
PLAFONNE `drought_memory` à ~0.52 (< seuil 0.6). Solution sanctionnée par le
kickoff = **accélération** : pré-charger la mémoire au seuil (`base.force_memoire`)
et laisser l'environnement composé (sol drainant + humidité basse) la MAINTENIR.
À reproduire pour tout signe piloté par une mémoire intégrée lentement.

## Journal de bord (MAJ en fin de chaque tronçon)
- **① CLOS** (golden NEUTRE `2ab026ad…`) : paquet `bancs/` posé (`base.py` helpers
  `build_banc_tile`/`monde`/`force_memoire`/`vieillir` ; `climatique.py:
  secheresse_sable` ; `__init__.py:BANCS`). Branchement `cmd_init` (`elif config in
  BANCS`) + import module + banque-joueur de la fabrique. Cadre d'oracle
  `tests/bancs/` (`oracle.py` + `test_climatique.py`). Vérifs : oracle 2/2,
  golden inchangé, serveur `init config="secheresse_sable"`→step→snapshot émet
  bien `secheresse` dans `leaf_symptoms`, tailles ≤ 34 LDC pur. Pont 0.5.3
  inchangé (pas de champ de protocole ajouté — `init config=<banc>` suffit).
- **② CLOS** (golden NEUTRE `2ab026ad…`) : `bancs/edaphique.py` (3 fabriques —
  `chlorose_acidophile` myrtille/pH 8.2 · `asphyxie_argile` basilic/argile gorgée +
  `asphyxie_memory` pré-chargée · `carence_npk` DEUX tournesols jumeaux
  carencé/témoin) + entrées `BANCS`. `tests/bancs/test_edaphique.py` : **7/7 verts**.
  Serveur : les 3 `init config=<banc>` répondent `ok:true` (config inconnue →
  erreur listant les bancs), pont 0.5.3 inchangé. Tailles 32/47 LDC pur (≪ 350).
  - **D47-C2 (asphyxie muette) TRANCHÉ** : le MOTEUR émet bien `asphyxie` dès que
    `asphyxie_memory > ASPHYXIE_HEALTH_SEUIL` (0.10). L'oracle est vert → l'écran muet
    du F5 n'est PAS un bug moteur ni un artefact de carte. Cause = (a) l'arrosage
    manuel n'a pas poussé la mémoire au-dessus de 0.10 dans la fenêtre observée
    (intégration LENTE, `ASPHYXIE_MEMORY_LERP=0.05/sem`, exige plusieurs semaines
    d'excès SOUTENU sur argile) ET/OU (b) le rendu C# ne mappe pas `asphyxie`. À
    confirmer au F5 du ⑤ sur CE banc : signe muet à l'écran ⇒ bug RENDU C#.
  - **D47-C6 (NPK uniformément pauvres) TRANCHÉ** : symptôme NORMAL d'un sol épuisé,
    pas un bug de carte. Oracle : sol carencé garde `n≈0`, croissance bridée par
    Liebig (h 29.5 < témoin 41.0), AUCUNE mort (cohérent D41, mort édaphique bloquée).
  - Observation bonus : `acclimatation` co-apparaît sur chlorose ET asphyxie — le
    stress doux déclenche le priming plastique (attendu, bénin) ; utile au ③.
- **③ CLOS** (golden NEUTRE `2ab026ad…`) : `bancs/climatique.py` + 2 fabriques —
  `acclimatation` (basilic, terre peu humide hum 0.30 + `drought_memory` 0.40 SOUS le
  seuil 0.6 + `expression[tolerance_secheresse]`=1.12 pré-posée → durcissement glauque
  SANS blesser) · `ombre_dense` (banc ISOLÉ : maison haute 1500 cm collée au flanc nord,
  tuile oy=350 sous l'ombre installée, light≈0.15, `shade_memory` pré-chargée 0.80 >
  seuil 0.6 → signe `ombre`). `tests/bancs/test_climatique.py` : **7/7 verts** (oracle
  acclimatation assertant AUCUN signe de dégât concurrent via `SIGNES_DEGAT`). Serveur :
  les 2 `init config=<banc>` → `ok:true`, config inconnue liste les 6 bancs ; pont 0.5.3
  inchangé. Tailles 34/44 LDC pur (≪ 350). Note : `acclimatation` co-occurre sur
  `ombre_dense` (shade_memory durcit aussi `tolerance_ombre`) — bénin, `ombre` reste le
  signe de DÉGÂT prioritaire.
  - **D47 (rendu `ombre` C#, dette 0.5.2)** : `ombre_dense` est l'instrument exact du
    tri — oracle VERT (moteur émet `ombre`) mais écran MUET au F5 tant que `PlantRenderer`
    n'a pas son mapping couleur/texture `ombre`. À EXHIBER au F5 du ⑤ → bug RENDU confirmé,
    pas carte. **Lever la dette 0.5.2 reste à planifier (rappel au bilan ⑤).**
- **④ CLOS** (golden NEUTRE `2ab026ad…`) : `bancs/biotique.py` (3 fabriques) +
  `base.force_faune` (pré-charge d'un champ de population, symétrique de `force_memoire`).
  `tests/bancs/test_biotique.py` : **9/9 verts** ; `oracle.run_banc_trace` ajouté (trace
  par semaine, pour les signes TRANSITOIRES). Serveur : les 3 `init config=<banc>` →
  `ok:true` + step ok, config inconnue liste les 9 bancs, pont 0.5.3 inchangé. Snapshot
  serveur de `infestation_ravageur` émet bien `ravageurs` dans `leaf_symptoms` (= la donnée
  que reçoit la vue). Tailles 50/30 LDC pur (≪ 350).
  - `infestation_ravageur` : DEUX basilics jumeaux, INFESTE (`puceron` forcé 0.5,
    microbiome 1.0 → herbivorie NON létale) + TEMOIN. FORÇAGE-PULSE (décroît 0.55/sem en
    hiver, warmth=0) → oracle à **2 sem** (hôte criblé VIVANT, témoin sain).
  - `verger_floraison` : 3 pommiers pré-vieillis 6 ans + état floral PRÉ-ARMÉ
    (`floraison=1.0`/`a_fleuri=True`) + abeilles pré-chargées. La FANAISON réelle (relaxe
    hors fenêtre photopériodique) déclenche la nouaison entomophile sur le pollen DÉPOSÉ
    par les butineurs → fruits. Oracle (6 sem) : max **7 butineurs** pendant la floraison,
    **3 fruits** noués.
  - `semis_tempere` : banc ISOLÉ. Tueurs neutralisés : MILDIOU (paillage SATURÉ sur toutes
    les tiges → aucun slot libre → l'aléa ne peut poser de rondelle `maladie`) + FROID
    (même paillage → protection cap 1.0) ; succession spontanée coupée
    (`germination_candidates=[]`) ; grains tomate+poivron déposés (la moitié dépôt de
    `planter`, `cmd_init` n'ayant pas de game_state). Oracle (8 sem) : tomate ET poivron
    VIVANTS (la porte de `planter` lève bien les Solanaceae).
  - **D47-C3 (criblage fantôme) TRANCHÉ** : le MOTEUR émet `ravageurs` (criblage de FORME)
    dès densité > RAVAGEURS_FLOOR (≈0.025, TRÈS bas). Oracle vert + snapshot émet `ravageurs`
    → pas un bug moteur. Au F5 du ⑤ : si le TÉMOIN montre aussi du criblé ⇒ bug RENDU C# ;
    sinon le criblage est sincère (le floor sous-perceptif explique le « fantôme »).
  - **D47-C4 (chaîne floraison muette) TRANCHÉ** : la chaîne complète
    floraison→pollen→butineurs→nouaison→fruits FONCTIONNE (banc vert). Donc « 0 fruit/0
    butineur » sur `full` n'est PAS une régression moteur mais des CONDITIONS de carte :
    la fenêtre photopériodique de floraison n'ouvre que ~sem 15 et la nouaison entomophile
    exige la FANAISON (~sem 35), ET des pollinisateurs présents (densité saisonnière +
    habitat/rondelle pollinisateur). Piste F5, pas de correctif moteur.
  - **D47-C5 (Solanaceae ne lèvent pas) TRANCHÉ** : elles lèvent ET survivent ici → la
    porte de `planter` est SAINE. Le symptôme de `full` venait de la fragilité Solanaceae
    (mildiou familial dès une rondelle `maladie` + froid de démarrage) — question de DESIGN
    (protéger les semis : paillage, semis intérieur), pas un bug.
