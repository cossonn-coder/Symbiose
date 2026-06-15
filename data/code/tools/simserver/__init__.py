"""
SYMBIOSE — tools/simserver/
Paquet du serveur de simulation (pont JSON stdin/stdout vers Godot). Éclaté de
l'ex-monolithe `tools/sim_server.py` au Sprint refactor global (SS⑤) : l'entrée
exécutée par Godot reste `tools/sim_server.py` (mince), qui importe ce paquet —
chemin/nom inchangés côté `SimBridge.cs` et `.spec` PyInstaller.

API publique ré-exportée (imports existants intacts) :
  - SimServer      : la classe serveur (assemblée par mixins)
  - main           : la boucle stdin/stdout
  - ENGINE_VERSION : version du protocole/moteur
"""
from .server import SimServer, main
from .version import ENGINE_VERSION

__all__ = ["SimServer", "main", "ENGINE_VERSION"]
