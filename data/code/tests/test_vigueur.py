"""
SYMBIOSE — tests/test_vigueur.py
Golden JOUEUR de la couche Vigueur (D11, sous-sprint 1) — distinct du golden
ÉCOLOGIQUE (`tests/test_golden.py`).

La couche Vigueur joueur vit dans `game_state["vigueur"]`, AU-DESSUS du tick, et
ne doit JAMAIS faire avancer la simulation écologique (docs/joueur/vigueur/conception_vigueur.md
§0/§5). Deux familles de vérifications :

  A. Contrats de la couche (déterministes, sans RNG) :
     1. No-op golden : un `game_state` SANS clé `vigueur` ne se voit JAMAIS
        injecter de Vigueur par le tick (c'est ce qui garde le golden écolo
        intact — si ce contrat casse, le golden bouge).
     2. Régen plafonnée : +REGEN_BASE/semaine, jamais au-dessus de vigueur_max.
     3. Refill saison : `courante = vigueur_max` quel que soit l'état antérieur.
     4. Interface paliers (D12) remplie par la maîtrise : palier_bonus neutre 1.0
        sans savoir ; vigueur_max / regen_rate en dépendent (section F : pont actif).

  B. Golden de trajectoire : on pilote une vraie boucle `engine` sur une fenêtre
     qui traverse une frontière de saison (régen sur la pente + snap du refill),
     et on hashe la trajectoire `courante` semaine par semaine. Toute dérive du
     cadencement du hook (mauvaise semaine de refill, double régen…) casse le
     hash.

> Refactor structurel (Sprint refactor global, SS⑤) : cette entrée orchestre
> désormais le paquet `tests/vigueur/` (harness partagé + un module par thème :
> contrats, gestes, façades, manger, macro, maitrise_seam, golden_traj). Même
> ordre d'exécution, même compteur `harness._results` — zéro cas retiré.

Usage (depuis data/code/) :
  python3 -m tests.test_vigueur            # vérifie contre vigueur_hash.txt
  python3 -m tests.test_vigueur --capture  # (re)capture le hash de référence
"""
from tests.vigueur import harness
from tests.vigueur.contrats import (test_noop_sans_joueur, test_regen_plafonnee,
                                     test_refill_saison, test_interface_paliers)
from tests.vigueur.gestes import (test_primitives_spend_gain, test_recolter,
                                   test_deraciner, test_tailler, test_ecraser,
                                   test_ecraser_plante, test_actions_hors_tick)
from tests.vigueur.facades import (test_facade_purete, test_facade_sante,
                                    test_facade_maturite, test_facade_qi_local,
                                    test_facade_gene_enveloppe, test_facade_descripteur)
from tests.vigueur.manger import (test_manger_gain_organe, test_manger_modulation_facade,
                                   test_manger_no_op_ecolo, test_manger_plafond)
from tests.vigueur.macro import (test_macro_facade_densite_ressource,
                                 test_macro_facade_purete, test_macro_descripteur,
                                 test_favoriser_auxiliaire, test_becher_vs_grelinette,
                                 test_ecraser_pression_revient)
from tests.vigueur.maitrise_seam import (test_pont_maitrise_vigueur,
                                         test_gains_ponctuels, test_seam_cout_action)
from tests.vigueur.golden_traj import test_golden_trajectoire


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Golden JOUEUR Vigueur (D11, sous-sprint 1)")
    print("=" * 60)
    test_noop_sans_joueur()
    test_regen_plafonnee()
    test_refill_saison()
    test_interface_paliers()
    test_primitives_spend_gain()
    test_recolter()
    test_deraciner()
    test_tailler()
    test_ecraser()
    test_ecraser_plante()
    test_actions_hors_tick()
    test_facade_purete()
    test_facade_sante()
    test_facade_maturite()
    test_facade_qi_local()
    test_facade_gene_enveloppe()
    test_facade_descripteur()
    test_manger_gain_organe()
    test_manger_modulation_facade()
    test_manger_no_op_ecolo()
    test_manger_plafond()
    test_macro_facade_densite_ressource()
    test_macro_facade_purete()
    test_macro_descripteur()
    test_favoriser_auxiliaire()
    test_becher_vs_grelinette()
    test_ecraser_pression_revient()
    test_pont_maitrise_vigueur()
    test_gains_ponctuels()
    test_seam_cout_action()
    test_golden_trajectoire()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in harness._results if ok)
    total = len(harness._results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
