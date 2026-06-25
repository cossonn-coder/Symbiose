# 2026-06-25 — Sprint MYCÉLIUM & INTERCONNEXIONS (①→⑥) — SPRINT TERMINÉ

> Exécution autonome `/sprint-auto sprints/sprint_mycelium_interconnexions`.
> Conception figée 2026-06-25 (`docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md`).
> Orchestrateur + 6 sous-agents au contexte frais (= `/clear` automatique entre
> tronçons). Source de vérité = moteur Python `data/code/`, Godot = vue (Option B).

## En une phrase
Le **mycélium** devient un acteur de plein droit : **un seul champ scalaire**
`mycelium ∈ [0,1]` dans `EcoFields` (patron `microbiome`) qui pousse sur le bois
humide tempéré et rend **trois services** selon le point de branchement —
saprophyte (décompo bois), liant (`om_stable`), mycorhizien (boost borné du `p`,
wood-wide-web) — nourrit la faune fongivore, se montre par des **carpophores**
(perception pure échantillonnée), colonise les structures bac/pile passées au
**niveau tuile**, et se fait **casser par le bêchage** (event-driven) tandis que
la grelinette le préserve.

## Décisions structurantes (rappel conception)
- **UN seul champ** rend les deux services bio (saprophyte + mycorhizien) ; la
  distinction est au *point de branchement*, pas dans l'état (décision i).
- **Mycorhize = boost `p` SEULEMENT**, borné (`MYCO_P_BONUS`) — aide à PUISER, ne
  déverrouille pas la fenêtre pH (philo #2, décision ii).
- **Carpophores = perception PURE** dérivée du champ, aucun état propre → golden-
  neutres.
- **Bêchage = EVENT-DRIVEN** au geste (`becher` retire un quantum, `grelinette`
  préserve) — surtout **PAS** via le champ `disturbance` (bruit de succession, ≠
  travail joueur).
- **Distinction stricte du pathogène** : ce mycélium est bénéfique ; les maladies
  fongiques M5 restent un acteur distinct et inchangé (zéro couplage).

## Tronçons (golden = re-figeage MAÎTRISÉ croissant, annoncé)
- **① champ `mycelium` + dynamique** (`fields/ecofields/mycelium.py`,
  `tick_mycelium` pur, tické après `tick_structure`) — effets §2 DÉBRANCHÉS, repos
  nul → golden **bit-identique** `2ab026ad…`. Commit `4fc9fd4`.
- **② saprophyte + liant** : terme `×(1+ALPHA_SAPRO·mycelium)` sur la décompo du
  SEUL tissu `bois` + apport très lent `LIANT_K·mycelium` à `om_stable`. Golden
  RE-FIGÉ MAÎTRISÉ `2ab026ad…` → **`9d13d4a7…`** ; isolation prouvée
  (`ALPHA_SAPRO=0 & LIANT_K=0` ⇒ retour exact). Commit `4ed4c4f`.
- **③ mycorhize** : `besoin_P *= 1+MYCO_P_BONUS·mycelium` dans `plant_uptake`
  (P seul, jamais N/K) + miroir `qi_local`. Golden RE-FIGÉ MAÎTRISÉ `9d13d4a7…` →
  **`00c1984a…`** ; dérive laser-localisée au seul champ `p` (`MYCO_P_BONUS=0` ⇒
  retour exact). Commit `ac269fe`.
- **④ faune fongivore + carpophores** : terme `FONGIVORE_GAIN·mycelium` sur le
  lombric ; `sample_carpophores` (perception pure, exposé au snapshot, pont
  **0.5.8**). Re-figeages prévus : population `6056713d…` → **`9ba39ab7…`**
  (lombric + prédateur merle) ; smoke → **`db5e7c66…`** (knock-on
  lombric→bioturbation ~0.001 sur 2 lignes om, anticipé par le kickoff §48-49) ;
  `FONGIVORE_GAIN=0` restaure les deux. Carpophores neutres. Commit `173b1e0`.
- **⑤ structures niveau tuile + colonisation + bêchage event-driven** :
  `poser_bac`/`poser_pile` bornés à un par tuile ; `Structure.colonisation ∈[0,1]`
  module la maturation et ensemence `eco.mycelium` au plot d'ancrage (réutilise le
  signal fongivore ④, lie c+d+e §3.3) ; `becher` retire `BECHAGE_MYCELIUM_MALUS`,
  `grelinette` préserve. Golden + population **INCHANGÉS** (event-driven, le smoke
  ne pose rien). Commit `ee1e03d`.
- **⑥ `epandre` 2 clics + vue Godot** : champ `colonisation` exposé au bloc
  `structures` du snapshot (pont **0.5.9**) ; `epandre` geste 2 temps côté vue
  (kind `E`, patron `deplacer_pot`, contrainte même tuile) ; `CarpophoreLayer.cs`
  NEUF (batché, lit le bloc carpophores) ; voile fongique ∝ colonisation dans
  `CompostStructure` ; palette `mycelium` F6. Golden + population INCHANGÉS,
  `dotnet build` vert. Commit `d6f3528`.

## Hash golden finaux
- smoke `tests/test_golden.py` : **`db5e7c66…`** (re-figé ④, stable ⑤⑥)
- population `tests/test_population.py` : **`9ba39ab7…`** (re-figé ④, stable ⑤⑥)
- pont : **0.5.9** ; `test_mycelium` 34/34, `test_structures` 80/80.

## Reste — F5 visuel = Nico (jamais lancé dans Godot, VM sans F5)
1. Ergonomie `epandre` 2 temps (saisie du bac, refus hors-tuile, annulation au
   changement de geste).
2. Lisibilité des carpophores (automne + humide + réseau dense, discrétion LOD).
3. Voile fongique sur le tas colonisé — ne pas le confondre avec un pathogène.
4. Overlay debug `mycelium` (F6).
Knobs placeholders à calibrer post-test : `ALPHA_SAPRO`, `LIANT_K`,
`MYCO_P_BONUS`, `FONGIVORE_GAIN`, `BECHAGE_MYCELIUM_MALUS`, seuils carpophores.
