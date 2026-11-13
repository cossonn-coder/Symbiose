"""
SYMBIOSE — bancs/ (paquet)
Registre des BANCS D'ESSAI : `BANCS[nom]` → fabrique `() -> (tiles, ecos, house,
banque)`. Une fabrique compose un monde paramétré qui force UNE condition
observable (cf. base.py). Le serveur (`cmd_init`) branche `config in BANCS` après
les cas `smoke`/`full` : `init config="<nom>"` monte le banc, sans toucher le
golden (les bancs ne sont jamais montés pour smoke/full).

Les tronçons ②③④ ajoutent leurs entrées ici (édaphique, climatique, biotique).
"""
from .climatique import (secheresse_sable, acclimatation, ombre_dense,
                         pluie_thermique, germination_multifacteur,
                         effondrement, pluie_continue, pluie_continue_post_init)
from .edaphique import (chlorose_acidophile, asphyxie_argile, carence_npk,
                       rotation_inoculum)
from .hydrologie import tourbiere
from .biotique import (infestation_ravageur, verger_floraison, semis_tempere,
                       etalement_floraison, grimpantes, floraison_saisons)
from .succession import succession_bascule
from .croissance import vieux_pommier, foret_ports
from .luxuriance import luxuriance
from .diversite import diversite_fondatrice
from .modele_spatial import modele_spatial
from .planche_especes import planche_especes, accroches_adultes
from .lianes import liane_relais
from .verger_mur import verger_mur
from .houppiers import houppiers, houppiers_25
from . import palette_gestes as _palette_gestes
from . import courrier as _courrier
from . import peripherie as _peripherie
from . import nucleation as _nucleation
from . import acces_gestes as _acces_gestes
from . import sol_canvas as _sol_canvas

BANCS = {
    "secheresse_sable": secheresse_sable,
    "acclimatation": acclimatation,
    "ombre_dense": ombre_dense,
    "pluie_thermique": pluie_thermique,
    "germination_multifacteur": germination_multifacteur,
    "effondrement": effondrement,
    "pluie_continue": pluie_continue,      # TEST seulement (D111 ①e, D-pluie)
    "chlorose_acidophile": chlorose_acidophile,
    "asphyxie_argile": asphyxie_argile,
    "carence_npk": carence_npk,
    "rotation_inoculum": rotation_inoculum,
    "tourbiere": tourbiere,
    "infestation_ravageur": infestation_ravageur,
    "verger_floraison": verger_floraison,
    "semis_tempere": semis_tempere,
    "etalement_floraison": etalement_floraison,
    "floraison_saisons": floraison_saisons,
    "grimpantes": grimpantes,
    "succession_bascule": succession_bascule,
    "vieux_pommier": vieux_pommier,
    "foret_ports": foret_ports,
    "luxuriance": luxuriance,
    "diversite_fondatrice": diversite_fondatrice,
    "modele_spatial": modele_spatial,
    "planche_especes": planche_especes,
    "accroches_adultes": accroches_adultes,
    "liane_relais": liane_relais,
    "verger_mur": verger_mur,
    "houppiers": houppiers,
    "houppiers_25": houppiers_25,
    "palette_gestes": _palette_gestes.palette_gestes,
    "courrier": _courrier.courrier,
    "peripherie": _peripherie.peripherie,
    "nucleation": _nucleation.nucleation,  # zoochorie ⑦ : perchoir, mort debout, hêtraie
    # accès aux gestes ④ : toutes les portes à portée, RIEN d'ouvert d'avance.
    "acces_gestes": _acces_gestes.acces_gestes,
    # gestes lisibles ③ : chaque trace au sol, paillis, cuvette, couché, sec, tas.
    "sol_canvas": _sol_canvas.sol_canvas,
}

# Hook POST-INIT par banc (palette de gestes ⑤) : callback OPTIONNEL `(game_state,
# player) -> None` appelé par `cmd_init` APRÈS la construction du moteur ET l'opt-in
# Vigueur — le SEUL point où l'état JOUEUR (maîtrise, gestes débloqués) existe (la
# fabrique de banc ne renvoie que le monde, pas le game_state). Le banc « palette »
# s'en sert pour OUVRIR d'emblée les gestes savants (bouturer/greffer) sans jouer
# jusqu'à la maîtrise réelle. Banc sans hook → absent → cmd_init ne fait rien de plus
# (comportement inchangé, golden NEUTRE : smoke/full ne sont pas des bancs).
BANC_POST_INIT = {"palette_gestes": _palette_gestes.post_init,
                  "courrier": _courrier.post_init,
                  # `peripherie` (D73 ⑦) : POSE la ceinture contrastée dans
                  # `game_state["ceinture"]` (la fabrique ne rend que le monde) et
                  # met les outils de paysage en poche → les 7 gestes sont
                  # cliquables dès l'ouverture.
                  "peripherie": _peripherie.post_init,
                  # `pluie_continue` (D111 ①e) : pose `pluie_forcee` → pluie chaque
                  # semaine (banc de TEST ; jamais en jeu, D-pluie).
                  "pluie_continue": pluie_continue_post_init,
                  # `nucleation` (zoochorie ⑦) : pose une hêtraie au nord (apport geai).
                  "nucleation": _nucleation.post_init,
                  # `acces_gestes` (④) : ceinture + Vigueur large, AUCUN déblocage.
                  "acces_gestes": _acces_gestes.post_init,
                  # `sol_canvas` (gestes lisibles ③) : gestes joués par leur façade,
                  # traces écrites puis antidatées.
                  "sol_canvas": _sol_canvas.post_init}

# Seed IMPOSÉ par banc (effondrement météo ④). La plupart des bancs sont neutres au
# seed (ils forcent leur condition par composition) → repli sur le défaut du serveur.
# `effondrement` fait EXCEPTION : il met en scène le collapse DÉTERMINISTE du seed
# 12345 (Grêle locale sévère semaine 218) — sans ce seed, la météo seedée ne pose
# aucune catastrophe à la fenêtre observée. Lu par `cmd_init` (banc absent → défaut
# serveur → comportement inchangé ; un `msg["seed"]` explicite reste prioritaire pour
# l'oracle/tests). golden NEUTRE : smoke/full ne sont pas des bancs.
BANC_SEED = {"effondrement": 12345}

# Semaine de départ par banc (retour F5 Nico 2026-07-04). La plupart démarrent à
# `week=1` (début printemps) — repli par défaut. `grimpantes` observe des FRILEUSES
# (haricot/jasmin) qu'un départ début printemps fige sous le seuil de croissance
# (~5 °C) pendant des semaines : on le décale à MI-PRINTEMPS pour voir la grimpe
# tout de suite. D122 ③ (année depuis l'équinoxe) : s9 ≈ mi-mai, T ≈ 13 °C — encore
# le printemps, au-dessus de tous les seuils de croissance → départs 9 / 12 / 20
# conservés (intentions écrites toujours remplies). Lu par `cmd_init` (banc absent → 1 → comportement inchangé,
# golden NEUTRE : smoke/full ne sont pas des bancs).
# `diversite_fondatrice` sème du TOURNESOL (t_germ_opt=20, sol chaud requis) : un
# départ début printemps fige la levée sous le seuil thermique pendant des semaines.
# Décalé MI-PRINTEMPS pour voir la désynchronisation des rythmes tout de suite.
# `foret_ports` (D91 ④) démarre en PLEIN ÉTÉ (semaine 20) : la densité foliaire
# du snapshot dérive de la saison (`foliage_density_at`) — un départ hiver
# montrerait les 8 CADUCS nus (seuls sapin/pommier persistants garderaient un
# feuillage). L'été donne les 10 couronnes pleines et sans coloration automnale,
# pour lire chaque PORT habillé (le banc n'observe PAS le rythme phénologique).
BANC_WEEK_DEPART = {"grimpantes": 9, "luxuriance": 9, "diversite_fondatrice": 9,
                    "foret_ports": 20,
                    # `planche_especes` (FORMES DES PLANTES ①) : plein été, même raison.
                    "planche_especes": 20,
                    "accroches_adultes": 20,
                    # `liane_relais` (HOUPPIER ②) : même raison, feuillage et lianes en pleine pousse.
                    "liane_relais": 20,
                    # `houppiers` (HOUPPIER ④) : même raison, couronnes pleines.
                    "houppiers": 20, "houppiers_25": 20,
                    # `effondrement` (④) démarre SEMAINE 217 (an 5) : le ciel est
                    # déjà au plomb à l'arrivée (convergence 2.0) et le reste ; deux
                    # pas de simulation amènent la frappe de Grêle locale (semaine 218)
                    # → la moitié voilée garde un noyau vivant, la moitié nue est fauchée.
                    # Compromis contraste/anticipation (cf. climatique.effondrement) —
                    # calibrage F5.
                    # D122 ③ : ex-1309/1310 — les fenêtres d'aléas au mois réel ont fait
                    # de la frappe de 1310 un Orage ; 218 = Grêle i=2.0, ciel à 2.0 dès 215.
                    "effondrement": 217,
                    # `courrier` (D79 ⑤) démarre SEMAINE 12 (fin de printemps, sol
                    # réchauffé) : les lettres sont POSÉES au post_init (pas via les
                    # jalons de saison), mais un départ tardif évite de figer lavande /
                    # trèfle sous le seuil thermique — le panneau montre des avancements
                    # diégétiques qui bougent plutôt que « rien ne pousse ».
                    "courrier": 12,
                    # `acces_gestes` (④) démarre SEMAINE 24 (fin d'été) : tous les
                    # jalons de saison des lettres qui enseignent sont passés (le
                    # dernier, l'essaim, est à 24) → le courrier arrive tout de suite.
                    "acces_gestes": 24}


def banc_categorie(nom: str) -> str:
    """Catégorie d'un banc = le MODULE thématique d'où vient sa fabrique
    (`bancs.climatique` → "climatique"). DÉRIVÉE, pas maintenue à la main : un
    banc neuf hérite tout seul de la catégorie de son fichier, aucune table à
    resynchroniser (le piège des menus qui mentent, D47). Repli "divers" si le
    module n'est pas résolvable (fabrique anonyme, lambda…)."""
    fabrique = BANCS.get(nom)
    module = getattr(fabrique, "__module__", "") or ""
    cat = module.rsplit(".", 1)[-1]
    return cat if cat and cat != "__init__" else "divers"
