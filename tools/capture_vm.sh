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

DEPOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="${GODOT:-$HOME/opt/godot/Godot_v4.6-stable_mono_linux_x86_64/Godot_v4.6-stable_mono_linux.x86_64}"
XROOT="${XROOT:-$HOME/opt/xvfb/root}"
SORTIE=/tmp/capture_symbiose BANC=smoke ZOOM="" CENTRE="" SOURIS="" GESTE="" VENT="" METEO="" SEMAINES="" DEFILE="" GRAINE="" FRAMES=3 FPS=10 BUILD=1

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
    -n) FRAMES="$2"; shift 2 ;;
    -f) FPS="$2"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    -h|--help) sed -n '2,44p' "$0"; exit 0 ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done

[ -x "$GODOT" ] || { echo "Godot absent : $GODOT" >&2; exit 1; }
[ -x "$XROOT/usr/bin/Xvfb-patched" ] || { echo "Xvfb absent : $XROOT" >&2; exit 1; }

# 1. Build C# (filet de compilation) — le Movie Maker lance les DLL compilées.
if [ "$BUILD" = 1 ]; then
  PATH="$HOME/.dotnet:$PATH" dotnet build "$DEPOT/Symbiose.csproj" -nologo -v q >/dev/null
fi

# 2. Xvfb sur un écran virtuel libre (démarré ici, tué en sortie).
export LD_LIBRARY_PATH="$XROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p /tmp/xk && ln -sf "$XROOT/usr/bin/xkbcomp" /tmp/xk/xkbcomp
ECRAN=:${CAPTURE_DISPLAY:-97}
"$XROOT/usr/bin/Xvfb-patched" "$ECRAN" -screen 0 1920x1080x24 -nolisten tcp >/tmp/xk/xvfb$ECRAN.log 2>&1 &
XPID=$!
trap 'kill $XPID 2>/dev/null || true' EXIT
for _ in $(seq 50); do [ -e "/tmp/.X11-unix/X${ECRAN#:}" ] && break; read -rt 0.1 <> <(:) || true; done

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
DISPLAY="$ECRAN" LIBGL_ALWAYS_SOFTWARE=1 "$GODOT" --path "$DEPOT" \
  --rendering-driver opengl3 --resolution 1920x1080 \
  --write-movie "$SORTIE/frame.png" --fixed-fps "$FPS" --quit-after "$FRAMES" \
  -- "${ARGS[@]}" >"$SORTIE/godot.log" 2>&1 || true
rm -f "$SORTIE/frame.wav"

N=$(ls "$SORTIE"/frame*.png 2>/dev/null | wc -l)
echo "$N image(s) dans $SORTIE (journal : $SORTIE/godot.log)"
[ "$N" -gt 0 ]
