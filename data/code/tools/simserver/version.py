"""
SYMBIOSE — tools/simserver/version.py
Version du protocole/moteur + constantes de repli partagées par les handlers.

Éclaté de l'ex-`tools/sim_server.py` (Sprint refactor global, SS⑤) : ces
constantes étaient en tête du module monolithe ; elles vivent désormais ici,
importées par les mixins de commandes / actions / sérialisation.
"""
from __future__ import annotations

# Version du protocole/moteur exposée dès le v0 (même philosophie que le futur
# save JSON : casse explicite si schéma incompatible). Locale au serveur pour
# l'instant — le « sprint save global » décidera où la centraliser.
# 0.2.0 (tranche 4) : commande `action` + bloc `player` dans le snapshot.
# 0.2.1 (tranche 5) : `target.segment` optionnel sur `tailler` (taille au clic).
# 0.2.2 (tranche 6·A) : 3 hints d'organes par plante au snapshot
#       (foliage_density, organ, organ_site) — pur rendu, lecture seule.
# 0.2.3 (tranche 6·B) : bloc `sprites` au snapshot (vie macro, D31 côté vue) —
#       par tuile et par guilde, tableaux COMPACTS [r, c, x_frac, y_frac,
#       activite]. Compact d'emblée : mesuré 705 Ko/snapshot en format objet
#       verbeux au pic d'automne du monde full (~8600 sprites) vs 210 Ko en
#       tableaux — la mitigation prévue au kickoff §4 s'impose à la mesure.
# 0.3.0 (tranche 6·C, fin de tranche) : commande `fields` (mode debug champs
#       écologiques) — registre par introspection + grilles par tuile à la
#       demande, HORS snapshot (volume : la vue ne paie que l'overlay ouvert).
# 0.3.1 (post-intégration) : `target.guilde` optionnel sur `ecraser` (écraser le
#       sprite cliqué quelle que soit sa guilde — défaut `ravageur` = compat).
# 0.3.2 (écraser·volet 2) : `ecraser` route aussi vers une PLANTE quand le `target`
#       la désigne par position (`x_cm`/`y_cm`, + `segment` optionnel) au lieu de
#       `r`/`c`+`guilde` — déforme / écime / fait mourir (sentier). Routage sur la
#       FORME du target (Q6) ; compat guilde animale inchangée.
# 0.3.3 (planter·arroser, sprint éponyme) : verbes `planter` (target tile +
#       `x_cm`/`y_cm` + `params.species`, clé catalogue) et `arroser` (target tile +
#       `x_cm`/`y_cm`, `params.urgence`/`phase`) — gestes sur le MILIEU. La position
#       continue se RÉSOUT en plot-foyer (`floor(/PLOT_CM)`) côté serveur, les
#       façades écrivent au plot. Banque-joueur attachée à l'init (remplie à la
#       récolte) + exposée au snapshot (`player.seeds`, lots plantables).
# 0.3.4 (décompo·compost ③, organes-fruits, absorbe D19) : le snapshot expose
#       `plant.fruits` = liste de fruits TRACÉS (vrai état moteur ≠ proxy `organ`),
#       chacun {segment, maturite, masse}. Le geste `manger` accepte
#       `target.fruit` (index dans cette liste) → consomme CE fruit, gain ∝ sa
#       maturité, l'organe disparaît (déplétion réelle). `manger` sans `fruit`
#       garde le mode générique (legacy). Nouaison/maturation/chute pilotées par
#       engine._tick_fruits ; les sur-mûrs tombent en litière `fruit`.
# 0.3.5 (décompo·compost ⑤, structures posables) : le snapshot expose
#       `eco.structures` par tuile (liste de {kind, plot, compost_mur}) — l'index
#       implicite = position dans la liste = `target.structure` des gestes. Six
#       verbes neufs au routeur : `poser_bac`/`poser_pile` (target plot {r,c},
#       planification), `composter`/`empiler_bois` (target plot {r,c} + `structure`,
#       déplacent la litière → contenu), `retourner` (target {structure}, accélère
#       la maturation), `epandre` (target plot {r,c} + `structure`, `params.q`
#       optionnel — restitue le compost mûr au sol en trio humus, borné par la
#       jauge). La pile pose en plus une rondelle `auxiliaire` (habitat §4.1).
# 0.3.6 (vue·rattrapage 02, cycle de vie visible) : le snapshot expose les
#       PLANTES MORTES persistantes (squelettes ②B) au lieu de les sauter —
#       chacune porte `dead=true` + {stade_mort ("seche"/"couchee"), bois_restant,
#       semaines_mort} et sa structure (silhouette nue à dessiner). Les vivantes
#       gagnent `dead=false` (drapeau explicite). PUR ajout de sérialisation
#       (lecture seule, `tile.plants` contient déjà les morts) → golden NEUTRE.
#       Champs optionnels côté vue (tolérance pré-0.3.6, comme les bumps précédents).
# 0.3.7 (vue·rattrapage 03, litière au sol) : le snapshot expose `litiere` par
#       tuile = `[[r, c, tissu_dominant, masse], …]`, la couche fraîche de
#       nécromasse de SURFACE par plot non vide (dominant = parcelle de plus
#       grande masse hors `diffus` ; masse = Σ des parcelles de surface ;
#       `diffus`, exsudats/humus permanent, écarté car non rendu). Liste creuse
#       (plots sans litière de surface OMIS). PUR ajout de sérialisation
#       (`eco.litiere` rempli par le tick) → golden NEUTRE. La vue dessine en
#       03·B (indice écologique discret, philo #5).
# 0.3.8 (vue·rattrapage 03 correctif F5) : chaque structure du bloc `structures`
#       gagne `contenu` = masse BRUTE en cours de maturation (Σ des parcelles
#       `st.contenu`), à côté de `compost_mur` (mûr). La vue remplit la caisse/
#       pile ∝ (contenu + compost_mur) → on VOIT le bac se remplir au compostage
#       (le brut, avant maturation) et se vider à l'épandage (le mûr). PUR ajout
#       de sérialisation (`st.contenu` déjà rempli par `composter`) → golden NEUTRE.
# 0.3.9 (pollinisation ③, butineurs déterministes §F) : le snapshot expose
#       `foragers` par tuile = `[[guild, r, c, x_frac, y_frac, espèce-cible,
#       charge], …]`, les agents butineurs (abeille/syrphe/papillon) échantillonnés
#       et marchés fleur-en-fleur par engine._tick_butineurs (eco.foragers). Ils
#       déposent réellement le pollen conspécifique dans `pollen_recu` (lu par la
#       nouaison §B au tronçon ④). PUR ajout de sérialisation (état transient déjà
#       calculé par le tick, n'écrit que pollen_recu/eco.foragers) → golden NEUTRE.
#       Champ optionnel côté vue (tolérance pré-0.3.9, comme les bumps précédents).
# 0.4.0 (pollinisation ⑥, ruche & miel §H/§I — couche joueur) : chaque structure du
#       bloc `structures` gagne `essaim` ∈ [0,1] (peuplement) et `miel` ∈ [0,MIEL_MAX]
#       (réserve), à 0 pour bac/pile. Deux verbes neufs au routeur : `poser_ruche`
#       (target plot {r,c}, planification — pose une ruche VIDE qui capture un essaim
#       sauvage au tick si le champ abeille local suffit) et `recolter_miel` (target
#       {structure} index — transfère le miel → Vigueur joueur, gain ∝ réserve, gaté
#       par l'équipement apicole débloqué par MAÎTRISE du concept pollinisation ;
#       sans équipement → récolte partielle, l'alarme/piqûre §J vient au ⑦). La ruche
#       peuplée renforce l'habitat abeille local (§H.2). Moteur ⑥ → golden NEUTRE
#       (le smoke n'instancie aucune ruche). Champs optionnels côté vue.
# 0.4.1 (pollinisation ⑦, piqûre — alarme émergente §J — couche joueur) : le snapshot
#       expose `alarme` par tuile = liste CREUSE `[[r, c, intensite], …]`, les foyers
#       de phéromone d'alarme apienne (champ `eco.alarme`). Posés au plot d'une action
#       directe coûteuse — `ecraser` une ABEILLE (gestes.py) ou `recolter_miel` SANS
#       équipement (ruche.py reçoit `eco` en plus) — et décrus chaque tick
#       (engine étape 13f, `fields.alarme.tick_alarme`). Pas de verbe neuf au routeur
#       (effet de bord des verbes existants). Godot lit l'intensité au curseur → les
#       abeilles du rayon PIQUENT (coût Vigueur + perturbation appliqués TEMPS RÉEL
#       côté vue, §J.3). Le moteur ne réinjecte l'alarme dans AUCUN champ figé (pur
#       puits) → golden NEUTRE (§J.4 ; le smoke n'écrase aucune abeille, ne récolte
#       aucun miel). Champ optionnel côté vue (tolérance pré-0.4.1).
# 0.5.0 (thermique ⑧, snapshot météo + carte température — 1er bloc du sprint
#       thermique au pont) : le snapshot gagne DEUX blocs lecture-seule. `weather`
#       = scalaire GLOBAL du tick courant (météo de `week-1`, recalculée par le
#       helper PUR sim.weather.weather_state) : {kind, intensity, scope
#       ("global"/"local"), nebulosite, t_air, signs} ; `signs` = préavis
#       diégétiques (weather_signs, horizon 2) avec flag `signed` (filtrage palier
#       D12 laissé à la vue). `temperature` = par tuile {snow (manteau ⑦),
#       t_sol (grille 2D rows×cols de la T de surface ⑤)} — états déjà calculés,
#       lus directement ; T_air uniforme NON dupliquée par plot. Mineure car schéma
#       ÉTENDU (pas cassé) : PUR ajout lecture-seule → golden NEUTRE, champs
#       optionnels côté vue (tolérance pré-0.5.0). Refactor léger associé : helper
#       partagé `weather_state` rebranché côté engine (boucle.py étape 1) ET snapshot
#       → un seul calcul météo, jamais deux qui dérivent (valeurs identiques, golden
#       inchangé). ⑨ (rendu Godot) + ⑩ (heatmap debug) consommeront ces blocs.
# 0.5.1 (sémiologie foliaire ①, D33) : le bool `chlorose` par plante est RETIRÉ et
#       fondu dans une LISTE `leaf_symptoms` = `[{cause, intensity}]` triée par
#       intensité décroissante (départage priorité fixe). Détecteurs CHRONIQUES purs
#       (sim/semiologie) — chlorose/sécheresse/asphyxie/ravageurs/sénescence —
#       chacun miroir du SEUIL de la mécanique qui blesse (le signe ne ment pas).
#       Liste vide = plante saine. Schéma ÉTENDU (chlorose bool → leaf_symptoms) :
#       PUR recalcul lecture-seule → golden NEUTRE (espèces neutres + sols drainants
#       du smoke ⇒ aucun symptôme). Champ optionnel côté vue (tolérance pré-0.5.1 ;
#       la vue consomme encore `chlorose` au ②/③ → retrait C# au tronçon ③). Les
#       marques ÉVÉNEMENTIELLES (maladie/gel/grele, décroissantes) arrivent au ②.
# 0.5.2 (mort par stress chronique ① + signe ③) : nouvelle cause `ombre` (carence
#       lumineuse chronique, étiolement) dans la LISTE `leaf_symptoms` — miroir du
#       dégât `shade_stress_damage` (shade_memory → santé). Extension de DONNÉES
#       (liste de causes ouverte), pas de schéma : la vue ignore une cause inconnue
#       (tolérance pré-0.5.2). À FAIRE côté C# : mapping couleur+texture du cas
#       « ombre » dans PlantRenderer (dette vue, hors moteur Python).
# 0.5.3 (plasticité ⑤, signe d'acclimatation P3) : nouvelle cause `acclimatation`
#       (durcissement plastique visible — feuillage coriace/glauque/cireux) dans la
#       LISTE `leaf_symptoms`. RÉPONSE, pas dégât : intensité = la plus forte
#       sur-expression des gènes adaptogènes, en rampe [EXPR_MIN, EXPR_MAX] de la
#       dynamique d'expression (sim/semiologie.acclimatation). Extension de DONNÉES
#       (liste de causes ouverte), pas de schéma : la vue ignore une cause inconnue
#       (tolérance pré-0.5.3). Détecteur = lecture pure (hors _PLANT_ATTRS du golden)
#       → golden NEUTRE (espèces du smoke sans stress vécu ⇒ expression = EXPR_MIN ⇒
#       aucun signe). Côté C# : teinte glauque dans ColorantTints (PlantRenderer).
ENGINE_VERSION = "0.5.3"

# Repli pour une espèce absente de REPRO_BY_SEASON (kickoff t6 : « fleur au
# printemps, fruit mûr en été/automne, rien l'hiver ») — raisonnable pour les
# herbacées du catalogue en attendant le VRAI état reproducteur (D19/D33).
DEFAULT_REPRO = {"printemps": "flower", "ete": "fruit_ripe",
                 "automne": "fruit_ripe", "hiver": None}

# Tolérance du match plante-par-position (kickoff t4 §8) : les positions du
# snapshot reviennent telles quelles dans la cible → l'epsilon n'absorbe que le
# bruit de sérialisation JSON (float64 round-trip, en pratique exact).
PLANT_EPSILON_CM = 0.1
