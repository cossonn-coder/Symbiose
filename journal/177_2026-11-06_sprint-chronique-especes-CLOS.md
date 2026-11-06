# 2026-11-06 — Sprint CHRONIQUE DES ESPÈCES (D127) — CLOS (①→④)

Exécuté en `/sprint-auto`. Golden `a10b7225…` **intact sur tout le sprint**.
Pont 0.6.9 → **0.6.10**. Conception : `docs/perf/run_eternel/conception_chronique_especes.md`.

## Tronçons
- **① `ca46b34` — causes de mort lues.** `sim/evenements.py` retire le préfixe
  « Santé », lit la cause canonique dans le `[reason]` des lignes `✗`
  (herbivorie, maladie, gel, grêle, vent, sécheresse, ombre, usure) ;
  `❄`/`✿` → `fin_de_cycle` ; raison inconnue → `autre` + champ `raison` brut,
  jamais « conflit ». Carnet (textes descriptifs/interprétatifs par cause) et
  aide (remèdes sur le milieu pour 6 causes). Bug joueur corrigé : une plante
  mangée n'est plus « cédée à plus vigoureux ».
- **② `30e9a61` — chronique côté serveur.** `tools/simserver/chronique.py` :
  effectifs/an de toutes les espèces, morts/an espèce × cause, levées par
  différence de comptage, registre non borné des disparitions et retours.
  Morts hors log comptées à part : `hors_tick` (gestes), `non_consignee`
  (campagnol). Section texte composée en Python, rendue dans `cmd_perf_report`.
  Coût 3,9 ms/tick [n=26, VM] (≈ 0,45 % du tick).
- **③ `1ca5c9d` — outil sans écran.** `tools/chronique_run.py` (chemin
  `cmd_init` + `cmd_step_week`, même comptage que le rapport C). Run
  `verger_mur` 200 ans → faits versés dans D127.
- **④ `40f350a` — vue.** `WorldView.PerfReport.cs` recopie la section telle
  quelle, tolère un pont ancien. Build vert.

## Faits du run 200 ans [seed 42, n=1 run, VM, 93 min]
- Cerisier éteint an 32, pommier an 41, figuier an 103 — **tous par sénescence
  du dernier pied**. « Plus que des noyers dès l'an 132 » était le bord de la
  fenêtre de 60 ans (`MAX_ANNEES`) : vrai dès l'an 103.
- 30 recrues malgré les levées coupées (noyer 18, figuier 9, pommier 3,
  cerisier 0) ; 25 morts sur 34 **par ombre** ; un seul noyer en an 200.
- **Question écologique ouverte (D127, moteur non corrigé)** : la relève meurt
  sous la canopée, le verger s'éteint. Voulu (sous-bois sans trouée) ou seuil
  d'ombre trop sévère pour les jeunes ligneux ? À concevoir à part.

## Refactor
Aucun fichier touché au-dessus de 300 LDC pur : rien à scinder.

## F5 (Nico)
Run turbo `verger_mur`, touche C après ≥ 10 ans : section `[chronique]`
(bilans « An X » tous les 10 ans + années marquées `*`, morts par cause,
registre des disparitions/retours).
