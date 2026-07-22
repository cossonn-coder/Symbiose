# ③ Comptabilité commutable + trace des conséquences

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/joueur/automate/conception_jardinier_automate.md` (§4, §6). Prérequis : ①② faits.

## Objectif
Câbler la **comptabilité commutable** de l'automate (flags `paie_vigueur`,
`credite_maitrise`, respect de `gestes_debloques`) et enrichir la **trace** avec les
**conséquences** des gestes (déverrouillages, paliers, morts).

## Fichiers à toucher
- `tools/jardinier_auto/profil.py` — presets `LIBRE`/`BRIDE` finalisés :
  `BRIDE = ProfilAutomate(paie_vigueur=True, credite_maitrise=True, ecrit_carnet=True)`
  (chaque axe reste réglable). `LIBRE` = tout False.
- `tools/jardinier_auto/execution.py` — avant chaque geste, **si `paie_vigueur`** :
  respecter `gestes_debloques` (ne PAS jouer un geste verrouillé → **impasse
  `geste_verrouille`**, §7). Les gestes paient déjà la Vigueur nativement
  (`cout_action`) — le flag `paie_vigueur=False` (mode libre) doit **court-circuiter**
  la contrainte de solde : soit re-créditer la Vigueur dépensée, soit initialiser le
  joueur avec une Vigueur non bornée. Choisir l'approche la moins intrusive (voir
  `sim/vigueur.py` : `spend`/`gain`/solde) et la documenter en tête de fichier.
- `tools/jardinier_auto/trace.py` — nouvelle catégorie d'entrée **conséquence** :
  `{semaine, type ∈ {deblocage, palier, mort}, detail}`. Après chaque tick de
  gestes, appeler les hooks de conséquence ci-dessous et consigner ce qu'ils
  renvoient.
- `tools/jardinier_auto/boucle.py` — après exécution, collecter les conséquences.

## Conséquences à tracer (§6)
- **Déverrouillages de gestes** : si `credite_maitrise`, appeler
  `sim.actions.evaluer_deblocages(gs, player)` (renvoie la liste triée des NOUVEAUX
  verbes ouverts) et consigner chaque nouveau verbe. Si `credite_maitrise=False`, NE
  PAS créditer la maîtrise (neutraliser le crédit) mais **on peut quand même noter
  dans la trace** ce qui SERAIT arrivé (utile au diagnostic — Nico veut « les
  conséquences »). Choix sobre : sous `credite_maitrise=False`, ne pas muter l'état
  de maîtrise du tout ; la trace note seulement les gestes joués.
- **Franchissements de palier** : comparer le palier de maîtrise avant/après (via
  `sim/maitrise.py`) si `credite_maitrise` ; consigner les hausses.
- **Morts** : diff des plantes vivantes avant/après le tick complet ; consigner les
  morts (utile pour corréler à un geste — ex. `deraciner`).

## Point de vigilance — le piège de la maîtrise auto-montante (Q4)
Le flag `credite_maitrise` EST la réponse : en mode `BRIDE` avec
`credite_maitrise=True`, un test long fait monter les paliers seul (extension,
magazine se déverrouillent) — c'est **voulu et tracé** (on teste la courbe de
progression). En `credite_maitrise=False`, l'automate joue les gestes mais la
maîtrise reste figée → on teste l'écologie sans dérive de progression. Le flag rend
le choix EXPLICITE et réglable, pas figé.

## Golden attendu
**INCHANGÉ.** Le golden n'a ni joueur ni maîtrise → aucune de ces clés n'est créée
→ no-op strict. Tests déterminisme toujours verts.

## Ce qu'il NE faut PAS faire
- NE PAS toucher le moteur ni `sim/maitrise.py`/`sim/vigueur.py` (seulement les
  APPELER). NE PAS créer de geste. NE PAS lancer `test_epaisseur_500ans`.
- NE PAS câbler les objectifs (④) ni la vue (⑥).

## Vérif de sortie
Golden intact + déterminisme vert. Banc `automate_demo` en profil `BRIDE` montrant :
Vigueur consommée, un geste verrouillé refusé → impasse, et (si `credite_maitrise`)
un déverrouillage consigné dans la trace. Mettre à jour `00_etat.md`.
