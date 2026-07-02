# ⑥ — Plante carnivore + couplage PUITS → `moustique` + voix

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` §5.3 + §9. Prérequis : ④ fait
> (champ `moustique`) + ③ (marais). **Golden NEUTRE hors smoke.** Tronçon le plus
> DÉLICAT : premier couplage PLANTE → champ FAUNE.

## Objectif
La plante carnivore (`Drosera`, rossolis) : premier **végétal-prédateur**. Elle
**prélève** de la faune de mare (`moustique`) sur ses plots → le flux insectes→azote
l'affranchit de la **faim d'azote** → elle prospère sur tourbe acide pauvre en N.

## Fichiers
- `plants/species/` : `class Drosera` (herbacée, strate basse, petite fleur
  entomophile faible, famille Droseraceae). Niche = marais acide pauvre.
- `plants/catalogue.py` : enregistrer.
- **Couplage puits** (NOUVEAU) : un point de greffe qui, pour chaque `Drosera`
  vivante, retire une fraction `CARNIVORE_CAPTURE` de la densité `moustique` sur
  ses `foliar_plots`, et lui fournit l'azote fonctionnel (pas de pénalité de carence
  N pour elle — son N vient des proies). Où : dans le tick (après `tick_populations`
  qui met à jour `moustique`), via un registre d'effets par espèce ou un hook
  `sim/engine/` dédié. Déterministe, borné (jamais densité < 0).
- **Faim d'azote neutralisée** : la carnivore ne subit pas la faim d'azote édaphique
  (le mécanisme NPK/Liebig existant) — modéliser son N « interne » (drapeau/gène ou
  terme qui compense), SANS bonus de croissance arbitraire (elle survit là où les
  autres carencent, elle ne pousse pas plus vite).
- Voix (§9) : encyclopédie 3 niveaux, carnet (`CONCEPT_DE` → `carnivorie`,
  `carence_azote`), pages (rossolis des sorcières, plante qui « mange » — fort lore),
  magazine (Droseraceae), événements (1ʳᵉ capture consignée au ledger).
- `tests/` : la `Drosera` fait BAISSER `moustique` localement (prélèvement réel,
  observable) ; elle survit sur sol pauvre en N là où une herbacée normale carence.

## Modèle
```
pour chaque Drosera vivante:
    pour (r,c) in foliar_plots:
        capture = CARNIVORE_CAPTURE * moustique[r][c]
        moustique[r][c] -= capture          # prélèvement réel (borné ≥ 0)
        # azote fonctionnel : la plante n'a pas de faim d'azote (N via proies)
```
Zéro RNG. Le prélèvement décale la faune (observable), c'est le flux — pas un gain
chiffré sur la plante.

## Golden
`Drosera` absente du smoke → **NEUTRE**. Le hook puits ne s'active que s'il existe
une `Drosera` (aucune dans le smoke) → digest inchangé. Preuves via banc `tourbiere`
(peupler d'une Drosera + moustiques). Consigner tout re-figeage imprévu = bug.

## Ce qu'il NE faut PAS faire
- Pas de bonus de croissance/vigueur direct : la carnivore ne fait qu'ÉCHAPPER à la
  faim d'azote (flux insectes→N), elle ne « gagne » rien de magique (philo #1/#2).
- Ne pas laisser `moustique` devenir négatif (borner).
- Ne pas recopier le mécanisme de prédation faune→faune : ici c'est plante→faune,
  un hook distinct (la carnivore n'est pas dans le registre `population`).

## F5
- La nuée de moustiques se raréfie-t-elle autour des rossolis (⑧, overlay `moustique`) ?
