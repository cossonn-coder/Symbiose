"""
SYMBIOSE — fields/ecofields/matiere_organique.py
Responsabilité : le cycle de la MATIÈRE ORGANIQUE d'une tuile — litière fraîche
(parcelles typées, remplace om_fresh), décomposition biogéochimique (cascade
fresh → active → stable → minéralisation N/P/K), maturation des structures
(bac/pile), et dépôt de nécromasse.

Mixin de comportement de `EcoFields` (scission refactor 2026-06-30, container
déjà dense). N'a aucun état propre : opère sur `self` (l'instance EcoFields).
Comportement bit-identique à l'ancien `container.py`.
"""

from __future__ import annotations

from .constants import *          # constantes de calibration écologique
from .litiere import *            # Parcelle, Structure, TISSU, MATUR_*, COLONISATION_*…
from .litiere import _fusion_parcelle, _lisser_ages   # helpers privés (hors import *)
from .nutriments import split_miner, cec_norm_at, leach_factor, dispo   # chimie N/P/K pure
from .thermique import microbe_clim_factor as _microbe_clim_factor      # cloche T × humidité (météo→champs ④)


class MatiereOrganiqueMixin:
    """Litière, décomposition, structures de compostage et nécromasse."""

    # --- Litière (couche fraîche : parcelles, remplace om_fresh) ---

    def om_fresh_at(self, r: int, c: int) -> float:
        """Σ des masses de parcelles du plot = ancien `om_fresh.at_plot(r,c)`."""
        return sum(p.masse for p in self.litiere[r][c])

    def bois_fresh_at(self, r: int, c: int) -> float:
        """Σ des masses de litière C-riche fraîche d'un plot (tissus `FAIM_N_TISSUS`
        = `bois`/BRF + `substrat` usé de champignons) — pilote la faim d'azote (⑦,
        §2.7). `substrat` reste INERTE tant qu'aucun acteur champignon ne le dépose
        (jamais dans le smoke) → cet accesseur ne voit que le `bois` aujourd'hui."""
        return sum(p.masse for p in self.litiere[r][c] if p.tissu in FAIM_N_TISSUS)

    def om_fresh_average(self) -> float:
        """Moyenne par plot de la litière fraîche = ancien `om_fresh.average()`."""
        n = self.rows * self.cols
        if not n:
            return 0.0
        total = sum(p.masse
                    for row in self.litiere for cell in row for p in cell)
        return total / n

    def deposer_litiere(self, r: int, c: int, tissu: str, masse: float) -> None:
        """Point d'entrée UNIQUE pour tout écrivain de matière fraîche.

        Fusion par tissu (`_fusion_parcelle`, §1.1) : masse cumulée, `age_sem`
        moyenné par la masse (le dépôt neuf, d'âge 0, rajeunit le tas). No-op si
        `masse ≤ 0`.
        """
        if masse <= 0.0:
            return
        _fusion_parcelle(self.litiere[r][c], tissu, masse)

    def retirer_litiere(self, r: int, c: int, tissu: str, masse: float) -> float:
        """Retire (au plus) `masse` de litière du `tissu` donné d'un plot — miroir
        de `deposer_litiere`, utilisé par le transport éolien (⑦, §5.6) qui DÉPLACE
        la litière d'un plot à l'autre. Cherche la parcelle du tissu, en soustrait
        `min(masse, parcelle.masse)`, supprime la parcelle si vidée (sauf `diffus`,
        permanente comme dans la décompo). No-op si `masse ≤ 0` ou tissu absent.
        Renvoie la masse RÉELLEMENT retirée (conservation : l'appelant la redépose)."""
        if masse <= 0.0:
            return 0.0
        cell = self.litiere[r][c]
        for p in cell:
            if p.tissu == tissu:
                pris = min(masse, p.masse)
                p.masse -= pris
                if p.masse <= 1e-9 and p.tissu != "diffus":
                    cell.remove(p)
                return pris
        return 0.0

    def deposer_dans_structure(self, struct: "Structure",
                               tissu: str, masse: float) -> None:
        """Ajoute de la matière au `contenu` d'une structure (miroir de
        `deposer_litiere`, même fusion par tissu). No-op si `masse ≤ 0` ou si le
        tissu est REFUSÉ par la structure (garde-fou §5 ; le geste pré-filtre)."""
        if masse <= 0.0 or not struct.accepte(tissu):
            return
        _fusion_parcelle(struct.contenu, tissu, masse)

    def decomp_speed(self, r: int, c: int) -> float:
        """Vitesse locale de décomposition (microbiome + bioturbation des vers) —
        facteur de la fragmentation des squelettes (`engine._tick_skeletons`, ②B) :
        un bois de squelette se fragmente au rythme du sol vivant local.

        NB : depuis le ④, `tick_decomposition` (inline) module EN PLUS la part
        biologique par la cloche pH `dispo(ph,"micro")` ET la cloche climatique
        `microbe_clim_factor(T_sol, humidité)` (météo→champs ④) ; pas ici — la
        fragmentation mécanique/fongique du bois mort est moins sensible au pH/climat
        que la minéralisation bactérienne (divergence assumée, calibrage post-test)."""
        micro = self.microbiome.at_plot(r, c) / 3.0
        speed = 0.5 + micro * 0.5
        worms = self.populations["lombric"] if self.populations else None
        if worms is not None:
            speed += WORM_DECOMP_BONUS * worms.at_plot(r, c)
        # ANAÉROBIE DU MARÉCAGE (③) : le bois mort d'un plot gorgé se fragmente aussi
        # moins vite (même flux ralenti que la minéralisation ci-dessus). marais=0 ⇒
        # ×1.0 ⇒ fragmentation des squelettes strictement INCHANGÉE au repos (golden).
        speed *= (1.0 - MARAIS_DECOMP_MALUS * self.marais_memory.at_plot(r, c))
        return speed

    def tick_decomposition(self) -> None:
        """
        Cycle biogéochimique hebdomadaire — cascade OM v4 (fresh → active → stable).

        Chaque compartiment se décompose à son propre rythme, modulé par le
        microbiome (sol vivant = recyclage rapide). La masse décomposée se
        répartit en trois : humification (compartiment suivant), minéralisation
        (→ N/P/K SPLITTÉE par tissu, §2.2), respiration (CO₂, perte nette).
        Aucune création de matière.

          fresh  ──décompose──┬─ humifie → active
                              ├─ minéralise → split_miner(tissu) → n/p/k
                              └─ respire (perdu)
          active ──décompose──┬─ humifie → stable
                              ├─ minéralise → split_miner("humus") → n/p/k
                              └─ respire (perdu)
          stable ──décompose──┬─ minéralise → split_miner("humus") → n/p/k
                              └─ respire (perdu)

        La litière feuillue nourrit surtout l'azote, le fruit la potasse, le bois
        peu (immobilisation). Puis lessivage DIFFÉRENCIÉ par nutriment, modulé par
        la CEC dérivée (texture + humus) : N≫K>P (§2.4/§2.5).
        """
        worms = self.populations["lombric"] if self.populations else None
        for r in range(self.rows):
            for c in range(self.cols):
                micro = self.microbiome.at_plot(r, c) / 3.0
                # ④ LOCKOUT pH : l'activité bactérienne suit une cloche autour du
                # neutre (ph → microbiome → minéralisation, couplage indirect sans
                # champ neuf). Module la part BIOLOGIQUE de la vitesse uniquement —
                # pas le socle abiotique (0.5) ni la bioturbation mécanique du ver.
                micro *= dispo(self.ph.at_plot(r, c), "micro")
                # MICROBIOME CLIMATIQUE (sprint météo→champs ④, §5) : l'activité suit
                # une CLOCHE de température et chute au SEC comme au gel. Terme
                # MULTIPLICATIF (pas de champ neuf), posé sur la MÊME part biologique
                # `micro` (se COMBINE avec pH/famine, ne les remplace pas, §Pièges).
                # f_clim=1 (sol doux et frais) ⇒ décompo strictement INCHANGÉE. Lit la
                # T_sol et l'humidité DÉJÀ calculées ce tick (thermique 2b, hydro 3
                # AVANT la décompo 4). Émergent : litière qui s'accumule l'hiver/en
                # sécheresse, recyclage qui repart au réchauffement/à la pluie.
                hum_norm = min(1.0, self.humidite.at_plot(r, c) / 3.0)
                micro *= _microbe_clim_factor(self.temperature_sol.at_plot(r, c), hum_norm)
                speed = 0.5 + micro * 0.5   # sol vivant décompose jusqu'à 2× plus vite
                # Bioturbation du LOMBRIC (④d : le ver, pas le cloporte, brasse l'humus
                # du sol) : accélère « un poil » la décompo locale (D31.2, option sobre ;
                # structure/aération = D30 différé). Cloporte = litière (dette si littéral).
                if worms is not None:
                    speed += WORM_DECOMP_BONUS * worms.at_plot(r, c)
                # ANAÉROBIE DU MARÉCAGE (sprint hydrologie & marécages ③) : un plot
                # gorgé en permanence (`marais_memory` → 1) manque d'oxygène → la
                # décompo se BLOQUE (`× (1 − MARAIS_DECOMP_MALUS · marais_memory)`).
                # La litière s'accumule sans se minéraliser → l'épaisseur monte via
                # `tick_epaisseur` = TOURBE émergente (aucun code neuf, couple D40).
                # marais_memory=0 (repos) ⇒ ×1.0 ⇒ décompo strictement INCHANGÉE.
                speed *= (1.0 - MARAIS_DECOMP_MALUS * self.marais_memory.at_plot(r, c))

                # Lectures AVANT toute mutation (ordre historique : d_active se
                # calcule sur l'active d'AVANT l'humification du frais → équivalence).
                fresh  = self.om_fresh_at(r, c)   # Σ parcelles, avant décompo (famine)
                active = self.om_active.data[r][c]
                stable = self.om_stable.data[r][c]

                # 1. Couche fraîche = parcelles de litière (§1.3). Chaque parcelle
                #    décompose à la cinétique de son tissu ; on accumule les flux
                #    humif/miner pour les appliquer en UN add (comme l'ancien fresh).
                cell = self.litiere[r][c]
                cell.sort(key=lambda p: TISSU_ORDER.index(p.tissu))
                fresh_humif = 0.0
                fresh_n = fresh_p = fresh_k = 0.0   # minéral splitté PAR tissu (§2.2)
                survivors = []
                for p in cell:
                    decay, humif, miner = TISSU[p.tissu]
                    d = p.masse * decay * speed
                    # Terme SAPROPHYTE (mycélium ②) : le champignon lignivore
                    # accélère la décompo du SEUL `bois` là où le réseau est
                    # installé (`×(1+ALPHA_SAPRO·mycelium)`). mycelium=0 ⇒ ×1.0
                    # ⇒ bois non colonisé strictement INCHANGÉ ; aucun autre tissu
                    # touché (spécialiste du ligneux). Flux → décompo, jamais la
                    # plante (philo #2). at_plot ∈ [0,1], zéro RNG (philo #3).
                    if p.tissu == "bois":
                        d *= 1.0 + ALPHA_SAPRO * self.mycelium.at_plot(r, c)
                    p.masse  -= d
                    p.age_sem += 1.0
                    fresh_humif += d * humif
                    dn, dp, dk = split_miner(p.tissu, d * miner)
                    fresh_n += dn; fresh_p += dp; fresh_k += dk
                    # (le reste est respiré — perte nette)
                    if p.tissu == "diffus" or p.masse > 1e-9:
                        survivors.append(p)   # `diffus` permanente même à masse 0
                self.litiere[r][c] = survivors

                # 2. Active   3. Stable
                d_active = active * OM_ACTIVE_DECAY * speed
                d_stable = stable * OM_STABLE_DECAY * speed

                self.om_active.add(r, c, -d_active + fresh_humif)
                self.om_stable.add(r, c, -d_stable + d_active * OM_ACTIVE_HUMIF)

                # Minéral issu des compartiments humifiés (sans tissu propre) :
                # ratio NPK « humus » moyen (§2.2). Bilan : frais splitté par tissu
                # + humus splitté → n/p/k (le reste respiré a déjà été ôté).
                humus_miner = d_active * OM_ACTIVE_MINER + d_stable * OM_STABLE_MINER
                dn, dp, dk = split_miner("humus", humus_miner)
                self.n.add(r, c, fresh_n + dn)
                self.p.add(r, c, fresh_p + dp)
                self.k.add(r, c, fresh_k + dk)

                # Puits microbien : sans carbone frais, les microbes meurent.
                # famine ∈ [0,1] : nulle si litière abondante, maximale si épuisée.
                famine = 1.0 - min(1.0, fresh / MICROBE_FOOD_REF)
                if famine > 0.0:
                    self.microbiome.data[r][c] *= (1.0 - MICROBE_DECAY_MAX * famine)

                # Lessivage DIFFÉRENCIÉ (§2.4) modulé par la CEC dérivée (§2.5) :
                # texture (CEC_PAR_SOL) + humus stable normalisé /5.0 (même échelle
                # que vitalité). N très mobile, P quasi nul, K moyen.
                om_n = min(1.0, self.om_stable.at_plot(r, c) / 5.0)
                cn = cec_norm_at(self.soil_type, om_n)
                # AMPLIFICATION PAR LA PLUIE (sprint météo→champs ③, §4) : on ne RECRÉE
                # pas le lessivage, on l'amplifie ∝ l'eau qui a DRAINÉ ce tick (lue dans
                # `drainage_last`, écrite par `tick_hydrology` AVANT nous, ordre §Pièges).
                # `facteur_pluie ≥ 1` : à 1 → leach_factor inchangé (= comportement ①) ;
                # > 1 → rétention^p < rétention → on lessive PLUS. Capé (anti-vidage).
                drainage_norm = min(1.0, self.drainage_last.at_plot(r, c) / DRAINAGE_PERTE_REF)
                facteur_pluie = 1.0 + LESSIVAGE_PLUIE_K * drainage_norm
                if facteur_pluie > FACTEUR_PLUIE_CAP:
                    facteur_pluie = FACTEUR_PLUIE_CAP
                # Hiérarchie de mobilité N≫K>P : N pleine amplification, K atténué, P
                # ÉPARGNÉ (puissance 1 — le phosphore est quasi immobile, §2.4).
                facteur_k = 1.0 + (facteur_pluie - 1.0) * LESSIVAGE_K_ATTENUATION
                self.n.data[r][c] *= leach_factor("N", cn) ** facteur_pluie
                self.p.data[r][c] *= leach_factor("P", cn)
                self.k.data[r][c] *= leach_factor("K", cn) ** facteur_k

    # --- Épaisseur de sol visible (D57, ①a) ---

    def _cible_epaisseur(self, r: int, c: int) -> float:
        """Cible bulk-density de l'épaisseur d'un plot (cm), dérivée des `om_*`.

        La litière FRAÎCHE foisonne d'autant plus qu'elle est JEUNE : chaque
        parcelle pèse `masse · 1/(1 + K_TASSE·age_sem)` (matelas aéré neuf →
        plaqué en vieillissant). L'humus active/stable est ajouté à densité
        décroissante (E_FRESH > E_ACTIVE > E_STABLE). Fonction PURE des champs MO
        (aucune mutation) → l'épaisseur SUIT la MO, elle ne la consomme pas
        (anti-double-comptage). Zéro RNG (philo #3)."""
        foisonnement_fresh = sum(
            p.masse / (1.0 + K_TASSE * p.age_sem) for p in self.litiere[r][c]
        )
        return (E_FRESH  * foisonnement_fresh
                + E_ACTIVE * self.om_active.data[r][c]
                + E_STABLE * self.om_stable.data[r][c])

    def tick_epaisseur(self) -> None:
        """Relaxation hebdomadaire de `epaisseur_sol` vers sa cible bulk-density.

        Un seul balayage O(plots × parcelles). Inertie ASYMÉTRIQUE : le sol monte
        vite sous un apport foisonnant (`TAUX_MONTEE`), descend lentement quand la
        MO se minéralise/se tasse (`TAUX_DESCENTE`) — un sol se construit plus vite
        qu'il ne s'érode sous couvert. Rognage naturel `EPAISSEUR_EROSION` chaque
        semaine (pluie, tassement de fond), plancher minéral 0 assuré par le
        GridField. AUCUN champ n'est lu en retour ce tronçon (eau/NPK = ①b) → golden
        NEUTRE (le champ n'entre dans aucune grandeur du digest). Déterministe."""
        for r in range(self.rows):
            for c in range(self.cols):
                cible = self._cible_epaisseur(r, c)
                actuel = self.epaisseur_sol.data[r][c]
                taux = TAUX_MONTEE if cible > actuel else TAUX_DESCENTE
                nouveau = actuel + (cible - actuel) * taux - EPAISSEUR_EROSION
                self.epaisseur_sol.set(r, c, nouveau)   # borné [0, EPAISSEUR_MAX]

    def tick_structures(self) -> None:
        """Maturation hebdomadaire du contenu des structures (⑤ phase B, §5.2)
        + COLONISATION FONGIQUE du tas (mycélium ⑤, §3.3/§3.4).

        Décompo CONFINÉE, miroir de `tick_decomposition` : chaque parcelle du
        contenu mûrit à la cinétique de son tissu (`TISSU[tissu]`), la fraction
        humifiée+minéralisée s'accumule dans `compost_mur` (compost mûr, jauge
        mesurée §5.3 — épandable en phase C), le reste est respiré (perte nette)
        et vieillit (`age_sem++`). Le bac mûrit vite (tendres), la pile très
        lentement (`bois`). `retourner` (drapeau `retourne_restant`) MULTIPLIE la
        vitesse et LISSE les âges du contenu pendant `RETOURNE_DUREE` semaines.

        COLONISATION (⑤, §3.3) : un tas qui contient de la matière à digérer se fait
        coloniser par le réseau (`struct.colonisation → 1`, knob `COLONISATION_K`) ;
        elle DÉCLINE à vide (tas épuisé/épandu). La colonisation MODULE la vitesse de
        maturation (`mult ×= 1 + COLONISATION_MATUR·colonisation` — voie fongique : la
        pile à bois mûrit SURTOUT par le champignon) et ENSEMENCE le champ `mycelium`
        au plot d'ancrage (`COLONISATION_SEED·colonisation`) → le tas vivant rayonne
        du réseau, et la faune fongivore ④ (`lombric` via `_mycelium_signal`) + les
        carpophores s'y installent (§3.4, le bac est ENFIN habité, par le MÊME patron
        qu'④, sans terme de faune neuf).

        Hors la colonisation, aucun champ du sol n'est touché (philo #2) : la
        maturation reste confinée à la structure ; c'est `epandre` (phase C) qui
        restitue au sol. **No-op STRICT si `structures == []`** (invariant golden ⑤ :
        boucle vide → zéro écriture, le smoke/population ne posent aucune structure).
        Déterministe : structures dans l'ordre d'insertion, contenu trié `TISSU_ORDER`,
        zéro RNG.
        """
        for struct in self.structures:
            # Colonisation fongique du tas (§3.3) : croît tant qu'il reste du contenu
            # à digérer (substrat humide riche en bois), décline à vide. Bornée [0,1].
            a_digerer = any(p.masse > 1e-9 for p in struct.contenu)
            if a_digerer:
                struct.colonisation += COLONISATION_K * (1.0 - struct.colonisation)
            else:
                struct.colonisation -= COLONISATION_K * struct.colonisation
            struct.colonisation = max(0.0, min(1.0, struct.colonisation))
            # Le tas colonisé ensemence le sol autour (plot d'ancrage) → faune ④ +
            # carpophores s'installent (§3.4). add borné [0,1] par le GridField.
            if struct.colonisation > 0.0:
                r0, c0 = struct.plot
                self.mycelium.add(r0, c0, COLONISATION_SEED * struct.colonisation)

            base = MATUR_BAC if struct.kind == "bac" else MATUR_PILE
            retourne = struct.retourne_restant > 0.0
            mult = MATUR_RETOURNE_MULT if retourne else 1.0
            mult *= 1.0 + COLONISATION_MATUR * struct.colonisation   # voie fongique (§3.3)
            struct.contenu.sort(key=lambda p: TISSU_ORDER.index(p.tissu))
            survivors = []
            for p in struct.contenu:
                decay, humif, miner = TISSU[p.tissu]
                d = p.masse * decay * base * mult
                p.masse  -= d
                p.age_sem += 1.0
                struct.compost_mur += d * (humif + miner)   # le reste est respiré
                if p.masse > 1e-9:
                    survivors.append(p)
            struct.contenu = survivors
            if retourne:
                _lisser_ages(struct.contenu)
                struct.retourne_restant -= 1.0

    def add_necromass(self, r: int, c: int,
                      biomass: float, harvested: bool = False,
                      tissu: str = "herbace") -> float:
        """
        Ajoute de la nécromasse au plot lors d'une mort ou récolte.
        harvested=True : une fraction est exportée (récolte) → moins de retour sol.
        Retourne la quantité effectivement déposée.

        `tissu` (décompo·compost ②, kickoff §A.2) : la couche fraîche est typée par
        constitution. Défaut `herbace` (tiges molles, résidus de récolte) → compat
        bit-identique avec ① ; les appelants raffinent (`feuille` pour les caducs
        via `sim.effects.tissu_mort`). Le `bois` du squelette mort se déposera
        lentement par fragmentation (phase B), PAS ici (la mort ne dépose que mou).
        """
        # Récolte exporte BIOMASS_EXPORT, mort laisse tout sur place.
        # La nécromasse fraîche entre par la litière (cascade ensuite).
        export_fraction = BIOMASS_EXPORT if harvested else 0.0
        deposited = biomass * (1.0 - export_fraction)
        self.deposer_litiere(r, c, tissu, deposited)
        return deposited
