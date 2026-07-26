"""
SYMBIOSE — tests/peripherie/
Paquet des suites PÉRIPHÉRIE (D73), éclaté de l'ex-monolithe `tests/test_peripherie.py`
(415 LDC, zone rouge) au refactor de clôture du sprint. L'entrée reste
`tests/test_peripherie.py` (lancée par `python3 -m tests.test_peripherie`), qui
orchestre les modules de ce paquet dans le MÊME ordre — zéro cas retiré, harness
`check`/`_results` partagé.

Découpage par tronçon du sprint, c'est-à-dire par responsabilité :
  - `harness.py`    — compteur de résultats + fabriques de ceintures de test ;
  - `ceinture.py`   — ① la génération elle-même (déterminisme, D92, ripisylve, bornes) ;
  - `exposition.py` — ② ce que la ceinture fait à la lumière et au vent ;
  - `flux.py`       — ③ ce qu'elle fait traverser (graines, eau, corridor).

Les tronçons ④⑤⑥⑦ vivent déjà dans leurs propres fichiers plats
(`test_peripherie_gestes.py`, `_eau_roche.py`, `_voix.py`, `_pont.py`) : ce
paquet ne concerne QUE ①②③.
"""
