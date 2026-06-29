"""
SYMBIOSE — fields/ecofields/rosee.py
Rosée & gelée blanche : calcul PUR du cycle thermo-hydrique NOCTURNE (par plot).

Isolé de `container.py` (déjà dense) comme `thermique.py` : le conteneur n'expose
qu'une fine méthode `tick_rosee` qui délègue ici. Fonction pure, zéro RNG
(déterminisme philo #3 — la météo est déjà tirée par `_hash_noise`).

Le PIVOT physique (CONCEPTION_METEO_CHAMPS §3) : on réutilise le MÊME thermomètre
nocturne que le gel (`t_min_nuit_at`). La nuit, un sol découvert sous un ciel clair
rayonne sa chaleur et se refroidit. AVANT de geler, ce sol froid CONDENSE la vapeur
de l'air — la rosée. Le même refroidissement produit donc un CONTINUUM lu sur un
seul thermomètre :

    t_rosée[r,c]  = T_air − ÉCART_ROSÉE_SEC + GAIN_HUM_ROSÉE · humidité_norm[r,c]
    cond[r,c]     = max(0, t_rosée[r,c] − t_min_nuit[r,c]) · ROSÉE_PAR_DEGRÉ

- `humidité_norm = min(1, humidite/3)` (même échelle que `tick_thermique`) : il n'y
  a pas de champ « humidité de l'air » dédié, on le dérive de l'humidité du SOL local
  (l'évapotranspiration humidifie l'air au ras du sol). Sol sec → grand écart au point
  de rosée (peu de rosée) ; sol humide → point de rosée proche de T_air (rosée facile).
- `t_min_nuit > 0` → ROSÉE LIQUIDE : on ajoute `cond` à `humidite`. Le sol nu, un peu
  humide, sous nuit claire est le grand capteur du matin → il FREINE la spirale de
  dessèchement (levier de survie en sécheresse, §3.6) sans ressusciter un désert.
- `t_min_nuit ≤ 0` → GELÉE BLANCHE : pas d'eau liquide ce matin ; le dépôt gèle et
  s'accumule dans `eco.givre` (carte par plot, miroir spatial du scalaire `snow`). Il
  est RESTITUÉ à `humidite` au tick où `t_min_nuit` repasse > 0 (FONTE DIFFÉRÉE §3.4) —
  couplage hydrique réaliste ET sûr (zéro perte, zéro dégât au socle).

Tension VOULUE (pas un bug, §3.6) : nuit COUVERTE → peu de refroidissement → peu de
rosée ; sol PAILLÉ → isolé (couvert haut dans `t_min_nuit`) → se refroidit peu → peu
de rosée (mais il retenait déjà son eau : pas de double peine) ; sol DESSÉCHÉ → point
de rosée au plancher → peu de rosée. Ne PAS « corriger » ces régimes.

Ordre dans la boucle : `tick_rosee` tourne en 2c, APRÈS la thermique (2b) et AVANT
l'hydrologie (3) — il lit l'humidité/la litière de FIN du tick précédent (cohérent
avec l'ordre nocturne, comme `tick_thermique`) et son dépôt est ensuite drainé/diffusé
normalement. Déterministe (plots dans l'ordre, zéro RNG). Ne pas réordonner.

Le DÉGÂT FOLIAIRE de la gelée blanche (§3.5, option « riche ») est DIFFÉRÉ : voir la
note de fin de fichier. Le socle ② = dépôt + fonte (B), sûr et golden-maîtrisé.
"""

from __future__ import annotations

from .constants import (ECART_ROSEE_SEC, GAIN_HUM_ROSEE, ROSEE_PAR_DEGRE,
                        ROSEE_LOG_SEUIL)
from .thermique import t_min_nuit_at


def tick_rosee(eco, t_air: float, nebulosite: float) -> list[str]:
    """Dépose la rosée (régime liquide) ou accumule/fond le givre (régime gelée
    blanche) sur chaque plot, depuis le thermomètre nocturne `t_min_nuit_at` et
    l'humidité du sol local. Écrit `eco.humidite` (rosée + fonte différée) et
    `eco.givre` (accumulation du dépôt gelé). Pur : zéro RNG, zéro autre effet.

    Renvoie une liste de marqueurs de log AGRÉGÉS PAR TUILE (`💧 rosée` /
    `❄ gelée blanche`) émis seulement si la condensation/fonte totale dépasse
    `ROSEE_LOG_SEUIL` (signe diégétique notable, philo #5 — capté par le ledger
    d'événements en ⑤). Aucune condensation nulle part → liste vide (golden-safe)."""
    total_rosee = 0.0   # eau liquide déposée (régime > 0 °C) sur la tuile
    total_givre = 0.0    # eau gelée nouvellement déposée (régime ≤ 0 °C)
    total_fonte = 0.0    # givre restitué à l'humidité (réchauffement)
    for r in range(eco.rows):
        for c in range(eco.cols):
            t_min    = t_min_nuit_at(eco, r, c, t_air, nebulosite)
            hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
            t_rosee  = t_air - ECART_ROSEE_SEC + GAIN_HUM_ROSEE * hum_norm
            cond     = max(0.0, t_rosee - t_min) * ROSEE_PAR_DEGRE
            if t_min > 0.0:
                # Régime LIQUIDE : la condensation du matin hydrate le sol, ET le
                # givre éventuellement accumulé les nuits froides précédentes FOND
                # (fonte différée §3.4). Le givre est remis à 0 ensuite.
                gel = eco.givre.at_plot(r, c)
                eco.humidite.add(r, c, cond + gel)
                if gel > 0.0:
                    eco.givre.set(r, c, 0.0)
                    total_fonte += gel
                total_rosee += cond
            elif cond > 0.0:
                # Régime GELÉE BLANCHE : le dépôt gèle, aucune eau liquide ce tick ;
                # on mémorise pour la fonte différée (borné [0,1] par le GridField).
                eco.givre.add(r, c, cond)
                total_givre += cond
    log: list[str] = []
    if total_rosee + total_fonte >= ROSEE_LOG_SEUIL:
        log.append(f"  💧 rosée [{eco.tile_id}] dépôt {total_rosee:.3f}"
                   + (f" + fonte {total_fonte:.3f}" if total_fonte > 0 else ""))
    if total_givre >= ROSEE_LOG_SEUIL:
        log.append(f"  ❄ gelée blanche [{eco.tile_id}] givre {total_givre:.3f}")
    return log


# --- Note : dégât foliaire de la gelée blanche (§3.5, DIFFÉRÉ) --------------
# La conception propose, en OPTION « riche », un léger dégât du givre sur le
# FEUILLAGE ÉTABLI exposé (≠ semis, déjà couverts par le gel tissulaire — périmètres
# disjoints, §3.5). Réutiliser `_mediated_damage` exigerait toutefois de l'étendre :
# il cible aujourd'hui le SEUL stade « semis » (mortalite.py:301). Élargir son
# sélecteur de stade est un changement transverse au-delà du socle ②, et le kickoff
# autorise explicitement à « se contenter de B (dépôt + fonte) si le calibrage rend le
# dégât trop brutal ». On RESTE donc sur le socle sûr (dépôt + fonte), golden-maîtrisé,
# et on laisse le dégât foliaire en dette (constante `GIVRE_SEVERITY_REF` réservée en
# tête de `constants.py`). Décision consignée dans `00_etat.md` (② → choix B seul).
