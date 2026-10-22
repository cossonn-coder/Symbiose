# ⑥ Manger un champignon et la vision

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §4.
**Golden** : NEUTRE (geste joueur hors tick + lecture). À vérifier.

## Objectif
1. **Manger un carpophore** : nouveau ciblage du verbe `manger` (aujourd'hui « plante » :
   `sim/actions/palette.py` ~l.48, `tools/simserver/plante_route.py`,
   `sim/actions/gestes.py::manger`). Effet selon la comestibilité du registre ③ :
   comestible → Vigueur (∝ comme un fruit) ; vénéneux/mortel → Vigueur effondrée
   (mortel plus fort), **jamais de mort** ; psychédélique → vision ; tue-mouches → vision
   ET perte de Vigueur. Le carpophore mangé disparaît pour la semaine (perception :
   mémoriser les carpophores consommés dans le `game_state`, PAS dans le tick).
   ⚠️ L'interrupteur « Vigueur infinie » (ON par défaut, `cmd_init`, pont 0.5.49) masque
   les pertes : tester avec l'interrupteur OFF.
2. **Vision (1 semaine de jeu)** : état joueur `vision` (semaine de fin) dans le
   `game_state`. Pendant l'effet, la LECTURE informationnelle passe au palier transcendant
   (carnet interprétatif — patron `sim/carnet.py::_reglage_anticipe` —, encyclopédie et
   info-bulle complètes). **Ne PAS** passer par `sim/maitrise.palier()` globalement : la
   vision ne doit toucher ni la Vigueur max (`palier_bonus`), ni l'extension de terrain,
   ni le magazine — seulement ce qu'on LIT.
3. **Les êtres parlent** : commande read-only du pont (au survol d'une plante ou d'une
   bête) qui GÉNÈRE 1 à 3 phrases à la 1ʳᵉ personne depuis les vrais besoins au moteur :
   plantes — eau (sec/noyé), lumière (ombre, qui la porte), sol (N/P/K, pH), voisins
   (allélopathie, compagnes, concurrence de racines), parasite/campagnol, vent ; bêtes —
   nourriture (fleurs de telle famille, proies), abri, humidité. Gabarits soignés dans un
   corpus dédié (≠ `signes_corpus`), choisis par hash déterministe. Au survol SEULEMENT.
4. **Overdose** (Nico) : un 2ᵉ psychédélique pendant l'effet → les phrases de TOUS les
   êtres visibles sont générées à chaque snapshot jusqu'à la fin de l'effet. Mesurer le
   coût snapshot (monde `full`) et le consigner [n=…].
5. **Ce qui reste** : chaque espèce (plante, bête, champignon) survolée assez pendant la
   vision (seuil de survols cumulés à fixer) gagne UN palier durable à la fin de l'effet,
   au plus une fois par vision, jamais jusqu'au transcendant.
- Tests : effets de chaque comestibilité, durée de vision, isolation (Vigueur max
  inchangée pendant la vision), overdose, crédit durable borné.
- Ouvrir la dette « voix des êtres écrites à la main par espèce » (déjà notée en phase C :
  voir `DETTE.md`).

## Ne PAS faire
Pas de dessin (⑧). Pas de mort du jardinier. Pas de phrases générées hors survol sauf overdose.
