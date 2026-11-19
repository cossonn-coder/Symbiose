# Conception — LISIBILITÉ DU BILAN (retours F5 plante vivante + D141)

> Figée le 2026-11-19 avec Nico. Suite directe de `conception_plante_vivante.md`
> (sprint A clos côté code). Placée AVANT `sprint_stress_au_bilan` (B).
> Sprint : `sprints/vegetal/sante/sprint_lisibilite_bilan/`.

## 1. Constat (F5 de Nico, banc `plante_vivante`, mesures VM seed 42, n=1)

| Retour F5 | Mesure / cause |
|---|---|
| « les 4 consoudes se ressemblent » | broutées parties à 0,35 (pas 0,2), refeuillées à 0,97 en 5 sem = 15 s à 3 s/sem ; port rosette à 1 segment |
| « le poivron meurt, grisé, puis disparaît sans matière organique » | le moteur dépose bien la litière (+~1,3/plot) ; tissu `herbace` rendu en amas abstraits (`LitterLayer`), seul `feuille` a un rendu de feuilles (`LeafLitterLayer`) |
| « je n'ai pas vu les info-bulles » | fenêtres courtes (« épuisé » ~2 sem, « refait » ~4 sem) ; non survolées au bon moment |
| « les plantes sont en anglais » (D141) | le pont envoie `species = cls.__name__` (`Comfrey`), l'étiquette et le rapport F4 l'affichent ; le nom français existe déjà : `cls.name` (« Consoude ») |
| (vu en mesurant) le poivron **rapetisse** en mourant, 58 → 47 cm | `height_at` = potentiel × `growth_factor`, et `growth_factor` suit une cible qui baisse au déficit (`sim/engine/croissance.py`) |

## 2. Décisions (Nico, 2026-11-19)

1. **Une plante ne rapetisse pas.** La hauteur bâtie est **acquise**. Un stress (déficit
   du bilan) **ralentit** la croissance, il ne retire pas de taille. Seule une
   **destruction** retire de la hauteur : taille, casse, broutage d'apex, écrasement,
   et la **mort des parties aériennes** (fin de cycle, repli hivernal d'une vivace
   herbacée qui repart de la souche). Le moteur reste la vérité (golden re-figé annoncé).
2. **Noms en français partout** à l'écran : étiquette « espèce · stade », info-bulle,
   dossier plante, rapport F4, chronique. Source unique = `cls.name` du catalogue (déjà
   français et accentué). Pas de table neuve ni de réglage de langue (un menu à une
   langue ne sert à rien) ; une 2ᵉ langue passerait plus tard par cette même source.
   La clé technique `species` (nom de classe) **reste** : la vue s'en sert d'identifiant
   (ports, sprites) — on ajoute un nom affiché, on ne renomme pas l'identifiant.
   Ferme **D141**.
3. **La litière d'herbacée se voit et se ramasse.** Rendu de tiges couchées couleur
   paille qui brunissent vers l'humus (patron `LeafLitterLayer`). Pas de nouveau geste :
   `composter` ramasse déjà toute litière tendre du plot (`sim/actions/compost.py`).
4. **Le banc se lit.** Consoudes broutées réellement à 0,2 de feuillage **et** à
   réserves basses : la refeuillaison est payée sur les réserves (≤ ½ réserve/sem), donc
   plus lente — fenêtre d'observation de plusieurs minutes. Les phrases d'info-bulle
   sont vérifiées par capture VM (Xvfb), pas seulement au F5.

## 3. Philo
#1/#2 : rien de direct sur les plantes, on corrige une lecture (hauteur) et des vues.
#5 : aucun chiffre ajouté au HUD ; ce qu'on voit = tiges au sol, feuilles moins denses,
une phrase. #3 : zéro RNG.

## 4. Perf
Hauteur acquise = un `max` par plante et par tick (négligeable). Vue : un semis de
tiges en lot comme les feuilles (même coût que `LeafLitterLayer`).

## 5. Tronçons
① hauteur acquise (moteur, RE-FIGÉ annoncé) · ② noms français (pont + vue, intact) ·
③ vue + banc (litière herbacée, consoudes, info-bulles vérifiées, intact).
