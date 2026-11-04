"""
SYMBIOSE — tools/simserver/serialize.py
Sérialisation lecture-seule du moteur vers JSON : `_world_static` (partie figée,
renvoyée au init) et `_snapshot` (état hebdo). Mixin de `SimServer` (Sprint
refactor global, SS⑤). Aucune écriture dans le moteur : on LIT l'état et on le
met en forme — c'est ce qui garantit que le golden reste intact.
"""
from __future__ import annotations

from sim.engine import saison_de
from .perf import perf_block   # banc d'observation perf (④) : RSS + assemblage
from sim import vigueur as V      # état Vigueur joueur (ensure/spend/gain, D11)
# Météo PURE (sprint thermique ⑧) : helper consolidé partagé avec l'engine
# (boucle.py étape 1) + signes diégétiques + cas calme. Recalculés ici car le
# snapshot LIT l'état sans accès aux locaux du tick — fonctions pures, golden NEUTRE.
from sim.weather import weather_state, weather_signs, CALME, T_MOY
# Ciel de la semaine (effondrement météo ②) : agrégat PUR read-only du ciel
# lisible (état courant + signes en avance + convergence du composé). Le pont
# le SÉRIALISE tel quel (④) — la couche d'affichage (encart Godot) rend, ne
# calcule rien. Zéro RNG, aucun champ de sim touché → golden NEUTRE.
from sim.ciel import ciel_semaine
# Palier de maîtrise « météo/climat » (D12) : c'est le MASQUE DE NOMMAGE de
# l'encart (§4.2). Le pont le lit côté serveur et le passe à `ciel_semaine`
# → le nom du composé n'est joint que si le palier suffit. Lecture pure d'un
# état joueur (opt-in) → golden NEUTRE (le golden tourne hors serveur).
from sim import maitrise as M
# Échantillonneur de vie macro (tranche 6·B) : fonction PURE et déterministe
# densité → entités (fields/population.py §3). L'échantillonnage se fait CÔTÉ
# SERVEUR — la vue n'a pas besoin de _hash_noise (kickoff t6 §4).
from fields.population import peindre_presence
from sim.champignon_role import pluie_semaine_precedente   # D111 ③
from .champignon_route import carpophores_compacts   # format compact (D112 ② : partagé avec le debug)
from .vision_cmds import bloc_vision, bloc_voix   # vision du jardinier (sol qui respire ⑥)
# LOD des émetteurs d'ombre (D67, sprint perf-lod-ombre ③) : on relit le SEUIL de
# pouvoir ombrageant pour DÉRIVER, par plante, si elle émet une ombre (miroir exact
# de la métrique de fields/light.py:compute). Lecture pure d'une constante de module
# → golden NEUTRE. La vue teinte les NON-émettrices sous le toggle debug.
from fields import light
# Seuil de perception d'une flaque (sprint hydrologie & marécages ②) : la liste
# creuse `eau_surface` ne consigne que les plots dont la lame le dépasse.
from fields.ecofields.constants import SEUIL_FLAQUE, COUVERTURE_RENDU_SEUIL, MARAIS_OFF, ALLELO_FLOOR, AUTOMNE_RAMP
# Semaine d'abscission PROPRE à un caduc (sprint DÉSYNC PHÉNOLOGIE ①, factorisée
# dans l'engine) : le pont la RÉUTILISE — pas de duplication de formule — pour
# tracer la rampe `automne` par-plante vers son largage. Fonction PURE.
from sim.engine.decompo import semaine_abscission
from sim.engine.transpiration import feuillage_visible
# Sémiologie foliaire (D33) : détecteurs PURS des stresseurs chroniques, miroirs
# fidèles des seuils des mécaniques qui blessent. Remplace le bool `chlorose` du ⑨
# par la liste `leaf_symptoms`. Recalcul pur côté serveur (moteur = source de
# vérité, zéro recalcul C#) → golden NEUTRE.
from sim import semiologie
# Légende des signes (PLANTE ASSEMBLÉE ⑥, 0.5.46) : ce que le joueur a APPRIS
# (signes, bêtes), lecture pure → l'info-bulle à deux niveaux de la vue (⑦).
from sim.signes import appris as signes_appris
# Déblocage des gestes (palette de gestes ①) : expo au snapshot des gestes ouverts
# pour l'avatar courant. Lecture pure d'un état joueur (opt-in) → golden NEUTRE.
from sim.actions import deblocage as DEBL
# Palette de gestes ⑤ (0.5.26) : expo au snapshot du LAYOUT curé + MACROS de
# l'avatar courant. Lecture pure d'un état joueur (opt-in) → golden NEUTRE.
from sim.actions import palette as PAL
# Table « stade reproducteur visible par saison » du prototype SVG (tranche 6,
# volet A) : import OUTIL → OUTIL (render_structure est un outil, pas le
# moteur), zéro duplication — la table validée visuellement au sprint
# Croissance reste la source unique du proxy saisonnier.
from tools.render_structure import REPRO_BY_SEASON

from .version import DEFAULT_REPRO
# Ceinture périphérique au pont (PÉRIPHÉRIE ⑦, D73) : le bloc `ceinture` du
# snapshot, opt-in (None sans ceinture). Vit dans `peripherie_route` avec le
# routage des gestes de paysage — un module = « la périphérie au pont ».
from .peripherie_route import ceinture_block
# Vent au pont (JARDIN VIVANT T3, 0.5.44) : masse d'air `weather.wind` + facteur
# d'abri par plante (lu SEULEMENT si le champ d'abri est déjà calculé). Pur.
from .vent_pont import wind_block, abri_facteur
from .quatre_feuilles_pont import marquer_quatre_feuilles
from .taille_pont import marquer_taille


def _activite_butineur(eco, agent) -> float:
    """Nourriture d'un butineur (D110) = `activite` de SON champ pollinisateur au plot
    de fin de tournée (ressource nectarifère déjà calculée par le tick). 0 si champ
    absent. Lecture pure, arrondie à 2 déc. comme les sprites."""
    field = eco.populations.get(agent.guild) if eco.populations else None
    return round(field.activite(agent.row, agent.col), 2) if field else 0.0


class SerializeMixin:
    """Mise en forme JSON du monde statique et du snapshot hebdomadaire."""

    # ------------------------------------------------------- sérialisation

    def _world_static(self) -> dict:
        """Partie STATIQUE du monde (renvoyée une fois, au init) : layout des
        tuiles + maison. Tout ce qui bouge chaque semaine va dans le snapshot."""
        gs = self.engine.game_state
        house = gs["house"]
        hx0, hy0, hx1, hy1 = house.footprint_bounds
        return {
            "tiles": [
                {"id": t.tile_id, "soil": t.soil_type,
                 "rows": t.grid_rows, "cols": t.grid_cols,
                 "origin_x_cm": t.origin_x_cm, "origin_y_cm": t.origin_y_cm}
                for t in gs["tiles"]
            ],
            "house": {"footprint_cm": [hx0, hy0, hx1, hy1],
                      "height_cm": house.height_cm},
        }

    def _snapshot(self, delta=None) -> dict:
        """Snapshot v0 minimal (kickoff tranche 1) : horloge + plantes vivantes.
        `week` = compteur moteur (prochaine semaine à simuler, 1 = rien simulé) ;
        year/season en sont dérivés. Par plante : position continue LOCALE à sa
        tuile (x_cm/y_cm + tile pour replacer en monde via origin_*_cm) et la
        structure de segments via structure_to_dict() (format Croissance·6, le
        même que tools/export_structure.py → PlantStructure.cs sait déjà lire)."""
        gs = self.engine.game_state
        week = gs["week"]
        week_in_year = ((week - 1) % 52) + 1
        saison = saison_de(week_in_year)
        # Segments allégés + cache de vecteurs arrondis (③, cf. segments_pont).
        segv = self._segments_vue
        segv.nouvelle_passe()
        # Pont en DELTA (FLUIDITÉ PC LEVIERS ④, 0.6.0) : OPT-IN de la requête
        # (`delta` = DeltaPont, cf. pont_delta). None → format complet historique.
        if delta is not None:
            delta.debut(week)
        plants = []
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            for p in tile.plants:
                cls = p.plant_class
                # Socle commun vivant/mort : l'identité (clé de diff côté vue =
                # tile|species|x|y), la position et la STRUCTURE — le bois à
                # dessiner, silhouette nue pour un squelette comme branchage pour
                # un vif. Tout le reste (organes, fruits) ne vaut que pour un vivant.
                base = {
                    "tile": tile.tile_id,
                    "species": cls.__name__,
                    "name": p.name,
                    "x_cm": p.x_cm, "y_cm": p.y_cm,
                    "stage": p.current_stage,
                    "stage_name": p.stage.name,
                    # 0,1 cm : silhouette LOD, la vue ne fait que dessiner (③, 0.5.57).
                    "height_cm": round(p.current_height, 1),
                    # Luxuriance par stratification (D65, sprint LUXURIANCE ⑥) —
                    # trois descripteurs PUR RENDU, lecture seule (hors _PLANT_ATTRS
                    # du golden → golden INTACT). Tous dérivés d'un état déjà calculé :
                    #  · `strate` = strate du stade COURANT (sol/basse/moyenne/haute/
                    #    grimpante) — pilote l'ORDRE DE DESSIN par strate côté vue
                    #    (couvre-sol SOUS potagère SOUS grimpante). Source de vérité
                    #    Python : la vue ne la recalcule pas, elle la LIT.
                    #  · `silhouette` = descripteur data d'espèce (tronçon ③,
                    #    silhouette_base : tapis/rosette/touffe/étalée/dressée/buisson) —
                    #    la vue choisit la FORME à dessiner.
                    #  · `clonal_mode` = mode de multiplication végétative
                    #    (none/stolon/rhizome/drageon) — indice de colonie clonale.
                    "strate": p.stage.strate,
                    "silhouette": cls.silhouette_base(),
                    "clonal_mode": cls.clonal_mode,
                }
                # Segments : liste complète, ou `pid` + `segd` en delta (0.6.0) ;
                # `neuve` = premier envoi de la plante → seul cas où partent les gènes.
                if delta is None:
                    base["segments"] = segv.segments(p.segments)
                    neuve = True
                else:
                    neuve = delta.plante(base, p, segv)
                # SQUELETTES post-mortem (décompo·compost ②B) : la mort ne retire
                # plus la plante — `engine._tick_skeletons` la garde TANT QU'il
                # reste du bois (seules les vivaces LIGNEUSES persistent ici ; les
                # herbacées, bois=0, sont retirées au tick même de leur mort, donc
                # jamais visibles dans un snapshot). On les EXPOSE en LECTURE pour
                # que la vue dessine la silhouette sèche/couchée. C'est de la pure
                # sérialisation (`tile.plants` contient déjà les morts) : aucune
                # écriture moteur → golden NEUTRE. `dead` est aussi posé (false) sur
                # les vivantes = drapeau explicite, lecture tolérante côté vue.
                if not p.is_alive:
                    base["dead"] = True
                    base["stade_mort"] = p.stade_mort          # "seche" | "couchee"
                    base["bois_restant"] = round(p.bois_restant, 4)
                    base["semaines_mort"] = p.semaines_mort
                    plants.append(base)
                    continue
                # Hints d'organes (tranche 6·A, kickoff §1) : les organes ne
                # sont PAS un état moteur (§J : reconstructibles à la volée) —
                # on expose le proxy SAISONNIER du prototype SVG, la vue
                # dessine. Les FLEURS restent sur ce proxy ; les FRUITS, eux,
                # ont désormais un vrai état moteur (`fruits`, ③).
                repro = REPRO_BY_SEASON.get(cls.__name__, DEFAULT_REPRO)
                base["dead"] = False
                # Vitalité continue (sprint SANTÉ & RÉSILIENCE ④, 0.5.28) :
                # `vitalite` ∈ [0,1] (1.0 = sain neuf) + `etat` discrétisé
                # ("sain"/"affaibli"/"malade"/"mort"). C'est un DESCRIPTEUR GLOBAL de
                # l'usure de la plante (érosion des stresseurs, convalescence) qui
                # COMPLÈTE les `leaf_symptoms` localisés : la vue teinte/désature le
                # feuillage ∝ vitalité (fond continu, philo #5) et compose avec les
                # marques de symptômes. PURE lecture d'un état déjà porté par
                # l'instance (`p.vitalite`/`p.etat`, portés par ①) — hors _PLANT_ATTRS
                # du golden → golden INTACT. Champs OPTIONNELS côté vue (tolérance
                # pré-0.5.28 → la vue retombe sur le mapping par symptômes seul).
                base["vitalite"] = round(p.vitalite, 3)
                base["etat"] = p.etat
                # Dossier de plante DEBUG (sprint retours UI/HUD T3, outil de test) :
                # l'état physiologique COURANT lu par le panneau au clic d'inspection
                # (WorldView.Dossier.cs → DossierPlantePanel). Trois ajouts LECTURE
                # SEULE d'un état DÉJÀ porté par l'instance (`plants/base/instance.py`)
                # — hors _PLANT_ATTRS du golden → golden INTACT (le golden tourne hors
                # serveur, ces clés ne naissent jamais pour lui).
                #  · `memoires` = les 8 intégrateurs lents de stress vécu (shade/
                #    drought/asphyxie/cold/infection/wind/root_herbivory/stress). C'est
                #    l'« histoire compressée » de la plante : shade_memory=0.8 = longtemps
                #    à l'ombre. Regroupés sous une clé pour ne pas polluer le socle.
                #  · `expression` = facteurs de plasticité ≠ 1.0 (durcissement acquis,
                #    sprint plasticité) ; dict FILTRÉ (une plante non acclimatée a tout à
                #    1.0 → dict vide, pas de bruit).
                #  · `age_weeks` (âge dans le stade) / `age_years` (âge total).
                base["memoires"] = {
                    "shade_memory": round(p.shade_memory, 3),
                    "drought_memory": round(p.drought_memory, 3),
                    "asphyxie_memory": round(p.asphyxie_memory, 3),
                    "cold_memory": round(p.cold_memory, 3),
                    "infection_memory": round(p.infection_memory, 3),
                    "wind_memory": round(p.wind_memory, 3),
                    "root_herbivory_memory": round(p.root_herbivory_memory, 3),
                    "pourriture_memory": round(p.pourriture_memory, 3),
                    "stress_memory": round(p.stress_memory, 3),
                }
                base["expression"] = {g: round(f, 3)
                                      for g, f in p.expression.items() if f != 1.0}
                base["age_weeks"] = p.age_weeks
                base["age_years"] = round(p.age_years, 2)
                # Patrimoine génétique (sprint DIVERSITÉ FONDATRICE ③) : le vecteur
                # de gènes de l'individu, exposé en DEBUG pour le survol (WorldView
                # affiche les gènes de rythme de la plante pointée → corréler « ce
                # pied est en avance » ↔ « ses gènes »). Dict clé→valeur, arrondi 3
                # déc. (déterministe, léger). PURE lecture d'un état déjà porté par
                # l'instance (`p.genes`, tiré au founder ①/hérité) : aucune écriture
                # moteur → golden NEUTRE (le snapshot n'est pas figé par test_golden).
                # `p.genes` est {} pour une plante neutre (pré-①) → dict vide toléré.
                if neuve:
                    base["genes"] = {g: round(v, 3) for g, v in p.genes.items()}
                # Sémiologie foliaire (D33, tronçon ①) : LISTE triée de symptômes
                # `[{cause, intensity}]` — généralise le bool `chlorose` du ⑨ à TOUS
                # les stresseurs chroniques (chlorose/sécheresse/asphyxie/ravageurs/
                # sénescence). Détecteurs PURS de sim/semiologie : chacun miroir du
                # SEUIL de la mécanique qui blesse (le signe ne ment pas, §2.4). La vue
                # teinte/déforme le feuillage ; elle ne relit aucun champ moteur. Liste
                # vide = plante saine. Lecture pure → golden NEUTRE (espèces neutres du
                # smoke, sols drainants : aucun symptôme).
                base["leaf_symptoms"] = semiologie.leaf_symptoms(p, eco, saison)
                foliage_density = cls.foliage_density_at(p, saison)
                base["foliage_density"] = round(foliage_density, 3)   # jauge [0,1] (③)
                # ÉMETTEUR d'ombre (LOD D67, ③) : miroir EXACT de la métrique de
                # fields/light.py:compute — pouvoir = hauteur × rayon canopée ×
                # densité foliaire, émettrice ssi ≥ SHADING_POWER_MIN. On réutilise la
                # densité déjà calculée (pas de recalcul). Lecture pure d'un DÉRIVÉ
                # (pas un état moteur neuf) → golden NEUTRE. La vue teinte les
                # NON-émettrices sous le toggle debug (semis sous-seuil que le LOD
                # écarte des boucles géométriques).
                pouvoir = p.current_height * cls.canopy_radius_at(p) * foliage_density
                base["emitteur"] = pouvoir >= light.SHADING_POWER_MIN
                base["organ"] = repro.get(saison)
                base["organ_site"] = cls.organ_site
                # Signaux phénologiques PAR-PLANTE (sprint DÉSYNC PHÉNOLOGIE ②) :
                # deux hints PUR RENDU qui débranchent fleurs et teinte automnale de
                # la SAISON GLOBALE (③ recale la vue sur eux). Hors _PLANT_ATTRS du
                # golden (comme organ/fruits/leaf_symptoms) → golden INTACT.
                #  · `floraison` = scalaire moteur `p.floraison ∈ [0,1]` (déjà porté
                #    par l'instance, écrit par engine._tick_floraison) : ③ dessine les
                #    fleurs ∝ ce scalaire, chaque pied fleurissant à SON tempo gène,
                #    au lieu du proxy saisonnier `base["organ"]`. Lecture pure.
                #  · `automne` = phénophase de coloration ∈ [0,1] : rampe montante sur
                #    les AUTOMNE_RAMP semaines qui précèdent la semaine d'abscission
                #    PROPRE du caduc (semaine_abscission, même tempo gène que ① — pas
                #    de duplication). 0 tout l'été (vert), 1 juste avant le largage ;
                #    ensuite foliage_density chute et la feuille disparaît. Ne concerne
                #    QUE les caducs (un persistant ne rougit pas → 0). DÉTERMINISTE
                #    (gène + week_in_year, zéro RNG). On NE touche PAS foliage_density_at
                #    (il sert la sim / fields/light.py) : on ne fait qu'ajouter un hint.
                base["floraison"] = round(p.floraison, 3)
                marquer_quatre_feuilles(base, p, gs.get("seed", 0))   # trèfle rare (0.6.5)
                # Abri local au vent (T3, 0.5.44) : clé OMISE si le champ d'abri
                # n'a jamais été calculé (la vue prend alors 1.0, pleine exposition).
                abri = abri_facteur(eco, p)
                if abri is not None:
                    base["abri"] = abri
                if cls.deciduous:
                    w = semaine_abscission(p)
                    automne = (week_in_year - (w - AUTOMNE_RAMP)) / AUTOMNE_RAMP
                    base["automne"] = round(max(0.0, min(1.0, automne)), 3)
                else:
                    base["automne"] = 0.0
                # Part de la couronne encore en place (AUTOMNE VISIBLE ③, 0.6.3) : la vue
                # éclaircit la couronne au rythme du largage. Lecture pure → golden neutre.
                base["feuillage"] = round(feuillage_visible(p, saison, week_in_year), 3)
                marquer_taille(base, p, week)   # coupe et pincement montrés (FORMES ②, 0.6.7)
                # Fruits traçables (③, D19) : VRAI état moteur (≠ proxy `organ`).
                # Index implicite = position dans la liste (clé du geste `manger`
                # ciblé). `segment` = ancrage structurel pour que la vue place le
                # sprite ; `maturite` pilote le rendu (vert→mûr→sur-mûr) et le gain
                # à la consommation ; `masse` la taille du sprite.
                base["fruits"] = [
                    {"segment": f.segment_id,
                     "maturite": f.maturite,
                     "masse": f.masse}
                    for f in p.fruits
                ]
                # Accroche de grimpe (D49 volet A, 0.5.18) : état `support` de la
                # plante — absent (libre / non-grimpante) ou {type, height_cm}.
                # `plant.support = (ref, height_appui)` où `ref` est un Support posé
                # (→ son `support_type`), la sentinelle MUR (str → "mur") ou une
                # PlantInstance HÔTE vivante (③ → "hote"). Duck-typing LOCAL (pas
                # d'import de sim/grimpe) : str = mur ; possède `support_type` = Support
                # posé ; sinon = hôte vivant. La vue en tire l'indice d'accroche + les
                # vrilles (⑥). PURE lecture → golden NEUTRE (aucune grimpante accrochée
                # dans le smoke → clé absente).
                if p.support is not None:
                    ref, h_appui = p.support
                    if isinstance(ref, str):
                        sup_type = "mur"
                    elif hasattr(ref, "support_type"):
                        sup_type = ref.support_type
                    else:
                        sup_type = "hote"
                    base["support"] = {"type": sup_type,
                                       "height_cm": round(h_appui, 2)}
                plants.append(base)
        # Vie macro (tranche 6·B, kickoff §4) : sprites échantillonnés depuis
        # les champs de population — PURE lecture (sample_sprites ne modifie
        # rien, positions par hash indépendantes de la semaine : un slot vit
        # toujours au même point, il apparaît/disparaît quand la densité
        # franchit son seuil).
        # SÉRIALISATION PAR ESPÈCE (faune ④e/⑥) : la clé est `f.spec.name` → depuis
        # la scission ④b/c/d le snapshot émet 10 clés d'espèce (puceron…cloporte) au
        # lieu des 3 anciennes guildes. Le pont accepte désormais `target.espece`
        # (⑥a, simserver/actions.py:ecraser ; `guilde` reste en repli pour la bascule
        # client). RESTE en ⑥b (vue Godot) : la TABLE sprite par espèce côté client.
        # Arrondis : x/y_frac 3 déc. (= 0,05 cm dans le plot), activite 2 —
        # et round() est déterministe, la clé de diff côté vue reste stable.
        # PERF VUE ② (0.5.45) : peintre « présence + points chauds »
        # (peindre_presence) à la place de sample_sprites + cap global — 1 individu
        # par espèce présente et par tuile, quelques-uns de plus aux pullulations,
        # en grappe pour les coloniales ; lombric et pollinisateurs jamais peints.
        # Le CHAMP reste intact (les gestes y retirent toujours un quantum).
        sprites = {}
        carpophores = {}
        pluie_prec = pluie_semaine_precedente(gs)
        foragers = {}
        structures = {}
        supports = {}
        litiere = {}
        alarme = {}
        temperature = {}
        condensation_by_tile = {}
        epaisseur_by_tile = {}
        altitude_by_tile = {}
        eau_surface_by_tile = {}
        marais_by_tile = {}
        couverture_by_tile = {}
        paillage_by_tile = {}
        allelopathie_by_tile = {}
        inoculum_by_tile = {}
        couvert_pose_by_tile = {}
        ombre_pose_by_tile = {}
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            # Toutes les espèces TOUJOURS présentes (listes vides comprises) —
            # invariant du protocole (une clé par espèce et par tuile).
            sprites[tile.tile_id] = {
                f.spec.name: [[s.row, s.col, round(s.x_frac, 3), round(s.y_frac, 3),
                               round(s.activite, 2)]
                              for s in peindre_presence(f, gs["seed"])]
                for f in eco.populations.values()}
            # Carpophores (sprint mycélium ④, §1.1) : champignons VISIBLES
            # échantillonnés du champ `mycelium` — PERCEPTION PURE (aucun état
            # moteur, dérivés du champ comme les sprites macro). Format COMPACT par
            # tuile : `[r, c, x_frac, y_frac, densite, rôle, espèce]`. Sol humide,
            # réseau dense, après la pluie → liste VIDE sinon → pont neutre. PURE lecture (sample_carpophores ne modifie rien) → golden NEUTRE.
            # INFO-BULLE DU VIVANT ① (0.5.47) : 6ᵉ champ = RÔLE LOCAL `b`/`r`/`h`
            # (bois / racines / humus, `sim/champignon_role`).
            # SOL QUI RESPIRE ③ (0.5.52) : fructification la semaine qui SUIT une
            # semaine de pluie (`pluie_prec`, calculé une fois hors boucle) et ESPÈCE
            # déduite de la niche (bois / humus / racines d'hôte) → 7ᵉ champ = clé
            # d'espèce (`fields/fongique.REGISTRE_FONGIQUE`). Racines indexées une
            # fois par tuile, seulement les semaines qui suivent une pluie.
            # SOL QUI RESPIRE ⑥ : échantillonnage factorisé (`sim/champignon_manger`,
            # même source que le geste `manger`) — moins les carpophores MANGÉS cette
            # semaine (mémoire de perception, jamais lue par le tick).
            # SOL QUI RESPIRE ⑧ (0.5.56) : 8ᵉ champ = SLOT (rang du quantum dans le
            # plot, `Carpophore.slot`) — clé `target.carpophore [r, c, slot]` du geste
            # `manger` ; le rang dans la liste ne le donne plus dès qu'un est mangé.
            carpophores[tile.tile_id] = carpophores_compacts(gs, tile, pluie_prec)
            # Butineurs déterministes (arc pollinisation §F, 0.3.9) : agents
            # échantillonnés/marchés par engine._tick_butineurs (eco.foragers, déjà
            # rempli par le tick). Format COMPACT (cf. `sprites`) par tuile :
            # [guild, r, c, x_frac, y_frac, espèce-cible, charge(0/1)]. PURE lecture
            # → golden NEUTRE. La vue dessine l'insecte de fleur en fleur.
            # INFO-BULLE DU VIVANT ① (0.5.47) : 8ᵉ champ = NOURRITURE (ressource
            # florale locale, `activite` du champ pollinisateur déjà calculée au
            # tick — même sens que l'`activite` des sprites).
            foragers[tile.tile_id] = [
                [a.guild, a.row, a.col, round(a.x_frac, 3), round(a.y_frac, 3),
                 a.target, int(a.carrying), _activite_butineur(eco, a)]
                for a in (eco.foragers or [])]
            # Structures posables (⑤, 0.3.5) : index implicite = position dans la
            # liste = `target.structure` des gestes. `compost_mur` = jauge mûre
            # épandable ; `contenu` = masse BRUTE en cours de maturation (Σ des
            # parcelles du contenu, 0.3.8). La vue remplit le bac/pile ∝
            # (contenu + compost_mur) → on VOIT la structure se remplir au
            # compostage (avant maturation) et se vider à l'épandage. PURE lecture.
            # Ruche (⑥, 0.4.0) : `essaim`/`miel` (0 pour bac/pile) → la vue dessine le
            # peuplement et la réserve de miel. PURE ajout de sérialisation.
            # Colonisation fongique (mycélium ⑤/⑥, 0.5.9) : `colonisation` ∈ [0,1]
            # = degré d'habitation du tas par le réseau (0 = tas neuf, 1 = pleinement
            # colonisé), 0 pour la ruche. La vue ⑥ en tire le VOILE FONGIQUE sur le
            # bac/pile (§3.3). État DÉJÀ tické par `tick_structures` (⑤) → simple
            # TRANSPORT, golden NEUTRE (le smoke ne pose aucune structure).
            structures[tile.tile_id] = [
                {"kind": st.kind, "plot": list(st.plot),
                 "compost_mur": round(st.compost_mur, 4),
                 "contenu": round(sum(p.masse for p in st.contenu), 4),
                 "colonisation": round(st.colonisation, 4),
                 "essaim": round(st.essaim, 4), "miel": round(st.miel, 4)}
                for st in eco.structures]
            # Supports de grimpe posés dans la tuile (D49 volet A, 0.5.18) :
            # structures NEUVES (tuteur/treillis/pergola, world/support.py) auxquelles
            # une grimpante compatible s'accroche pour monter (§4). Format par support
            # `{type, x_cm, y_cm, height_cm, finesse}`, repère TUILE-local (cm) comme
            # les plantes. La vue en dessine le placeholder procédural (pieu/grille/
            # portique, ⑥). PURE lecture (`tile.supports`, rempli par les gestes
            # poser_tuteur/treillis/pergola ④) → golden NEUTRE : le smoke n'en pose
            # aucun → liste vide. Le MUR maison n'est PAS ici (il vit dans le bloc
            # `house` statique) ; seuls les supports POSABLES transitent par le snapshot.
            supports[tile.tile_id] = [
                {"type": s.support_type, "x_cm": round(s.x_cm, 2),
                 "y_cm": round(s.y_cm, 2), "height_cm": round(s.height_cm, 2),
                 "finesse": s.finesse}
                for s in tile.supports]
            # Litière typée par plot (décompo·compost ①, rendue par la vue en
            # 03·B) : la couche fraîche de nécromasse au sol. On n'expose QUE ce
            # qui se dessine — la parcelle `diffus` (exsudats racinaires, humus
            # permanent, masse souvent > 0 via croissance) n'est PAS de la litière
            # de surface : on l'écarte du tissu dominant ET du total. Format
            # COMPACT (cf. `sprites`) : par plot non vide `[r, c, tissu_dominant,
            # masse, age_sem]` — dominant = parcelle de plus grande masse hors
            # `diffus`, masse = Σ des parcelles de surface (densité ∝ masse côté
            # vue). Les plots sans litière de surface sont OMIS (liste creuse).
            # 0.5.51 : + `bois_masse, bois_age_sem` (index 5-6, 0.0 sans bois).
            # 0.5.55 (⑦bis) : + `bois_diam_cm` (index 7, 0.0 sans bois) — la vue ⑧
            # dessine brindille / branche / souche selon la grosseur.
            # `age_sem` (rendu feuillage ⑥, 0.5.6) = ÂGE MOYEN pondéré par la masse
            # des parcelles de surface : proxy d'ÉTAT DE DÉCOMPO déjà calculé par le
            # moteur (`Parcelle.age_sem`, semaines depuis dépôt) — la vue assombrit/
            # désature la litière de feuilles à mesure qu'elle vieillit (dérive vers
            # l'humus, §6.3). TRANSPORT pur (donnée existante, aucun calcul moteur
            # nouveau) → golden NEUTRE. PURE lecture (`eco.litiere` déjà rempli par
            # le tick).
            plots = []
            for r in range(eco.rows):
                for c in range(eco.cols):
                    surface = [p for p in eco.litiere[r][c]
                               if p.tissu != "diffus" and p.masse > 0.0]
                    if not surface:
                        continue
                    dominant = max(surface, key=lambda p: p.masse)
                    total = sum(p.masse for p in surface)
                    # Âge moyen pondéré par la masse (total > 0 garanti : surface
                    # ne retient que les parcelles masse > 0). Litière fraîche
                    # (age ≈ 0) = brun-roux vif ; vieillie, elle fond dans le sol.
                    age_moy = sum(p.age_sem * p.masse for p in surface) / total
                    # Bois mort (D111 ②, 0.5.51) : masse + âge de la parcelle `bois`
                    # MÊME sous des feuilles dominantes → la vue (⑧) dessine la branche
                    # et son stade de décompo. Fusion par tissu ⇒ ≤ 1 parcelle `bois`.
                    bois = next((p for p in surface if p.tissu == "bois"), None)
                    # Masse de feuilles (AUTOMNE VISIBLE ③, 0.6.3) MÊME sous un autre
                    # tissu dominant : le tapis de ⑤ ne dépend plus du tissu dominant.
                    feuille = next((p for p in surface if p.tissu == "feuille"), None)
                    plots.append([r, c, dominant.tissu,
                                  round(total, 4), round(age_moy, 3),
                                  round(bois.masse, 4) if bois else 0.0,
                                  round(bois.age_sem, 3) if bois else 0.0,
                                  round(bois.diam_cm, 2) if bois else 0.0,
                                  round(feuille.masse, 4) if feuille else 0.0])
            litiere[tile.tile_id] = plots
            # Phéromone d'alarme apienne (⑦, §J, 0.4.1) : liste CREUSE des plots en
            # alarme `[r, c, intensite]` (foyers > 0 seulement). Godot lit l'intensité
            # au curseur → les abeilles présentes piquent (réaction temps réel, coût
            # Vigueur côté vue). PURE lecture (`eco.alarme` rempli par les déclencheurs
            # + décru par le tick) → golden NEUTRE (vide tant qu'aucune abeille écrasée
            # / aucun miel récolté nu). Champ optionnel côté vue (tolérance pré-0.4.1).
            af = getattr(eco, "alarme", None)
            foyers = []
            if af is not None:
                for r in range(eco.rows):
                    for c in range(eco.cols):
                        v = af.data[r][c]
                        if v > 0.0:
                            foyers.append([r, c, round(v, 4)])
            alarme[tile.tile_id] = foyers
            # Carte température par tuile (sprint thermique ⑧, §B) : ÉTATS
            # persistants déjà calculés par le tick → lecture DIRECTE (≠ météo
            # scalaire, recalculée par fonction pure plus bas). `snow` = manteau
            # neigeux scalaire (⑦, voile blanc ∝ snow côté vue). `t_sol` = grille 2D
            # rows×cols de la température de surface spatialisée (heatmap ⑩) ;
            # T_air uniforme N'EST PAS dupliquée par plot (elle vit dans `weather`).
            # PURE lecture (`eco.snow`/`eco.temperature_sol` remplis par le tick)
            # → golden NEUTRE. Champ optionnel côté vue (tolérance pré-0.5.0).
            temperature[tile.tile_id] = {
                "snow": round(eco.snow, 3),
                "t_sol": [[round(eco.temperature_sol.data[r][c], 2)
                           for c in range(eco.cols)] for r in range(eco.rows)],
            }
            # Carte de CONDENSATION par tuile (sprint météo→champs ⑤, §6, 0.5.10) :
            # liste CREUSE des plots `[r, c, rosee, givre]` où il y a eu rosée
            # liquide ce matin (`eco.rosee_last`, écrite par `tick_rosee`) ou du givre
            # accumulé (`eco.givre`, gelée blanche non encore fondue). La vue Godot en
            # tire les GOUTTES scintillantes (rosee > 0, été/printemps) et le GIVRE
            # blanc (givre > 0, hiver) — rendu C# = dette D24, ⑤ n'expose que la donnée.
            # Plots secs/sans dépôt OMIS (liste creuse, comme `litiere`/`alarme`).
            # PURE lecture (champs remplis par le tick) → golden NEUTRE pour le pont ;
            # le smoke en pose (nuits claires) mais le pont ne RÉINJECTE rien. Champ
            # optionnel côté vue (tolérance pré-0.5.10).
            rl = getattr(eco, "rosee_last", None)
            gv = getattr(eco, "givre", None)
            condensation = []
            if rl is not None and gv is not None:
                for r in range(eco.rows):
                    for c in range(eco.cols):
                        rosee = rl.data[r][c]
                        givre = gv.data[r][c]
                        if rosee > 0.0 or givre > 0.0:
                            condensation.append(
                                [r, c, round(rosee, 4), round(givre, 4)])
            condensation_by_tile[tile.tile_id] = condensation
            # Carte d'ÉPAISSEUR de sol par tuile (D57 ②, §4) : grille 2D dense
            # rows×cols de `eco.epaisseur_sol` en cm (relaxation vers la cible
            # bulk-density, remplie par `tick_epaisseur` ①a). La vue en extrude un
            # RELIEF iso (dessus du plot remonté de `epaisseur_cm × PxPerCmZ`) → on
            # voit le sol monter (humus qui s'accumule) et descendre (décompo/
            # tassement/érosion). PURE lecture (champ déjà tické) → golden NEUTRE.
            # Champ optionnel côté vue (tolérance pré-0.5.16).
            epaisseur_by_tile[tile.tile_id] = [
                [round(eco.epaisseur_sol.data[r][c], 2)
                 for c in range(eco.cols)] for r in range(eco.rows)]
            # Carte d'ALTITUDE par tuile (sprint hydrologie & marécages ①, §1) :
            # grille 2D dense rows×cols du MICRO-RELIEF topographique `eco.altitude`
            # en cm (socle géométrique FIXE, initialisé hétérogène par `init_eco`,
            # DÉCORRÉLÉ de l'humus). La vue en tire le relief du terrain (⑧) et
            # portera l'écoulement visible (②). À NE PAS confondre avec `epaisseur`
            # (humus foisonnant). PURE lecture (champ jamais tické) → golden NEUTRE.
            # Champ optionnel côté vue (tolérance pré-0.5.17 → terrain plat).
            altitude_by_tile[tile.tile_id] = [
                [round(eco.altitude.data[r][c], 2)
                 for c in range(eco.cols)] for r in range(eco.rows)]
            # Lame d'EAU DE SURFACE par tuile (sprint hydrologie & marécages ②, §2) :
            # liste CREUSE `[[r, c, lame], …]` des plots portant une lame > SEUIL_FLAQUE
            # (la plupart des plots sont SECS → liste courte, patron `litiere`/`alarme`).
            # La vue en tire les FLAQUES (lame translucide bleutée ∝ profondeur, ⑧).
            # PURE lecture (champ déjà tické par `tick_ruissellement`) → aucun impact
            # golden. Champ optionnel côté vue (tolérance pré-0.5.18 → pas de flaque).
            eau_surface_by_tile[tile.tile_id] = [
                [r, c, round(eco.eau_surface.data[r][c], 3)]
                for r in range(eco.rows) for c in range(eco.cols)
                if eco.eau_surface.data[r][c] > SEUIL_FLAQUE]
            # Carte de MARÉCAGE par tuile (sprint hydrologie & marécages ③) : liste
            # CREUSE `[[r, c, marais, etat], …]` des plots où `marais_memory > MARAIS_OFF`
            # (marais naissant ou installé). `marais` ∈ [0,1] = intensité (la vue
            # « noircit » le sol ∝ mémoire, philo #5) ; `etat` = booléen d'hystérèse
            # (`est_marais`). La plupart des plots sont SECS → liste courte (patron
            # `eau_surface`). PURE lecture (champ déjà tické par `tick_marais`) → aucun
            # impact golden. Champ optionnel côté vue (tolérance pré-0.5.27 → pas de marais).
            # MARE VIVANTE ① (0.6.2) : + `lame` (5ᵉ, `eau_surface` BRUTE, même sous
            # SEUIL_FLAQUE → la vue dessine le marnage progressif : vase luisante sous
            # une lame mince) et `glace` (6ᵉ, ∈ [0,1], `tick_glace`). Pré-0.6.2 : 4 champs.
            mmem = getattr(eco, "marais_memory", None)
            marais_by_tile[tile.tile_id] = [
                [r, c, round(mmem.data[r][c], 3), eco.est_marais(r, c),
                 round(eco.eau_surface.data[r][c], 3), round(eco.glace.data[r][c], 3)]
                for r in range(eco.rows) for c in range(eco.cols)
                if mmem is not None and mmem.data[r][c] > MARAIS_OFF]
            # Carte de COUVERTURE DU SOL par tuile (sprint LUXURIANCE ①, D65 §2.1,
            # exposée au pont au ⑥) : liste CREUSE `[[r, c, cov], …]` des plots
            # tapissés (cov > SEUIL) — fraction du sol couverte par les strates
            # basses (sol+basse), scattée par `tick_couverture`. La vue en tire le
            # TAPIS (densité de rendu au sol ∝ cov, indice diégétique philo #5) : sol
            # nu ↔ sol tapissé se distingue à l'œil, sans chiffre. Liste creuse (patron
            # `litiere`/`eau_surface`) : la plupart des plots sont nus au démarrage.
            # PURE lecture (champ déjà tické par la boucle) → golden NEUTRE (le pont ne
            # réinjecte rien). Champ optionnel côté vue (tolérance pré-0.5.19 → pas de
            # tapis). `couverture_sol` peut être None sur un vieil eco (défaut lazy) →
            # garde-fou getattr.
            cov = getattr(eco, "couverture_sol", None)
            couverture_by_tile[tile.tile_id] = [
                [r, c, round(cov.data[r][c], 3)]
                for r in range(eco.rows) for c in range(eco.cols)
                if cov is not None and cov.data[r][c] > COUVERTURE_RENDU_SEUIL]
            # Carte de PAILLAGE par tuile (sprint équilibre invasion ⑧, D69) : liste
            # CREUSE `[[r, c, profondeur, nature], …]` des plots mulchés (profondeur
            # > 0). `profondeur` ∈ [0,1] = densité du mulch au sol (champ `eco.paillage`,
            # posé par le geste `pailler`, décru par `tick_paillage`) ; `nature` ∈
            # {paille, brf, aiguilles} = matériau du mulch (`nature_at`, ④) → la vue
            # teinte/texture par matériau ET module l'opacité par profondeur. Liste
            # creuse (patron `litiere`/`couverture`) : la plupart des plots sont NUS.
            # PURE lecture (champ déjà tické par `tick_paillage`) → golden NEUTRE : le
            # smoke ne paille jamais → paillage=0 partout → liste vide. Champ optionnel
            # côté vue (tolérance pré-0.5.20 → pas de mulch dessiné). `paillage` peut
            # être None sur un vieil eco (défaut lazy) → garde-fou getattr.
            pai = getattr(eco, "paillage", None)
            nat = getattr(eco, "paillage_nature", None)
            paillage_by_tile[tile.tile_id] = [
                [r, c, round(pai.data[r][c], 3), (nat[r][c] or "paille")]
                for r in range(eco.rows) for c in range(eco.cols)
                if pai is not None and pai.data[r][c] > 0.0]
            # Carte d'ALLÉLOPATHIE par tuile (sprint ALLÉLOPATHIE ⑥, kickoff §Pont) :
            # liste CREUSE `[[r, c, concentration], …]` des plots chargés en
            # allélochimiques (au-dessus du plancher de snap-à-0 ALLELO_FLOOR — la
            # plupart des plots sont propres → liste courte, patron `alarme`/
            # `couverture`). On expose `allelo_effectif` (allélopathie AMBIANTE +
            # autotoxicité du plot), MAIS sans espèce de référence → seul le champ
            # ambiant sort ici (l'autotox ④ est spécifique-espèce ; la vue F6 la lit
            # via son propre registre `get_field` "autotox"). Concrètement =
            # `allelopathie.at_plot`. La vue en tire l'indice DIÉGÉTIQUE de sol
            # PELÉ/nu sous un émetteur fort (halo sans levée autour du noyer/armoise,
            # philo #5 : pas de chiffre) et l'overlay F6 double la lecture technique.
            # PURE lecture (`eco.allelopathie` déjà tické par `tick_allelopathie` ①)
            # → golden NEUTRE : le pont ne réinjecte rien. Champ optionnel côté vue
            # (tolérance pré-0.5.29 → pas de halo). `allelopathie` peut être None sur
            # un vieil eco (défaut lazy) → garde-fou getattr.
            al = getattr(eco, "allelopathie", None)
            allelopathie_by_tile[tile.tile_id] = [
                [r, c, round(al.data[r][c], 4)]
                for r in range(eco.rows) for c in range(eco.cols)
                if al is not None and al.data[r][c] > ALLELO_FLOOR]
            # Carte de MÉMOIRE D'INOCULUM par tuile (sprint mémoire d'inoculum ④) :
            # liste CREUSE `[[r, c, famille_dominante, charge_totale], …]` des SEULS
            # plots viciés (`eco.inoculum.load` est un dict SPARSE indexé par plot →
            # un plot resté sain n'a AUCUNE entrée, la liste reste courte, patron
            # `marais`/`eau_surface`). Par plot chargé : la famille dominante (bucket
            # de plus forte charge — la maladie qui hiverne le plus) + la charge
            # totale toutes familles confondues (`inoculum.total`, sert la niche
            # molène ③ et la heatmap). La vue F6 en tire l'overlay « charge pathogène »
            # (sain → rouge/brun vicié). PURE lecture d'un champ déjà tické par
            # `tick_decay` → golden NEUTRE (le smoke ne vicie aucun plot → dict vide →
            # liste vide). Champ optionnel côté vue (tolérance pré-0.5.39 → pas
            # d'overlay). `inoculum` peut être absent d'un vieil eco → garde-fou getattr.
            ino = getattr(eco, "inoculum", None)
            plots_ino = []
            if ino is not None:
                for (r, c), bucket in ino.load.items():
                    if not bucket:
                        continue
                    dominante = max(bucket, key=bucket.get)
                    total = sum(bucket.values())
                    plots_ino.append([r, c, dominante, round(total, 4)])
            inoculum_by_tile[tile.tile_id] = plots_ino
            # Couvertures POSÉES par le joueur (effondrement météo ③, tronçon ④ au
            # pont) : deux listes CREUSES par tuile `[[r, c, dose], …]` des plots
            # abrités — `couvert_pose` (écran physique du VOILE/CLOCHE, protège gel/
            # grêle) et `ombre_pose` (occultation de l'OMBRIÈRE, rafraîchit contre
            # canicule/sécheresse). Champs alloués PARESSEUSEMENT (None au repos → la
            # plupart des mondes n'ont RIEN de posé, liste vide, patron `paillage`).
            # La vue en tire les placeholders procéduraux (voile translucide / filet
            # d'ombre, CoverLayer). PURE lecture (aucun tick propre, cf.
            # couvertures_posees.py) → golden NEUTRE : le smoke ne pose aucune
            # couverture → champs None → listes vides. Champ optionnel côté vue
            # (tolérance pré-0.5.43). Garde-fou getattr (vieil eco sans le mixin).
            cvp = getattr(eco, "couvert_pose", None)
            couvert_pose_by_tile[tile.tile_id] = [
                [r, c, round(cvp.data[r][c], 3)]
                for r in range(eco.rows) for c in range(eco.cols)
                if cvp is not None and cvp.data[r][c] > 0.0]
            omp = getattr(eco, "ombre_pose", None)
            ombre_pose_by_tile[tile.tile_id] = [
                [r, c, round(omp.data[r][c], 3)]
                for r in range(eco.rows) for c in range(eco.cols)
                if omp is not None and omp.data[r][c] > 0.0]
        # Météo scalaire GLOBALE du tick (sprint thermique ⑧, §A) : la météo qui a
        # produit l'état COURANT est celle de la semaine DÉJÀ simulée = `week − 1`
        # (`week` = prochaine à simuler). `weather_state` étant PURE, on la RECALCULE
        # (rien à stocker côté moteur) → golden NEUTRE. `signs` = préavis diégétique
        # des événements à venir (1-2 sem, philo #5) ; on expose le flag `signed`,
        # le filtrage par palier de maîtrise (D12) reste à la charge de la VUE.
        # À l'init (rien simulé, `last < 1`) : temps calme, normale, pas de signe.
        last = gs["week"] - 1
        if last >= 1:
            # `pluie_forcee` : banc de test `pluie_continue` (D111 ①e) — même météo
            # que le tick l'a vécue ; absent en jeu → False.
            ev, t_air, nebul = weather_state(gs["seed"], last, gs.get("pluie_forcee", False))
            signs = weather_signs(gs["seed"], last, horizon=2)
        else:
            ev, t_air, nebul, signs = CALME, T_MOY, 0.10, []
        weather = {
            "kind": ev.kind,
            "intensity": round(ev.intensity, 3),
            "scope": ev.scope,
            "nebulosite": round(nebul, 3),
            "t_air": round(t_air, 2),
            "signs": [
                {"kind": s.kind, "in_weeks": s.in_weeks,
                 "signs": list(s.signs), "signed": s.signed}
                for s in signs
            ],
            # Masse d'air (JARDIN VIVANT T3, 0.5.44) : {force, direction, gusts},
            # même semaine `last` ; la vue en tire l'onde de vent sur les plantes.
            "wind": wind_block(gs["seed"], last),
        }
        # « Ciel de la semaine » (effondrement météo ②→④, sim/ciel.py) : agrégat
        # PUR de tout ce que le joueur peut LIRE du ciel — état de fond, signes
        # 1-2 sem en avant, et surtout la CONVERGENCE du composé catastrophe (le
        # ciel qui va « virer au plomb » à l'approche de « l'hiver de tous les
        # dangers »). L'encart Godot (④) le rend en fenêtre diégétique (couleur/
        # nuages/halo/brume qui s'assombrit ∝ convergence), sans chiffre ni icône
        # calendrier (philo #5). Le NOMMAGE est masqué CÔTÉ MOTEUR : `ciel_semaine`
        # ne joint `nom_compose` que si le palier maîtrise météo suffit (§4.2) —
        # la vue reçoit un nom déjà gaté, elle ne décide rien (« Godot bête »).
        # Évalué au front courant `last` (= dernière semaine simulée, même repère
        # que `weather`) → les signes portent sur les semaines À VENIR. PURE lecture
        # (fonctions météo pures, zéro RNG) → golden NEUTRE. À l'init (rien simulé)
        # on évalue en semaine 1 (le ciel du tout début).
        palier_meteo = M.palier(gs, gs["current_player"], "météo")
        cs = ciel_semaine(gs["seed"], last if last >= 1 else 1,
                          palier_climat=palier_meteo)
        ciel = {
            "evenement_courant": cs.evenement_courant,
            "nebulosite": round(cs.nebulosite, 3),
            "convergence": cs.convergence,
            "signes": [
                {"kind": s.kind, "in_weeks": s.in_weeks,
                 "signs": list(s.signs), "signed": s.signed}
                for s in cs.signes
            ],
            "signe_compose": list(cs.signe_compose),
            "nom_compose": cs.nom_compose,
        }
        # Bloc joueur (tranche 4, lecture seule) : la vue affiche la Vigueur
        # au HUD. vigueur_max passe par la façade (bonus maîtrise compris).
        # `seeds` (0.3.3) = lots PLANTABLES de la banque-joueur, {clé catalogue:
        # nombre} (lots vides masqués) — la vue propose les graines disponibles à
        # `planter`. Pur compteur : la génétique reste côté moteur (D17/D22).
        player = gs["current_player"]
        st = V.ensure_player(gs, player)
        bank = gs.get("player_seed_bank")
        seeds = {sp: len(lot) for sp, lot in bank.lots.items()
                 if lot} if bank is not None else {}
        # Palette de gestes ① (0.5.23) : la liste TRIÉE des gestes OUVERTS pour
        # l'avatar courant (BASE ∪ débloqués) — la palette Godot n'affiche QUE
        # l'ouvert (colonne gauche, D11). `debloques_recents` = verbes ouverts au
        # DERNIER tick (voie savoir), pour la notification diégétique ; consommé à
        # la lecture (on le vide pour ne le signaler qu'une fois). Lecture d'un
        # état joueur (opt-in) → golden NEUTRE (le golden tourne hors serveur).
        gestes_ouverts = DEBL.gestes_debloques(gs, player)
        recents = gs.get("gestes_debloques_recents", {}).pop(player, [])
        # Palette de gestes ⑤ (0.5.26) : le LAYOUT de l'avatar courant — `slots`
        # curés (ordre/sélection des gestes à portée, vide = « tout ouvert » côté
        # vue) + `macros` (séquences ordonnées rejouées sur la MÊME cible cliquée,
        # D1/D5). Persisté PAR AVATAR (D10) dans la save. Lecture PURE (opt-in) :
        # un avatar sans palette retombe sur le défaut SANS écrire → golden NEUTRE.
        palette_layout = PAL.palette_layout(gs, player)
        # Banc d'observation perf (sprint « run éternel » ④) : bloc LECTURE SEULE
        # pour l'overlay debug F4 côté Godot — `ms_tick` (durée du dernier tick,
        # mesurée AUTOUR de tick_semaine() dans commands.py, None si rien encore
        # simulé), `n_plants` (VIVANTES du snapshot, l'axe qui doit plafonner),
        # `rss_mo` (RSS du process serveur, la mémoire qui doit se stabiliser
        # avec N). Le tout dérive d'un état déjà calculé → golden NEUTRE : le
        # golden tourne hors serveur, ce bloc n'existe jamais pour lui.
        n_plants = sum(1 for p in plants if not p.get("dead"))
        perf = perf_block(getattr(self, "_last_ms_tick", None), n_plants)
        snap = {"week": week, "week_in_year": week_in_year,
                "year": (week - 1) // 52 + 1, "season": saison,
                "player": {"vigueur": st["courante"],
                           "vigueur_max": V.vigueur_max(gs, player),
                           "seeds": seeds,
                           "gestes_debloques": gestes_ouverts,
                           "debloques_recents": recents,
                           "palette": palette_layout,
                           "appris": signes_appris(gs, player),
                           "vision": bloc_vision(gs, player)},
                "perf": perf,
                "plants": plants, "sprites": sprites, "foragers": foragers,
                "carpophores": carpophores,
                "structures": structures, "supports": supports,
                "litiere": litiere, "alarme": alarme,
                "weather": weather, "temperature": temperature,
                "condensation": condensation_by_tile,
                "epaisseur": epaisseur_by_tile,
                "altitude": altitude_by_tile,
                "eau_surface": eau_surface_by_tile,
                "marais": marais_by_tile,
                "couverture": couverture_by_tile,
                "paillage": paillage_by_tile,
                "allelopathie": allelopathie_by_tile,
                "inoculum": inoculum_by_tile,
                "couvert_pose": couvert_pose_by_tile,
                "ombre_pose": ombre_pose_by_tile,
                "ciel": ciel,
                "containers": self._containers_snapshot(gs, saison)}
        # OVERDOSE (sol qui respire ⑥) : les phrases de TOUS les êtres, à chaque
        # snapshot, le temps de l'effet. Clé ABSENTE sinon (coût nul hors overdose).
        voix = bloc_voix(gs, player, sprites, foragers, carpophores)
        if voix is not None:
            snap["voix"] = voix
        # Ceinture périphérique (PÉRIPHÉRIE ⑦, D73) : bloc OPT-IN de 4 secteurs
        # (`ceinture_block`, cf. peripherie_route). Présent UNIQUEMENT quand le
        # monde porte une ceinture → un monde sans périphérie (smoke, bancs
        # thématiques) émet un snapshot bit-pour-bit inchangé et la vue retombe sur
        # `DecorLayer.BuildProfile(seed)`. C'est ce bloc qui fait de `DecorLayer` un
        # CONSOMMATEUR au lieu d'un générateur (D92 refermée par le haut). PURE
        # lecture d'un état déjà tické (repousse/ouvrages/érosion) → golden NEUTRE.
        ceinture = ceinture_block(gs)
        if ceinture is not None:
            snap["ceinture"] = ceinture
        # Jardinier automate (sprint jardinier_auto ⑥) : bloc OPT-IN. Présent UNIQUEMENT
        # quand un automate est actif → un snapshot F5 ordinaire (sans automate) est
        # bit-pour-bit inchangé (la vue existante ne voit jamais la clé). PURE lecture
        # de la trace/objectifs déjà écrits par la boucle (hors tick) → golden NEUTRE.
        if getattr(self, "_automate", None) is not None:
            snap["automate"] = self.automate_block(gs)
        if delta is not None:
            snap["delta"] = delta.fin()   # {complet, disparues} (pont_delta)
        return snap

    def _containers_snapshot(self, gs: dict, saison: str) -> list:
        """Conteneurs posés par le joueur (pots/bacs ④, 0.5.7). Index implicite =
        position dans la liste = `target.container` des gestes. Format par conteneur :
        identité (id/kind/substrat/mobile/fond_ouvert), position monde (x_cm/y_cm,
        que `deplacer_pot` change → la vue replace le pot), géométrie (rows/cols,
        volume — pilote l'effet nain) ; `plants` = la/les plante(s) du mini-sol en
        forme COMPACTE (espèce/position/structure/fruits/symptômes — assez pour la
        future vue ⑥) ; `eco_summary` = scalaires HUD au plot (0,0) du mini-sol
        (humidité/NPK/pH/microbiome/structure). PURE lecture (`gs["containers"]` déjà
        tické par la boucle 17b) → golden NEUTRE : le smoke ne pose aucun conteneur,
        la liste est VIDE → bloc `[]`. Index = `target.container` (cf. routeur)."""
        out = []
        for ctn in gs.get("containers", []):
            eco = ctn.eco
            cplants = []
            for p in ctn.plants:
                pd = {"species": p.plant_class.__name__, "name": p.name,
                      "x_cm": p.x_cm, "y_cm": p.y_cm,
                      "stage": p.current_stage, "stage_name": p.stage.name,
                      "height_cm": p.current_height,
                      "dead": not p.is_alive,
                      "segments": self._segments_vue.segments(p.segments)}
                if p.is_alive:
                    # Vitalité continue (0.5.28, miroir du vivant en pleine terre) :
                    # même descripteur global d'usure pour la plante d'un conteneur.
                    pd["vitalite"] = round(p.vitalite, 3)
                    pd["etat"] = p.etat
                    pd["leaf_symptoms"] = semiologie.leaf_symptoms(p, eco, saison)
                    pd["fruits"] = [{"segment": f.segment_id, "maturite": f.maturite,
                                     "masse": f.masse} for f in p.fruits]
                cplants.append(pd)
            out.append({
                "id": ctn.container_id, "kind": ctn.kind,
                "substrat": ctn.substrat, "volume": ctn.volume_litres,
                "x_cm": ctn.x_cm, "y_cm": ctn.y_cm,
                "mobile": ctn.mobile, "fond_ouvert": ctn.fond_ouvert,
                "rows": ctn.rows, "cols": ctn.cols,
                "plants": cplants,
                "eco_summary": {
                    "humidite": round(eco.humidite.at_plot(0, 0), 4),
                    "n": round(eco.n.at_plot(0, 0), 4),
                    "p": round(eco.p.at_plot(0, 0), 4),
                    "k": round(eco.k.at_plot(0, 0), 4),
                    "ph": round(eco.ph.at_plot(0, 0), 4),
                    "microbiome": round(eco.microbiome.at_plot(0, 0), 4),
                    "structure": round(eco.structure_sol.at_plot(0, 0), 4)},
            })
        return out
