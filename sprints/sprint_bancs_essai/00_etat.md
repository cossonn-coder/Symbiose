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
| ② | banc édaphique (chlorose/asphyxie/NPK) + oracles → tri D47-C2/C6 | NEUTRE | À FAIRE |
| ③ | banc climatique (acclimatation/ombre dense) + oracles + note rendu `ombre` C# | NEUTRE | À FAIRE |
| ④ | banc biotique (ravageur/floraison→fruits/semis tempéré) + oracles → tri D47-C3/C4/C5 | NEUTRE | À FAIRE |
| ⑤ | sélecteur Godot (menu C#) + F5 + bilan D47 (trancher, verser bugs en dette) | NEUTRE | À FAIRE |

## Golden
- Départ (post-plasticité) : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`.
- **Attendu INCHANGÉ à tous les tronçons** (bancs branchés hors smoke/full).
- Pont : **0.5.3** (inchangé ① à ④ ; bump éventuel au ⑤ uniquement si un champ de
  protocole est ajouté pour le sélecteur — sinon `init config=<banc>` suffit).

## REPRISE
① CLOS. Prochain : `02_edaphique.md` (chlorose acidophile / asphyxie argile /
carence NPK + oracles → tri D47-C2/C6). RÉUTILISER le pattern du ① :
- Fabriques dans `bancs/edaphique.py`, entrées ajoutées à `bancs/__init__.py:BANCS`.
- Briques : `build_banc_tile(..., ph=..., n=..., p=..., k=...)` force n'importe
  quel champ de `EcoFields.get_field` (ph/n/p/k/structure_sol) via `fill`.
- Pour chlorose : espèce ACIDOPHILE (`ph_opt < SEUIL_ACIDOPHILE`, ex. `myrtille`)
  sur sol forcé alcalin (`ph` ≈ PH_MAX). Pour asphyxie : argile + `humidite` haute
  (> HUM_EXCES) — vérifier si une pré-charge `asphyxie_memory` est nécessaire
  (même piège que la sécheresse : un champ peut décroître via la météo seedée).
- Oracle : nouveau `tests/bancs/test_edaphique.py` réutilisant `oracle.run_banc` /
  `signes_du_plot` / `premiere_plante`.

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
