# Tronçon 01 — Gestes manuels `pincer` + `arracher`

> Tu démarres À FROID. Lis d'abord `CLAUDE.md`, puis `00_etat.md` (état du sprint),
> puis `docs/joueur/outils/conception_acquisition_outils.md` §A. Ce kickoff suffit à
> implémenter le tronçon. Lancement moteur depuis `data/code/`.

## Objectif
Ajouter deux gestes structurels de BASE (sans outil), complétant le gradient
`pincer < arracher < couper/tailler` : à mains nues on peut déjà agir sur la
structure. Répond au F5 « pas d'option couper » (un geste d'emblée), et pose le
contraste que le sécateur (tronçon 02) viendra raffiner.

## Modèle (cf. §A du doc de conception)
- **`pincer`** — régime DOUX du seam : `atteindre_segment(plant, seg_id,
  intensite=<valeur < COUPE_NETTE>)` (ex. 0.5). Baisse l'auxine locale → aucun
  segment retiré, débourrement ÉMERGENT au `grow_plant` suivant (philo #2). **Rien
  déposé au sol.** Coût FAIBLE.
- **`arracher`** — régime NET : `atteindre_segment(..., intensite=1.0)` (écimage +
  sous-arbre, comme `tailler`) → dépose la masse `bois` retirée en litière
  (`eco.deposer_litiere(*plant.position, "bois", masse)`, MÊME calcul que `tailler`
  via `BOIS_PAR_CM`) **ET** appelle `plant.erode(VITALITE_STEP)` — la déchirure
  manuelle stresse la plante (différenciateur main/outil). Coût ÉLEVÉ (perturbateur,
  philo #1). Le gain Vigueur d'organe : **pas de gain** (on jette, on ne récupère
  pas proprement — contraste avec `tailler` qui rend un peu de Vigueur).

## Fichiers à toucher
1. `sim/actions/gestes.py` — façades `pincer` et `arracher`, sur le modèle de
   `tailler` (`gestes.py:260`) : `spend` le coût EN AMONT (refus si Vigueur
   insuffisante, rien écrit), puis seam, puis (arracher) dépôt litière + `erode`.
   Sélecteur de segment : réutilise `_segment_cible`/`segment_id` comme `tailler`.
   Constantes `VITALITE_STEP`, `BOIS_PAR_CM`, `COUPE_NETTE` : déjà importées dans
   ce module (cf. `ecraser_plante`/`tailler`).
2. `sim/actions/couts.py` — `COUTS["pincer"]=FAIBLE`, `COUTS["arracher"]=ELEVE` ;
   `OBJETS_TOUCHES["pincer"]=("taille",)`, `OBJETS_TOUCHES["arracher"]=("taille",)`
   (famille taille, **second terme absent = pas d'outil** : la maîtrise taille
   atténue le coût, aucun outil requis).
3. `sim/actions/palette.py` — `"pincer":"plante"`, `"arracher":"plante"`.
4. `sim/actions/__init__.py` — exporter `pincer`, `arracher` dans l'API publique
   (liste `__all__` + import), comme `tailler`.
5. `tools/simserver/actions.py` — dispatch des verbes `pincer` / `arracher`
   (patron `couper`, `actions.py:176`) : résolution plante par position, `bilan`,
   messages diégétiques (« pincé : {nom} », « branche arrachée à la main :
   {nom} »). **Bump protocole** au numéro libre après 0.5.30 + entrée `version.py`.

## Golden
**INCHANGÉ.** Ces gestes sont opt-in joueur, hors tick ; le smoke ne les exerce
pas. Lance `python3 -m tests.test_golden` : le hash NE DOIT PAS bouger. S'il bouge,
tu as touché le tick → annule.

## Tests ciblés (ajoute une petite suite, patron des tests d'actions existants)
- `pincer` sur une plante branchée : auxine du segment ciblé baissée, **nombre de
  segments inchangé**, Vigueur débitée du coût FAIBLE.
- `arracher` : sous-arbre retiré (segments < avant), litière `bois` déposée au plot,
  **vitalité érodée** (`plant.vitalite` a baissé), Vigueur débitée ÉLEVÉ.
- Refus Vigueur insuffisante : rien écrit (structure + vitalité intactes), aucune
  dépense.

## NE FAIS PAS
- Ne touche PAS `couper`/`tailler`/`bouturer` (déjà bons).
- Ne code AUCUN débourrement explicite (« +N latéraux ») — il ÉMERGE au tick.
- Pas de champ « propreté » : le différenciateur est le seul appel `erode`.
- Pas de re-figeage golden.

## Fin de tronçon
Mets à jour `00_etat.md` §REPRISE (01 fait, prochain = 02) et commit
(`feat(moyens) ① : gestes manuels pincer + arracher — gradient main/outil`).
