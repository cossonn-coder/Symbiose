#!/usr/bin/env bash
# SYMBIOSE — captures de l'info-bulle d'une BÊTE / d'un CARPOPHORE (INFO-BULLE DU VIVANT ③).
# Lance le banc world/WorldView.BancVivant.cs sous Xvfb : pose ×4 sur l'entrée la plus
# proche du point visé, souris dessus, recadrage PNG 640×400, texte de l'info-bulle au log.
#
# USAGE : capture_vivant.sh CIBLE FICHIER.png [-b BANC] [-c X,Y] [-w SEMAINES] [-a] [-t] [-V 1|2] [--no-build]
#   CIBLE = bete | carpophore[,b|r|h] · -a palier3 (bête nommée) · -t technique (Maj+F3)
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../../../../../tools/lib_vm_godot.sh"
CIBLE="$1" PNG="$(realpath -m "$2")"; shift 2
BANC=full CENTRE="" SEM="" BUILD=1 ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    -b) BANC="$2"; shift 2 ;;  -c) CENTRE="$2"; shift 2 ;;
    -w) SEM="$2"; shift 2 ;;   -a) ARGS+=(--capture-palier3=1); shift ;;
    -t) ARGS+=(--capture-technique=1); shift ;;
    -V) ARGS+=(--capture-vision="$2"); shift 2 ;;   # sol qui respire ⑧ : 1 vision, 2 overdose
    --no-build) BUILD=0; shift ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done
SORTIE="${SORTIE:-/tmp/capture_vivant}"
vm_verifier
if [ "$BUILD" = 1 ]; then vm_build; fi
vm_xvfb ":${CAPTURE_DISPLAY:-95}"
mkdir -p "$SORTIE"
ARGS+=(--capture-banc="$BANC" --capture-vent=0 --capture-vivant="$CIBLE" --capture-vivant-png="$PNG")
[ -n "$CENTRE" ] && ARGS+=(--capture-centre="$CENTRE")
[ -n "$SEM" ] && ARGS+=(--capture-semaines="$SEM")
DISPLAY="$ECRAN" LIBGL_ALWAYS_SOFTWARE=1 "$GODOT" --path "$DEPOT" \
  --rendering-driver opengl3 --resolution 1920x1080 --fixed-fps 10 \
  -- "${ARGS[@]}" >"$SORTIE/godot.log" 2>&1 || true
grep '^\[Vivant\]' "$SORTIE/godot.log" || { echo "pas de ligne [Vivant] — voir $SORTIE/godot.log" >&2; exit 1; }
