"""
SYMBIOSE — fields/ecofields/hydrologie.py
Responsabilité : le cycle HYDROLOGIQUE d'une tuile (évaporation couplée à la
T_sol + au ciel clair + au vent, pluie de fond/météo infiltrée ∝ structure,
rétention soil_memory, drainage par type de sol).

Mixin de comportement de `EcoFields` (scission refactor 2026-06-30, container
déjà dense). Aucun état propre : opère sur `self`. Comportement bit-identique
à l'ancien `container.py`.
"""

from __future__ import annotations

from .constants import *          # BASE_RAIN, EVAP_*, DRAINAGE*, SOIL_RETENTION…
from .nutriments import cec_norm_at   # module la rétention d'épaisseur par la composition (①b)


class HydrologieMixin:
    """Cycle hydrologique complet de la tuile."""

    def tick_hydrology(self, soil_type: str = "terre",
                       drainage_override: float | None = None,
                       pluie_event: float = 0.0,
                       nebulosite: float = 1.0,
                       vent_masse_air: float = 0.0,
                       vent_field: "GridField | None" = None) -> list:
        """
        Cycle hydrologique complet. Ordre strict :
          1. Évaporation atmosphérique (couplée à la température : chaud → +)
          2. Pluie de fond (apport diffus constant)
          3. Rétention sol (couplage soil_memory)
          4. Drainage naturel — fonction du `soil_type` (§2.3 a, Q11)
        L'uptake racinaire est géré séparément dans engine.

        `soil_type` (passé par l'engine, qui porte la `Tile`) choisit le drainage
        dans `DRAINAGE_PAR_SOL` ; défaut/inconnu → `DRAINAGE` (terre = 0.993,
        valeur historique) → la tuile terre du golden reste bit-identique.

        `drainage_override` (sprint pots/bacs ①) : si fourni (non `None`), il
        REMPLACE le drainage choisi par `soil_type`. Un conteneur (mini-sol)
        passe ainsi le drainage de SON substrat (registre `world.substrat`).
        Défaut `None` → comportement actuel inchangé : aucun appelant existant ne
        le passe → les tuiles restent BIT-IDENTIQUES (golden neutre).

        `pluie_event` (sprint météo→champs ①, §2.2) : apport d'eau de l'événement
        météo du tick (`PLUIE_APPORT[event.kind]`, positif=pluie, négatif=pluie de
        fond tarie en sécheresse). Ajouté à `BASE_RAIN` PUIS infiltré ∝ structure du
        sol (étape 2) — l'apport météo suit le MÊME canal que la pluie de fond, donc
        un sol battu en laisse ruisseler une part. Borné `BASE_RAIN + pluie_event ≥ 0`
        (on ne soustrait jamais d'eau arbitrairement : l'évaporation s'en charge).
        Défaut 0 → appelants existants (conteneurs pots/bacs) strictement inchangés.

        RETOUR (sprint pots/bacs ⑤) : la PERTE de drainage par cellule, sous forme
        `[(r, c, perte), …]` (perte = `h_avant_drainage · (1 − drainage)`, l'eau
        qui s'écoule du fond). Une tuile la JETTE (aucun appelant existant ne lit
        le retour → strictement rétrocompatible, golden bit-identique). Un conteneur
        à FOND OUVERT/percé l'INJECTE dans l'humidité de la tuile sous lui (pont
        matière §5). On RETOURNE la perte plutôt que de dupliquer la boucle
        hydrologique côté `world` (piège du kickoff : ne pas la ré-implémenter).

        EFFET DE BORD (sprint météo→champs ③, §4) : la perte de drainage par plot est
        AUSSI écrite dans `self.drainage_last` (carte transiente du tick), que
        `tick_decomposition` lit pour AMPLIFIER le lessivage NPK ∝ l'eau qui draine.

        `nebulosite` ∈ [0,1] et `vent_masse_air` ∈ [0,1+] (sprint VENT &
        ÉVAPOTRANSPIRATION ②, §3) : les DEUX pilotes neufs de l'évaporation, scalaires
        PAR TICK (météo uniforme sur la tuile, comme T_air — pas des champs par plot).
        Ciel clair (`nebulosite→0`) ET vent fort assèchent en plus de la chaleur.
        Calculés par la boucle (`weather_state` ④ + `wind_at` ① — la couche `fields`
        n'importe pas `sim`, donc on les reçoit en argument). DÉFAUTS `nebulosite=1.0`
        (ciel couvert → terme rayonnement NUL) et `vent_masse_air=0.0` (calme → terme
        vent NUL) : tout appelant existant qui ne les passe pas (conteneurs pots/bacs)
        reste BIT-IDENTIQUE. La boucle, elle, passe les vraies valeurs → re-figeage
        golden LARGE ANNONCÉ (l'évaporation réagit enfin au ciel clair et au vent).
        """
        drainage = (drainage_override if drainage_override is not None
                    else DRAINAGE_PAR_SOL.get(soil_type, DRAINAGE))
        # Apport total de la pluie de fond + météo, borné ≥ 0 (on ne retire jamais
        # d'eau ; en sécheresse l'apport négatif tarit la pluie de fond, sans plus).
        apport = max(0.0, BASE_RAIN + pluie_event)
        pertes: list = []
        for r in range(self.rows):
            for c in range(self.cols):
                h = self.humidite.data[r][c]
                # 1. Évaporation : multiplicateur de base diminué quand il fait
                # chaud (au-dessus de EVAP_TEMP_REF), borné par EVAP_MIN.
                # Lit DÉSORMAIS la T_sol microclimatique (sprint thermique ①) : un
                # plot ensoleillé surchauffe et s'assèche, un plot ombragé reste frais.
                temp = self.temperature_sol.data[r][c]
                evap = EVAPORATION - EVAP_TEMP_COEF * max(0.0, temp - EVAP_TEMP_REF)
                # RAYONNEMENT + VENT (sprint VENT & ÉVAPOTRANSPIRATION ②, §3) : deux
                # pertes ADDITIVES de plus. Ciel clair (1−nébulosité→1) assèche le jour
                # — c'est le contre-flux exact de la rosée des nuits claires, qui sans
                # lui faisait monter l'humidité jusqu'à l'asphyxie (D39). Le vent balaie
                # la couche limite humide → évaporation ↑ (uniforme au ②, spatialisé ③).
                evap -= EVAP_RAD_COEF * (1.0 - nebulosite)
                # VENT : champ d'abri SPATIALISÉ si fourni (③ : `eco.vent[r,c]` — un
                # coin abrité s'assèche moins, un goulet venturi plus), sinon masse
                # d'air UNIFORME (②, fallback rétro-compatible pour pots/bacs).
                vloc = vent_field.data[r][c] if vent_field is not None else vent_masse_air
                evap -= EVAP_WIND_COEF * vloc
                # COUVERTURE DU SOL (sprint LUXURIANCE ①, D65 §2.1) : un sol couvert par
                # un tapis bas (couvre-sol) perd MOINS d'eau — l'eau reste piégée sous le
                # feuillage. On rapproche le multiplicateur d'évaporation de 1.0 (rétention
                # pure) ∝ la couverture : `evap += (1−evap)·FRAC·couverture`. C'est un FLUX
                # (l'eau du plot est conservée), jamais un bonus sur la plante (philo #2).
                # Couverture NULLE (aucune plante basse) → terme nul → évaporation
                # inchangée. La tuile 2 du golden porte du Clover (strate basse) → terme
                # actif → RE-FIGEAGE MAÎTRISÉ ANNONCÉ (humidité un peu plus haute sous couvert).
                cov = self.couverture_sol.data[r][c]
                evap += (1.0 - evap) * COUVERTURE_EVAP_FRAC * cov
                if evap < EVAP_MIN:
                    evap = EVAP_MIN
                h *= evap                                           # 1. évaporation
                # 2. pluie de fond INFILTRÉE ∝ structure (⑧, couplage lecteur §2.3) :
                # un sol grumeleux absorbe toute la pluie de fond, un sol compacté en
                # laisse RUISSELER une part (perdue). Lit la structure du tick précédent
                # (champ lent → OK). structure terre héritée 0.7 < 1.0 → golden re-figé.
                h += apport * self.structure_sol.at_plot(r, c)      # 2. pluie (fond+météo) infiltrée
                h += self.soil_memory.at_plot(r, c) * SOIL_RETENTION  # 3. rétention
                # 3b. RÉTENTION D'ÉPAISSEUR (D57 ①b) : miroir de la rétention (3),
                # un sol PROFOND garde l'eau. Lit `epaisseur_sol` du tick PRÉCÉDENT
                # (l'hydro tourne AVANT `tick_epaisseur` 13b-bis — décalage 1 tick
                # uniforme, déterministe, voulu ①a), normalisée par une borne plausible.
                # MODULÉE PAR LA COMPOSITION (`cec_norm_at`, patron nutriments) : l'humus
                # profond compte PLUS sur sable pauvre/drainant que sur argile déjà
                # rétentrice — effet émergent, jamais direct sur la plante (philo #2). Le
                # revers asphyxie (D39, sol gorgé) n'est PAS bridé (conséquence assumée).
                # epaisseur=0 (mini-sol de conteneur qui ne ticke pas l'épaisseur) ⇒ terme
                # nul ⇒ bit-identique pour eux.
                ep_n = min(1.0, self.epaisseur_sol.at_plot(r, c) / EPAISSEUR_NORM_REF)
                om_n = min(1.0, self.om_stable.at_plot(r, c) / 5.0)
                h += ep_n * EPAISSEUR_RETENTION * cec_norm_at(soil_type, om_n)  # 3b. épaisseur
                perte = h * (1.0 - drainage)
                pertes.append((r, c, perte))                        # eau du fond (⑤)
                # On MÉMORISE la perte par plot (③) pour le lessivage amplifié de
                # `tick_decomposition` — on lit le flux déjà calculé, on ne RE-CALCULE
                # PAS l'hydrologie ailleurs (piège du kickoff, cf. sprint pots/bacs).
                self.drainage_last.set(r, c, perte)
                h *= drainage                                       # 4. drainage (par sol)
                # 5. CAPTURE DU SURPLUS (sprint hydrologie & marécages ②) : les pores
                # ne stockent pas au-delà de HUM_CAP. L'excédent `h − HUM_CAP` ne se
                # jette plus (écrêtage silencieux du GridField) mais part en LAME DE
                # SURFACE `eau_surface`, qui ruisselle ensuite (`tick_ruissellement`).
                # h ≤ HUM_CAP dans l'immense majorité des cas (drainage+évap) ⇒ terme
                # NUL ⇒ eau_surface reste 0 ⇒ golden NEUTRE tant qu'aucun plot ne gorge ;
                # les plots saturés du smoke en produisent → re-figeage LARGE ANNONCÉ.
                if h > HUM_CAP:
                    self.eau_surface.add(r, c, h - HUM_CAP)
                    h = HUM_CAP
                self.humidite.set(r, c, h)
        return pertes
