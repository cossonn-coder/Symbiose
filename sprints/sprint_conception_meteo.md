# Sprint conception — Météo / Climat + signes diégétiques

> **Kickoff autosuffisant.** Démarre à froid : lis ce fichier, puis les
> sources ci-dessous. Pas de contexte préalable nécessaire.

## Nature du sprint

- **Conception seule. AUCUN code.** Livrable = un **document de conception
  à étudier** (cf. règle : météo/climat = physique/éco hors expertise directe
  de Nico → produire un doc raisonné, pas une rafale de questions à trancher).
- Petit/moyen → **non découpé** en sous-sprints.
- Couvre la dette **D16** (forecast) et la catégorie **Z2** (signes
  diégétiques) du backlog.

## Avant de commencer

1. Vérifier que git est à jour (`git status` propre).
2. Lire dans `CLAUDE.md` la section **« Gestion des aléas météo »** (modèle
   déjà acté : signes diégétiques, action en deux temps prépa/réaction,
   ~20 % imprévisible sauf transcendant) — c'est le cahier des charges figé,
   ne pas le contredire.
3. Lire **D16** dans `DETTE.md` (décaler le tirage en `forecast` 1-2 semaines
   en avance dans `engine.py` pour alimenter les signes).
4. Survoler les sources de vérité concernées (lecture ciblée, ne pas tout
   charger) :
   - `data/code/fields/noise.py` — fondation déterministe (le climat doit en
     dériver, seed global + hash spatial, philo #3).
   - `data/code/sim/engine.py` — boucle 52 semaines, où s'insère le forecast.
   - `data/code/fields/ecofields.py` — champs `humidite`/`fertilite`/… que la
     météo doit moduler (philo #1/#2 : agir sur le MILIEU, jamais bonus/malus
     direct sur les plantes).

## Périmètre de conception (le doc doit trancher chacun)

1. **Modèle climatique déterministe** — comment générer la météo à partir du
   seed, cohérent avec `noise.py`. Climat Normandie ~49°N (4 saisons,
   tempérées, océaniques). Catalogue des événements : gel/gelée tardive,
   canicule, sécheresse, tempête/vent fort, grêle, pluie prolongée,
   redoux… (fréquences, saisonnalité, intensité).
2. **Couplage aux champs écologiques** — chaque type d'événement agit sur
   quels champs (`humidite`, température implicite, etc.) et comment. Jamais
   sur la plante directement : flux → contrainte → réponse émergente.
3. **Forecast (D16)** — mécanique du tirage décalé 1-2 semaines, structure de
   donnée, comment il reste déterministe et reproductible.
4. **Signes diégétiques (Z2)** — table signe → événement (oiseaux, ciel,
   anneau lunaire, brume, sol qui craquelle…), fiabilité croissante avec la
   maîtrise du concept « météo/climat », et la part **~20 % imprévisible**
   tant qu'on n'est pas transcendant.
5. **Palier de maîtrise « météo/climat »** — ce que chaque palier débloque
   (interprétation explicite des signes au seuil ; tout prévisible au
   transcendant).
6. **Articulation Vigueur** — gestes de **préparation** (temps figé, Vigueur
   modérée : paillage, voiles, brise-vent) vs **réaction** (temps réel,
   Vigueur élevée : arrosage ciblé, sauver une plante). Lister les gestes,
   pas les chiffrer finement (calibrage post-test).

## Garde-fous

- Français systématique, pédagogie explicite (Nico vient du C/Python embarqué).
- **Max 3 questions à la fois.** Préférer un doc argumenté à des questions
  ouvertes sur le domaine bio/physique.
- Ne rien implémenter. Le portage/implémentation est un sprint ultérieur
  (qui, lui, sera découpé en sous-sprints `sprint_meteo_impl/00_etat.md` +
  `0N_*.md`, et devra préserver `tests/test_golden.py`).

## En fin de sprint

- Écrire le doc de conception (proposer l'emplacement : `journal.md` +
  éventuel doc dédié sous `sprints/` ou `data/code/`).
- Mettre à jour `journal.md` (décisions du sprint).
- Mettre à jour `DETTE.md` (D16 → conçu) et `BACKLOG.md` (sprint suivant =
  implémentation météo).
