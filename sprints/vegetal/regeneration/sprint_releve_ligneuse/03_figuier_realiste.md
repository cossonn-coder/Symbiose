# ③ Figuier réaliste — pas de graine sans blastophage, des rejets de souche

À lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/regeneration/conception_releve_ligneuse.md` §2 (figuier), §3.3.

## Objectif
En Normandie le figuier ne fait pas de graine fertile (son pollinisateur, le
blastophage, n'y passe pas l'hiver) ; il se propage par rejets. Coder la
fertilité comme une **condition climatique** (évolutive vers d'autres climats).

## Modèle
1. **Donnée d'espèce** (`data/code/plants/perennials/fruitiers.py`, classe `Fig`) :
   un attribut déclarant le pollinisateur obligatoire et son enveloppe, p. ex.
   `graine_si_hiver_min_c = 7.0` (mois le plus froid minimal, °C) avec commentaire
   « blastophage, *Blastophaga psenes*, aire méditerranéenne [ordre de grandeur] ».
   Défaut `None` sur `PlantBase` (`plants/base/familles.py`, près des attributs
   `clonal_*`) = aucune condition. Nom exact au choix du tronçon, en français.
2. **Prédicat** dans `data/code/sim/reproduction.py` : `graine_fertile(cls) -> bool`
   = condition absente OU `T_MOY − T_AMP` (normales de `sim/weather.py`, mois le
   plus froid) ≥ seuil. Couches : `sim.reproduction` → `sim.weather` = même couche,
   vérifier l'absence de cycle d'import (`sim/weather.py` n'importe pas
   `sim.reproduction`). Exporter dans `sim/__init__.py` comme ses voisins.
3. **Gates** (là seulement) :
   - `sim/engine/mortalite.py` `_reproduction` : un parent dont `graine_fertile`
     est faux est sauté (ni `add_species`, ni recrue directe).
   - `sim/engine/boucle.py` (~l.529, pont récolte → banque-joueur) : pas de `Seed`
     si `graine_fertile` est faux.
   - **NE PAS** modifier `is_seed_bearing` : il gate aussi la floraison
     (`sim/engine/floraison.py`) et la paternité (`find_father`). Les figues
     continuent de nouer et d'être mangées.
4. **Rejets** : `Fig.clonal_mode = "drageon"`, `clonal_radius_cm` ~100 [choix :
   rejets à 1 m du tronc]. Dans `sim/clonal.py`, `_mature()` lit le dernier stade :
   pour un arbre (`hasattr(cls, "age_curve")`) lire `plant.age_years >=
   cls.maturity_years` (le figuier n'a qu'un stade « arbre » → sinon mûr dès la
   naissance). Les non-arbres (framboisier `drageon`, trèfle…) inchangés.
   Le ramet copie déjà gènes et `form_seed`.
5. **Voix** (règle « toute plante = ses voix ») :
   - Encyclopédie `data/code/sim/encyclopedie_corpus/ligneux.py`, entrée
     `"figuier"` : niveau 2 ou 3, une phrase sur la figue sans graine fertile hors
     du pays du blastophage et la propagation par rejets.
   - Carnet : si une cause/concept existe pour les ramets (`grep -n "Ramet" sim/carnet.py sim/evenements.py`),
     vérifier qu'un rejet de figuier est lu ; sinon ne rien inventer, le consigner
     dans `00_etat.md`.

## Golden
**INCHANGÉ** attendu : pas de figuier dans le smoke ; le `_mature` d'arbre ne
touche que les espèces clonales à `age_curve` (aucune avant ce tronçon). S'il
bouge : STOP.

## Tests
Test neuf (`tests/test_figuier_realiste.py`) : `graine_fertile(Fig)` faux sous les
normales actuelles, vrai si l'on monkeypatche `T_MOY`/`T_AMP` vers un climat doux ;
`graine_fertile(AppleTree)` vrai ; un figuier mûr ne dépose rien en banque-sol ;
un figuier de 1 an n'émet pas de ramet, un figuier mûr en émet un (déterministe,
plusieurs semaines). `tests.test_golden`, suites clonales
(`grep -l "clonal\|ramet" tests/test_*.py`), encyclopédie. **Jamais `test_epaisseur_500ans`.**

## Ne PAS faire
- Créer un acteur blastophage (faune) : simple condition climatique.
- Rendre le climat paramétrable (hors sujet) : on lit les constantes existantes.
