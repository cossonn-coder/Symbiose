"""
SYMBIOSE — tests/test_peripherie.py
Tests ciblés de la CEINTURE (sprint PÉRIPHÉRIE, tronçons ①②③, D73).
Spec : `docs/champs/peripherie/conception_peripherie.md` + kickoffs
`sprints/champs/peripherie/sprint_peripherie/01_ceinture.md`,
`02_exposition_abri.md`, `03_graines_eau_corridor.md`.

Trois familles de vérifications, une par tronçon :

  ① `tests/peripherie/ceinture.py`   — la ceinture PRODUITE : déterminisme (A),
     D92 refermée sur 300 000 seeds (B), ripisylve (C), bornes des scalaires (D) ;
  ② `tests/peripherie/exposition.py` — ce qu'elle fait à la LUMIÈRE et au VENT :
     neutralité qui protège le golden (E), saisonnalité de l'ombre (F), porosité
     linéaire/quadratique (G), caches (H) ;
  ③ `tests/peripherie/flux.py`       — ce qu'elle fait TRAVERSER la limite : pluie
     de graines (I), nappe de berge (J), corridor de lisière (K), plus la géométrie
     de bord partagée par les trois flux (③bis).

> Refactor de clôture du sprint : cette entrée orchestre désormais le paquet
> `tests/peripherie/` (harness partagé + un module par tronçon). Le monolithe
> atteignait 415 LDC pur (zone rouge > 400) ; même ordre d'exécution, même
> compteur `harness._results` — zéro cas retiré.
>
> Les tronçons ④⑤⑥⑦ ont leurs propres fichiers plats :
> `test_peripherie_gestes.py`, `test_peripherie_eau_roche.py`,
> `test_peripherie_voix.py`, `test_peripherie_pont.py`.

Usage (depuis data/code/) :
  python3 -m tests.test_peripherie
"""
import sys

from tests.peripherie import harness
from tests.peripherie.ceinture import (test_determinisme, test_ripisylve,
                                       test_bornes, test_d92)
from tests.peripherie.exposition import (test_neutralite, test_saisonnalite,
                                         test_porosite, test_caches)
from tests.peripherie.flux import (test_plots_de_bord, test_graines,
                                   test_berge, test_corridor)


def main():
    test_determinisme()
    test_ripisylve()
    test_bornes()
    test_neutralite()
    test_saisonnalite()
    test_porosite()
    test_caches()
    test_plots_de_bord()
    test_graines()
    test_berge()
    test_corridor()
    test_d92()
    n_ok = sum(1 for _, ok in harness._results if ok)
    n = len(harness._results)
    print(f"\n[test_peripherie] {n_ok}/{n} OK")
    if n_ok != n:
        print("ÉCHECS : " + ", ".join(name for name, ok in harness._results if not ok))
        sys.exit(1)
    print("[test_peripherie] PASS")


if __name__ == "__main__":
    main()
