# ② Atelier, courrier et observations : poser les marqueurs

**Lire avant** : `CLAUDE.md`, `00_etat.md`, le doc de conception §3.2-§3.3, et le
kickoff ① (pour les noms de marqueurs réellement gravés).
**Nature** : Python + pont, hors tick. **Golden : INTACT**.

## Objectif
Rendre praticables les portes lues par ① : outils à l'Atelier, lettres qui
enseignent, observations du jardin.

## État du code (vérifié le 2026-11-12)
- `sim/outils.py` : registre `OUTILS` (clé → `marqueur`, `cout_vigueur`, `offre`),
  `acquerir_outil` pose le marqueur puis `evaluer_deblocages`. Registre `MATERIAUX`
  (botte de paille → stock de mulch).
- `tools/simserver/voix.py::cmd_atelier` sérialise les outils ; `possede` n'est
  calculé que pour le sécateur (`False` en dur pour les autres) : à corriger avec
  `outils._possede`.
- `sim/quetes.py::_verser_recompense` (tags `graine`, `vigueur`, `maitrise`, `page`,
  `vivace`, `structure`) ; `_offrir_structure` pose un bac sans marquer `poser_bac`.
  Lettres dans `sim/quetes_corpus.py` (9 lettres ; voisins Marcel, Léa, Amélie,
  Bertrand, Gaston, Odette). `sim/quetes.py` n'importe pas `sim.actions`.
- `tools/simserver/maitrise_pont.py::_observer` lit le journal du tick après chaque
  semaine (au-dessus du tick). `sim/zoochorie.py` écrit une ligne
  « 🐦 Merle : … » quand le merle prend des fruits.
- Grimpantes : `sim/grimpe.py`, `sim/growth/tige_libre.py` (tige qui pousse sans
  appui). Survol d'une espèce : `maitrise_pont.observer_espece`.
- Voix : fiches d'outils dans `sim/outil_corpus.py`, types dans
  `sim/encyclopedie_types.py`.

## À faire
1. **Outils neufs** dans `OUTILS` (coûts = placeholders de calibrage F5, modérés,
   payables sur la Vigueur de base 100) : `broyeur` (`posseder_broyeur`), `pots`
   (`posseder_pots`), `tuteurs` (`posseder_tuteurs`), `greffoir`
   (`posseder_greffoir`), `voile` (`posseder_voile`). Chaque outil reçoit sa fiche
   dans `sim/outil_corpus.py` si elle manque (un outil sans voix est muet).
   `cmd_atelier` : `possede` vrai pour tout outil dont le marqueur est posé.
2. **Récompense `("technique", objet)`** dans `_verser_recompense` : découvre la
   technique puis fait réévaluer les déblocages. Intention : la lettre enseigne.
   Le sens des imports est à vérifier avant de placer l'appel à
   `evaluer_deblocages` (import local dans la fonction si un import de tête créait
   un cycle ; le driver `tools/simserver/courrier.py::avancer_quetes` est une autre
   place possible pour la réévaluation).
   Les lettres de greffe et d'essaim posent en plus le marqueur d'événement lu par
   ① (`lettre_greffe`, `lettre_essaim`) ; choisir une forme de récompense qui porte
   les deux, sans dupliquer la logique.
3. **Posséder vaut avoir posé** : `_offrir_structure` marque l'action de pose
   correspondante (`poser_bac` pour un bac) pour le joueur courant, puis
   réévaluation. La lettre d'Odette ouvre ainsi `composter`, `retourner`, `epandre`.
4. **Lettres neuves** (4) dans `sim/quetes_corpus.py`, dans la voix des voisins
   existants, chacune avec un désir à combler (condition déjà supportée par la
   grammaire des quêtes) et un déclencheur de saison : palissage (Gaston et ses
   haricots à rames), greffe (un voisin arboriculteur ; ajouter un donneur si aucun
   ne convient), apiculture (essaim offert : la récompense enseigne la technique,
   elle ne pose PAS de ruche), culture en pot. Français accentué, ton des lettres
   existantes, pas de consigne de jeu.
5. **Observations** :
   - `merle_seme` : dans `_observer`, à la lecture d'une ligne de dispersion du
     merle, `marquer_evenement` puis réévaluation.
   - `grimpante_sans_appui` : quand le joueur survole une grimpante sans support à
     portée (ou lecture de l'état post-tick, au choix du tronçon selon ce que le
     code expose déjà), poser le marqueur. Ne rien ajouter au tick.
6. **Test d'atteignabilité** : retirer la liste « promis par ② » posée au ① ; le
   test lit désormais les vrais marqueurs d'`OUTILS` et vérifie que chaque événement
   cité par une porte a un poseur (recherche du nom dans le code, ou registre
   explicite des marqueurs posables).
7. Tests : étendre `tests/test_quetes.py` et `tests/test_acquisition_outils.py`
   (lettre → technique → geste ouvert ; bac offert → composter ouvert ; achat de
   tuteurs → `poser_tuteur` ouvert → après pose, `poser_perchoir` et `palisser`
   ouverts : c'est la fermeture de D133).

## Vérification
`python3 -m tests.test_golden` inchangé ; suites quêtes, outils, déblocage,
atteignabilité vertes.

## À ne pas faire
- Aucune lettre ne donne un geste sans désir comblé.
- Pas de bonus sur une plante (#2). Pas d'aléa (#3).
- Ne pas toucher `sim/zoochorie.py` ni le tick : on lit son journal.
