# ⑦ Profil `semiologique` — OPTIONNEL, hors chaîne

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md` (§9). Prérequis : ①→⑤ tiennent.
> **OPTIONNEL** : à n'implémenter que si les tronçons ①-⑤ ont tenu et que Nico le
> demande. Ne PAS le lancer par défaut en `/sprint-auto`.

## Objectif
Implémenter le second profil de perception, **`semiologique`** : l'automate ne lit
QUE ce qu'un joueur voit à l'écran (pas de valeur continue). L'écart de performance
entre `omniscient` et `semiologique` **mesure la qualité de la sémiologie du jeu** —
un défaut de design #5 rendu chiffrable pour la première fois.

## Préalable INDISPENSABLE — recenser les signes émis
Avant de coder la perception, **recenser les signes diégétiques réellement émis** par
le moteur (c'est le vrai coût de ce tronçon) :
- `plant.etat` discrétisé {sain/affaibli/malade/mort} (`plants/base/instance.py`) ;
- les **signes** diégétiques (chercher les émetteurs : `ombre`, `acclimatation`,
  `flétrissure`, signes météo… — grep `signe` dans `sim/`, `fields/`) ;
- les **notifications** et marqueurs du carnet exposés au joueur.
Produire d'abord une **note de recensement** dans `00_etat.md` (ce que le joueur
PEUT voir), puis mapper chaque facteur limitant (§5) sur les signes qui le trahissent.

## Fichiers à toucher
- `tools/jardinier_auto/perception.py` — implémenter le profil `semiologique`
  (remplace le stub `NotImplementedError` du ①) : ne lit que `plant.etat`, les signes
  et notifications recensés. AUCUNE lecture de `vitalite` continue, `qi_local`,
  champs `EcoFields` bruts.
- `diagnostic.py` — un diagnostic dérivé des seuls signes (plus grossier, forcément).

## Modèle / points précis
- Le diagnostic sémiologique est **volontairement plus pauvre** : si un facteur
  limitant n'a **aucun signe visible**, l'automate ne peut PAS le diagnostiquer → il
  n'agit pas. C'est exactement le signal recherché : **un facteur invisible est un
  défaut de sémiologie** (à consigner, cf. impasses §7 — nouvelle cause
  `facteur_invisible`).
- Comparer au banc ⑤ : rejouer le même monde en `omniscient` puis `semiologique`,
  mesurer l'écart (survie des cultivées, rendement, N impasses). **L'écart chiffre la
  qualité de la sémiologie.**

## Golden attendu
**INCHANGÉ.** Toujours hors tick.

## Ce qu'il NE faut PAS faire
- NE PAS ajouter de signe au moteur pour « boucher un trou » — un facteur invisible
  est un RÉSULTAT à remonter (défaut #5 chiffré), pas à masquer.
- NE PAS toucher le moteur. NE PAS lancer `test_epaisseur_500ans`.

## Vérif de sortie
Note de recensement des signes dans `00_etat.md` + banc ⑤ étendu comparant
omniscient vs semiologique + golden intact. Consigner l'écart mesuré (le chiffre de
qualité sémiologique).
