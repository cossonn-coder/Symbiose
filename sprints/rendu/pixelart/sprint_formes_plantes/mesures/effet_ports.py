# SYMBIOSE — mesure du tronçon ⑥ (FORMES DES PLANTES) : qui passe par quel chemin de dessin, en
# jeu ? Fait tourner le monde `full` et classe chaque pied vivant de fin d'an 1, 2 et 3 d'après
# les tables de la vue (`FichesPort`, `PortsPrairie`, `FichesLiane`) ; le reste = les arbres.
# Usage, depuis data/code/ : python3 <ce fichier> [--seed 42] [--automate]
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.getcwd())
VUE = os.path.join(os.getcwd(), "..", "..", "visuals")


def cles(fichier, table):
    texte = open(os.path.join(VUE, fichier), encoding="utf-8").read()
    bloc = texte[texte.index(table):]
    bloc = bloc[:bloc.index("};")]
    return set(re.findall(r'\["(\w+)"\]\s*=', bloc))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--automate", action="store_true")
    a = ap.parse_args()
    from tools.simserver.server import SimServer
    ports = cles("PlantRenderer.PortsFiches.cs", "FichesPort = new()")
    prairie = cles("PlantRenderer.Prairie.cs", "PortsPrairie = new()")
    lianes = cles("PlantRenderer.Lianes.cs", "FichesLiane = new()")
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": a.seed})
    if a.automate:
        srv.cmd_automate({"op": "on", "profil": {"desherbage": "curatif"}})
    for sem in range(1, 157):
        srv.cmd_step_week({})
        if sem % 52:
            continue
        vivants = [p for t in srv.engine.game_state["tiles"] for p in t.plants if p.is_alive]
        par = collections.Counter(p.plant_class.__name__ for p in vivants)
        classe = collections.Counter()
        for nom, n in par.items():
            classe["port" if nom in ports else "prairie" if nom in prairie else "liane" if nom in lianes else "arbre"] += n
        esp = lambda t: sorted(n for n in par if (n in t))
        print(f"an {sem // 52} : {len(vivants)} pieds, {len(par)} espèces ; pieds {dict(classe)}")
        print("  à fiche :", esp(ports))
        print("  prairie :", esp(prairie), " lianes :", esp(lianes))
        print("  autres  :", sorted(n for n in par if n not in ports | prairie | lianes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
