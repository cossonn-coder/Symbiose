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
| ③ | banc climatique (acclimatation/ombre dense) + oracles + note rendu `ombre` C# | NEUTRE | À FAIRE |
| ④ | banc biotique (ravageur/floraison→fruits/semis tempéré) + oracles → tri D47-C3/C4/C5 | NEUTRE | À FAIRE |
| ⑤ | sélecteur Godot (menu C#) + F5 + bilan D47 (trancher, verser bugs en dette) | NEUTRE | À FAIRE |

## Golden
- Départ (post-plasticité) : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`.
- **Attendu INCHANGÉ à tous les tronçons** (bancs branchés hors smoke/full).
- Pont : **0.5.3** (inchangé ① à ④ ; bump éventuel au ⑤ uniquement si un champ de
  protocole est ajouté pour le sélecteur — sinon `init config=<banc>` suffit).

## REPRISE
②  CLOS. Prochain : `03_climatique.md` (acclimatation / ombre dense + oracles +
note rendu `ombre` C#). RÉUTILISER le pattern ①② :
- Fabriques dans `bancs/climatique.py` (déjà créé au ①, contient `secheresse_sable`),
  entrées ajoutées à `bancs/__init__.py:BANCS`.
- Acclimatation : stress DOUX prolongé → sur-expression plastique (`expression > 1`),
  signe `acclimatation` (déjà observé en co-occurrence au ② sur chlorose/asphyxie —
  le stress déclenche le priming). Ombre dense : maison HAUTE/PROCHE (cf. `monde(...,
  house=House(...))`) → `shade_memory` au-delà de SHADE_DAMAGE_THRESHOLD, signe `ombre`.
- ⚠️ `ombre` : rendu C# manquant (dette 0.5.2) — l'oracle sera vert mais l'écran muet ;
  c'est le cas-école du tri D47 (bug RENDU, pas carte). NOTER au bilan ⑤.
- Oracle : nouveau `tests/bancs/test_climatique.py` (existe déjà au ①) — y ajouter
  `test_acclimatation` / `test_ombre_dense`.

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
