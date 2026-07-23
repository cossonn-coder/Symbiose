# SYMBIOSE — tools/jardinier_auto/profil.py
# Profil de l'automate : une DATACLASS gelée qui rassemble les six axes de
# configuration (CONCEPTION_JARDINIER_AUTOMATE §4). Tout est commutable par
# profil ; les anciens modes bride/libre de l'amorce deviennent de simples
# PRESETS de ces flags orthogonaux.
#
# Tronçon ① : tous les axes sont PRÉSENTS mais seuls `perception` (lu ici, via
# perception.py) est réellement câblé. Les autres (paie_vigueur, credite_maitrise,
# desherbage, part_recoltee, ecrit_carnet) sont posés dès maintenant pour que les
# tronçons ②→④ n'aient qu'à les LIRE, sans changer la signature du profil.
#
# `frozen=True` : un profil est une constante de configuration, jamais muté en
# cours de route → déterminisme (philo #3), et hashable (utilisable en clé).

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ProfilAutomate:
    """Configuration immuable d'une session d'automate (§4 de la conception)."""

    perception: str = "omniscient"       # "omniscient" | "semiologique"
    paie_vigueur: bool = False           # dépense cout_action / borne au solde (③)
    credite_maitrise: bool = False       # les gestes alimentent la maîtrise (③)
    desherbage: str = "curatif"          # "curatif" | "aucun" | "systematique" (②)
    part_recoltee: float = 1.0           # fraction récoltée ∈ [0,1] — slider (②)
    ecrit_carnet: bool = False           # écritures narratives dans le carnet (③)
    verbosite_log: int = 1               # verbosité de LECTURE du log (D87 ①)

    # `verbosite_log` (0=décision · 1=détail · 2=perception fine) NE contraint PAS
    # l'écriture : le journal (trace.py) est TOUJOURS écrit complet — c'est ce qui en
    # fait un oracle de déterminisme. Cet axe n'est qu'un DÉFAUT de lecture, consommé
    # par `filtre.filtrer(..., niveau_max=profil.verbosite_log)` quand une vue veut
    # abréger. Présent dès ① pour que les tronçons ②→⑤ n'aient qu'à le LIRE.

    # --- Sémantique des axes réglés au tronçon ② (lus par perception/boucle) ----
    def seuil_concurrence(self) -> int | None:
        """Combien de férales à portée racinaire déclenchent une `concurrence_ferale`
        (→ `deraciner`), selon le mode `desherbage` (§4) :
          - `aucun`        → None : jamais de désherbage (la concurrence n'est pas
            même diagnostiquée) ;
          - `curatif`      → 2 : on n'arrache QUE si la pression férale est réelle
            (une seule adventice n'est pas encore le facteur limitant) ;
          - `systematique` → 1 : toute férale à portée d'une cultivée est arrachée.
        """
        return {"aucun": None, "curatif": 2, "systematique": 1}.get(self.desherbage, 2)

    def n_a_recolter(self, n_mur: int) -> int:
        """Nombre de plantes mûres à réellement récolter ce tick, `slider` (§4/Q5) :
        `round(part_recoltee × n_mûrs)`. `part_recoltee=1.0` (défaut) → tout (=①) ;
        `0.0` → rien (les fruits tombent, nourrissent la faune, ferment la boucle
        décompo). Population-level : on récolte les `k` premières mûres dans l'ordre
        stable, on laisse tomber le reste — déterministe, sans RNG (philo #3)."""
        return int(round(self.part_recoltee * n_mur))


# --- Presets nommés (combinaisons d'axes, cf. §4) -------------------------------
# LIBRE : aucune comptabilité — l'automate joue « pour voir », sans budget ni
#   crédit de maîtrise ni trace narrative. Régime de mesure « jardin tenu » brut.
LIBRE = ProfilAutomate(
    paie_vigueur=False, credite_maitrise=False, ecrit_carnet=False,
)

# BRIDE : comptabilité complète — l'automate paie sa Vigueur, crédite la maîtrise
#   et écrit au carnet, comme un vrai joueur. Le bridage réel (respect de
#   `gestes_debloques`, budget) est câblé au tronçon ③ ; ici seuls les flags sont
#   posés.
BRIDE = ProfilAutomate(
    paie_vigueur=True, credite_maitrise=True, ecrit_carnet=True,
)
