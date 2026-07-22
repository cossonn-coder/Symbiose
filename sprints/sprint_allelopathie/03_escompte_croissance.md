# ③ Escompte CROISSANCE / vigueur

> Kickoff autosuffisant. Reprise à froid = `CLAUDE.md` + `00_etat.md` + ce fichier
> + `docs/vegetal/allelopathie/conception_allelopathie.md` §C. Prérequis : ①② faits. Golden **re-figeage à
> ÉVALUER** (isolé).

## Objectif

Étendre l'inhibition aux **plantes déjà levées** : une plante sensible dont les
racines explorent des plots chargés en `allelopathie` subit un **escompte de
croissance/vigueur** (facteur multiplicatif borné). Jamais un décrément direct de
santé (philo #2) — on réduit le **gain** de croissance, l'écosystème fait le reste
(dépérissement émergent : la plante affaiblie devient vulnérable à l'ombre, aux
ravageurs, à la sécheresse).

## Fichiers à toucher

- `sim/growth.py` (ou `sim/vigueur_plante.py`, là où la croissance/vigueur lit déjà
  les contraintes de milieu — repérer le point où les facteurs édaphiques modulent
  le gain) — appliquer `f_croissance` au gain de croissance/vigueur.
- Réutiliser l'**empreinte racinaire** déjà dérivée (plots explorés, comme l'uptake
  NPK/eau) pour lire la concentration moyenne — **ne pas recalculer** la géométrie
  racinaire si elle est déjà disponible (mémoïser, cf. règle projet).

## Modèle / formules

- `f_croissance = 1 − ESC_MAX · SENS_esp · rampe(allelopathie_racinaire)`, borné.
- `allelopathie_racinaire` = concentration **moyenne** de `allelopathie` sur les
  plots explorés par les racines (même empreinte que l'uptake).
- `ESC_MAX` = escompte maximal (placeholder, < 1 pour ne jamais annuler la
  croissance d'un coup). `rampe` = même saturante douce qu'au ② (cohérence).
- `SENS_esp` = même trait `allelopathie_sensibilite` qu'au ②.

## Golden attendu

**Re-figeage à ÉVALUER**, isolé au tronçon. Se produit **seulement si** un émetteur
mature charge le champ près d'une plante sensible **présente au smoke**. Au ③ les
traits `allelopathie_emission` valent encore 0 (renseignés au ⑤) → **golden
probablement NEUTRE** ici aussi. **Invariant dur** : `allelopathie = 0` ⇒
`f_croissance = 1` ⇒ croissance **inchangée**. Lancer `python3 -m tests.test_golden`.
Si dérive inattendue (champ non nul sans émetteur doté) : bug, investiguer avant de
re-figer. Si dérive légitime : **isoler, mesurer, annoncer** le nouveau hash dans
`00_etat.md`.

## Ce qu'il NE faut PAS faire

- Ne PAS décrémenter directement `vitalite`/santé (philo #2 : escompter le GAIN).
- Ne PAS recalculer l'empreinte racinaire si déjà disponible (mémoïser).
- Ne PAS toucher la germination (②) ni l'autotoxicité (④).
- Ne PAS annuler totalement la croissance (`ESC_MAX` borné < 1).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Vérif

Golden + test ad hoc : planter une espèce sensible sur plots chargés `allelopathie`
→ gain de croissance/vigueur réduit vs témoin non chargé ; à `allelopathie=0`,
croissance identique au témoin.
