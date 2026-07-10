"""
SYMBIOSE — sim/seeds.py
Banque de graines du joueur (D17) — la moitié transportable du couple de banques.

Deux banques distinctes (Sprint génétique 2026-06-03) :
  - SeedBank-sol      : champ écologique latent, par espèce × plot, génétique
                        vectorielle (moyenne+variance). Vit dans `fields.SeedBank`
                        (couche `species`), reste AU TERRAIN au déménagement.
  - SeedBank-joueur   : ce fichier. Inventaire discret, lots de graines par
                        espèce, génétique héritée/sélectionnée. SUIT L'AVATAR.

Ponts (engine) : récolte d'une plante mûre → graine dans la banque-joueur ;
semis depuis la banque-joueur → plante portant la génétique de la graine.

Le vecteur de gènes (plants.genetics.GENE_NAMES) est extensible ; seul `hauteur`
est rempli au départ.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field

from plants import PLANT_CATALOGUE


@dataclass
class Seed:
    """Une graine : espèce (clé catalogue) + vecteur de gènes hérité + état
    d'EXPRESSION primé hérité de la mère (plasticité ④, priming transgénérationnel).
    `expression` = `child_expression(mère)` filtré aux entrées non-neutres ; vide ⇒
    graine neutre. Voyage AVEC la graine par tous les canaux (récolte →
    banque-joueur → `planter` → germination), au même titre que les gènes : toute
    graine = un descendant qui naît pré-armé si la mère l'était.

    `genes` VIDE par défaut (sprint DIVERSITÉ FONDATRICE ①) : une graine SANS lignée
    — sachet magazine, graine de démo — ne porte AUCUN gène ⇒ la levée lui tire un
    patrimoine FONDATEUR propre (`founder_genes`, plus un clone neutre). Une graine
    RÉCOLTÉE reçoit explicitement `dict(plant.genes)` (hérédité réelle) → non vide →
    conservée telle quelle."""
    species: str                       # clé PLANT_CATALOGUE, ex: "tomate"
    genes: dict = field(default_factory=dict)
    expression: dict = field(default_factory=dict)

    @property
    def plant_class(self):
        return PLANT_CATALOGUE.get(self.species)


class PlayerSeedBank:
    """
    Banque de graines du joueur — lots par espèce, transportable (suit l'avatar
    au déménagement, contrairement à la banque-sol). Sérialisable JSON (save
    lisible par profil, cf. cycle de sauvegarde).
    """

    def __init__(self):
        self.lots: dict[str, list[Seed]] = {}

    def add(self, seed: Seed) -> None:
        self.lots.setdefault(seed.species, []).append(seed)

    def count(self, species: str | None = None) -> int:
        if species is None:
            return sum(len(v) for v in self.lots.values())
        return len(self.lots.get(species, []))

    def take(self, species: str) -> Seed | None:
        """Retire et renvoie une graine de l'espèce (FIFO), ou None si vide."""
        lot = self.lots.get(species)
        return lot.pop(0) if lot else None

    def mean_gene(self, species: str, gene: str = "hauteur") -> float | None:
        """Moyenne d'un gène sur le lot d'une espèce (suivi de la sélection)."""
        lot = self.lots.get(species)
        if not lot:
            return None
        return sum(s.genes.get(gene, 1.0) for s in lot) / len(lot)

    # --- Sérialisation JSON (save lisible, pas binaire) ---

    def to_dict(self) -> dict:
        def _seed(s):
            d = {"species": s.species, "genes": s.genes}
            if s.expression:                 # omis si neutre (save lisible)
                d["expression"] = s.expression
            return d
        return {sp: [_seed(s) for s in lot]
                for sp, lot in self.lots.items() if lot}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "PlayerSeedBank":
        bank = cls()
        for sp, lot in d.items():
            bank.lots[sp] = [Seed(species=s["species"], genes=dict(s["genes"]),
                                  expression=dict(s.get("expression", {})))
                             for s in lot]
        return bank

    @classmethod
    def from_json(cls, text: str) -> "PlayerSeedBank":
        return cls.from_dict(json.loads(text))

    def __repr__(self) -> str:
        parts = " ".join(f"{sp}×{len(lot)}" for sp, lot in self.lots.items() if lot)
        return f"PlayerSeedBank[{parts or 'vide'}]"


def semer_fondateur(tile, plant_class: type, r: int, c: int,
                    seed: int, week: int = 0):
    """Semis DIRECT naturalisé (sprint DIVERSITÉ FONDATRICE ①) : plante l'espèce
    (`tile.add_plant`) PUIS lui pose un patrimoine génétique FONDATEUR propre
    (`founder_genes`, tiré sur la position continue de l'instance) au lieu du vecteur
    neutre. Remplace les `add_plant` bruts des BANCS D'ESSAI monde-réel (golden,
    main.py) → les 8 cultivées de démo ne sont plus des clones parfaits, comme la
    germination férale. `seed` = seed global du terrain (déterminisme, philo #3).
    Renvoie l'instance créée (ou None si le plot est invalide, comme `add_plant`)."""
    from fields import founder_genes            # couche : sim ← fields
    p = tile.add_plant(plant_class, r, c)
    if p is not None:
        p.genes = founder_genes(plant_class, seed, week, r, c, p.x_cm, p.y_cm)
    return p
