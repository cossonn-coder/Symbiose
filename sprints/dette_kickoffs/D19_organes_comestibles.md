# Dette D19 — Modèle d'organes comestibles (action « manger »)

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. **Conception AVANT code.** Ampleur **moyenne**.
> ⚠️ **À cadrer avec le tronçon Croissance·5** (organes procéduraux) : les deux
> parlent des **mêmes** feuille/fleur/fruit — ne pas modéliser l'organe deux fois.

## Ce que c'est, en une phrase
Donner du **grain** à l'action « manger » : aujourd'hui manger rend de la Vigueur à
la **granularité plante entière** (proxy), répétable à l'infini tant que `vigueur_max`
n'est pas atteinte. On veut : (a) des **organes distincts** feuille/fleur/fruit, (b)
une **déplétion + repousse** (le vrai frein anti-spam), (c) une **valeur nutritive
signée par espèce/organe** (fruit mûr `+`, feuille de bourrache `un peu +`, limace
`−`).

## L'état du moteur aujourd'hui (vérifié)
- `sim/actions.py::manger(game_state, player, plant, eco) -> float` : **coût NUL**,
  **gain ∝ `vigueur_plante(plant)`** (façade read-only `santé × maturité × qi_local
  × gène`), **no-op écologique**, plante laissée vivante. C'est un **proxy** : on
  « mange la plante » abstraitement, pas un organe précis.
- `plants/base.py` : `PlantInstance.organs: list` existe **mais reste vide** (`# tronçon
  5`) ; attribut de classe `organ_site ∈ {"terminal","lateral"}` (où naissent
  fleurs/fruits) **déclaré, pas encore peuplé**.
- `docs/vegetal/croissance/conception_croissance.md` **§H.2** (organes tout procéduraux : bouton → fleur →
  fruit vert → fruit mûr, stades d'organe, palette/saison) et **§D.5** (mise à fruit :
  les organes reproducteurs se forment **selon le profil espèce**, la taille « met à
  fruit » émerge sans `+=`). **C'est là que les organes naissent réellement** — d'où
  le couplage.
- D31.3 a livré le **prérequis « cibler un individu de la vie macro »** : `ecraser`
  est réel (retire un quantum de `ravageur` au plot). Donc « manger un individu »
  (gain négatif sur un nuisible) n'a plus qu'à réutiliser ce ciblage.

## Ce qui est déjà tranché (DETTE.md D19, ne pas re-débattre)
- La **comptabilité Vigueur** du gain est faite (coût NUL, gain ∝ maturité). On ne
  retouche pas la primitive `gain`.
- « Option rigolote, **pas prioritaire** » (Nico, 2026-06-04). Donc : viser un modèle
  **simple et émergent**, pas un système nutritionnel complet.
- Le **signe** de « manger un individu de la vie macro » : on mange **un individu**,
  **pas la population** (limace = `−`, etc.).

## 🔵 Choix de design à trancher
### Choix 1 — Où vit l'organe consommable ?
- **(A) ⭐ Réutiliser `inst.organs`** peuplé par le tronçon Croissance·5 : un organe
  = `{type, stade, position, mûri}`. Manger en **retire un** (déplétion réelle) ; il
  **repousse** au fil des ticks de croissance (le moteur en génère de nouveaux).
  **Pour** : un seul modèle d'organe pour le rendu (t5) ET la consommation (D19),
  déplétion/repousse **émergentes** de la croissance, zéro variable neuve. **Contre** :
  D19 **dépend** de t5 (ne peut finir avant que les organes existent vraiment).
- **(B) Compteur abstrait par plante** `organes_dispo: {feuille:n, fleur:n, fruit:n}`
  qui se reconstitue à un taux saisonnier, **indépendant** de la structure. **Pour** :
  livrable tout de suite, sans attendre t5. **Contre** : un **2ᵉ** modèle d'organe à
  réconcilier avec t5 plus tard (dette dans la dette).

> Reco : **(A)** si tu fais D19 **pendant/après** Croissance·5 (le cas normal vu
> l'ordre du backlog) ; **(B)** seulement si tu veux jouer avec « manger » **avant**
> t5. Le couplage est la vraie raison d'avoir mis ce ⚠️ en tête.

### Choix 2 — Granularité de la déplétion/repousse (le frein anti-spam)
La déplétion est **le** mécanisme qui empêche le spam de Vigueur. Question : à quelle
vitesse un organe mangé se reconstitue ?
- **(A) ⭐ Par cycle phénologique** : un fruit mangé ne revient qu'à la **prochaine
  fructification** (saisons). Frein fort, écologiquement vrai, pousse à diversifier
  les sources (philo : récompense la diversité). Les **feuilles** repoussent plus
  vite que les **fruits**.
- **(B) Taux fixe par semaine** : repousse linéaire, plus prévisible, moins fidèle.

> Reco : **(A)** — c'est exactement le « vrai frein » que DETTE.md décrit. Le signe
> du gameplay : on ne vit pas en grignotant un seul plant, on entretient un jardin.

### Choix 3 — Table de valeur nutritive signée
Le **signe et l'ampleur** du gain dépendent de *ce* qu'on mange. Proposition de
modèle **data-driven minimal** (à poser sur `PlantBase`/catalogue, comme les gènes) :
`nutrition: {feuille: x, fleur: y, fruit: z}` (réels signés), défaut sobre par
famille. Côté vie macro : `nutrition` sur la guilde (`ravageur: −`, etc.).
Le gain final = `base_organe × maturité_organe × nutrition_espèce`.
- **À trancher** : tables par **espèce** (riche, beaucoup de data) vs par **famille**
  (sobre, défauts hérités, surchargeable). Reco : **par famille avec override
  espèce** — calque exact du patron `SOIL_SIGNATURE`/gènes déjà en place.

## Périmètre (sous Choix 1=A, le cas couplé t5)
1. **Conception** : section dans `docs/vegetal/croissance/conception_croissance.md` §H.2 (ou doc dédié)
   actant : organe consommable = entrée de `inst.organs` ; déplétion = retrait ;
   repousse = régénération par la croissance ; table `nutrition` data-driven.
2. **Impl.** : `manger` prend une **cible organe** (depuis le clic Godot plus tard ;
   en test/engine, sélecteur déterministe comme `tailler`) ; retire l'organe ; gain
   = `f(type, stade, nutrition)`. Variante `manger_individu(eco, r, c)` qui retire un
   quantum de population macro et rend un gain **signé** (réutilise le ciblage
   `ecraser`).
3. **Golden** : `manger` est **event-driven hors tick** → **golden écolo INTACT**.
   Étendre `tests/test_vigueur.py` (déplétion : 2ᵉ « manger » du même organe rend
   moins/rien jusqu'à repousse ; gain signé sur un nuisible).

## Hors périmètre
Le **rendu** des organes (= tronçon Croissance·5). L'équilibrage fin des valeurs
nutritives (post-test). Portage C# (D24). Toute mécanique de « faim » du joueur (le
jeu n'en a pas — manger = source de Vigueur, pas survie).

## Vérification
```
cd data/code
python3 -m tests.test_vigueur   # déplétion + repousse + gain signé — passe
python3 -m tests.test_golden    # INCHANGÉ — manger est hors tick
python3 -m tests.test_croissance # si Choix 1=A : organes peuplés cohérents
python3 main.py
```
Critère dur : manger **épuise** un organe précis qui **repousse** au rythme du
cycle, le gain **dépend de l'espèce/organe** (signé), et **aucun golden de tick ne
bouge**. MAJ `DETTE.md` D19.
