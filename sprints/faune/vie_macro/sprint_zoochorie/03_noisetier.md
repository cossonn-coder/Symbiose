# ③ Le noisetier — espèce neuve et ses cinq voix (D42)

Lire d'abord : `CLAUDE.md` (règles « le catalogue grandit avec les idées » et « toute
plante ajoutée = toutes ses voix »), `00_etat.md`, doc
`docs/faune/vie_macro/conception_zoochorie.md` §4.4,
`docs/narration/voix/conception_voix_narratives.md` (les 5 dispositifs). ② fait :
prédicat `recrue_par_fruits`, glandée (`glandee_periode_ans`, `facteur_glandee`).

## Objectif
Ajouter *Corylus avellana* (noisetier, coudrier), l'espèce emblématique des caches
d'écureuil et de mulot, fruitier unifié dès sa naissance.

## Fiche moteur (ordres de grandeur, à commenter comme les autres ligneux)
- Classe `HazelTree(PerennialWoody)` — fichier : avec les forestiers
  (`plants/perennials/forestiers.py`) si la taille LDC le permet
  (`tools/compte_ldc.py`, bande ≤ 300/400), sinon fichier neuf
  `plants/perennials/arbustes.py` (une responsabilité : arbustes de haie).
- Famille Betulaceae, genre *Corylus*. Arbuste en cépée 4-6 m, couronne ~2-3 m de
  rayon ; `rejet_souche` fort (≈ 0,9 : se recèpe, taillis classique) ; longévité
  ~80 ans (souche bien plus) ; `maturity_years` ≈ 8 ; `shade_tolerance` ≈ 1,05
  (semi-sciaphile, sous-bois clair et lisière).
- `pollination_mode = "wind"`, chatons **précoces** : floraison fin janvier-février
  (`bloom_forcing_gdd` bas — lire comment les autres espèces fixent leur date,
  `sim/engine/floraison.py`, et viser février). `nectar = 0`. Si le moteur a un
  canal « pollen offert aux butineurs », le brancher (pollen précoce = T6 de la
  complétude) ; sinon noter en dette, ne pas l'inventer.
- `fruitier = True`, noisettes : `fruits_par_site`, `fruit_masse`,
  `fruit_semaines_maturation` (mûres en septembre) ; `graine_viabilite_ans` 1 ;
  `glandee_periode_ans` ≈ 2.
- Croissance procédurale : port en cépée (plusieurs tiges depuis la souche) si un
  `port_archetype` existant l'approche ; sinon le plus proche, commenté. Pas de
  nouveau mécanisme de croissance.
- Enregistrement : `plants/perennials/__init__.py`, `plants/catalogue.py`
  (clé `"noisetier"`), et partout où le grep de `BeechTree` montre une liste
  d'espèces qui doit le connaître (bancs `houppiers`, `croissance` si pertinent).

## Les cinq voix
1. **Encyclopédie** (`sim/encyclopedie_corpus/ligneux.py`) : fiche 3 niveaux — voir
   (cépée, chatons jaunes en plein hiver) ; cycle (fleurs femelles minuscules
   rouges, vent, noisettes en septembre) ; effets (nourrit écureuil, mulot, geai ;
   les noisettes oubliées font les haies ; taillis recépé tous les 7-10 ans).
2. **Carnet** (`sim/carnet.py`, `CONCEPT_DE`) : rattacher les événements du
   noisetier aux concepts existants (reproduction, rejet de souche) ; le concept
   neuf `dispersion` sera posé au ⑦ — ne pas l'anticiper ici.
3. **Pages secrètes** (`sim/pages_corpus.py`, optionnel) : la baguette de coudrier
   du sourcier, savoir paysan — une page courte.
4. **Magazine** (`sim/magazine.py`) : rattachement famille/offre selon §2.4 de la
   conception des voix (regarder comment chêne/hêtre y figurent).
5. **Événements** (`sim/evenements.py`) : les marqueurs de cycle de vie existants
   (floraison, nouaison, chute) doivent le couvrir ; vérifier par un test que les
   chatons et la chute des noisettes produisent bien un événement.
Signes (`sim/signes_corpus.py`) et voix des êtres (`sim/voix_etres_corpus.py`) :
ajouter son entrée si ces tables sont indexées par espèce.

## Ne PAS faire
- Pas de disperseur (④-⑥), pas de rendu C# (⑧).
- Ne pas le placer dans le golden ni dans `full` (golden neutre).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Tests
`tests/test_noisetier.py` : fleurit en février (semaine dans la fenêtre), noue par
le vent avec un second pied à portée, dépose des grains `chute` à l'automne ; voix :
encyclopédie présente aux 3 niveaux, au moins un événement de cycle. Lancer
`test_encyclopedie`, `test_carnet`, `test_evenements`, `test_croissance`.

## Golden
`a10b7225…` **INCHANGÉ** attendu.

## Perf
Nulle (espèce absente des mondes mesurés).

## F5
Aucun (vue au ⑧).
