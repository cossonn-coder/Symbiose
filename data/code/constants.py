"""
SYMBIOSE — constants.py
Constantes d'échelle spatiale partagées (fondation pure, aucun import interne).

Posé à la racine d'exécution `data/code/` : tout le monde peut s'appuyer dessus
sans créer de cycle. Sépare l'échelle (géométrie du monde) de la génétique
(plants/genetics.py) et du bruit déterministe (fields/noise.py).
"""

PLOT_CM = 50.0   # 1 plot = 50×50 cm (maille potagère, échelle actée)
