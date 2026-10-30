"""
SYMBIOSE — tests/test_ciel_compose.py
Préavis dramatique du composé + « ciel de la semaine » (sprint effondrement météo ②).

On vérifie la LECTURE agrégée de la météo (aucun champ de simulation touché) :
  1. Convergence : à l'approche du collapse connu (seed 12345, an 5 → Grêle i≈2.0
     en semaine 218), la convergence est STRICTEMENT supérieure à une semaine calme.
  2. Pureté : `ciel_semaine` renvoie deux structures ÉGALES sur deux appels (déterminisme,
     philo #3, zéro RNG vivant).
  3. Masque de maîtrise (§4.3/§5) : le NOM du composé n'apparaît qu'au palier ≥ seuil ;
     sous le seuil, le ciel s'assombrit quand même (signe intensifié présent) mais rien
     ne le nomme.

Lancement : python3 -m tests.test_ciel_compose   (depuis data/code/)
"""

from sim.ciel import (
    convergence, ciel_semaine, est_compose,
    COMPOSE_SEUIL, NOMMAGE_PALIER, NOM_COMPOSE,
)

SEED = 12345
# Semaine d'observation À L'APPROCHE du collapse : la Grêle i≈2.0 tombe en 218,
# elle entre donc dans le `forecast` court observé depuis 216 (an 5).
WEEK_APPROCHE = 216   # D122 ③ : ex-1308 (fenêtres d'aléas recalées au mois réel)
WEEK_CALME = 1300     # aucune convergence : ciel dégagé les semaines suivantes


def test_convergence_superieure_a_semaine_calme():
    """À l'approche de l'an 5, la convergence dépasse strictement une semaine calme."""
    approche = convergence(SEED, WEEK_APPROCHE)
    calme = convergence(SEED, WEEK_CALME)
    assert approche > calme, (
        f"convergence à l'approche {approche} devrait dépasser le calme {calme}")
    assert calme == 0.0, "la semaine témoin doit être calme (convergence nulle)"
    # Le collapse connu franchit bien le seuil de gravité → c'est un composé.
    assert est_compose(SEED, WEEK_APPROCHE)


def test_ciel_semaine_pur():
    """Pureté : deux appels identiques renvoient une structure ÉGALE (déterminisme)."""
    a = ciel_semaine(SEED, WEEK_APPROCHE, palier_climat=5)
    b = ciel_semaine(SEED, WEEK_APPROCHE, palier_climat=5)
    assert a == b, "ciel_semaine doit être une fonction pure (résultat stable)"


def test_nom_compose_masque_par_palier():
    """Le nom du composé n'est révélé qu'au palier ≥ seuil ; sous le seuil, le ciel
    s'assombrit quand même (signe intensifié) mais reste innommé (§5)."""
    # Composé bien présent à cette semaine (préalable du test de nommage).
    assert est_compose(SEED, WEEK_APPROCHE)

    novice = ciel_semaine(SEED, WEEK_APPROCHE, palier_climat=NOMMAGE_PALIER - 1)
    expert = ciel_semaine(SEED, WEEK_APPROCHE, palier_climat=NOMMAGE_PALIER)

    assert novice.nom_compose is None, "sous le seuil, le composé ne se nomme pas"
    assert expert.nom_compose == NOM_COMPOSE, "au seuil, le composé se nomme"

    # Le signe perceptif, lui, est montré aux DEUX (le ciel s'assombrit pour tous).
    assert novice.signe_compose and expert.signe_compose
    assert novice.signe_compose == expert.signe_compose
    # La convergence (donnée brute) ne dépend pas du palier.
    assert novice.convergence == expert.convergence >= COMPOSE_SEUIL


def main():
    test_convergence_superieure_a_semaine_calme()
    test_ciel_semaine_pur()
    test_nom_compose_masque_par_palier()
    print("[ciel_compose] PASS — convergence + pureté + masque de maîtrise")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
