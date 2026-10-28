"""
SYMBIOSE — tools/simserver/gc_pont.py
Réglage du RAMASSE-MIETTES de Python pour le serveur du pont (sprint FLUIDITÉ PC
PARTAGE, tronçon ①). Appelé une fois le monde monté (fin de `cmd_init`).
Le moteur (`sim/`) n'en sait rien : c'est un réglage du PROCESSUS serveur.

Constat (VM, s85-100, monde `full`, mode delta) [n=1 run] : le ramasse-miettes
cyclique coûtait 25-47 ms par semaine, plus une collecte complète (génération 2)
toutes les ~7 semaines à 151-224 ms — il parcourt à chaque fois les ~200 k objets
suivis, dont l'essentiel est le monde monté à l'init (tuiles, grilles, catalogue)
qui ne deviendra jamais un déchet.

Deux gestes :
  1. `gc.freeze()` : tous les objets vivants à cet instant passent dans une
     génération « permanente » que le ramasse-miettes ne parcourt plus jamais.
     On collecte juste avant (`unfreeze` + `collect`) pour ne pas figer de
     déchets — et pour libérer le monde d'un `init` précédent (relance d'un banc
     depuis le menu), sinon il resterait figé à vie.
  2. seuil de génération 0 relevé (`SEUIL_GEN0`) : la collecte jeune se déclenche
     après plus d'allocations, donc moins souvent (chaque passe coûte surtout son
     coût fixe de parcours des objets jeunes).
Aucun résultat ne change : le ramasse-miettes ne libère que des CYCLES déjà
inaccessibles. Seules les adresses mémoire (`id()`) peuvent différer — vérifié
par `tools/verif_pont_identique.py` (deux processus, réglage on/off).

📖 Pédagogie (côté embarqué) : c'est l'équivalent de placer les tables
constantes en flash plutôt qu'en RAM scrutée par un watchdog — ce qui ne bougera
plus n'a pas à être revérifié à chaque cycle.
"""
from __future__ import annotations
import gc

# Interrupteur pour les outils de vérification (on/off dans deux processus).
ACTIF = True
# Seuil de la génération 0 (défaut CPython : 2000 allocations nettes).
SEUIL_GEN0 = 50_000


def regler_gc() -> None:
    """Fige le monde monté et espace les collectes jeunes. Idempotent."""
    if not ACTIF:
        return
    gc.unfreeze()
    gc.collect()
    gc.freeze()
    _, g1, g2 = gc.get_threshold()
    gc.set_threshold(SEUIL_GEN0, g1, g2)
