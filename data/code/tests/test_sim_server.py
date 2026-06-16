"""
SYMBIOSE — tests/test_sim_server.py
Golden du PONT (sprint Intégration Godot ↔ Python, tranche 1).

Lance tools/sim_server.py en vrai sous-process (comme Godot le fera) et joue le
protocole v0 par les pipes. Couvre les contrats du kickoff 01_pont_minimal.md :

  1. forme        — init/step_week/snapshot répondent {"ok": true, ...} bien
                    formés, engine_version présent, monde 2 tuiles + maison ;
  2. avancement   — step_week ×4 → week passe de 1 à 5, des plantes vivantes
                    dans le snapshot ;
  3. robustesse   — ligne malformée / cmd inconnue / step avant init →
                    {"ok": false} et le serveur SURVIT (répond encore après) ;
  4. déterminisme — 2 runs même seed → réponses byte-identiques ;
  5. arrêt propre — EOF sur stdin (Godot mort sans quit) → le process meurt ;
  6. monde full   — init(config="full") (tranche 2) : layout 3×3 de main.py
                    (8 tuiles SECTORS, sols variés, origins distincts, maison
                    [600,600]→[1400,1400], 53 plantes), config inconnue refusée ;
  7. actions v1   — (tranche 4) bloc `player` au snapshot, régen + refill de
                    saison via le tick moteur, manger/deraciner par POSITION,
                    URGENCE_MULT visible sur ecraser, refus métier
                    (applied:false) sur verbe inconnu / cible introuvable /
                    Vigueur insuffisante AVEC serveur survivant, déterminisme
                    2 runs avec les MÊMES actions. Le golden écolo, lui, ne
                    passe JAMAIS par ce serveur → intact par construction ;
  8. taille au segment — (tranche 5) `tailler` avec `target.segment` explicite
                    (la branche cliquée) : le snapshot JOINT perd exactement le
                    sous-arbre ciblé ; segment hors bornes / collet / non
                    entier → applied:false SANS coût et le serveur survit ;
                    le repli params.cible (t4) reste intact ;
  9. hints organes — (tranche 6·A) chaque plante du snapshot porte
                    foliage_density (0..1, saisonnier), organ (proxy
                    REPRO_BY_SEASON + repli DEFAUT) et organ_site
                    (terminal|lateral) ; caduc en hiver → densité 0 et
                    organ null pour tout le monde. Pur rendu, lecture seule.
 10. vie macro    — (tranche 6·B) bloc `sprites` au snapshot : par tuile et
                    par guilde, tableaux compacts [r, c, x_frac, y_frac,
                    activite] issus de sample_sprites (PUR, déterministe).
                    Forme et bornes (cap 4/plot/guilde, fracs ∈ [0,1]),
                    démarrage à zéro (populations vides semaine 1), émergence
                    estivale, positions STABLES d'une semaine à l'autre (un
                    slot vit toujours au même point), lecture sans effet de
                    bord. Le déterminisme byte-à-byte (section 4) couvre
                    aussi ce bloc.
 12. planter·arroser — (sprint éponyme, protocole 0.3.3) gestes de milieu par
                    POSITION (x_cm/y_cm → plot-foyer côté serveur). `planter` :
                    refus espèce inconnue / lot vide / hors tuile / tuile
                    introuvable SANS coût ; banque-joueur exposée au snapshot
                    (`player.seeds`, vide à l'init, remplie à la récolte) ; un
                    dépôt réussi DÉCROÎT le lot de 1 et paie FAIBLE. `arroser` :
                    le champ humidité monte de DOSE au plot visé, coût MODÉRÉ
                    (× URGENCE_MULT en urgence), cumul PLAFONNÉ à 3.0.
                    Déterminisme byte-à-byte des deux gestes.
 11. champs debug — (tranche 6·C) commande `fields` HORS snapshot : registre
                    découvert par introspection (12 GridField d'EcoFields +
                    4 guildes), grilles par tuile row-major (rows×cols
                    cohérents, len(values) exact), guilde interrogeable
                    aussi, champ inconnu → ok:false AVEC serveur survivant,
                    avant init → ok:false, lecture pure (2 appels
                    identiques).

Mesure aussi la taille du snapshot (octets/semaine) — la donnée qui tranchera
« complet vs diffs » (cf. 00_etat.md, pas d'optimisation avant mesure).

> Refactor structurel (Sprint refactor global, SS⑤) : cette entrée orchestre
> désormais le paquet `tests/simserver/` (harness `ServerProc` partagé + un
> module par section : base, actions, taille, organes, macro, fields, planter,
> structures). Même ordre d'exécution, même compteur `harness._results` — zéro
> check retiré. `python3 tools/sim_server.py` reste lancé en vrai sous-process.

Usage (depuis data/code/) :
  python3 -m tests.test_sim_server
"""
import sys

from tests.simserver import harness
from tests.simserver.base import test_v0_contract
from tests.simserver.actions import test_actions_v1
from tests.simserver.taille import test_taille_au_segment
from tests.simserver.organes import test_hints_organes
from tests.simserver.macro import test_vie_macro
from tests.simserver.fields import test_champs_debug
from tests.simserver.planter import test_planter_arroser
from tests.simserver.structures import test_structures
from tests.simserver.morts import test_morts, test_pommier_fruite


def main() -> int:
    test_v0_contract()       # sections 1–6 : forme, robustesse, déterminisme, arrêt, full
    test_actions_v1()        # section 7
    test_taille_au_segment() # sections 8 + 8b
    test_hints_organes()     # section 9
    test_vie_macro()         # section 10
    test_champs_debug()      # section 11
    test_planter_arroser()   # section 12
    test_structures()        # section 13
    test_morts()             # section 14 : squelettes exposés (0.3.6)
    test_pommier_fruite()    # section 14b : levier pommier mûr → fruits dès l'été

    # --- bilan ----------------------------------------------------------------
    n_fail = sum(1 for _, ok in harness._results if not ok)
    print(f"\n[test_sim_server] {'PASS' if n_fail == 0 else 'FAIL'} — "
          f"{len(harness._results) - n_fail}/{len(harness._results)} checks verts")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
