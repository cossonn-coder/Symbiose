# 2026-07-24 — Sprint QUÊTES (D79) — CLOS

`/sprint-auto sprint_quetes` (①→⑤). Implémente le **système de quêtes** conçu &
figé le matin même (voir entrée 141). D79 = **module MOTEUR joueur neuf**
`sim/quetes.py` (opt-in, jamais dans le golden), **PAS** un enveloppement de D78
(qui vit dans le harnais automate) : partage la forme `(geste, quantité, cible)`,
pas le code. Golden **`57c166d8…` INCHANGÉ sur les 5 tronçons**, `dotnet build`
VERT, `test_quetes` 52/52.

## ① Module `sim/quetes.py` + conditions cumulées — `512b79e`
`Quete` frozen (`id/donneur/condition/recompense/declencheur`), état **opt-in**
`game_state["quetes"]`, API `ajouter_quete`/`quetes_actives`/`progression`/
`est_accomplie`, hook `notifier_geste` qui compte les conditions
`("recolte_cumulee", geste, quantité, cible)` sur le **geste joueur** (pas de
re-parse du ledger, F2) et émet une ligne ✉ au ledger à l'accomplissement.
Branché dans `tools/simserver/plante_route.py` par **rebind local de `bilan`**
(notifie après geste réussi, zéro changement des branches). `test_quetes` 12/12.
**Golden INCHANGÉ** (opt-in strict).

## ② Conditions d'état sur snapshot — `6e4a3b3`
3 conditions d'état (`hauteur_min`/`floraison_min`/`nombre_vivant_min`),
évaluées sur le **snapshot des tiles hors tick** via les prédicats existants
(`current_height`, `floraison ≥ 0.5`). `evaluer_etat(gs)` clôt les quêtes
comblées + ✉ ledger ; `avancement(gs, id)` rend la **phrase diégétique V2**
(4 bandes, zéro chiffre) pour cumulées ET état. `SEUIL_FLEURI` redéfini
localement (règle de couches `sim ← engine`). `test_quetes` 25/25. Golden INCHANGÉ.

## ③ Déclenchement déterministe + corpus lettres — `fe27cdf`
Corpus déclaratif `sim/quetes_corpus.py` : **6 lettres anonymes** (V1, voix
épistolaire, non-directives) couvrant les 2 familles de conditions, les 5
récompenses simples et les 3 formes de déclencheur (une vise le kiwi = cible
`inatteignable` assumée, F3). Dans `quetes.py` : champ `texte_lettre`,
`evaluer_declencheurs` (ouverture déterministe par palier maîtrise / jalon
saison, ids triés, plafond `PLAFOND_QUETES_ACTIVES=6`), `remettre_recompenses`
(graine/vigueur/maitrise/page, idempotent, `None`=plaisir pur, #2 OK),
`est_atteignable`. **Zéro RNG.** `test_quetes` 42/42. Golden INCHANGÉ.

> Note : plafond fixé à **6** (le kickoff disait « ex. 3 », valeur d'exemple non
> figée) — constante calibrable au banc.

## ④ Récompenses matérielles rares (V3) — `a2bfdf1`
`("vivace", espèce, années)` instancie une pérenne du `PERENNIAL_CATALOGUE` puis
la fait croître par le **vrai chemin** (`grow_plant`, `années×52` ticks, plein
soleil) → segments cohérents « comme si elle avait poussé » (déterministe,
`form_seed_at`, zéro RNG). `("structure", kind)` pose un **bac gratuit** (un
cadeau ne facture pas de Vigueur) avec unicité tuile. **Philo #2 respectée** :
acteur neuf, jamais de buff sur plante existante. Récompense **« outil » différée
→ dette D93** (aucun inventaire d'outils n'existe). `test_quetes` 52/52. Golden
INCHANGÉ.

## ⑤ Vue Godot panneau courrier + pont — `14b98aa`
Pont : commande read-only `courrier` (`CourrierMixin`) → `etat_courrier()` =
lettres triées {id, donneur, texte_lettre, avancement diégétique, accomplie,
atteignable}, chiffre exact **debug-only (#5)**. Driver `avancer_quetes`
(déclencheurs → clôture d'état → récompenses idempotentes) câblé **hors tick**
dans `cmd_step_week`. C# : `SimBridge.Courrier()` + `CourrierPanel` (lettre
verbatim, coche ✉/☑, rêve inatteignable grisé) + **onglet Courrier au hub** +
banc F5 `bancs/courrier.py`. Protocole **0.5.40**. Build C# **VERT**. Golden
INCHANGÉ, `test_quetes` 52/52.

## Notes
- **Micro-dette signalée** (non gravée) : le parseur carnet ne câble pas la ligne
  ✉ des quêtes (marqueur social sans position, hors regex `evenements.py`) — la
  ligne est ignorée sans dommage.
- **Refactor auto-léger no-op** : plus gros fichier du sprint `sim/quetes.py` à
  279 LDC pur (🟢 sous 300), rien à scinder.
- `test_sim_server` 269/270 = seul l'échec **PRÉEXISTANT** (nouaison pommier
  pré-âgé, décalage phénologique) rouge, décorrélé (vérifié au stash).
- **DETTE** : D79 → CLOSE, D93 (outil différé) ajoutée au ④. **BACKLOG** mis à jour.

## Reste F5 Nico
- `init config="courrier"`, clic maison → onglet **Courrier** : 5 lettres, une
  par famille (tomates/tournesol/lavande/verger « presque le compte ») + kiwi
  inatteignable grisé.
- Calibrages à sentir en jeu : valeurs de récompense (`vigueur 30`…), seuils de
  conditions, plafond 6, jalons saison des déclencheurs.
