# ① Hauteur acquise — une plante ne rapetisse pas (moteur)

Lire d'abord `docs/vegetal/sante/conception_lisibilite_bilan.md` (§1, §2.1).

## Objectif
Aujourd'hui, pour les espèces **non procédurales**, `height_at` vaut potentiel × `growth_factor`
× génétique (`plants/base/familles.py` `height_at` ; arbres non migrés :
`plants/perennials/base.py` `height_at`, potentiel = `_interp(age_years)`). Or
`growth_factor` suit une cible qui baisse quand le bilan est en déficit
(`sim/engine/croissance.py`, bloc « Growth factor (D140 G ②) ») : une plante affamée
**perd des centimètres** (poivron du banc `plante_vivante` : 58 → 47 cm en 6 sem, seed 42).

Intention : la hauteur **bâtie** est **acquise**. `growth_factor` continue de régler la
**vitesse** de croissance (`sim/growth/phases.py` la lit) mais ne retire plus de taille.

## Modèle (intention — placement à vérifier au code)
- Mémoire par plante de la hauteur atteinte ; la hauteur rendue ne descend jamais sous
  elle tant que les parties aériennes vivent.
- Elle **retombe** seulement sur destruction de parties aériennes : taille/élagage,
  casse (vent, neige), broutage d'apex s'il existe, écrasement, mort de la plante, et
  **repli aérien** d'une vivace herbacée (dormance hivernale : la consoude, la menthe
  repartent de la souche — leur hauteur doit pouvoir redescendre l'hiver).
  Repère les chemins qui changent légitimement de hauteur avant de bâtir.
- Les espèces **procédurales** (`procedural_growth`, hauteur = max z de la structure de
  segments) ne sont **pas** concernées si leur structure ne rétrécit pas sous déficit :
  vérifie-le (mesure), ne les touche que si elles rapetissent aussi.
- Point transversal à vérifier tôt : `height_at` est appelé depuis un getter
  (`PlantInstance.current_height`) ; n'y mets pas d'écriture d'état — la mise à jour de
  la mémoire se fait une fois par tick dans le moteur (après la mise à jour de
  `growth_factor`). Couches : `plants ← fields ← sim ← engine`.

## Preuves attendues
- Test ciblé neuf : un poivron à l'ombre en famine ne perd pas de hauteur jusqu'à sa
  mort ; une plante taillée perd bien de la hauteur ; une vivace herbacée redescend en
  dormance (choisis une espèce du catalogue qui le fait).
- Re-mesure du banc `plante_vivante` (scène OMBRE) : hauteur des poivrons constante ou
  croissante.

## Golden
**RE-FIGÉ annoncé** : la hauteur pèse sur l'ombre, l'empreinte et la nécromasse à la mort.
Preuve exigée : avec la mémoire de hauteur neutralisée (retour à l'ancien calcul), le hash
revient à l'actuel `8f2dd7add938b4cb…`. Consigne le nouveau hash dans `00_etat.md` et
`tests/golden_hash.txt` selon la procédure du projet.

## À ne pas faire
Pas de changement de `growth_factor` lui-même ni de sa cible ; pas de toucher au bilan ;
pas de C# (la vue lit déjà la hauteur via le pont). Ne lance jamais `test_epaisseur_500ans`.
