# ① Banc de calibration + métrique vitalité SOL (VUE)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Spec de
> référence : `docs/meta/calibrage/conception_calibration_realiste.md` (§0, §2.3, §7①).
> Sprint : calibration réaliste. Ce tronçon ne touche QUE la VUE (métrique sol) et
> ajoute un outil. **Un fichier moteur modifié à la fois.**

## Objectif

1. Promouvoir le banc de mesure jetable en outil versionné réutilisable
   `data/code/tools/banc_calibration.py`.
2. Réaligner les normalisateurs de la **métrique de vitalité du SOL** (`eco.vitalite`,
   `fields/ecofields/sol.py`) sur la plage d'opération réelle, pour qu'elle **cesse
   d'aplatir tous les états près de 0.01–0.07** et **discrimine** bon vs mauvais sol.

## Contexte mesuré (déjà établi, ne pas re-mesurer 500 ans)

- `eco.vitalite(r,c)` = `micro·0.35 + om_active·0.25 + fert·0.20 + om_stable·0.20
  − disturb·0.15`, clampé [0,1], moyenné (`vitalite_average`). **Aucun lecteur dans
  le tick** — c'est une grandeur de VUE (snapshot `summary()["vitalite"]`, overlay F6).
- Plages réelles (banc 50 ans, seed 42) : microbiome moyen ~0.02–0.35 (plot riche
  ~0.5, pic transitoire ~2.3) ; om_active plafonne ~0.67 ; **om_stable monte 0.15→
  2.66 à 50 ans, encore en hausse (accumulateur centennal → ~5)**.
- Normalisateurs actuels : microbiome/3.0, om_active/5.0, om_stable/5.0,
  fertilite_index/3.0 — les deux premiers écrasent (÷ trop grand).

## À faire

### A. Outil `tools/banc_calibration.py`
Crée-le en t'inspirant du banc de conception (mesure : vivantes, `plant.vitalite`
moy/médiane, `eco.summary()["vitalite"]`, microbiome, om_active/max, om_stable/max,
lumiere_moy, sur N années, monde dense 2×6×8 ET lâche 2×12×16). Construction du
monde = miroir de `tests/test_golden.py:build_world` (mêmes semis fondateurs, seed
42, maison centrée). Paramétrable `python3 -m tools.banc_calibration [annees]`.
Sortie tableau lisible. **Conserver le code** (règle projet) — ne rien supprimer.
⚠ **NE PAS lancer de run 500 ans** (interdit, cf. `00_etat.md`) : 10 ans dense +
10 ans lâche suffisent, 50 ans optionnel.

### B. Constantes nommées (`fields/ecofields/constants.py`)
Ajoute, près des normalisations de sol :
```
MICROBE_EFFECT_REF = 0.6   # microbiome « plein effet » (plage réelle plot riche ~0.5)
OM_ACTIVE_REF      = 1.0   # om_active « plein effet » (plafond réel ~0.67)
```
(Commentaire pédagogique EXIGÉ, exclu du décompte LDC.) **Ne PAS** créer/toucher de
constante pour om_stable : il reste sur /5.0 (accumulateur centennal, VOULU).

### C. Métrique vitalité sol (`fields/ecofields/sol.py`, méthode `vitalite`, ~l.127-146)
- ligne `micro = min(1.0, self.microbiome.at_plot(r, c) / 3.0)` →
  `/ MICROBE_EFFECT_REF`.
- ligne `active = min(1.0, self.om_active.at_plot(r, c) / 5.0)` → `/ OM_ACTIVE_REF`.
- ligne `structure = ... om_stable ... / 5.0` → **INCHANGÉE**.
- `fert = ... fertilite_index / 3.0` → **INCHANGÉE** (calibration NPK = P2).
- Importe les constantes dans `sol.py` (mêmes imports que les autres constantes du
  module).

### D. Calibration & ancres (via le banc)
Après le changement, lance `tools/banc_calibration.py` et vérifie que la vitalité sol :
- **discrimine** : un sol mûr (an 20-50, humus riche) lit nettement plus haut qu'un
  sol jeune/pauvre (an 1-2) ou dégradé ;
- **est en bande lisible** : jeune/pauvre ~0.1–0.2, mûr/riche ~0.5+, dégradé ~0.05
  (ancres indicatives, pas des cibles absolues).
- **Si la pénalité `disturbance` (poids 0.15, `VIT_W_DISTURB`) domine encore** et
  écrase la bande (mûr riche reste < ~0.3), tu es AUTORISÉ à ré-équilibrer les poids
  `VIT_W_*` (`constants.py`) : garde somme des poids positifs ≈ 1 et le clamp [0,1].
  Documente la nouvelle pondération dans `00_etat.md` (dérive expliquée).

## Golden
**Re-figé LOCALISÉ.** Seul le champ `"vitalite"` des lignes `ECO` du digest change
(la métrique n'a aucun lecteur tick → rien d'autre ne bouge). Procédure :
1. `python3 -m tests.test_golden` → FAIL attendu, **UNIQUEMENT** sur `vitalite=` des
   lignes ECO. **VÉRIFIE le diff** : si un attribut de plante, un autre champ ECO, ou
   un log bouge → tu as introduit un effet de bord, ANNULE et corrige (la métrique
   ne doit PAS avoir de lecteur tick).
2. Re-capture : `python3 -m tests.test_golden --capture`. Note le nouveau hash dans
   `00_etat.md`.
3. Relance les 11 suites ciblées (`tests/`) : elles doivent PASSER (aucune ne lit la
   métrique sol ; si une casse, investiguer).

## Ce qu'il NE faut PAS faire
- Toucher `om_stable/5.0` (dans vitalité OU ailleurs).
- Toucher un lecteur du TICK (uptake, maladie, decompo, soil_memory, qi_local,
  croissance saturation) — c'est le tronçon ②.
- Toucher `fertilite_index/3.0` ou les nutriments (P2).
- Lancer un run 500 ans.

## Fin de tronçon
Mets à jour `00_etat.md` (§REPRISE + nouveau hash golden + poids si modifiés), commit
(fichiers nommés : `tools/banc_calibration.py`, `fields/ecofields/constants.py`,
`fields/ecofields/sol.py`, `tests/golden_hash.txt`, `00_etat.md`), puis tronçon ②.
