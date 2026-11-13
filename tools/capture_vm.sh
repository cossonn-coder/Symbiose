#!/usr/bin/env bash
# SYMBIOSE — tools/capture_vm.sh (sprint JARDIN VIVANT, T0 — banc de capture VM)
#
# Lance le jeu Godot SUR LA VM SANS ÉCRAN (Xvfb + rendu logiciel llvmpipe) et
# écrit N images PNG via le Movie Maker de Godot. Ce sont les « yeux » de
# l'agent : il ouvre les PNG avec l'outil Read AVANT le F5 de Nico.
# Pas un livrable joueur ; le F5 de Nico n'est pas touché (mode capture inactif
# sans argument, cf. world/WorldView.Capture.cs).
#
# USAGE (depuis n'importe où) :
#   tools/capture_vm.sh [-o DOSSIER] [-b BANC] [-z ZOOM] [-c X,Y] [-n FRAMES] [-f FPS] [--no-build]
#     -o  dossier de sortie            (défaut /tmp/capture_symbiose, VIDÉ avant)
#     -b  monde/banc à monter          (défaut smoke ; full, propre, ou un banc
#                                       du registre Python BANCS)
#     -z  palier de zoom               (0.5 1 2 4 8 16 32 ; défaut = cadrage)
#     -c  point visé en cm monde X,Y   (défaut = centre du monde 1000,1000)
#     -s  souris en px écran X,Y       (survol : losange de plot, étiquette)
#     -g  slot de geste armé 0..9      (losange qui « respire »)
#     -v  vent imposé FORCE[,DIR_RAD]  (0 = calme ; DIR = d'où il vient) — T3
#     -m  météo imposée KIND[,INT[,DUREE_S]] (Canicule, « Pluie prolongée », Orage… ;
#                                       après DUREE_S s de jeu → météo du snapshot) — T4
#     -w  semaines de warmup           (défaut 12) — T4
#     -d  défilé « jardin vivant » (F12) : 7 situations × 10 s de jeu — T5
#     -S  seed du monde                (défaut 42 ; 12345 = collapse d'effondrement) — T5
#     -r  orientation D35 0..3         (quarts de tour de vue) — D106 T2
#     -x  couches masquées N1,N2       (noms de nœuds, cf. perf_vm.sh) — D106 T2
#     -T  n semaines en TURBO après le montage (semaine paresseuse) — D106 T4
#     -p  saut caméra X,Y (cm monde) à la fin des semaines turbo — D106 T4
#     -l  planche des paliers ×0,5→×32 (touche L), SEC s de jeu par palier, sur la
#         plante la plus proche de -c ; copie la dernière image de chaque palier en
#         DOSSIER/planche_xN.png (prévoir -n ≥ 7×SEC×FPS + amorçage) — D106 T7
#     -a  aide clavier F1 affichée (mode Aide) — PLANTE ASSEMBLÉE ③
#     -P  debug palier3 au montage (info-bulle apprise) — PLANTE ASSEMBLÉE ⑦
#     -t  info-bulle en affichage technique (Maj+F3) — PLANTE ASSEMBLÉE ⑦
#     -D  F10 ×2 (reconstruction forcée du décor) après SEC s de jeu — FLUIDITÉ PC ②
#     -B  banc décor F10 ON dès le montage (4 motifs côte à côte) — FLUIDITÉ PC ③
#     -k  planche du kit d'éléments (touffes, fleurons) — PLANTE ASSEMBLÉE ④
#     -J  écran de chargement au montage (premières images) — HOUPPIER ④
#     -G  planche de l'atlas de gerbes (bois + feuilles, 4 paliers) — HOUPPIER ④
#     -Y  ESPECE : banc de la clé stable, coupe une branche d'un pied de cette espèce, verdict
#         `[CleStable]` dans godot.log — HOUPPIER ④ (prévoir -n ≥ 120)
#     -F  palette SNES (F11) allumée au montage — CASSÉ À L'ÉCRAN ① (banc mesure_da)
#     -O  ombres portées coupées (touche O) — CASSÉ À L'ÉCRAN ① (masque des sprites)
#     -H  maison + lisière transparentes (touche H) au montage — CASSÉ À L'ÉCRAN ②
#     -6  heatmap F6 ouverte au montage (1er champ du cycle) — CASSÉ À L'ÉCRAN ②
#     -j  angle horaire du soleil imposé en degrés (−90 matin, 0 midi, 90 soir) ;
#         le journal donne l'angle ÉCRAN pour mesure_da.py --soleil — CASSÉ À L'ÉCRAN ③
#     -L  palette indexée coupée (F11) : la capture « avant » de ③
#     -K  planche de la faune (icônes ×2→×16, fond uni ; mesure_da --pas 1) — ⑤
#     -C  cueillette : clic « manger » sur chaque fruit du port le plus proche de -c,
#         verdict `[Cueillette]` dans godot.log — FORMES DES PLANTES ④
#     -A  OUTIL[,OUTIL] : achète ces outils à l'Atelier ; palette relevée avant et après au journal
#         `[AccesGestes]`, menu du clic droit ouvert à l'image — ACCÈS AUX GESTES ④ (-n ≥ 240)
#     -Q  1|VERBE : tiroir des gestes ouvert au montage ; avec un VERBE, ce geste est choisi dans le
#         tiroir après 4 s (journal `[Tiroir]`) — PALETTE & TIROIR ① (-n ≥ 60 avec un verbe)
#     -M  D118 (c) : compte le bois dessiné DEVANT la maison que le clic voit comme plante
#         (journal `[ClicMur]`, lecture seule) — PALETTE & TIROIR ③ (-n ≥ 60)
#     -n  nombre d'images              (défaut 3)
#     -f  images/s simulées            (défaut 10 → 3 images = 0,3 s de jeu)
#   Sortie : DOSSIER/frame00000000.png, frame00000001.png, … (1920×1080).
#   Exemple : tools/capture_vm.sh -b smoke -z 8 -c 600,600 -n 3
#
# MESURES (2026-10-15, VM, llvmpipe) : ~10-20 s pour 3 images du smoke
#   (amorçage Godot + pont Python + warmup inclus) ; rendu ~12 % du temps réel
#   → animation lente à capturer, préférer peu d'images. Les FPS sont FIXES
#   (Movie Maker) : le temps de jeu avance de 1/FPS par image, quel que soit
#   le temps de calcul réel → capture déterministe à seed égale.
#
# DÉPENDANCES HORS DÉPÔT (jamais committées) :
#   ~/opt/godot/Godot_v4.6-stable_mono_linux_x86_64/  Godot 4.6 stable .NET
#   ~/opt/xvfb/root/   Xvfb + deps extraits des .deb Debian (dpkg-deb -x, sans
#     sudo). Xvfb cherche `xkbcomp` dans un chemin COMPILÉ (/usr/bin) : la copie
#     `Xvfb-patched` a ce chemin remplacé par /tmp/xk (même longueur d'octets),
#     et ce script y relie xkbcomp à chaque lancement (/tmp vidé au reboot).
#   Réinstallation : cf. sprints/rendu/pixelart/sprint_jardin_vivant/00_etat.md.
set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib_vm_godot.sh"   # DEPOT GODOT XROOT + vm_* (D106 T1)
SORTIE=/tmp/capture_symbiose BANC=smoke ZOOM="" CENTRE="" SOURIS="" GESTE="" VENT="" METEO="" SEMAINES="" DEFILE="" GRAINE="" ORIENT="" CACHER="" TURBO="" PAN="" PLANCHE="" AIDE="" KIT="" PAL3="" TECH="" DECORF10="" DECORBANC="" FAUNE="" PALETTE="" CUEILLETTE="" ACCES="" TIROIR="" CLICMUR="" OMBRES="" MAISON="" F6="" HEURE="" SANSLUT="" FRAMES=3 FPS=10 BUILD=1

while [ $# -gt 0 ]; do
  case "$1" in
    -o) SORTIE="$2"; shift 2 ;;
    -b) BANC="$2"; shift 2 ;;
    -z) ZOOM="$2"; shift 2 ;;
    -c) CENTRE="$2"; shift 2 ;;
    -s) SOURIS="$2"; shift 2 ;;
    -g) GESTE="$2"; shift 2 ;;
    -v) VENT="$2"; shift 2 ;;
    -m) METEO="$2"; shift 2 ;;
    -w) SEMAINES="$2"; shift 2 ;;
    -d) DEFILE=1; shift ;;
    -S) GRAINE="$2"; shift 2 ;;
    -r) ORIENT="$2"; shift 2 ;;
    -x) CACHER="$2"; shift 2 ;;
    -n) FRAMES="$2"; shift 2 ;;
    -f) FPS="$2"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    -T) TURBO="$2"; shift 2 ;;
    -p) PAN="$2"; shift 2 ;;
    -l) PLANCHE="$2"; shift 2 ;;
    -a) AIDE=1; shift ;;
    -k) KIT=1; shift ;;
    -G) GERBES=1; shift ;;
    -J) CHARGEMENT=1; shift ;;
    -Y) CLESTABLE="$2"; shift 2 ;;
    -F) PALETTE=1; shift ;;
    -O) OMBRES=1; shift ;;
    -H) MAISON=1; shift ;;
    -6) F6=1; shift ;;
    -j) HEURE="$2"; shift 2 ;;
    -L) SANSLUT=1; shift ;;
    -K) FAUNE=1; shift ;;
    -C) CUEILLETTE=1; shift ;;
    -A) ACCES="$2"; shift 2 ;;
    -Q) TIROIR="$2"; shift 2 ;;
    -M) CLICMUR=1; shift ;;
    -D) DECORF10="$2"; shift 2 ;;
    -B) DECORBANC=1; shift ;;
    -P) PAL3=1; shift ;;
    -t) TECH=1; shift ;;
    -h|--help) sed -n '2,63p' "$0"; exit 0 ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done

vm_verifier

# 1. Build C# (filet de compilation) — le Movie Maker lance les DLL compilées.
if [ "$BUILD" = 1 ]; then vm_build; fi

# 2. Xvfb sur un écran virtuel libre (démarré ici, tué en sortie).
vm_xvfb ":${CAPTURE_DISPLAY:-97}"

# 3. Godot en rendu logiciel + Movie Maker → PNG.
rm -rf "$SORTIE"; mkdir -p "$SORTIE"
ARGS=(--capture-banc="$BANC")
[ -n "$ZOOM" ] && ARGS+=(--capture-zoom="$ZOOM")
[ -n "$CENTRE" ] && ARGS+=(--capture-centre="$CENTRE")
[ -n "$SOURIS" ] && ARGS+=(--capture-souris="$SOURIS")
[ -n "$GESTE" ] && ARGS+=(--capture-geste="$GESTE")
[ -n "$VENT" ] && ARGS+=(--capture-vent="$VENT")
[ -n "$METEO" ] && ARGS+=(--capture-meteo="$METEO")
[ -n "$SEMAINES" ] && ARGS+=(--capture-semaines="$SEMAINES")
[ -n "$DEFILE" ] && ARGS+=(--capture-defile=1)
[ -n "$GRAINE" ] && ARGS+=(--capture-seed="$GRAINE")
[ -n "$ORIENT" ] && ARGS+=(--capture-orient="$ORIENT")
[ -n "$CACHER" ] && ARGS+=(--capture-cacher="$CACHER")
[ -n "$TURBO" ] && ARGS+=(--capture-turbo="$TURBO")
[ -n "$PAN" ] && ARGS+=(--capture-pan="$PAN")
[ -n "$PLANCHE" ] && ARGS+=(--capture-planche="$PLANCHE")
[ -n "$AIDE" ] && ARGS+=(--capture-aide=1)
[ -n "$KIT" ] && ARGS+=(--capture-kit=1)
[ -n "${GERBES:-}" ] && ARGS+=(--capture-gerbes=1)
[ -n "${CHARGEMENT:-}" ] && ARGS+=(--capture-chargement=1)
[ -n "${CLESTABLE:-}" ] && ARGS+=(--capture-cle-stable="$CLESTABLE")
[ -n "$PAL3" ] && ARGS+=(--capture-palier3=1)
[ -n "$TECH" ] && ARGS+=(--capture-technique=1)
[ -n "$DECORF10" ] && ARGS+=(--capture-decor-f10="$DECORF10")
[ -n "$DECORBANC" ] && ARGS+=(--capture-decor-banc=1)
[ -n "$PALETTE" ] && ARGS+=(--capture-palette=1)
[ -n "$OMBRES" ] && ARGS+=(--capture-ombres=0)
[ -n "$MAISON" ] && ARGS+=(--capture-maison=1)
[ -n "$F6" ] && ARGS+=(--capture-f6=1)
[ -n "$HEURE" ] && ARGS+=(--capture-heure="$HEURE")
[ -n "$SANSLUT" ] && ARGS+=(--capture-lut=0)
[ -n "$FAUNE" ] && ARGS+=(--capture-faune=1)
[ -n "$CUEILLETTE" ] && ARGS+=(--capture-cueillette=1)
[ -n "$ACCES" ] && ARGS+=(--capture-acces="$ACCES")
[ -n "$TIROIR" ] && ARGS+=(--capture-tiroir="$TIROIR")
[ -n "$CLICMUR" ] && ARGS+=(--capture-clicmur=1)
DISPLAY="$ECRAN" LIBGL_ALWAYS_SOFTWARE=1 "$GODOT" --path "$DEPOT" \
  --rendering-driver opengl3 --resolution 1920x1080 \
  --write-movie "$SORTIE/frame.png" --fixed-fps "$FPS" --quit-after "$FRAMES" \
  -- "${ARGS[@]}" >"$SORTIE/godot.log" 2>&1 || true
rm -f "$SORTIE/frame.wav"

# Planche (D106 T7) : le jeu journalise « [Planche] fin ×N — frame F » ; F compte
# les images dessinées, l'image Movie Maker n° F−1 est la dernière du palier.
if [ -n "$PLANCHE" ]; then
  grep -o '\[Planche\] fin ×[0-9.,]* — frame [0-9]*' "$SORTIE/godot.log" | while read -r _ _ Z _ _ F; do
    SRC=$(printf '%s/frame%08d.png' "$SORTIE" $((F - 1)))
    [ -f "$SRC" ] && cp "$SRC" "$SORTIE/planche_x${Z#×}.png"
  done
  ls "$SORTIE"/planche_x*.png 2>/dev/null || echo "planche : aucun palier complet (augmenter -n)" >&2
fi

N=$(ls "$SORTIE"/frame*.png 2>/dev/null | wc -l)
echo "$N image(s) dans $SORTIE (journal : $SORTIE/godot.log)"
[ "$N" -gt 0 ]
