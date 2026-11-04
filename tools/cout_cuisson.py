#!/usr/bin/env python3
"""cout_cuisson — combien coûte un coup de pinceau, espèce par espèce ?

Outil *du dépôt* (sprint FORMES DES PLANTES ③). `[Cuisson] pinceau … ms/plante` mélange
toutes les espèces d'une scène, et deux runs ne tournent pas à la même charge. Ici, le banc
`planche_especes` passe devant le pinceau espèce par espèce, un Godot à la fois, avec la
trace `[cout]` de BakeQueue (`SYMBIOSE_COUT_CUISSON=1`). Toutes les espèces sont mesurées
dans la même passe : les écarts entre ports restent lisibles même si la VM est chargée.

📖 Pédagogie : on prend la MÉDIANE, parce que le premier coup de pinceau d'une espèce paie
aussi la compilation à la volée (JIT) de sa fonction et la création de ses palettes ; un
écart de 10 fois sur cet échantillon n'a rien à voir avec le dessin.

Usage (faire `dotnet build Symbiose.csproj` avant) :
    python3 tools/cout_cuisson.py [--zoom 4] [--especes tournesol,ortie] [--tours 1]
"""

import argparse
import collections
import os
import statistics
import subprocess
import sys
import tempfile

from mesure_silhouettes import OUTILS, BANC, SOURIS, COUCHES, centre_de, table_especes


def une_passe(espece, zoom, pied):
    """Échantillons (espèce du catalogue C#, ms, sommets) d'un Godot cadré sur `espece`."""
    x, y, h = pied
    cx, cy = centre_de(x, y, h)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([os.path.join(OUTILS, "capture_vm.sh"), "--no-build", "-b", BANC, "-w", "0",
                        "-z", f"{zoom:g}", "-c", f"{cx:g},{cy:g}", "-v", "0", "-O", "-x", COUCHES,
                        "-s", SOURIS, "-n", "4", "-o", tmp],
                       check=True, stdout=subprocess.DEVNULL,
                       env={**os.environ, "SYMBIOSE_COUT_CUISSON": "1"})
        with open(os.path.join(tmp, "godot.log"), encoding="utf-8", errors="replace") as f:
            for ligne in f:
                if ligne.startswith("[cout] "):
                    _, nom, ms, sommets = ligne.split()
                    yield nom, float(ms.replace(",", ".")), int(sommets)  # locale de la VM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zoom", type=float, default=4.0)
    ap.add_argument("--especes", help="liste séparée par des virgules (défaut : toutes)")
    ap.add_argument("--tours", type=int, default=1)
    a = ap.parse_args()
    table = table_especes()
    choisies = a.especes.split(",") if a.especes else sorted(table)
    ms_par, sommets_par = collections.defaultdict(list), collections.defaultdict(list)
    for _ in range(a.tours):
        for espece in choisies:
            print(espece, file=sys.stderr)
            for nom, ms, sommets in une_passe(espece, a.zoom, table[espece]):
                ms_par[nom].append(ms)
                sommets_par[nom].append(sommets)
    print(f"| espèce | ms médiane ×{a.zoom:g} | sommets | n coups |\n| --- | --- | --- | --- |")
    for nom in sorted(ms_par, key=lambda n: -statistics.median(ms_par[n])):
        print(f"| {nom} | {statistics.median(ms_par[nom]):.3f} | "
              f"{statistics.median(sommets_par[nom]):.0f} | {len(ms_par[nom])} |")


if __name__ == "__main__":
    main()
