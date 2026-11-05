# ① Bourgeons dormants + banc espacé — golden INTACT attendu

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception `docs/vegetal/croissance/conception_verger_vivant.md` §2 et §4, `sim/growth/phases.py` (`grow_plant`, `_debourrement`, `_elaguer`), `sim/growth/cladoptose.py`, `sim/engine/branches.py`, `sim/precroissance.py`, `bancs/verger_mur.py`, `tests/bancs/test_verger_mur.py`.

## Objectif

Un arbre qui a perdu des branches reconstruit sa couronne à partir de bourgeons latents, tant qu'il est vivant et éclairé. Le verger ne fond plus.

## À faire

1. **Réveil de bourgeons dormants** sur les ligneux procéduraux. Conditions : la couronne est sous son plafond (`max_segments`, avec une marge, essai à 85 %), `vitalite > 0`, la lumière suffit. Rythme borné et réveil déterministe (hash sur `form_seed`, la semaine et un ordinal), collet exclu. Un segment réveillé débourre par le `_debourrement` existant. Placement libre : dans `grow_plant` (pur, sans `eco`, mais `light_field` y est passé) ou côté `sim/engine`. Le sens des imports est `plants ← fields ← sim ← engine` : vérifier avant d'importer. La pré-croissance (`pre_croitre`) appelle `grow_plant` : décider s'il doit s'y appliquer et le dire au bilan, car les arbres de départ changent.
2. **Pas de boucle avec la cladoptose** : une branche tombée à l'ombre ne doit pas repousser chaque semaine sous la même ombre. Gate lumière (locale, ou de la plante) à montrer par mesure : nombre de cladoptoses par an avant/après sur un arbre ombragé.
3. **Banc `verger_mur` espacé** : les arbres sont aujourd'hui à 4-4,5 m, et le pommier reçoit 0,23 à 0,35 de lumière en saison feuillée. Espacer, quitte à agrandir la bande ou à ne garder qu'un noyer par cadre, tout en gardant les **deux** noyers pour la pollinisation anémophile. L'oracle de `test_verger_mur` doit rester vert.
4. **Effet mesuré** : `verger_mur` 5 ans et `full` 5 ans, seed 42, avant/après. Pour chaque arbre et chaque année : segments, apex, vitalité, fruits. Tick médian par an. Référence sans correction [`full`, seed 42, n=1 run, VM] : cerisier an 5 à 17 segments, 1 apex, 4 fruits ; tick médian an 5 à 1 017 ms. Un tronçon sans effet mesuré n'est pas un succès.
5. Golden, suites `test_croissance*`, `test_cladoptose*` ou leurs équivalents (`ls tests`), `tests/bancs/test_verger_mur`, puis bilan dans `00_etat.md` et commit.

## Golden

**INTACT** : `a10b7225…` identique avec un patch brut (un bourgeon toutes les 4 semaines, sous 85 % du plafond) [smoke, patch mémoire]. S'il bouge : anomalie, pas de re-figeage.

## NE PAS

Toucher aux seuils de casse (`CASSE_*`, `NEIGE_*`) ni à la cladoptose (`CLADO_*`). Toucher à l'humidité ni à l'asphyxie (D127). Lancer `tests/test_epaisseur_500ans.py`. Appeler DeepSeek.
