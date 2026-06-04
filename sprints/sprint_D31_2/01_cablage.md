# Sprint D31.2 — Câblage écologique de la vie macroscopique (Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico apprend, vient du C/Python
> embarqué, débutant Godot/C#).

## Ce que c'est, en une phrase

D31.1 a créé 4 champs de population **calculés mais lus par rien** (golden
intact). D31.2 **branche ces champs dans la simulation** : ce qu'on voit
(sprites) devient ce qui agit (santé/services). **C'est le re-figeage assumé du
golden** — unique, propre, journalisé, exactement comme le sprint météo.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_VIE_MACRO.md` — **§1** (la décision structurante : la
   dynamique vit DANS le tick, pourquoi le découplage casserait l'apprentissage),
   **§2.2** (chaîne trophique + « le terme `predator` disparaît »), **§7**
   (interfaces dettes, surtout D30 pour les vers), **§8** (périmètre D31.2),
   **§9** (tableau : ce qui re-fige / ce qui ne re-fige pas).
2. `journal.md` — entrée **`2026-06-04 — Sprint impl. D31.1`** (ce qui existe
   déjà, le modèle de tick multiplicatif, le hash golden).
3. `DETTE.md` — **D31** (statut : D31.1 fait), **D30** (structure/compaction du
   sol — non implémentée, c'est pour ça que le câblage des vers est le point
   ouvert ci-dessous).
4. Code : `data/code/fields/population.py` (les champs + `sample_sprites`) ;
   `data/code/sim/effects.py:451` (`herbivory_pressure`, le scalaire à
   remplacer) + **`:487`** (le terme `predator` reconstruit de proxies, à
   retirer du calcul) + `:584` (site d'appel) ; `data/code/sim/reproduction.py:45`
   (`pollinator_reach`) + `:59` (`find_father`).

## Périmètre — les 4 câblages (CONCEPTION_VIE_MACRO.md §8 #2)

Chaque champ cesse d'être décoratif et **nourrit la sim**. La règle d'or : la
santé/les services lisent **la densité locale du champ** (`eco.populations[...]
.at_plot(r, c)`), plus aucun proxy reconstruit.

1. **Herbivorie ← `ravageur`.** Dans `herbivory_pressure` (`effects.py:451`), la
   pression sur la santé doit dériver de `eco.populations["ravageur"].at_plot(r,c)`
   (et non plus de `biomass_local × HERBIVORY_BASE`). C'est le ravageur **visible**
   qui mord.
2. **Prédation ← `auxiliaire`.** Le terme `predator` (`effects.py:487`,
   reconstruit de biodiversité+rondelles+stabilité) **disparaît du calcul** :
   la régulation devient `eco.populations["auxiliaire"].at_plot(r,c)`.
   → **Conserver le code (garde-fou « ne jamais jeter de code »)** : ne pas
   supprimer, **commenter** l'ancien bloc avec une note « SUPPLANTÉ D31.2 —
   conservé pour mémoire », comme le codebase le fait déjà (cf.
   `engine.py` WEATHER_ALEA « Grêle » conservée pour mémoire).
3. **`pollinator_reach` ← `pollinisateur`.** Dans `reproduction.py:45`, le rayon
   de croisement insecte est aujourd'hui modulé par les **rondelles** ; il doit
   l'être par la **densité locale du champ pollinisateur**. ⚠ **Changement
   d'interface** : `pollinator_reach(mother, tile)` n'a pas accès à `eco` →
   threader `eco` jusqu'ici (via `find_father(...)` et le site d'appel dans
   `engine._reproduction`). Garder les rondelles comme **terme-source d'habitat**
   du champ (elles agissent déjà via `_pollinisateur_habitat_grid`), pas comme
   modulateur direct en double.
4. **Aération/structure ← `vers_de_terre`** — **LE POINT OUVERT.** D30
   (structure/compaction du sol) **n'est pas implémentée** ; §7 laisse explicite
   le choix « transiter par `vers_de_terre` ou par un champ `structure_sol`
   dédié — question D30 ouverte ». **Défaut raisonnable proposé** : ne **pas**
   inventer D30 ici. Soit (a) laisser `vers_de_terre` **non câblé** en D31.2 (il
   reste calculé/visible, golden-neutre pour ce volet) et le renvoyer à D30 ;
   soit (b) un couplage **léger et borné** déjà naturel (p.ex. les vers
   accélèrent un poil la minéralisation/décomposition locale). **Décider avec le
   défaut le plus sobre, le signaler dans le compte rendu.** Ne pas se forcer à
   un gros système sol pour cocher la case.

## Hors périmètre (gated)

- Façades `vigueur_*` + gestes joueur (favoriser/écraser/fourche-bêche) → **D31.3**.
- Gain signé « manger un individu » → **D19**.
- Prédateurs de sommet (oiseaux) → laissés vides.
- Le **rendu Godot** des sprites (D31.1 a livré le contrat Python `sample_sprites`).
- Calibrage fin (intensité du boom-bust, seuils) → post-test.

## Garde-fous (non négociables)

- **RE-FIGEAGE GOLDEN — c'est attendu ici, pas un bug.** Procédure :
  1. **Baseline AVANT de coder** : `python3 -m tests.test_golden` doit afficher
     PASS `ee79dd66…` (l'état D31.1). Note-le.
  2. Câble. Le golden **VA** diverger → c'est correct (la santé dépend maintenant
     des champs). Quand le comportement te semble bon, **re-fige** :
     `python3 -m tests.test_golden --capture` → nouveau hash.
  3. **Le golden de champ `population_hash.txt` re-fige AUSSI** : maintenant que
     l'herbivorie tue/épargne différemment, le feuillage change → la ressource du
     ravageur change → les densités changent. `python3 -m tests.test_population
     --capture`. **Boucle écologique refermée = les deux hash bougent une fois.**
  4. **Journalise les deux nouveaux hash** dans `journal.md` (entrée dédiée) et
     mets à jour `DETTE.md` D31 (D31.2 fait) + `BACKLOG.md`.
- **Déterminisme préservé.** Lire un champ déterministe ne casse rien ; **aucun
  nouveau RNG**. Si tu gardes des tirages `_hash_noise` pour l'application
  probabiliste de la pression, garde les **mêmes canaux** (ne décale pas les
  flux existants des autres mécaniques — c'est ça qui ferait diverger des
  trajectoires NON voulues, au-delà du re-figeage attendu).
- **Ne jamais jeter/supprimer de code** : `predator` et l'ancien calcul de
  pression sont **commentés** (« SUPPLANTÉ D31.2 »), pas effacés.
- **Règle de couches** : `plants ← fields ← sim ← engine ← main`. Imports
  absolus. Lancement depuis `data/code/`.
- **`main.py` doit toujours tourner.**
- **Un re-figeage UNIQUE.** Tout doit être câblé dans ce tronçon avant de
  re-figer, pour ne pas multiplier les captures.

## Validation comportementale (au-delà du hash)

- `tests/test_auxiliaires.py` compare tuiles attire-auxiliaires vs témoins et
  **compte les dégâts d'herbivorie**. Aujourd'hui : AUX 0 / TÉMOIN ~26. Après
  câblage, la régulation passe par le **champ auxiliaire** : le contraste doit
  **persister** (les auxiliaires réduisent toujours les dégâts), via le nouveau
  chemin. **Mets à jour le test** si ses valeurs changent (garde le test, adapte
  les attentes — ne le supprime pas). C'est la preuve que la boucle
  d'apprentissage « habitat → auxiliaires → moins de ravageurs » fonctionne.
- Vérifie une trace courte : un ravageur qui monte, des auxiliaires qui
  rattrapent, des plantes qui souffrent **là où la densité ravageur est haute**
  (cohérence vu↔agi, §1).

## Ampleur

Un seul tronçon autosuffisant (pas de re-découpage). Si le câblage des vers
(point #4) menace de déborder vers un vrai système sol (D30), **tranche pour
l'option sobre et signale-le** — ne pars pas dans D30.

## À la fin

`DETTE.md` (D31 → D31.2 faite, hash) + `journal.md` (entrée + **deux** nouveaux
hash : golden engine ET population) + `BACKLOG.md`. Puis commit.
