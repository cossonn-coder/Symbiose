# 2026-06-18 — Conception « catalogue enrichi » (plantes + animaux nommés) — FIGÉE

**Sprint** : Catalogue enrichi · tronçon ① (doc-conception). **Golden INTACT**
(0 ligne `data/code`/C# ; smoke `5fddfe54…` inchangé). Livrable unique :
[`docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`](../docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md).

## Pourquoi

Le moteur a accumulé des features riches (thermique, pollinisation/cycle de vie,
décompo, vigueur/maîtrise, écrasement, compétition, succession) mais le cast
actuel (17 plantes, faune en **guildes abstraites**) les **exerce inégalement** :
plusieurs leviers sont codés et **jamais activés**. Le doc audite, révèle les
trous, et sélectionne les espèces à ajouter pour **souligner leur inclusion** dans
ces features.

## Ce que le doc fige

- **Audit + 2 matrices espèce × feature** (existant + ajouts) + vocabulaire de
  raccordement (quels champs relient une espèce à chaque feature).
- **Trous nommés** : aucune `evergreen` ni `biennial` exercée ; pas d'ombellifère
  (Apiaceae → syrphes) ; pas d'hôte de chenilles nommé ; fruitiers/biomasse
  limités ; familles à 1 espèce ; faune non nommée hors pollinisateurs.
- **~10 plantes** sélectionnées par niche : thym, lavande (evergreen) ; mâche
  (couvre-sol d'hiver) ; carotte (Apiaceae, biennial, hôte machaon) ; bourrache,
  consoude (Boraginaceae) ; moutarde (Brassicaceae) ; ortie (Urticaceae, hôte) ;
  courgette (Cucurbitaceae, fruitier) ; ail (Amaryllidaceae, répulsif).
- **Faune nommée** : modèle **TRANCHÉ** → défaut « parfum » (variante sprite +
  encyclopédie, **même champ**, golden neutre) pour ravageur/auxiliaire/vers ;
  exception « vrai type data-driven » pour les nouveaux **pollinisateurs**
  (bourdon, osmie). Catalogue : puceron/limace/doryphore, coccinelle/carabe/
  chrysope/merle/hérisson, lombric/cloporte, bourdon/osmie — chacun **interconnecté**.

## Découpage ②+ arrêté (§7 du doc)

| # | Lot | Golden |
|---|---|---|
| ② | Plantes lot 1 (familles connues : thym/lavande/bourrache/consoude/moutarde) | re-figé maîtrisé ou neutre |
| ③ | Plantes lot 2 (carotte/ortie/courgette/mâche/ail + 5 familles + `_ATTRACT_*` + vérif `biennial`/`evergreen`) | re-figé maîtrisé + corrections moteur éventuelles |
| ④ | Faune nommée — parfums (A) | NEUTRE |
| ⑤ | Faune nommée — pollinisateurs (B) bourdon/osmie | re-figé maîtrisé (pollen/nouaison) |
| ⑥ | Vue Godot / sprites / encyclopédie | NEUTRE |

**Alerte moteur (§7.2)** : `life_cycle="biennial"` et `winter_strategy="evergreen"`
sont **codés mais jamais exercés** → ③ devra les **vérifier** (trou possible).
