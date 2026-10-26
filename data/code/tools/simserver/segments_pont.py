"""
SYMBIOSE — tools/simserver/segments_pont.py
Sérialisation ALLÉGÉE des segments d'une plante pour le snapshot du pont
(sprint FLUIDITÉ AN 2, tronçon ③, protocole 0.5.57).

Pourquoi un sérialiseur à part ? Les segments font ~80 % du poids du snapshot
(an 2 : ~16 500 segments, ~4,7 Mo de JSON). `PlantInstance.structure_to_dict()`
reste le format COMPLET et FIDÈLE (round-trip exact) dont ont besoin la
restauration de structure, `tests/test_croissance.py`, `tools/profile_monde.py`…
On ne le touche donc PAS : on écrit ici une version « vue » de la même liste.

Ce qui change par rapport à `Segment.to_dict()` :
  - `auxin` est RETIRÉ : la vue ne le lit pas (grep C# : seul un commentaire de
    `core/PlantStructure.cs` le mentionne). C'est un état interne de la
    morphogénèse (dominance apicale), pas un indice visuel.
  - les flottants sont ARRONDIS à la précision perceptible :
      · `base` (cm) et `length_cm` à 0,01 cm — plus fin que les 0,1 cm du kickoff
        parce que la vue enchaîne base + dir × longueur : à 1,56 px/cm × 32 (zoom
        max) une erreur de 0,05 cm ferait ~2,5 px de jour entre deux segments ;
        à 0,01 cm l'écart reste sous le demi-pixel ;
      · `dir` (vecteur unitaire) à 1e-3 — erreur d'angle ≤ ~1 mrad, soit < 0,01 cm
        au bout d'un segment de 8 cm ;
      · `thickness_cm` à 0,01 cm — plancher mesuré 0,3 cm (s120, monde `full`) →
        erreur relative ≤ 2 %, invisible sur une largeur de trait.
  - `has_bud` est RETIRÉ aussi : ni la vue (même commentaire C#) ni aucun test /
    outil ne le lit dans le snapshot (grep) — ~15 octets × 16 500 segments.
  - `parent`, `is_apex`, `age_weeks` sont transmis tels quels (entiers / booléens ;
    `is_apex` et `age_weeks` sont lus en C#, `parent` par `tests/simserver/taille.py`).

📖 Pédagogie (côté embarqué) : c'est la même idée qu'une trame série où l'on
choisit la largeur de chaque champ à la résolution du capteur — envoyer 17 chiffres
significatifs pour une position qu'on dessine au pixel, c'est payer la bande
passante (et ici le `json.dumps` + le parse Godot) pour du bruit. `round()` est
déterministe → deux snapshots du même état restent identiques octet à octet.

Coût (mesuré s120, 655 plantes, 16 500 segments) : `round(x, 2)` passe par
l'arrondi décimal exact de CPython (~0,8 µs) → 8 arrondis × 16 500 segments
doublaient la sérialisation des segments. Deux parades :
  1. `round(x * 100) / 100` (~0,35 µs) : `round` SANS ndigits est un simple rint ;
     l'entier n divisé par 100 donne le double le plus proche du décimal n/100,
     dont la repr courte est ce décimal (repr identique à `round(x, 2)` sur
     100 000 tirages ; seuls des cas « pile au milieu » pourraient différer —
     sans importance, le résultat reste DÉTERMINISTE) ;
  2. un CACHE PAR SEGMENT à deux générations : `base`/`dir` sont des tuples
     IMMUABLES que la croissance ne remplace que si la géométrie change (mesuré
     s60→s63 : 95 % des segments gardent les mêmes objets d'une semaine à
     l'autre, 68 % gardent aussi longueur ET épaisseur). Clé = `id(segment)` +
     gardes d'identité/égalité (l'entrée RETIENT le segment → son id ne peut pas
     être recyclé tant qu'elle vit). Chaque snapshot ne garde que les entrées
     servies pendant SA passe → mémoire bornée au monde courant.
     ⚠️ Les listes `base`/`dir` arrondies sont PARTAGÉES d'un snapshot à l'autre :
     un lecteur en processus ne doit pas les muter (aucun ne le fait — le pont
     les sérialise, les tests les lisent).
📖 C'est un cache « double tampon » : on lit l'ancienne génération, on écrit la
neuve, puis on permute — ce qui n'a pas été relu disparaît tout seul (pas de LRU).
"""
from __future__ import annotations


class SegmentsVue:
    """Sérialiseur de segments pour la vue, avec cache des valeurs arrondies.
    Une instance par serveur ; `nouvelle_passe()` en tête de chaque `_snapshot()`."""

    def __init__(self):
        # id(segment) → (segment, base, dir, length, thickness,   ← clé de validité
        #                base_arrondie, dir_arrondie, length_arr, thickness_arr)
        self._ancien: dict = {}   # entrées de la passe N-1
        self._neuf: dict = {}     # entrées servies pendant la passe N

    def nouvelle_passe(self) -> None:
        """Permute les générations : ce qui n'a pas resservi est oublié."""
        self._ancien, self._neuf = self._neuf, {}

    def entrees(self, segments) -> list:
        """Les entrées de cache (mêmes arrondis que `segments`) d'une liste de
        segments, pour le pont en DELTA (`pont_delta`, 0.6.0) : indices 5-8 =
        base, dir, longueur, épaisseur arrondies. Même garde que `segments`."""
        ancien_get, neuf = self._ancien.get, self._neuf
        out = []
        for s in segments:
            b, d, lg, ep = s.base, s.dir, s.length_cm, s.thickness_cm
            e = ancien_get(id(s))
            if (e is None or e[0] is not s or e[1] is not b or e[2] is not d
                    or e[3] != lg or e[4] != ep):
                e = (s, b, d, lg, ep,
                     [round(b[0] * 100) / 100, round(b[1] * 100) / 100,
                      round(b[2] * 100) / 100],
                     [round(d[0] * 1000) / 1000, round(d[1] * 1000) / 1000,
                      round(d[2] * 1000) / 1000],
                     round(lg * 100) / 100, round(ep * 100) / 100)
            neuf[id(s)] = e
            out.append(e)
        return out

    def segments(self, segments) -> list:
        """Liste de dicts segment pour le snapshot (format `Segment.to_dict()` SANS
        `auxin` ni `has_bud`, flottants arrondis). Mêmes clés que celles lues par
        `PlantStructure.ParseSegment` côté C# (+ `parent`) ; même ordre que
        `structure_to_dict()` (l'index = `target.segment` des gestes de taille)."""
        ancien_get, neuf = self._ancien.get, self._neuf
        out = []
        ajoute = out.append
        for s in segments:
            b, d, lg, ep = s.base, s.dir, s.length_cm, s.thickness_cm
            e = ancien_get(id(s))
            # Garde de validité : MÊME objet segment (son id ne peut pas avoir été
            # recyclé : l'entrée le retient), mêmes tuples base/dir (immuables →
            # identité = valeur), mêmes flottants longueur/épaisseur.
            if (e is None or e[0] is not s or e[1] is not b or e[2] is not d
                    or e[3] != lg or e[4] != ep):
                e = (s, b, d, lg, ep,
                     [round(b[0] * 100) / 100, round(b[1] * 100) / 100,
                      round(b[2] * 100) / 100],
                     [round(d[0] * 1000) / 1000, round(d[1] * 1000) / 1000,
                      round(d[2] * 1000) / 1000],
                     round(lg * 100) / 100, round(ep * 100) / 100)
            neuf[id(s)] = e
            ajoute({
                "parent": s.parent,
                "base": e[5],
                "dir": e[6],
                "length_cm": e[7],
                "thickness_cm": e[8],
                "age_weeks": s.age_weeks,
                "is_apex": s.is_apex,
            })
        return out
