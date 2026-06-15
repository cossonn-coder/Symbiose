"""
SYMBIOSE — tests/simserver/
Paquet des suites du PONT (sim_server), éclaté de l'ex-monolithe
`tests/test_sim_server.py` au Sprint refactor global (SS⑤). L'entrée reste
`tests/test_sim_server.py` (lancée par `python3 -m tests.test_sim_server`), qui
orchestre les sections de ce paquet dans le MÊME ordre — zéro check retiré,
harness `ServerProc`/`check`/`_results` partagé.
"""
