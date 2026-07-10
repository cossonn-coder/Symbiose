"""
SYMBIOSE — sim/actions/greffe.py
Geste GREFFER (sprint PALETTE DE GESTES, tronçon ③).
Spec : `docs/conception/CONCEPTION_PALETTE_GESTES.md` §3.6 + kickoff
`sprints/sprint_palette_gestes/03_greffe.md`.

Greffe PAR LE JOUEUR : on soude un rameau (le GREFFON, scion) sur une plante
établie (le PORTE-GREFFE, rootstock). Le porte-greffe adopte l'IDENTITÉ AÉRIENNE
du greffon — sa `plant_class` (donc son feuillage, ses fleurs, ses fruits) et ses
gènes AÉRIENS — tout en CONSERVANT son système RACINAIRE et son établissement
(âge, racines, stade) → précocité agronomique de la greffe (D8). C'est un
changement d'IDENTITÉ, jamais un bonus chiffré (philo #2).

INVARIANTS (philo de design) :
  #1/#2 — geste DIRECT sur le vivant (permis mais coûteux, #1) : coût ÉLEVÉ côté
          Vigueur joueur (geste savant, `couts.cout_action`). L'effet n'est pas un
          malus/bonus mais une RECOMPOSITION génétique (aérien du greffon / racinaire
          du porte-greffe) → réponse biologique émergente (#2).
  #3    — DÉTERMINISTE, zéro RNG : la reprise est ACQUISE si le gate famille passe.
          Un « échec aléatoire » de greffe serait un tirage vivant interdit (#3) ; la
          seule difficulté est la COMPATIBILITÉ (même famille botanique).
  #6    — refus EN AMONT sans dépense (greffon/porte-greffe non greffables, ou
          familles incompatibles) — pas de punition d'une tentative impossible.

GARDE-FOU DE COUCHE : ce module vit au-dessus du tick écologique. Le golden
(`tests/test_golden.py`) est une succession spontanée SANS joueur → n'invoque
jamais `greffer` → no-op strict, golden inchangé.

Couche : `sim` lit `plants` (genetics.species_compatible, GENE_NAMES) et
`sim.actions.couts`.
"""
from __future__ import annotations

from plants.genetics import species_compatible, GENE_NAMES
from sim.vigueur import spend
from sim.actions.couts import cout_action, _objets_action

# --- Partition des gènes AÉRIEN / RACINAIRE (D8, au CŒUR du module) -----------
# La greffe SOUDE la partie AÉRIENNE du greffon (couronne : tige, feuilles, fleurs,
# fruits) sur la partie RACINAIRE du porte-greffe. On répartit donc chaque gène du
# vecteur (`GENE_NAMES`) selon l'organe qu'il gouverne — le résultat pioche chaque
# gène dans la BONNE source :
#
#  AÉRIENS (pris du GREFFON — c'est SON identité aérienne qui prend le dessus) :
#    - hauteur              : port/taille de la couronne (aérien).
#    - phenologie_florale   : DATE de floraison → gouverne fleur/fruit (aérien).
#    - resistance_pathogene : sensibilité fongique du FEUILLAGE/fruit (aérien).
#    - rusticite_froid      : résistance au gel des TISSUS aériens (couronne exposée).
#    - port_trapu           : thigmomorphogénèse de la TIGE (port aérien).
#
#  RACINAIRES / ÉTABLISSEMENT (CONSERVÉS du PORTE-GREFFE — son sous-sol reste) :
#    - tolerance_secheresse : tolérance hydrique des RACINES.
#    - tolerance_asphyxie   : tolérance à l'anoxie des RACINES.
#    - tolerance_ombre      : vigueur du système établi en lumière (racines/vigueur).
#    - vigueur              : fitness/rétablissement porté par le SYSTÈME établi.
#    - germination_thermique: trait de LEVÉE d'une graine — sans objet sur un
#                             porte-greffe déjà levé → on garde le sien (inerte ici).
#
# Le porte-greffe est déjà LEVÉ et ÉTABLI : on ne touche NI son âge, NI son stade,
# NI ses racines — c'est tout l'intérêt (précocité, D8). Seuls sa `plant_class` et
# ses gènes aériens changent.
GENES_AERIENS: frozenset[str] = frozenset({
    "hauteur", "phenologie_florale", "resistance_pathogene",
    "rusticite_froid", "port_trapu",
})
# Tout ce qui n'est PAS aérien reste au porte-greffe (dérivé → rien ne se perd si
# un gène neuf s'ajoute en queue de GENE_NAMES : il tombe côté racinaire par défaut,
# choix conservateur — on garde l'établissement plutôt que de le déraciner).
GENES_RACINAIRES: frozenset[str] = frozenset(GENE_NAMES) - GENES_AERIENS


def peut_greffer(scion, rootstock) -> bool:
    """Gate de la greffe (lecture SEULE, aucune mutation) :
      • greffon ET porte-greffe VIVANTS ;
      • les deux réellement GREFFABLES (`plant_class.greffable`, ligneuses
        fruitières) ;
      • espèces COMPATIBLES = même FAMILLE botanique (`species_compatible`).
    Toute condition manquante → refus EN AMONT, avant toute dépense (philo #6)."""
    if not scion.is_alive or not rootstock.is_alive:
        return False
    if not getattr(scion.plant_class, "greffable", False):
        return False
    if not getattr(rootstock.plant_class, "greffable", False):
        return False
    return species_compatible(scion.plant_class, rootstock.plant_class)


def _genes_greffes(scion, rootstock) -> dict:
    """Vecteur de gènes du porte-greffe APRÈS greffe : chaque gène pioché dans la
    BONNE source (aérien → greffon, racinaire/établissement → porte-greffe). On lit
    via `.gene(name)` (1.0 si absent du vecteur) → jamais de KeyError, un vecteur
    partiel se complète en neutre. Déterministe (philo #3)."""
    return {
        g: (scion.gene(g) if g in GENES_AERIENS else rootstock.gene(g))
        for g in GENE_NAMES
    }


def greffer(game_state: dict, player: str, scion, rootstock, eco) -> bool:
    """Greffe le greffon `scion` sur le porte-greffe `rootstock` — geste à 2 temps
    côté pont (1er clic = greffon, 2e clic = porte-greffe ; ici les deux cibles sont
    déjà résolues). BINAIRE tout-ou-rien (modèle `planter`/`bouturer`) : la greffe
    n'est appliquée QUE si le gate passe ET si le coût Vigueur est INTÉGRALEMENT payé.

    Séquence :
      1. gate `peut_greffer` — refus AVANT toute dépense si incompatibles/non greffables ;
      2. coût Vigueur joueur ÉLEVÉ (`cout_action`) — si `spend < 1.0`, on renonce (le
         porte-greffe reste intact) ;
      3. RECOMPOSITION du porte-greffe : il adopte la `plant_class` du greffon (donc
         son feuillage/fleurs/fruits, lu partout par duck-typing sur `plant_class`)
         et ses gènes AÉRIENS ; il CONSERVE ses gènes racinaires + son établissement
         (âge/stade/racines INCHANGÉS → précocité, D8). Le greffon (un rameau prélevé)
         est CONSOMMÉ : on ne le plante pas, il disparaît (retiré de sa tuile s'il y est).

    Le `eco` est accepté pour l'homogénéité de signature avec les autres gestes (gate
    physiologique éventuel futur) ; inutilisé ici (le gate est purement génétique).

    Renvoie True si la greffe a effectivement pris. Déterministe, no-op golden
    (le smoke n'appelle jamais ce geste)."""
    if not peut_greffer(scion, rootstock):
        return False                          # refus EN AMONT — aucune Vigueur dépensée (philo #6)

    cost = cout_action(game_state, player, "greffer",
                       _objets_action("greffer", rootstock))
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → greffe non faite

    # Recomposition aérien/racinaire (D8). L'ordre importe peu : on lit les deux
    # sources AVANT toute écriture (le nouveau vecteur est construit d'abord).
    nouveaux_genes = _genes_greffes(scion, rootstock)
    rootstock.plant_class = scion.plant_class   # identité AÉRIENNE (rendu/floraison/fruit)
    rootstock.genes = nouveaux_genes
    # Âge / stade / racines / position du porte-greffe : INCHANGÉS (établissement
    # conservé → démarrage rapide, D8). On ne ré-initialise RIEN au stade graine.

    # Le greffon est un RAMEAU prélevé, pas une plante entière : après la soudure il
    # n'existe plus en tant qu'individu. On le marque MORT (santé 0 + `morte`), à
    # l'identique de `deraciner`/`deposer_mort` : `is_alive` passe False → il quitte le
    # vivant au prochain balayage de la tuile (le tick le retire). Le pont, qui tient
    # la tuile du greffon, peut aussi le retirer immédiatement (`remove_plant`) pour un
    # retour visuel instantané. On NE dépose PAS de squelette (un rameau, pas un tronc).
    scion.health = 0
    scion.morte = True
    return True
