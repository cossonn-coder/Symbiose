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
# 0.5.4 (bancs d'essai ⑤, sélecteur Godot) : commande `list_bancs` → `{bancs:
#       [...]}` = `sorted(BANCS)`, le registre des bancs d'essai. AUCUN moteur
#       requis (lecture du registre) → appelable avant `init`, sert à PEUPLER le
#       menu Godot (le C# ne duplique pas les noms : Python reste source unique,
#       un menu périmé = le piège D47). Pur ajout de commande lecture-seule →
#       golden NEUTRE. Un vieux binaire pré-0.5.4 répond « commande inconnue » →
#       SimBridge.ListBancs() renvoie [] → le sélecteur retombe sur full/smoke.
# 0.5.5 (rendu feuillage ⑤, croissance progressive — 1er tronçon au pont) : le
#       miroir C# du segment (`record struct Segment`, core/PlantStructure.cs)
#       LIT désormais `age_weeks` du snapshot de structure, qui pilote côté vue le
#       facteur `leafGrowth ∈ [0,1]` (la jeune feuille grandit sur ~1,5 sem, E1).
#       ⚠️ Aucun changement de sérialisation Python : `age_weeks` est DÉJÀ émis par
#       `Segment.to_dict()` (plants/base/stades.py) dans `structure_to_dict()` —
#       on ne fait que le CONSOMMER côté C# (champ jusqu'ici ignoré au parse).
#       TRANSPORT pur (donnée déjà calculée par la morphogénèse) → golden NEUTRE.
#       Champ tolérant côté vue (un snapshot pré-0.5.5 émet déjà la clé ; un binaire
#       plus vieux qui ne l'émettrait pas → leafGrowth = 1 par défaut, pas de pop-in).
# 0.5.6 (rendu feuillage ⑥, chute + litière — DERNIER tronçon du sprint) : le bloc
#       `litiere` par tuile gagne un 5ᵉ champ par plot → `[r, c, tissu_dominant,
#       masse, age_sem]`. `age_sem` = ÂGE MOYEN pondéré par la masse des parcelles
#       de SURFACE (état de décompo, semaines depuis dépôt), donnée DÉJÀ calculée
#       par le moteur (`Parcelle.age_sem`) → simple TRANSPORT, golden NEUTRE. La vue
#       rend la litière de FEUILLES (tissu `feuille`) en SILHOUETTES d'espèce
#       (LeafLitterLayer, repli Elliptique car l'espèce d'origine N'EST PAS traçable
#       côté moteur — la Parcelle est typée par tissu, pas par espèce, §6.3) et
#       DÉRIVE leur teinte morte/sèche vers le sol ∝ age_sem (assombrir/désaturer
#       jusqu'à fondre dans l'humus). L'abscission « casse au pétiole » = pur fait de
#       rendu (la feuille cesse d'être peinte sur la plante, pas de moignon brun) ;
#       aucun champ neuf requis pour ça. Schéma ÉTENDU (4 → 5 éléments) : un binaire
#       pré-0.5.6 émet 4 éléments → la vue retombe sur age_sem = 0 (litière fraîche,
#       lecture tolérante). Champ optionnel côté vue.
# 0.5.7 (pots/bacs ④, mobilité + snapshot conteneurs) : nouveau bloc `containers`
#       au snapshot — liste des pots/bacs posés par le joueur (index implicite =
#       `target.container`). Par conteneur : id/kind/substrat/volume/mobile/
#       fond_ouvert/rows/cols, position monde x_cm·y_cm (que `deplacer_pot` change),
#       `plants` (forme compacte espèce/position/structure/fruits/symptômes pour la
#       future vue ⑥) et `eco_summary` (scalaires HUD du mini-sol au plot 0,0). Plus
#       3 verbes de la commande `action` : `poser_pot` / `poser_bac_culture` (pose
#       par POSITION monde, coût MODÉRÉ — le bac de CULTURE est distinct du bac à
#       COMPOST `poser_bac` de ⑤), `deplacer_pot` (déplace un pot par index, coût
#       Vigueur JOUEUR seule, refus si immobile/bac, AUCUN choc plante — philo #2) et
#       `planter_conteneur` (place une plante du banc-graines DANS un conteneur). PURE
#       extension de DONNÉES (bloc neuf) + commandes neuves → golden NEUTRE : le smoke
#       ne pose AUCUN conteneur → `containers: []`. Un binaire pré-0.5.7 ignore le
#       bloc et répond « verbe inconnu » aux 3 gestes (tolérance pré-0.5.7). VUE C#
#       différée (tronçon ⑥, Option B) : seul le moteur Python est branché ici.
# 0.5.8 (mycélium ④, faune fongivore + carpophores) : nouveau bloc `carpophores`
#       au snapshot — liste CREUSE par tuile des champignons VISIBLES `[[r, c,
#       x_frac, y_frac, densite], …]`, échantillonnés du champ `mycelium` par
#       `sample_carpophores` (PERCEPTION pure, aucun état moteur, comme les sprites
#       macro). Apparaissent en automne, sol humide, réseau dense → liste VIDE hors
#       saison / mycélium nul. PUR ajout lecture-seule → golden NEUTRE (les
#       carpophores ne touchent AUCUN champ). En PARALLÈLE, côté moteur (hors pont) :
#       le champ `mycelium` gonfle une fraction du détritivore du sol (`lombric`,
#       collemboles fongivores) via `signal_fn=_mycelium_signal` (knob FONGIVORE_GAIN)
#       — interconnexion champignon ↔ faune (§1.1), terme ADDITIF, mycelium=0 ⇒
#       neutre. Re-figeage MAÎTRISÉ du golden de POPULATION (faune touchée), pas du
#       smoke écologique (la faune n'entre pas dans son hash). VUE C# différée (⑥).
# 0.5.9 (mycélium ⑥, vue : tas colonisé) : chaque structure du bloc `structures`
#       gagne `colonisation` ∈ [0,1] (degré d'habitation fongique du tas, 0 pour la
#       ruche), à côté de `compost_mur`/`contenu`/`essaim`/`miel`. La vue ⑥ en tire le
#       VOILE FONGIQUE (filaments blancs) sur le bac/pile (§3.3). État DÉJÀ tické par
#       `tick_structures` (⑤) → simple TRANSPORT lecture-seule, golden NEUTRE (le smoke
#       ne pose aucune structure → bloc inchangé). Champ optionnel côté vue (tolérance
#       pré-0.5.9 → 0 = pas de voile). `epandre` 2 clics (UX source→cible) N'EST PAS un
#       incrément de protocole : le verbe accepte DÉJÀ {tile, structure, r, c} (0.3.5),
#       seule la VUE change (2 temps de désignation). Aucun autre champ ne bouge.
# 0.5.10 (météo→champs ⑤, interconnexions + voix + pont) : nouveau bloc
#       `condensation` au snapshot — liste CREUSE par tuile `[[r, c, rosee, givre],
#       …]` des plots ayant porté de la rosée LIQUIDE ce matin (`eco.rosee_last`) ou
#       du GIVRE accumulé (`eco.givre`, gelée blanche). La vue Godot en tire les
#       gouttes scintillantes / le givre blanc (rendu C# = dette D24). Plots secs OMIS
#       (liste creuse comme `litiere`/`alarme`). PUR ajout lecture-seule → golden
#       NEUTRE pour le pont (le pont ne réinjecte rien). En PARALLÈLE, côté moteur
#       (hors pont, golden léger ANNONCÉ) : la rosée RELIE le vivant — la faune du
#       matin (limace/cloporte) est ABREUVÉE (bump d'habitat ∝ rosée, `population.py`)
#       et une canopée CAPTE la rosée → allège le stress hydrique foliaire
#       (`croissance.py::_update_physiology`). Voix : encyclopédie (concepts `rosee`/
#       `gelee_blanche`), carnet (CONCEPT_DE → météo), pages secrètes (P21/P22). Champ
#       optionnel côté vue (tolérance pré-0.5.10).
# 0.5.11 (UI voix narratives ①, chaîne de maîtrise + 4 voix au pont) : QUATRE
#       commandes READ-ONLY neuves (`carnet`/`encyclopedie`/`pages`/`magazine`) qui
#       relaient VERBATIM le corpus des voix (invariant « Godot bête ») — `carnet`
#       ({filtre} optionnel), `encyclopedie` ({espece}→fiche N1/N2/N3 sinon index),
#       `pages` (ids trouvées + texte, ordre du corpus), `magazine` ({espece}→fiche
#       produit sinon offres). PLUS le verbe `acheter_magazine` de la commande
#       `action` (params.espece, chemin Vigueur unique : gate offre → débit
#       COUT_MAGAZINE → graine en banque ; `result.achete` bool + `bilan`
#       rafraîchi). Enfin la CHAÎNE DE MAÎTRISE qui alimente les voix, 3 hooks HORS
#       tick dans le pont (golden intact) : A `observer` après tick (espèces
#       vivantes + concepts eau/lumière/météo/pollinisation du log), B `detecter`
#       (crédit de palier), C `noter_geste` dans `cmd_action` (imputation du geste à
#       son plot). Palier 3 atteint → révélation d'une page « récompense ». PUR
#       ajout de commandes/verbe + hooks opt-in joueur → golden NEUTRE (le moteur
#       tourne sans serveur). Un binaire pré-0.5.11 répond « commande inconnue » aux
#       4 lectures et « verbe inconnu » à l'achat (tolérance côté vue).
# 0.5.12 (UI voix, retours F5 Nico) : l'OBSERVATION d'une espèce passe du balayage
#       automatique post-tick (toute plante vivante) au SURVOL souris — une plante
#       n'est apprise que si on passe la souris dessus (posture naturaliste). Hook A
#       espèces retiré de `observer_apres_tick` ; NOUVELLE commande `observer`
#       ({species}=nom de classe du snapshot → clé catalogue résolue côté Python,
#       découverte idempotente). Les CONCEPTS (eau/lumière/météo/pollinisation)
#       restent découverts par le vécu (log). PLUS commande `debug` ({op}) pour le
#       F5 : `palier3` (force palier 3 partout → magazine+pages+interprétatif),
#       `observer_tout` (découvre les espèces présentes), `reset` (maîtrise+pages à
#       zéro). Ajout de commandes opt-in joueur → golden NEUTRE. Un binaire
#       pré-0.5.12 répond « commande inconnue » à `observer`/`debug` (tolérance vue).
# 0.5.13 (UI voix, retour F5) : filtre CARNET par espèce (`carnet` accepte
#       `filtre.espece`, clé catalogue) + commande `aide` ({espece} → remèdes des
#       problèmes récents de l'espèce, chacun avec `concept` + `debloque` = concept
#       maîtrisé ≥ seuil ; corpus `sim/aide.py`, « debug d'abord » structuré pour un
#       gating de jeu futur). Ajouts read-only opt-in joueur → golden NEUTRE. Un
#       binaire pré-0.5.13 ignore `filtre.espece` et répond « commande inconnue » à
#       `aide` (tolérance côté vue).
# 0.5.14 (épaisseur de sol ①a, D57) : nouveau champ STOCKÉ `epaisseur_sol` par plot
#       (cm de sol foisonnant au-dessus de la roche-mère) + tick `tick_epaisseur`
#       (relaxation vers une cible bulk-density dérivée des `om_*`, foisonnement de la
#       litière fraîche ∝ 1/(1+K·age_sem), inertie asymétrique monte-vite/descend-lent,
#       érosion). C'est l'expression PHYSIQUE du cycle MO (la matière qui tombe épaissit
#       le sol, tassement/décompo la rognent, humus l'exhausse). Initialisé AU REPOS
#       (`init_eco` : cible sur l'om_stable de fond D56). AUCUN effet en retour ce
#       tronçon (eau/NPK = ①b, relief extrudé = ②) → lu par PERSONNE → golden NEUTRE.
#       Champ exposé au registre `get_field` (overlay debug F6 `fields`) ; pas de
#       nouvelle sérialisation snapshot (l'exposition au pont = tronçon ②). Le save
#       disque du champ suivra le sprint save global (aucun save disque n'existe encore).
# 0.5.15 (épaisseur de sol ①b, D57) : le champ `epaisseur_sol` (①a) AGIT enfin sur
#       l'écologie via DEUX flux du sol (jamais un bonus direct sur la plante, philo #2).
#       (1) RÉTENTION D'EAU (`tick_hydrology`, terme miroir de la rétention soil_memory) :
#       un sol profond garde l'eau, MODULÉ par la composition (`cec_norm_at`) — l'humus
#       compte plus sur sable pauvre que sur argile déjà rétentrice ; asphyxie D39 NON
#       bridée. (2) ACCÈS NPK (`plant_uptake`) : un sol profond met une plus grande part
#       du stock N/P/K à disposition (amplificateur BORNÉ du besoin, patron MYCO_P_BONUS ;
#       à epaisseur=0 → ×1.0 ⇒ jamais pire que le baseline → D41 famine PRÉSERVÉE, Liebig
#       plafonne toujours par le stock réel). Les deux lisent l'épaisseur du tick PRÉCÉDENT
#       (hydro/uptake AVANT `tick_epaisseur` 13b-bis — décalage 1 tick uniforme). Golden
#       RE-FIGÉ ANNONCÉ (deux flux neufs) ; dérive localisée aux plots épais, bornée
#       (test 500 ans anti-emballement : convergence vérifiée). Pas de sérialisation
#       snapshot neuve (l'exposition au pont = tronçon ②, relief extrudé).
# 0.5.16 (épaisseur de sol ②, D57) : le champ `epaisseur_sol` (①a) est enfin EXPOSÉ
#       au snapshot — nouveau bloc `epaisseur` par tuile = grille 2D dense rows×cols
#       en cm (patron `temperature.t_sol`). La vue en extrude un RELIEF iso (le dessus
#       de chaque plot remonte de `epaisseur_cm × PxPerCmZ`) → on VOIT le sol monter
#       (humus qui s'accumule) et descendre (décompo/tassement/érosion), et les objets
#       posés (plantes/litière/macro/structures) sont recalés d'autant. PURE lecture
#       (champ déjà tické par 13b-bis) → golden NEUTRE. Champ optionnel côté vue
#       (tolérance pré-0.5.16 → relief plat). VUE C# = parties B/C de ce tronçon.
# 0.5.17 (hydrologie & marécages ①, altitude) : nouveau champ STOCKÉ `altitude` par
#       plot (cm de micro-relief TOPOGRAPHIQUE du terrain, ≠ `epaisseur_sol` = humus)
#       + son EXPOSITION au snapshot — nouveau bloc `altitude` par tuile = grille 2D
#       dense rows×cols en cm (patron `epaisseur`). Socle géométrique FIXE (aucun tick
#       ne l'écrit ; seuls les gestes creuser/drainer de ⑦ le modifieront), initialisé
#       HÉTÉROGÈNE par `init_eco` sur un canal de hash DÉCORRÉLÉ de l'humus (relief et
#       fertilité ne coïncident pas, philo #3/#7). Support de l'ÉCOULEMENT de l'eau (②,
#       du haut vers le bas) et du relief du terrain (⑧). Lu par PERSONNE ce tronçon
#       (aucun tick, aucun effet) → golden NEUTRE. Champ exposé au registre `get_field`
#       (overlay debug F6) + au snapshot. Champ optionnel côté vue (tolérance
#       pré-0.5.17 → terrain plat). VUE C# (relief altitude) = tronçon ⑧.
# 0.5.18 (grimpantes ⑥, D49 volet A — supports + accroche au pont) : DEUX ajouts
#       lecture-seule. (1) nouveau bloc `supports` par tuile = liste des supports de
#       grimpe POSABLES `[{type ("tuteur"/"treillis"/"pergola"), x_cm, y_cm,
#       height_cm, finesse}, …]` (repère tuile-local, `tile.supports` rempli par les
#       gestes poser_* ④) → la vue en dessine le placeholder procédural (pieu/grille/
#       portique). (2) chaque plante grimpante ACCROCHÉE gagne `support` =
#       `{type, height_cm}` (type ∈ tuteur/treillis/pergola/mur/hote) → la vue en tire
#       l'indice d'accroche + les vrilles (rendu différé RENDU_FEUILLAGE §7/E6, débloqué
#       par la mécanique ①→④). La grimpe elle-même est GRATUITE côté vue : les segments
#       montent/s'affalent déjà dans le snapshot (décision A géométrique) → PlantRenderer
#       les dessine sans code neuf. PURE extension de DONNÉES (blocs/champs neufs) →
#       golden NEUTRE : le smoke ne pose aucun support et n'accroche aucune grimpante
#       → `supports: {tuile: []}` et aucune clé `support` par plante. Un binaire
#       pré-0.5.18 ignore le bloc/champ (tolérance côté vue, comme les bumps précédents).
# 0.5.19 (luxuriance par stratification ⑥, D65 — vue Godot au pont) : TROIS ajouts
#       lecture-seule pour rendre la LUXURIANCE visible. (1) chaque plante gagne
#       `strate` (sol/basse/moyenne/haute/grimpante, strate du stade COURANT),
#       `silhouette` (tapis/rosette/touffe/étalée/dressée/buisson, silhouette_base ③)
#       et `clonal_mode` (none/stolon/rhizome/drageon) — pilotent l'ordre de dessin
#       par strate (couvre-sol SOUS potagère SOUS grimpante), la FORME de la silhouette
#       et l'indice de colonie clonale. (2) nouveau bloc `couverture` par tuile = liste
#       CREUSE `[[r, c, cov], …]` du champ `couverture_sol` (①) au-dessus de
#       COUVERTURE_RENDU_SEUIL → la vue en tire le TAPIS au sol (densité ∝ cov, indice
#       diégétique philo #5). Tous DÉRIVÉS d'un état déjà calculé (strate du stade,
#       descripteur data, champ tické), HORS _PLANT_ATTRS du golden → golden INTACT
#       (le pont ne réinjecte rien). Un binaire pré-0.5.19 n'émet ni ces clés plante ni
#       le bloc `couverture` → la vue retombe sur l'ordre Y-sort seul, silhouette par
#       défaut, pas de tapis (lecture TOLÉRANTE, comme tous les bumps précédents).
ENGINE_VERSION = "0.5.19"

# Repli pour une espèce absente de REPRO_BY_SEASON (kickoff t6 : « fleur au
# printemps, fruit mûr en été/automne, rien l'hiver ») — raisonnable pour les
# herbacées du catalogue en attendant le VRAI état reproducteur (D19/D33).
DEFAULT_REPRO = {"printemps": "flower", "ete": "fruit_ripe",
                 "automne": "fruit_ripe", "hiver": None}

# Tolérance du match plante-par-position (kickoff t4 §8) : les positions du
# snapshot reviennent telles quelles dans la cible → l'epsilon n'absorbe que le
# bruit de sérialisation JSON (float64 round-trip, en pratique exact).
PLANT_EPSILON_CM = 0.1
