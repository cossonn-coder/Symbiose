# SYMBIOSE — tools/jardinier_auto/filtre.py
# VUES LECTURE SEULE du journal de l'automate (trace.py). Le log est TOUJOURS écrit
# complet (tous niveaux, toutes catégories) : c'est ce qui en fait un oracle de
# déterminisme. La verbosité et le ciblage ne s'appliquent qu'À LA LECTURE, ici —
# jamais à l'écriture. Un run filtré et un run brut partagent EXACTEMENT le même log
# sous-jacent.
#
# Trois primitives PURES (aucune ne mute le journal ni ses lignes) :
#   - filtrer : sélection par champs (categorie, espece, objectif_id, zone,
#     niveau_max) — conserve l'ordre d'append du journal ;
#   - trier   : vue re-ordonnée par la clé canonique de raisonnement (§ trace) ;
#   - rendre  : texte lisible DÉRIVÉ des champs (jamais l'inverse — le texte n'est
#     jamais la source de vérité).
#
# Zéro RNG, zéro horodatage horloge : à journal égal, sortie égale (philo #3).

from __future__ import annotations

from .trace import _RANG_CATEGORIE


def filtrer(journal: list, *, categorie: str | None = None,
            espece: str | None = None, objectif_id: str | None = None,
            zone: tuple | None = None, niveau_max: int | None = None) -> list:
    """Sélectionne les lignes du `journal` selon des contraintes de champ. `None` =
    pas de contrainte sur ce champ. `niveau_max` garde les lignes de niveau
    `<= niveau_max` (la verbosité de lecture : 0 = décisions seules, 2 = tout).
    Renvoie une NOUVELLE liste (les lignes elles-mêmes ne sont pas copiées ni
    mutées), dans l'ordre d'origine — l'ordre d'append reste la vérité chronologique.

    `.get(...)` partout → robuste aux lignes fabriquées à la main ou legacy dont un
    champ commun serait absent (traité comme None)."""
    out = []
    for ligne in journal:
        if categorie is not None and ligne.get("categorie") != categorie:
            continue
        if espece is not None and ligne.get("espece") != espece:
            continue
        if objectif_id is not None and ligne.get("objectif_id") != objectif_id:
            continue
        if zone is not None and ligne.get("zone") != zone:
            continue
        if niveau_max is not None and ligne.get("niveau", 0) > niveau_max:
            continue
        out.append(ligne)
    return out


def trier(lignes: list) -> list:
    """Vue RE-ORDONNÉE par la clé canonique `(semaine, rang_catégorie, objectif_id,
    zone)` — l'ordre du RAISONNEMENT (perception→…→résultat) au sein d'un tick, pas
    l'ordre d'écriture. Tri STABLE (les ex æquo gardent leur ordre d'append). Clé
    totale et déterministe : chaînes et tuples comparables, `None` normalisé (`""`
    pour objectif_id, `()` pour zone) → jamais de TypeError, jamais de RNG."""
    return sorted(lignes, key=lambda l: (
        l.get("semaine", 0),
        _RANG_CATEGORIE.get(l.get("categorie"), 99),
        l.get("objectif_id") or "",
        l.get("zone") or (),
    ))


def _txt_zone(zone: tuple | None) -> str:
    """Rend une zone `(tile_id, r, c)` en `tile_id(r,c)`, ou '' si absente."""
    if not zone:
        return ""
    tid, r, c = zone
    return f"{tid}({r},{c})"


def rendre(ligne: dict) -> str:
    """Texte lisible DÉRIVÉ des champs d'une ligne (débogage humain). Couvre les
    catégories legacy (geste/impasse/consequence, clés à plat) et neuves (charge
    dans `detail`). Le texte n'est JAMAIS relu par le code — pure présentation."""
    cat = ligne.get("categorie", "?")
    sem = ligne.get("semaine", "?")
    tete = f"S{sem} [{cat}]"

    if cat == "geste":
        return (f"{tete} {ligne.get('geste')} → {ligne.get('cible')} "
                f"(facteur {ligne.get('facteur_limitant')}) = {ligne.get('resultat')}")
    if cat == "impasse":
        return (f"{tete} {ligne.get('cause')} : {ligne.get('cible')} "
                f"(facteur {ligne.get('facteur_limitant')}) sur {ligne.get('tile_id')}")
    if cat == "consequence":
        return f"{tete} {ligne.get('type')} : {ligne.get('detail')}"

    # Catégories neuves : localisation + detail dict aplati (clés triées → stable).
    loc = []
    if ligne.get("espece"):
        loc.append(str(ligne["espece"]))
    z = _txt_zone(ligne.get("zone"))
    if z:
        loc.append(z)
    if ligne.get("objectif_id"):
        loc.append(f"#{ligne['objectif_id']}")
    detail = ligne.get("detail") or {}
    faits = " ".join(f"{k}={detail[k]}" for k in sorted(detail))
    corps = " ".join(p for p in (" ".join(loc), faits) if p)
    return f"{tete} {corps}".rstrip()
