# ④ Semis d'intérieur (pot dans la maison) + geste `repiquer` (D140 C.4-C.5)

Lire d'abord `docs/vegetal/genetique/conception_depart_jardin.md` §2 C.4-C.5.

## Existant (vérifié 2026-11-18)
- Pots : `world/container.py` (`Container`, `make_container`, `planter_dans`, position
  monde `x_cm, y_cm`, mini-`EcoFields`, tick : lumière à la position avec ombre
  maison → thermique → hydrologie…). Gestes `poser_pot`, `planter_conteneur`,
  `deplacer_pot` (`sim/actions/conteneurs.py`, coûts `sim/actions/couts.py`,
  déblocage `sim/actions/deblocage.py`, familles `sim/actions/familles.py`, palette
  `sim/actions/palette.py`).
- Maison : `world/building.py` (`House`, emprise + ombre). **Aujourd'hui un pot posé
  dans l'emprise de la maison serait dans l'ombre totale** : il faut un état « dans la
  maison ».
- Aucun geste `repiquer`.

## Objectif
1. **Pot dans la maison** : un pot dont la position est dans l'emprise de la maison
   (ou un emplacement dédié « rebord de fenêtre » — choisir le plus simple, le dire)
   est À L'INTÉRIEUR :
   - thermique : pas de gel, nuit et jour doux (constantes d'intérieur nommées et
     commentées, ex. ≈ 15 °C la nuit, ≈ 20 °C le jour) ;
   - pas de pluie (arrosage du joueur seulement) ;
   - lumière = fraction de la lumière extérieure (fenêtre, constante nommée,
     ≈ 0,3) → l'étiolement ÉMERGE de la croissance par faible lumière (vérifier que
     le moteur fait déjà filer une plante à l'ombre ; sinon le signaler, ne pas
     inventer un malus).
   - `poser_pot` / `deplacer_pot` doivent pouvoir viser l'intérieur.
2. **Geste `repiquer`** (pot → pleine terre) : la plante quitte le conteneur et est
   placée au plot visé avec ses gènes, son âge, sa structure, sa vitalité. **Choc de
   repiquage** : croissance ralentie quelques semaines, plus fort si les racines
   étaient à l'étroit (volume du pot / taille de la plante) — par un état de la plante
   lu par la croissance (patron de la repousse après taille, `sim/growth/` /
   `instance.py`), pas un bonus/malus de vitalité arbitraire. Le pot reste, vidé.
   - Câbler partout comme les gestes de pots : coût (`couts.py`), déblocage (même
     condition que `planter_conteneur`), famille et palette, pont
     (`tools/simserver`, commande d'action + snapshot), automate pas encore (⑤).
   - Voix : une note de carnet au premier repiquage (et au premier choc visible),
     concept existant le plus proche (vérifier `sim/concept_corpus.py`).
3. **Monde `full`** : à l'ouverture, quelques pots de tendres (tomate, basilic,
   poivron) en plants DANS la maison (fabrique du ③).
4. Tests ciblés : pot intérieur ne gèle pas une nuit à −3 °C ; reçoit moins de lumière ;
   `repiquer` déplace la plante (même id/gènes), vide le pot, applique le choc ; refus
   propre si le plot est invalide ou le pot vide.

## Golden
**INTACT** (gestes event-driven, absents du smoke). Le pont n'est pas vu par le golden :
comparer un snapshot JSON du pont avant/après (seules des clés ajoutées) et bumper la
version du protocole (`tools/simserver/version.py`).

## Ne PAS faire
- Créer une serre ou une structure neuve ; rendre la maison chauffée pour les plantes
  au sol ; toucher à la vue C# (c'est le ⑥).

## F5
Au ⑥.
