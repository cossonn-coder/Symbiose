# SYMBIOSE — tools/jardinier_auto/rapport.py
# RAPPORT D'IMPASSES AGRÉGÉ (§7, livrable ⑤) — le « trous de gameplay » lisible.
# Le détecteur d'impasses (impasses.py) consigne, tick par tick, chaque facteur
# limitant diagnostiqué SANS geste-réponse applicable. Ce module ne fait AUCUNE
# mesure neuve : il RELIT le journal (`automate_journal`) et agrège les entrées de
# catégorie `impasse` par (cause, facteur, tuile) en un résumé texte.
#
# Fonction PURE (lecture seule du game_state) → aucun effet moteur, golden intact.
# Déterministe : tri stable sur des clés totales (philo #3), zéro RNG.

from __future__ import annotations

from .trace import journal

# Libellés lisibles des causes d'impasse (impasses.py) pour le rapport humain.
_LIBELLE_CAUSE = {
    "geste_inexistant": "aucun geste dans la table (mécanique absente du jeu)",
    "geste_verrouille": "geste verrouillé (maîtrise/action non débloquée)",
    "ravitaillement_manquant": "ravitaillement manquant (pailler sans mulch)",
    "objectif_inatteignable": "objectif inatteignable (cible absente, hors moyen)",
}


def _impasses(game_state: dict) -> list:
    """Les entrées de journal de catégorie `impasse`, dans l'ordre chronologique."""
    return [e for e in journal(game_state) if e.get("categorie") == "impasse"]


def agreger_impasses(game_state: dict) -> dict:
    """Agrège les impasses par clé `(cause, facteur_limitant, tile_id)` → compte.
    Renvoie un dict ordinaire (comptage) ; la mise en forme est déléguée à
    `rapport_impasses`. Séparé pour être testable sans parser du texte."""
    compte: dict[tuple, int] = {}
    for e in _impasses(game_state):
        cle = (e["cause"], e["facteur_limitant"], e["tile_id"])
        compte[cle] = compte.get(cle, 0) + 1
    return compte


def rapport_impasses(game_state: dict) -> str:
    """Résumé texte des « trous de gameplay » rencontrés par l'automate. Groupé par
    CAUSE (le type de trou), puis détaillé par (facteur, tuile). Ex. :

        RAPPORT D'IMPASSES — 240 signalements
        ● ravitaillement manquant (pailler sans mulch) — 228
            sol_nu           sur T0   ×  57
            sol_nu           sur T3   ×  57
        ● aucun geste dans la table (mécanique absente du jeu) — 12
            exces_eau        sur T2   ×  12

    Chaîne vide si aucune impasse (jardin sans trou détecté)."""
    compte = agreger_impasses(game_state)
    total = sum(compte.values())
    if total == 0:
        return "RAPPORT D'IMPASSES — aucune impasse détectée."

    # Sous-total par cause (pour l'ordre des sections : cause la plus fréquente
    # d'abord, puis nom pour départager → tri total déterministe).
    par_cause: dict[str, int] = {}
    for (cause, _facteur, _tid), n in compte.items():
        par_cause[cause] = par_cause.get(cause, 0) + n
    causes_triees = sorted(par_cause.items(), key=lambda kv: (-kv[1], kv[0]))

    lignes = [f"RAPPORT D'IMPASSES — {total} signalement(s)"]
    for cause, sous_total in causes_triees:
        libelle = _LIBELLE_CAUSE.get(cause, cause)
        lignes.append(f"● {libelle} — {sous_total}")
        # Détail (facteur, tuile) de cette cause, plus fréquent d'abord puis clé.
        details = sorted(
            ((f, t, n) for (c, f, t), n in compte.items() if c == cause),
            key=lambda x: (-x[2], x[0], x[1]))
        for facteur, tile_id, n in details:
            lignes.append(f"    {facteur:<18} sur {tile_id:<5} × {n:>4}")
    return "\n".join(lignes)
