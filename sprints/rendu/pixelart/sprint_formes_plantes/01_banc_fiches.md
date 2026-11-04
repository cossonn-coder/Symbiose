# ① Banc, mesure des silhouettes, fiches — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §1, §4.1, §4.2, §6 ; `docs/vegetal/croissance/fiches_arbres.md` (modèle) ; `data/code/bancs/palette_gestes.py` (`_adulte`) ; `tools/mesure_da.py`.

## Objectif

Voir et chiffrer l'état actuel des 40 espèces, et écrire ce que chacune devrait être.

## À faire

1. **Banc `planche_especes`** dans `data/code/bancs/`, ajouté au registre `BANCS` : les 40 espèces de `PLANT_CATALOGUE`, un pied par emplacement, adultes (patron `_adulte`), assez espacés pour que les sprites ne se touchent pas à ×1 et ×4 (les grandes au nord, tri Y). Départ en été (`BANC_WEEK_DEPART`). Maison et lisière ne doivent pas masquer les pieds. Composition pure, aucune mécanique. Exposer la table espèce → position (ex. constante du module), pour cadrer chaque capture.
2. **Fleurs et fruits sur le banc** : ils doivent être visibles sur une capture. Vérifier ce qui s'allume sur un banc court ; sinon capter à une autre semaine ou forcer dans la fabrique, patron `bancs/mesure_floraison.py`. Consigner le procédé.
3. **`tools/mesure_silhouettes.py`**, outil de dépôt sans dépendance, réutilisant `tools/da_image.py` et le masque de `mesure_da --ref` : un masque par espèce, gabarit, proportions, teinte moyenne, recouvrement normalisé par paires. Sortie : tableau des paires, liste des paires confondues (conception §6). Déterministe.
4. **Mesure « avant »** à ×1 et ×4, `mesures/avant.md` (PNG non committés) : paires confondues, hauteur dessinée / `height_cm` par espèce. **Recalibrer** si besoin les seuils `[choix]` de la conception : ils doivent signaler l'effet générique ici, et rester atteignables. Reporter tout changement dans la conception.
5. **Lire les PNG** de quelques espèces et le dire dans le bilan : la mesure concorde-t-elle avec l'œil ?
6. **`docs/vegetal/croissance/fiches_herbacees.md`** : les 36 espèces de conception §4.2 (les 33 de ports + tomate, lierre, jasmin), plus l'ortie et la lupuline explicitement renvoyées par D126. Format conception §4.1. Pour les couples proches (blé/seigle, thym/lavande, moutarde/bourse-à-pasteur, menthe/basilic, fraisier/violette) dire ce qui les distingue. Échelle : le monde est à l'échelle réelle, 1 plot = 50 cm. Si une espèce ne tient pas dans son port, le signaler.
7. `python3 -m tests.test_golden` (depuis `data/code/`), suite `tests/simserver` si le registre de bancs y est listé.

## Golden

**INTACT** : le banc n'est jamais monté pour le golden.

## NE PAS

Modifier le rendu. Modifier une espèce du catalogue. Lancer `tests/test_epaisseur_500ans.py`.
