# 2026-07-13 — Conception ALLÉLOPATHIE RACINAIRE — FIGÉE (`/conception`)

Sujet choisi par Nico (parmi allélopathie / zoochorie / climat pluriannuel /
épidémie spatiale). **Trou mécanique NET** : l'allélopathie n'existait qu'en
narration (blurbs encyclopédie), aucune mécanique. Comble aussi le TODO
`plants/base/familles.py:440` (« faute d'action moteur qui injecte du NÉGATIF dans
le champ, on triche avec un `adjacency_bonus` »).

## Contexte de découverte

En cherchant le prochain sujet, mon 1er conseil (« arc pollinisation à
implémenter ») s'est révélé **FAUX** : audit du code → l'arc pollinisation est
**entièrement terminé** (moteur ①→⑦ + vue Godot F5, clôture `304b2c0`, sprint sous
`sprints/_clos/`). BACKLOG.md ligne 49 et la mémoire n'avaient jamais été mis à
jour à la clôture → **corrigés** (commit `baa89c6`). Leçon gravée : vérifier le
code réel avant de recommander un sprint « à faire ».

## Décisions arrêtées (D1→D6)

- **D1** — cible = **germination ET croissance** (l'inhibition ferme la niche des
  voisines + escompte la vigueur des établies ; une plante peut dépérir sous un
  noyer).
- **D2** — inhibition **SÉLECTIVE** : émetteur auto-tolérant + `sensibilité` par
  espèce (compagnonnage chimique stratégique).
- **D3** — **autotoxicité / fatigue du sol** incluse, tronçon isolé : la
  monoculture s'empoisonne, la rotation repose le sol (pépite permaculture).
- **D4** — champ **UNIQUE** `allelopathie` (1 GridField, concentration agrégée) ;
  auto-tolérance + sensibilité gérées à la LECTURE. `soil_memory` ne trace PAS
  l'espèce → l'autotoxicité (④) trace l'identité séparément.
- **D5** — émetteurs = existants (**noyer** juglone fort / **tournesol** modéré /
  **aulx-aromatiques** léger, lève le TODO) + AJOUT **armoise** (vivace toxique) &
  **seigle** (engrais vert allélopathique), chacune ses **5 voix**.
- **D6** — courbes en **rampe douce continue** (Monod, pas de seuil dur), cohérent
  avec `niche_index` ; escompte croissance = facteur multiplicatif borné.

## Modèle (garde-fous philo #2/#3/#5/#7)

Injection `inject_field` sur l'empreinte racinaire (scatter borné, pas d'O(N²)) →
décroissance labile **modulée microbiome** (sol vivant détoxifie = interconnexion) →
lectures : germination `f_allelo = 1 − SENS·rampe(conc)`, croissance
`f_croissance = 1 − ESC_MAX·SENS·rampe(conc_racinaire)`. Jamais de malus direct sur
la plante — tout passe par le champ.

## Découpe = 6 tronçons (prêt `/sprint-auto`)

①champ+injection+décroissance [NEUTRE] → ②germination [probable neutre] →
③croissance [re-figeage à évaluer] → ④autotoxicité [**golden RE-FIGÉ MAÎTRISÉ
annoncé**] → ⑤espèces+voix [neutre] → ⑥vue Godot overlay F6 + indices diégétiques
[INTACT].

Spec : `docs/conception/CONCEPTION_ALLELOPATHIE.md`. Sprint :
`sprints/sprint_allelopathie/` (00_etat + 01→06). Backlog mis à jour. Pas de
nouvelle entrée DETTE (le TODO `familles.py:440` n'était pas D-numéroté ; il sera
levé au tronçon ⑤).
