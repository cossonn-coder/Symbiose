# ②ter Des arbres vraiment adultes — pré-croissance, ombre par espèce, flux de branches

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (§②bis : mécanique en place, 0 branche tombée
sur `full` 104 sem.), dette **D105** (`DETTE.md`), conception §2.
**Golden** : re-figeage AUTORISÉ uniquement si la tolérance à l'ombre du pommier (seul
ligneux du smoke) change en B — dérive localisée, expliquée, hash consigné. La pré-croissance
(A) ne touche PAS la config `smoke`.
**Mandat Nico (2026-10-22)** : « avancer de la manière qui favorise le résultat » = du bois
qui tombe réellement en continu pour nourrir les champignons du bois (③④).

## Constat (②bis)
- `full` ne contient qu'un ligneux, le pommier pré-vieilli : `age_years = maturity_years`
  (`tools/simserver/commands.py` config `full`) SANS structure (D105 : 1 segment, ~22 cm).
  Une pousse ne s'élague pas → 0 branche. Seul le bois initial nourrit (fond de 60 %/an).
- Tous les arbres ont `shade_tolerance_base` ≈ 0,9 → bouleau et hêtre identiques face à
  l'ombre ; la cladoptose (`sim/growth/cladoptose.py`) ne peut pas les distinguer.
- Seuil 0,18 → 0-2 branches/an ; à 0,30 chêne/hêtre perdent 32 → 12 segments (élagage
  massif) → il manque un BORNAGE du rythme, pas seulement un seuil.

## A. Pré-croissance des ligneux pré-vieillis (ferme D105)
- À l'init `full`/`propre`, pour chaque plante pré-vieillie, dérouler la morphogénèse sur
  son âge (`grow_plant` × semaines, fonction pure, déterministe, HORS tick) pour qu'elle
  ait la structure d'un arbre de son âge. Lumière : `light_field=None` (arbre isolé) ou
  mieux si disponible à l'init. Coût d'init raisonnable (mesurer, < quelques secondes).
- Vérifier : rendu/footprint cohérents (`update_footprint`), nouaison toujours OK
  (`test_pommier_fruite`), le pont sérialise la structure (snapshot plus gros : mesurer).
- Mettre à jour D105 dans `DETTE.md` (close ou réduite — `vieillir()` des bancs F5
  `verger_floraison`/`floraison_saisons` : le corriger aussi si c'est le même helper).

## B. Tolérance à l'ombre par espèce (donnée)
- Écologie : héliophiles stricts (bouleau, cerisier, pommier, figuier, noyer) bas ;
  intermédiaires (chêne) ; sciaphiles (hêtre, charme, if/sapin) hauts. Poser des valeurs
  différenciées sur l'échelle EXISTANTE de `shade_tolerance_base` (lire ses autres
  lecteurs : étiolement, `shade_stress_damage`… avant de choisir les valeurs, pour ne pas
  tuer d'ombre les héliophiles du jeu). Valeurs consignées dans `00_etat.md`.

## C. Flux de branches réglé et borné
- Recaler la cladoptose sur les arbres ADULTES de A : cible [ordre de grandeur] 2-6
  branches/an pour un arbre adulte, plus chez l'héliophile, moins chez le sciaphile.
- BORNER le rythme : au plus un sous-arbre par arbre par fenêtre (ex. quelques semaines),
  jamais une couronne rasée d'un coup ; le leader et les charpentières éclairées protégés.
- La casse tempête/neige garde son propre rythme (événementiel).

## Mesure & vérif
- `mesures/bois_mort.py` : graine 1521550718, `full`, 104 sem. [n=1 run] : branches/an
  par cause et par arbre, plots avec bois > 0 aux sem. 0/52/104, masse de bois, mycélium
  max/médian. Succès = le bois au sol ne tend PAS vers 0 sur 2 ans (flux ≳ décomposition).
- Tests : étendre `test_bois_mort` (pré-croissance déterministe ; arbre pré-vieilli a
  ≫ 1 segment ; rythme borné). `test_pommier_fruite`, `test_croissance`, `test_sim_server`.
- **Perf** : tick ≤ +5 % vs après ②bis (un arbre adulte a plus de segments) ; D114 ouverte,
  ne pas la résorber ici, signaler si dépassé.

## Ne PAS faire
Pas de C#. Pas de champignon. Pas d'ajout d'espèce ni de plante dans `full` (composition
du monde = décision de Nico). Pas de RNG vivant. Pas de test 500 ans.
