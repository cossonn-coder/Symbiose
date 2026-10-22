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
# 0.5.20 (équilibre invasion ⑧, D69 — vue Godot du paillage) : DEUX ajouts. (1) le
#       snapshot expose `paillage` par tuile = liste CREUSE `[[r, c, profondeur,
#       nature], …]` des plots mulchés (profondeur > 0 ; nature ∈ paille/brf/aiguilles).
#       La vue en tire le TAPIS de mulch au sol (teinte/texture par matériau, opacité ∝
#       profondeur, MulchLayer). PURE lecture (`eco.paillage`/`eco.paillage_nature` déjà
#       tickés par `tick_paillage`) → golden NEUTRE : le smoke ne paille jamais →
#       paillage=0 partout → liste vide. (2) DEUX verbes neufs au routeur `action` :
#       `pailler` (target plot {tile, r, c}, `params.nature` — dépose du mulch, consomme
#       le stock de la nature, refus en amont si stock vide) et `broyer` (target par
#       POSITION continue {tile, x_cm, y_cm} sur un SQUELETTE — fragmente son bois en
#       BRF au stock). Ces gestes ÉTAIENT déjà dans le moteur (③/④) ; ⑧ les BRANCHE au
#       pont. Un binaire pré-0.5.20 ignore le bloc `paillage` et répond « verbe inconnu »
#       aux 2 gestes (tolérance côté vue, comme tous les bumps précédents).
# 0.5.21 (perf LOD des émetteurs d'ombre ③, D67 — vue Godot au pont) : chaque plante
#       VIVANTE du snapshot gagne `emitteur` ∈ {true, false} = DÉRIVÉ du pouvoir
#       ombrageant (hauteur × rayon canopée × densité foliaire ≥ SHADING_POWER_MIN),
#       miroir EXACT de la métrique de `fields/light.py:compute`. false = semis
#       sous-seuil que le LOD écarte des deux boucles géométriques (reçoit toujours la
#       lumière, n'ÉMET plus d'ombre). La vue teinte ces NON-émettrices sous un toggle
#       debug (F7) → on VOIT qui le LOD retire. PURE lecture d'un dérivé (aucun état
#       moteur neuf, la densité est déjà calculée pour `foliage_density`) → golden
#       NEUTRE. Un binaire pré-0.5.21 n'émet pas la clé → la vue retombe sur `true`
#       (défaut = émettrice, aucune plante teintée ; tolérance comme tous les bumps).
# 0.5.22 (diversité fondatrice ③ — banc d'observation au pont) : chaque plante VIVANTE
#       du snapshot gagne `genes` = dict clé→valeur (arrondi 3 déc.) de son patrimoine
#       génétique (tiré au founder ①/hérité). Sert le SURVOL GÈNES debug (WorldView.
#       Genes.cs, touche G) : la vue relit les gènes de rythme (`vigueur`,
#       `germination_thermique`, `phenologie_florale`) de la plante pointée. PURE
#       lecture d'un état déjà porté par l'instance (`p.genes`) → golden NEUTRE (le
#       snapshot n'est pas figé par test_golden). Nouveau banc montable `init
#       config="diversite_fondatrice"` (64 tournesols à patrimoine propre sur sol
#       catena) — jamais monté pour smoke/full. Un binaire pré-0.5.22 ignore la clé
#       `genes` (dict vide → survol muet ; tolérance comme tous les bumps).
# 0.5.23 (palette de gestes ① — déblocage au pont) : le bloc `player` du snapshot
#       gagne DEUX clés. `gestes_debloques` = liste TRIÉE des verbes OUVERTS pour
#       l'avatar (set de BASE ∪ ce que la maîtrise/les actions ont débloqué, table
#       `sim/actions/deblocage.GESTE_UNLOCK`) → la palette Godot (tronçon ④, colonne
#       gauche D11) n'affiche QUE l'ouvert. `debloques_recents` = verbes ouverts au
#       DERNIER tick par la voie savoir (franchissement de palier), consommé à la
#       lecture → notification diégétique unique. La commande `action` gagne un champ
#       `debloques` (verbes ouverts par un geste DÉCLENCHEUR réussi : poser_bac ouvre
#       composter…). Nouveau geste BRUT `couper` (ancêtre de `tailler`, D12) au
#       catalogue de coûts + sa fiche encyclopédie. PURE lecture/écriture d'un état
#       JOUEUR opt-in (hors tick) → golden NEUTRE (le golden tourne sans serveur, ces
#       clés ne naissent jamais). Un binaire pré-0.5.23 n'émet pas ces clés → la vue
#       retombe sur « tout dispo » (tronçon ④, tolérance comme tous les bumps).
# 0.5.24 (palette de gestes ② — bouture au pont) : nouveau verbe `bouturer` à la
#       commande `action` — geste à 2 TEMPS côté VUE (mémoire des 2 clics dans Godot,
#       serveur STATELESS comme `epandre`/`deplacer_pot`). Un seul appel porte la MÈRE
#       par position continue (`target.x_cm`/`y_cm`, comme tailler) ET le plot cible
#       par `params.r`/`params.c` (2e clic). La façade `sim.actions.bouturer` fait foi :
#       gate d'espèce (`plant_class.bouturable`, flag NEUF défaut False), maturité +
#       vigueur de la mère, coût MODÉRÉ, pose d'un CLONE génétique (patron `clonal.py`,
#       gènes copiés + priming hérité), bouffée de `stress_memory` sur la mère (philo
#       #1/#2). Une bouture réussie pose le marqueur écologique `bouture_spontanee`
#       (voie expérimentale émergente D12 → ouvre `bouturer` par `("evenement", …)`).
#       Nouveau geste `bouturer` au catalogue de coûts + technique `bouture` + fiches
#       encyclopédie (geste + technique) + concept carnet `bouture`→reproduction.
#       PURE extension (geste event-driven hors tick, flag NEUTRE par défaut) → golden
#       NEUTRE (le smoke n'invoque aucun geste, aucune espèce bouturable n'est semée
#       par lui). Un binaire pré-0.5.24 répond « verbe inconnu » à `bouturer`
#       (tolérance comme tous les bumps).
# 0.5.25 (palette de gestes ③ — greffe au pont) : nouveau verbe `greffer` à la
#       commande `action` — geste à 2 TEMPS côté VUE (mémoire des 2 clics dans Godot,
#       serveur STATELESS comme `bouturer`). Un seul appel porte le PORTE-GREFFE par
#       position continue (`target.x_cm`/`y_cm`, cible primaire — il RESTE) ET le
#       GREFFON par `params.scion_x_cm`/`scion_y_cm` (1er clic, MÊME tuile). La façade
#       `sim.actions.greffer` fait foi : gate `peut_greffer` (les deux VIVANTS +
#       `plant_class.greffable` — flag NEUF défaut False, ligneuses fruitières — +
#       même FAMILLE botanique via `species_compatible`), coût ÉLEVÉ, RECOMPOSITION
#       aérien/racinaire (D8 : le porte-greffe adopte la `plant_class` du greffon + ses
#       gènes AÉRIENS, garde ses gènes RACINAIRES + son établissement âge/stade/racines
#       → précocité), greffon CONSOMMÉ (santé 0 + `morte`). DÉTERMINISTE (philo #3 : la
#       reprise est ACQUISE si le gate passe, zéro RNG). Nouveau geste `greffer` au
#       catalogue de coûts (`ELEVE`, objets `greffe`/`greffoir`) + technique `greffe`
#       (dans TECHNIQUES) + fiches encyclopédie (geste `greffer` + technique `greffe`)
#       + concept carnet `greffe`→reproduction (gabarit dédié). Câblé à la voie savoir
#       `("maitrise", "greffe", 1)` de ① (clé posée en ①). PURE extension (geste
#       event-driven hors tick, flag NEUTRE par défaut) → golden NEUTRE (le smoke
#       n'invoque aucun geste, aucune espèce greffable n'est greffée par lui). Un binaire
#       pré-0.5.25 répond « verbe inconnu » à `greffer` (tolérance comme tous les bumps).
# 0.5.26 (palette de gestes ⑤ — macros + persistance du layout) : le bloc `player`
#       du snapshot porte désormais `palette` = {slots, macros} de l'avatar courant
#       (LAYOUT curé + MACROS D1/D5/D10, lecture pure d'un état joueur opt-in). NOUVELLE
#       commande `palette` (write, bornée à l'état joueur comme `observer`/`debug`) :
#       PERSISTE un changement de layout envoyé par la VUE — `msg.slots` (liste de
#       verbes curés, remplace) et/ou `msg.macros` (liste de {nom, sequence}, remplace).
#       La façade `sim.actions.definir_palette` fait foi : chaque macro est VALIDÉE en
#       cohérence de cible (tous les sous-gestes partagent la MÊME famille de cible via
#       `FAMILLE_CIBLE` — un clic unique doit tous les alimenter) AVANT écriture (refus
#       en bloc, transaction). Le MOTEUR ne « connaît » pas les macros : la vue REJOUE
#       la séquence comme N gestes `action` normaux sur la même cible (chacun paie sa
#       Vigueur, philo #1). PURE extension (état joueur opt-in, hors tick, aucun RNG) →
#       golden NEUTRE (le golden tourne hors serveur, aucune clé `palette` créée). Un
#       binaire pré-0.5.26 répond « commande inconnue » à `palette` (tolérance côté vue).
# 0.5.27 (hydrologie & marécages ③, marécage) : nouveau champ STOCKÉ `marais_memory`
#       par plot ∈ [0,1] (intégration lente d'une flaque qui dure, hystérèse d'état
#       `est_marais`) — EFFETS moteur : décompo anaérobie ralentie (→ tourbe émergente)
#       + acidification du pH vers PH_TOURBE. EXPOSITION au snapshot : nouveau bloc
#       `marais` par tuile = liste CREUSE `[[r, c, marais, etat], …]` des plots où la
#       mémoire dépasse MARAIS_OFF (la vue « noircit » le sol ∝ intensité, philo #5).
#       `marais_memory` exposé AUSSI au registre `get_field` (overlay F6). Effets NULS
#       au repos (aucune flaque durable ⇒ marais_memory=0 ⇒ facteurs ×1.0/+0.0) →
#       golden NEUTRE hors banc. Un binaire pré-0.5.27 ignore le bloc `marais` (tolérance
#       côté vue, comme les bumps précédents). VUE C# (sol de marais) = tronçon ⑧.
# 0.5.28 (santé & résilience ④, vitalité continue au pont + vue) : chaque plante
#       VIVANTE (en pleine terre ET en conteneur) gagne DEUX clés lecture-seule au
#       snapshot — `vitalite` ∈ [0,1] (float arrondi 3 déc., 1.0 = sain neuf) et
#       `etat` (str discrétisé : "sain"/"affaibli"/"malade"/"mort", seuils de ①).
#       C'est le DESCRIPTEUR GLOBAL de l'usure de la plante (érosion des stresseurs
#       via `erode()` divisée par la constitution `resilience_base`, convalescence
#       modulée par la vigueur) qui COMPLÈTE les `leaf_symptoms` localisés : la vue
#       C# module la teinte/saturation du feuillage ∝ vitalité (sain = vert plein →
#       affaibli = terne/désaturé → malade = jauni) dans la palette pixel-art
#       (Palette16), en composant avec les symptômes (fond global + marques). PURE
#       lecture d'un état déjà porté par l'instance (`p.vitalite`/`p.etat`, ①) —
#       hors _PLANT_ATTRS du golden → golden INTACT. Un binaire pré-0.5.28 n'émet
#       pas ces clés → la vue retombe sur le mapping par `leaf_symptoms` seul
#       (tolérance côté vue, comme tous les bumps précédents).
# 0.5.29 (allélopathie ⑥, vue : champ au snapshot + indice diégétique) : nouveau
#       bloc `allelopathie` au snapshot — liste CREUSE par tuile `[[r, c,
#       concentration], …]` des plots chargés en allélochimiques (au-dessus du
#       plancher ALLELO_FLOOR de snap-à-0 ; la plupart des plots sont propres →
#       liste courte, patron `alarme`/`couverture`). Lecture DIRECTE de
#       `eco.allelopathie` (champ AMBIANT tous émetteurs confondus, tické par
#       `tick_allelopathie` ①) : la vue en tire l'indice DIÉGÉTIQUE de sol PELÉ
#       sous un émetteur fort (halo sans levée autour du noyer/armoise, philo #5,
#       pas de chiffre). Les champs `allelopathie` ET `autotox` (GridField déclarés
#       aux ① et ④) sont DÉJÀ exposés au registre `get_field` (overlay debug F6
#       `fields`) par l'introspection — aucun ajout de commande. PURE lecture d'un
#       état déjà tické → golden INTACT (le pont ne réinjecte rien ; le golden
#       tourne hors serveur). Un binaire pré-0.5.29 ignore le bloc `allelopathie`
#       (tolérance côté vue, comme tous les bumps précédents).
# 0.5.30 (jardinier automate ⑥, vue Godot) : nouvelle commande `automate`
#       (op ∈ {on, off, objectif, status}) qui MONTE/DÉMONTE le jardinier automate
#       déterministe (paquet `tools.jardinier_auto`) en OPTION F5 et lui pousse des
#       objectifs (geste+quantité+cible) en planification. Quand un automate est
#       actif, il joue ENTRE deux ticks dans `cmd_step_week` (APRÈS tick_semaine,
#       invariant H2 — jamais dans le tick) via les MÊMES façades `sim.actions` que
#       le joueur (philo #2), et le snapshot gagne un bloc OPT-IN `automate` =
#       {actif, profil, trace (N dernières entrées : gestes/impasses/conséquences),
#       objectifs (id/geste/quantité/cible/progression/accompli)}. La vue en tire le
#       journal/impasses + l'onglet objectifs (filtre trace par `objectif_id`).
#       Opt-in STRICT : sans `automate on`, `self._automate` est None → aucun bloc
#       émis, snapshot inchangé, aucun geste joué → golden INTACT (le golden tourne
#       hors serveur ; ce chemin n'existe jamais pour lui). Un binaire pré-0.5.30
#       ignore la commande (erreur pont non fatale) et n'émet pas le bloc → la vue
#       retombe sur « pas d'automate » (tolérance, comme tous les bumps précédents).
# 0.5.31 (acquisition des moyens d'agir ①, gestes manuels) : DEUX verbes neufs à la
#       commande `action`, gestes structurels de BASE à mains nues (gradient
#       `pincer < arracher < couper/tailler`, spec §A) — désignés par POSITION
#       continue comme `tailler` (`target.x_cm`/`y_cm` + `params.cible`
#       apex/branche + `target.segment` optionnel du clic). `pincer` (coût FAIBLE) :
#       régime DOUX du seam (auxine ↓, AUCUN retrait) → débourrement ÉMERGENT au tick
#       (philo #2), rien déposé au sol. `arracher` (coût ELEVE) : régime NET à la main
#       (écime + litière `bois`, MÊME calcul que `tailler`) MAIS appelle `plant.erode`
#       (la déchirure manuelle stresse la plante — DIFFÉRENCIATEUR main/outil, philo
#       #1/#6) et NE rend AUCUNE Vigueur (on jette). Les façades `A.pincer`/`A.arracher`
#       font foi. PURE extension (gestes event-driven, opt-in joueur, hors tick) →
#       golden INTACT (le smoke est une succession sans joueur, ces verbes ne sont
#       jamais appelés). Un binaire pré-0.5.31 répond « verbe inconnu » aux 2 gestes
#       (tolérance côté vue, comme tous les bumps précédents).
# 0.5.32 (acquisition des moyens d'agir ②, sécateur à l'Atelier — CŒUR D82) :
#       verbe neuf `acheter_outil` à la commande `action`, chemin Vigueur UNIQUE
#       sans tuile (`params.outil`, jumeau d'`acheter_magazine`). La façade
#       `sim.outils.acquerir_outil` fait foi : gate l'offre du registre `OUTILS`
#       data-driven + idempotence (outil déjà possédé → pas de re-débit) + débite
#       le `cout_vigueur` + POSE le marqueur `posseder_secateur` (via
#       `marquer_action`) + rouvre la chaîne taille `couper`→`tailler` (via
#       `evaluer_deblocages`) — lève D82 (rien ne posait ce marqueur, toute la
#       famille taille était morte). `result.achete` bool + `bilan` rafraîchi ;
#       les verbes fraîchement ouverts apparaissent dans `player.gestes_debloques`
#       du snapshot (0.5.23). PURE extension (verbe event-driven, opt-in joueur,
#       hors tick) → golden INTACT (le smoke tourne sans joueur, ce verbe n'est
#       jamais appelé). Un binaire pré-0.5.32 répond « verbe inconnu » à
#       `acheter_outil` (tolérance côté vue, comme tous les bumps précédents).
# 0.5.33 (acquisition des moyens d'agir ③, ravitaillement mulch — 2 verbes) : DEUX
#       verbes neufs à la commande `action`, sourçant le mulch qui manquait (lève
#       l'impasse `RAVITAILLEMENT_MANQUANT`). `glaner` (canal 1, target plot
#       {tile, r, c}, patron `becher`) : ramasse la litière de SURFACE tendre du plot
#       (feuille/fleur/herbace/fruit) → crédite le stock nature NEUVE `feuilles`
#       (ajout à `NATURES_MULCH`, profil paille-tendre distinct du BRF) ; refus en
#       amont si sol propre. Coût FAIBLE, geste BASE sans outil. `acheter_materiau`
#       (canal 3, chemin Vigueur UNIQUE sans tuile, `params.materiau`, jumeau
#       d'`acheter_outil`) : gate l'offre du registre `MATERIAUX` data-driven
#       (`botte_paille`) + débite le `cout_vigueur` + crédite le stock de mulch de la
#       nature (import EXTERNE parallèle au magazine, PAS idempotent = consommable).
#       En PARALLÈLE, canal 2 = DONNÉES seules : `ble`/`chanvre` ajoutés à
#       `BANQUE_DEPART` (config `full`) → cultivables tôt → `recolter_paille` alimente
#       le stock. PURE extension (verbes event-driven, opt-in joueur, hors tick ;
#       nature `feuilles` lue seulement par un paillage `feuilles`, jamais au smoke)
#       → golden INTACT. Un binaire pré-0.5.33 répond « verbe inconnu » à `glaner`/
#       `acheter_materiau` (tolérance côté vue, comme tous les bumps précédents).
# 0.5.34 (acquisition des moyens d'agir ④, vue Godot — vitrine Atelier au pont) :
#       NOUVELLE commande READ-ONLY `atelier` → `{outils: [{cle, cout_vigueur,
#       possede}], materiaux: [{cle, nature, dose, cout_vigueur}]}`, la vitrine de
#       l'Atelier de la maison (offre d'OUTILS + MATÉRIAUX à acquérir contre Vigueur).
#       Miroir lecture-seule des verbes d'ACHAT déjà en place (`acheter_outil` 0.5.32,
#       `acheter_materiau` 0.5.33) : la commande relaie les registres `OUTILS`/
#       `MATERIAUX` (offre bornée à la Vigueur) + la possession de l'outil, DÉRIVÉE de
#       `est_debloque(couper)` (⇔ marqueur `posseder_secateur` posé) — aucun état neuf,
#       « Godot bête » : la vue LIT et met en page (AtelierPanel, jumeau du Magazine).
#       PUR ajout de commande lecture-seule (aucun tick, aucune écriture) → golden
#       INTACT (le golden tourne sans serveur, cette commande n'est jamais appelée).
#       Un binaire pré-0.5.34 répond « commande inconnue » → l'Atelier s'affiche vide
#       côté vue (tolérance comme tous les bumps précédents). Côté MOTEUR, les 3 gestes
#       manuels/glanage (`pincer`/`arracher`/`glaner`) sont ajoutés à `GESTES_BASE`
#       (sim/actions/deblocage.py) — ils étaient absents de la table de déblocage, ce
#       qui les GRISAIT à jamais dans la palette Godot ; la spec §A/§C les déclare de
#       BASE (mains nues, amorçables sans outil). No-op golden (set jamais matérialisé
#       hors joueur). AUCUN verbe neuf : les 5 verbes de la vue (`acheter_outil`/
#       `acheter_materiau`/`pincer`/`arracher`/`glaner`) existaient déjà (01-03).
# 0.5.35 (hydrologie & marécages ⑦, gestes de terrassement) : DEUX verbes neufs à la
#       commande `action`, gestes sur le MILIEU au PLOT {tile, r, c} (patron
#       `grelinette`), coûteux en Vigueur et EVENT-DRIVEN (hors tick → golden neutre).
#       `creuser` (coût ÉLEVÉ, technique `terrassement`+`bêche`) : `altitude ← max(0,
#       altitude − CREUSER_DELTA)` (le JOUEUR façonne une CUVETTE → au ruissellement ②
#       l'eau y converge, mare émergente) + `microbiome −= BECHAGE_MICROBIOME_MALUS`
#       (retourner la terre perturbe le sol, comme `becher`). `drainer` (coût MODÉRÉ) :
#       `eau_surface ← 0` (vide la flaque) + `marais_memory *= 1 − DRAINER_ASSECHE`
#       (assèchement forcé — répété, la mémoire repasse sous MARAIS_OFF et l'état marais
#       se lève au `tick_marais` ③). Les façades `A.creuser`/`A.drainer` font foi (coût,
#       bornes des GridField altitude≥0/microbiome≥0/eau_surface≥0/marais_memory≥0).
#       `altitude` cesse d'être purement déterministe : creuser la modifie (hors tick).
#       Les 2 gestes rejoignent `GESTES_BASE` (rustiques à la bêche, dès le 1ᵉ avatar) →
#       palette Godot les propose. PURE extension (gestes event-driven, opt-in joueur,
#       hors tick) → golden INTACT (le smoke est une succession sans joueur, ces verbes
#       ne sont jamais appelés). Un binaire pré-0.5.35 répond « verbe inconnu » à
#       `creuser`/`drainer` (tolérance côté vue, comme tous les bumps précédents). VUE C#
#       (relief creusé, flaque/marais drainés) = tronçon ⑧.
# 0.5.36 (fenêtrage UI T1, sélecteur défilable + filtrable) : la commande
#       `list_bancs` renvoie désormais `{bancs: [{nom, categorie}, …]}` (au lieu
#       d'une liste de noms nus) — la CATÉGORIE = le module thématique d'où vient
#       la fabrique du banc (`bancs.climatique` → "climatique"), DÉRIVÉE par
#       `banc_categorie` (aucune table à resynchroniser). Trié par nom (affichage
#       déterministe). Sert le FILTRE par catégorie du nouveau sélecteur Godot
#       (panneau haut-gauche défilable). Lecture du registre (aucun moteur) →
#       golden NEUTRE (le golden tourne hors serveur ; smoke/full ne sont pas des
#       bancs). Un binaire pré-0.5.36 renvoie des noms nus → SimBridge.ListBancs()
#       les mappe en catégorie "divers" (tolérance, compat binaire gelé).
# 0.5.37 (fenêtrage UI T2, options d'init au montage) : `cmd_init` accepte DEUX
#       champs OPTIONNELS du panneau Paramètres du launcher. `carnet_anticipe: bool`
#       → pose `game_state["options"][player]["carnet_anticipe"]`, lu DÉJÀ par
#       `sim/carnet._reglage_anticipe` (SEUIL_ANTICIPE=1 : le carnet bascule en
#       interprétatif dès palier 1). `encyclo_demarrage: "vierge"|"amorcee"|"fournie"`
#       → amorce des DÉCOUVERTES (palier 1, fiche encyclo niveau 1 seule, PAS le
#       carnet) via le mécanisme EXISTANT `maitrise.decouvrir` : "amorcee" = cultivées
#       de départ (BANQUE_DEPART), "fournie" = tout le catalogue, "vierge"/absent =
#       rien. Champs ABSENTS → aucun effet (smoke/full ne les passent jamais) → golden
#       INTACT. Un binaire pré-0.5.37 ignore silencieusement ces deux champs de
#       `cmd_init` (tolérance : options sans effet, le monde monte quand même).
# 0.5.38 (retours UI/HUD T3, dossier de plante DEBUG) : chaque plante VIVANTE du
#       snapshot gagne TROIS clés lecture-seule pour l'outil de test « dossier de
#       plante » (clic en mode inspection F2 → panneau debug read-only, du rang des
#       overlays F6/F7). `memoires` = dict des 8 intégrateurs lents de stress vécu
#       (shade/drought/asphyxie/cold/infection/wind/root_herbivory/stress ∈ [0,1],
#       l'« histoire compressée » de la plante — il n'existe PAS de chronologie par
#       instance côté moteur, ces scalaires en tiennent lieu) ; `expression` = dict
#       FILTRÉ des facteurs de plasticité ≠ 1.0 (durcissement acquis ; plante non
#       acclimatée → dict vide) ; `age_weeks`/`age_years` (âge dans le stade / total).
#       PURE lecture d'un état DÉJÀ porté par `plants/base/instance.py` (hors
#       _PLANT_ATTRS du golden) → golden INTACT (le golden tourne hors serveur). Un
#       binaire pré-0.5.38 n'émet pas ces clés → le panneau retombe sur les champs
#       absents (lecture tolérante ContainsKey, comme tous les bumps précédents).
# 0.5.39 (mémoire d'inoculum ④, vue Godot) : nouveau bloc `inoculum` par tuile au
#       snapshot = liste CREUSE `[[r, c, famille_dominante, charge_totale], …]` des
#       SEULS plots viciés (dict `eco.inoculum.load` SPARSE → un plot sain n'a aucune
#       entrée, liste courte, patron `marais`/`eau_surface`). Par plot chargé : la
#       famille dont le bucket est le plus lourd (la maladie qui hiverne le plus) +
#       la charge totale toutes familles (`inoculum.total`, sert la niche molène ③
#       et la heatmap F6 « charge pathogène »). PURE lecture d'un champ déjà tické
#       par `tick_decay` (④g) → golden NEUTRE : le smoke ne vicie aucun plot →
#       dict vide → liste vide. Un binaire pré-0.5.39 ignore le bloc (la heatmap
#       `inoculum` retombe sur 0 = sol sain ; tolérance comme tous les bumps).
# 0.5.40 (système de quêtes D79 ⑤, vue Godot du courrier) : nouvelle commande
#       READ-ONLY `courrier` → `lettres` = liste (triée par id) des quêtes du joueur,
#       chacune {id, donneur, texte_lettre, avancement (phrase DIÉGÉTIQUE, jamais un
#       chiffre), accomplie (coche), atteignable (rêve hors catalogue = kiwi, F3)}. Le
#       CHIFFRE exact (progression/condition) n'est joint QUE si `msg.debug` (V2/#5).
#       Ouvrir le panneau ÉVALUE les quêtes d'état sur le snapshot (hors tick, point
#       d'évaluation légitime) mais NE VERSE aucune récompense. En parallèle, le DRIVER
#       des quêtes (arrivée des lettres mûres + clôture d'état + versement idempotent)
#       est câblé dans `step_week` HORS tick (opt-in : le golden tourne hors serveur →
#       jamais appelé → golden intact ; snapshot inchangé, aucun bloc `quetes` sérialisé).
#       Un binaire pré-0.5.40 répond « commande inconnue » à `courrier` (l'onglet
#       Courrier s'affiche vide, inoffensif — tolérance comme tous les bumps).
# 0.5.41 (périphérie D73 ⑦, vue Godot — DERNIER tronçon du sprint) : nouveau bloc
#       OPT-IN `ceinture` au snapshot = les 4 secteurs cardinaux de la périphérie
#       (`cote`, `type`, `essence`, `hauteur_canopee`, `densite_ligneuse`,
#       `souche_memory`, `ligne_eau`, `altitude_relative`, `entaille_cm`, `ouvrage`).
#       C'est la fin de la dette D58·T4 : `DecorLayer.BuildProfile(seed)` CESSE
#       d'être la source du décor et devient un REPLI — la vue consomme désormais la
#       vérité Python, ce qui referme **D92 par le haut** (le hash C# mal brassé
#       donnait 96 % de terrains aux 4 côtés identiques et zéro falaise ; le tirage
#       Python du ① donne 2,7 % / 52 %). Le bloc est ABSENT d'un monde sans ceinture
#       (smoke, bancs thématiques) → snapshot inchangé, repli local côté vue. PLUS
#       **SIX verbes neufs** à la commande `action`, tous ciblant un SECTEUR
#       (`target.cote` ∈ 0..3, granularité D-1) : `abattre`/`receper`/`eteter` (④,
#       gatés par hache/serpe via `GESTE_UNLOCK`) et `endiguer`/`deriver`/
#       `entailler` (⑤). `creuser` N'EST PAS dupliqué : il est routé vers la MARE de
#       bordure quand sa cible porte un `cote` (clic hors jardin), au plot sinon —
#       routage sur la FORME du target, comme `ecraser` (0.3.2). Enfin la ceinture
#       est POSÉE à l'init (`generer_ceinture(seed)`) pour les mondes de JEU (`full`,
#       `propre`) et par le banc `peripherie` (§D) ; `smoke` et les autres bancs
#       restent SANS périphérie (fixtures inchangées). PURE extension (bloc
#       lecture-seule + gestes event-driven hors tick) → golden INTACT : le golden
#       tourne hors serveur et n'a aucune clé `ceinture`. Un binaire pré-0.5.41
#       n'émet pas le bloc (→ `DecorLayer` garde son profil local) et répond « verbe
#       inconnu » aux 6 gestes (tolérance comme tous les bumps précédents).
# 0.5.42 (humectation foliaire ③, geste arroser pied/feuillage) : le verbe `arroser`
#       gagne un champ OPTIONNEL `params.feuillage` (bool, défaut False). False = arrosage
#       AU PIED (comportement STRICTEMENT inchangé, écrit `eco.humidite` seul — le bon
#       geste permacole) ; True = ASPERSION du feuillage (écrit `humidite` COMME au pied
#       **et** pose la carte transiente `eco.aspersion_last`, lue au tick suivant par
#       l'humectation foliaire → mildiou ↑ / oïdium ↓). Coût IDENTIQUE dans les deux modes
#       (§2.5 : le choix est écologique, pas économique — le mauvais geste produit sa
#       CONSÉQUENCE, pas un surcoût). La carte `aspersion_last` est remise à plat CHAQUE
#       tick (`tick_semaine`, APRÈS `_update_physiology`). PURE extension (champ optionnel,
#       geste event-driven hors tick ; carte nulle au repos) → golden INTACT (le smoke ne
#       joue aucun `arroser`). Un binaire pré-0.5.42 ignore `params.feuillage` → arrose
#       toujours au pied (tolérance côté vue, comme tous les bumps précédents).
# 0.5.43 (effondrement météo ④, encart « état du ciel » + couvertures posées au
#       pont) : TROIS blocs lecture-seule neufs au snapshot, tous PURS.
#       (1) `ciel` = agrégat du « ciel de la semaine » (sim/ciel.py, tronçon ②) :
#       {evenement_courant, nebulosite, convergence, signes ([{kind, in_weeks,
#       signs, signed}]), signe_compose ([libellés] perceptifs si un composé
#       catastrophe approche, () sinon), nom_compose (nom du composé « l'hiver de
#       tous les dangers », joint UNIQUEMENT si le palier maîtrise météo ≥ seuil —
#       masque de nommage §4.2 appliqué CÔTÉ MOTEUR)}. L'encart Godot en tire une
#       fenêtre DIÉGÉTIQUE sur le ciel (couleur/nuages/halo/brume qui s'assombrit
#       ∝ convergence, philo #5 : pas de chiffre ni d'icône calendrier). Évalué au
#       front courant (dernière semaine simulée) → les signes portent sur les
#       semaines À VENIR (préavis). (2)+(3) `couvert_pose` et `ombre_pose` = deux
#       listes CREUSES par tuile `[[r, c, dose], …]` des plots abrités par une
#       couverture POSÉE (voile/cloche → couvert_pose ; ombrière → ombre_pose,
#       tronçon ③). La vue en tire les placeholders procéduraux (voile translucide
#       / filet d'ombre, CoverLayer). PURE lecture d'états déjà portés/tickés
#       (fonctions météo pures + champs de milieu alloués paresseusement) → golden
#       NEUTRE : le smoke ne pose rien et le golden tourne hors serveur. Un binaire
#       pré-0.5.43 n'émet pas ces blocs → l'encart s'affiche neutre et aucun
#       placeholder n'est dessiné (tolérance côté vue, comme tous les bumps).
# 0.5.44 (jardin vivant T3, vent en onde) : DEUX ajouts lecture-seule. (1) Sous-bloc
#       `weather.wind = {force, direction, gusts}` — masse d'air de la dernière semaine
#       simulée (`sim.wind.wind_at` + `gust_profile`, PURES) ; `direction` (rad) = D'OÙ
#       vient le vent ; à l'init = calme (force 0). (2) Clé OPTIONNELLE par plante
#       vivante `abri` = facteur d'abri local au plot-foyer (1 = exposé, < 1 abrité,
#       > 1 venturi), lu dans le cache géométrique de `fields/abri.py` ; OMISE tant que
#       le champ d'abri n'a jamais été calculé (jamais forcé, D99). La vue en tire
#       l'onde de flexion des plantes + l'inclinaison de la pluie. PURE lecture →
#       golden NEUTRE. Un binaire pré-0.5.44 n'émet ni l'un ni l'autre → la vue reste
#       immobile (vent nul) et prend abri = 1.0 (tolérance comme tous les bumps).
# 0.5.45 (PERF VUE ②, vie macro) : le bloc `sprites` garde sa FORME
#       (`{tuile: {espèce: [[r, c, x_frac, y_frac, activite], …]}}`, toutes les
#       espèces en clé) mais change de PEINTRE : `peindre_presence` remplace
#       `sample_sprites` + `cap_sprites_global` — 1 individu par espèce présente et
#       par tuile, jusqu'à 3 points chauds de plus, grappes (≤ 6) pour puceron /
#       moustique / cloporte ; lombric et pollinisateurs : listes VIDES. Plus de cap
#       « 4 par plot » (une grappe en compte jusqu'à 6). PURE lecture → golden NEUTRE.
# 0.5.46 (PLANTE ASSEMBLÉE ⑥, légende des signes) : DEUX ajouts rétro-compatibles.
#       (1) `observer` accepte un champ OPTIONNEL `signe` (+ `tile`, `x_cm`/`y_cm`) :
#       la plante survolée porte ce signe visible → note au ledger `kind="signe"`
#       (dédup par espèce, signe, saison), hors tick ; réponse + `signe_note`.
#       (2) `player.appris = {signes: [...], faune: [...]}` au snapshot — signes dont
#       le palier du concept atteint le seuil du carnet interprétatif, bêtes dont le
#       palier atteint ce même seuil (`sim/signes.appris`, LECTURE PURE → golden
#       NEUTRE). Encyclopédie : 8ᵉ type `signe` (fiche ouverte quand appris). Debug
#       `palier3` crédite aussi les concepts des signes et la faune nommée. Un
#       binaire pré-0.5.46 n'émet pas `appris` → la vue reste descriptive. (3) Commande
#       `legende` (lecture seule, statique) : `vu` de chaque signe et de chaque bête.
# 0.5.47 (INFO-BULLE DU VIVANT ①, D110 a·b·g) : ajouts rétro-compatibles.
#       (1) `carpophores` : 6ᵉ champ = rôle local `b`/`r`/`h` (bois frais / racines
#       vivantes / humus, `sim/champignon_role`). (2) `foragers` : 8ᵉ champ =
#       nourriture (`activite` du champ pollinisateur au plot, 2 déc.). (3)
#       `observer` d'une bête ou de `champignon` crédite +1 palier par SAISON neuve
#       d'observation (plafond 3, `sim/signes.crediter_saison`, mémoire
#       `maitrise[joueur]["_saisons_vues"]`) ; jamais une plante. (4)
#       `player.appris.faune` inclut `champignon`. (5) `legende` + `faune_role`,
#       `champignon`, `voix_saine`, `abondance`, `nourriture` (bornes mesurées),
#       `reseau`. Tout hors tick → golden NEUTRE. Un client pré-0.5.47 ignore les
#       champs en plus (tableaux lus par index).
# 0.5.48 (INFO-BULLE DU VIVANT ③) : ajout rétro-compatible. `observer` d'une bête
#       ou de `champignon` renvoie aussi `appris` (forme de `player.appris`, lecture
#       pure) → la vue nomme la bête dès le survol qui franchit le palier. Hors
#       tick → golden NEUTRE.
# 0.5.49 (réglage de test « Vigueur infinie », demande Nico 2026-10-22) : `cmd_init`
#       accepte le champ OPTIONNEL `vigueur_infinie: bool` → pose
#       `game_state["options"][player]["vigueur_infinie"]`, lu par `sim/vigueur.spend`
#       (aucun débit, ratio 1.0). Défaut ON côté panneau Paramètres tant que dure la
#       phase de test. Absent → aucun effet → golden INTACT. Un binaire pré-0.5.49
#       ignore le champ (les gestes coûtent leur prix normal).
# 0.5.50 (LE SOL QUI RESPIRE ①, D111 bilan hydrique) : schéma du snapshot INCHANGÉ,
#       mais le CLIMAT du moteur change (épisodes de pluie toutes saisons → le bloc
#       `weather` porte bien plus souvent « Pluie prolongée »/« Orage » ; rosée sur
#       l'humidité de l'air ; transpiration foliaire saisonnière). Ajout : banc de
#       TEST `pluie_continue` (`init config="pluie_continue"`, pluie forcée chaque
#       semaine via `game_state["pluie_forcee"]`, lue aussi par le bloc `weather`).
#       Golden RE-FIGÉ (annoncé par le kickoff).
ENGINE_VERSION = "0.5.50"

# Repli pour une espèce absente de REPRO_BY_SEASON (kickoff t6 : « fleur au
# printemps, fruit mûr en été/automne, rien l'hiver ») — raisonnable pour les
# herbacées du catalogue en attendant le VRAI état reproducteur (D19/D33).
DEFAULT_REPRO = {"printemps": "flower", "ete": "fruit_ripe",
                 "automne": "fruit_ripe", "hiver": None}

# Tolérance du match plante-par-position (kickoff t4 §8) : les positions du
# snapshot reviennent telles quelles dans la cible → l'epsilon n'absorbe que le
# bruit de sérialisation JSON (float64 round-trip, en pratique exact).
PLANT_EPSILON_CM = 0.1
