#!/usr/bin/env bash
# SYMBIOSE — tools/perf_vm.sh (sprint RENDU VISIBLE T1 — banc FPS temps réel)
#
# Lance le jeu SUR LA VM SANS ÉCRAN (Xvfb + llvmpipe) en TEMPS RÉEL — pas de
# Movie Maker, `--print-fps` — et mesure le coût de frame. Le jeu, en mode
# capture, imprime une ligne `[perf] fps=… ms=… draw=… obj=… prim=…` par
# seconde (world/WorldView.PerfMesure.cs) ; ce script ignore les premières
# (amorçage, cuisson) puis moyenne les N suivantes.
#
# ⚠️ Les FPS VM ne valent PAS ceux du PC de Nico (rendu logiciel). La métrique
#    portable est `draw` (envois GPU par frame). Charge VM (`uptime`) > ~4 →
#    runs aberrants : le script avertit.
#
# USAGE :
#   tools/perf_vm.sh [-b BANC] [-z ZOOM] [-c X,Y] [-x NOM1,NOM2] [-k SAUT] [-n N]
#                    [-t TIMEOUT_S] [-S SEED] [-w SEMAINES] [-T TURBO] [--no-build]
#     -b  monde/banc (défaut full)          -z  palier de zoom (défaut 0.5)
#     -c  point visé en cm monde X,Y        -x  couches masquées par nom de nœud
#         (Ground Decor Objects MacroLife ForagerLayer Carpophores Couverture
#          Allelopathie Mulch Puddle Litter LeafLitter Snow Covers Weather Sky
#          Vignette — cf. world/WorldView.Couches.cs)
#     -k  relevés [perf] ignorés en tête (défaut 4)   -n  relevés moyennés (défaut 8)
#     -t  délai max total en s (défaut 300)  -S seed (défaut 42)  -w warmup semaines
#     -T  n semaines en TURBO pendant la mesure (gel hebdomadaire, D106 T4) : la
#         sortie ajoute la pire frame (max) et le total de frames > 250 ms (gels)
#   Exemple : tools/perf_vm.sh -z 0.5 -x Ground
#   Journal complet : /tmp/perf_symbiose/godot.log
set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib_vm_godot.sh"   # DEPOT GODOT XROOT + vm_*
BANC=full ZOOM=0.5 CENTRE="" CACHER="" SAUT=4 N=8 DELAI=300 GRAINE="" SEMAINES="" TURBO="" BUILD=1

while [ $# -gt 0 ]; do
  case "$1" in
    -b) BANC="$2"; shift 2 ;;
    -z) ZOOM="$2"; shift 2 ;;
    -c) CENTRE="$2"; shift 2 ;;
    -x) CACHER="$2"; shift 2 ;;
    -k) SAUT="$2"; shift 2 ;;
    -n) N="$2"; shift 2 ;;
    -t) DELAI="$2"; shift 2 ;;
    -S) GRAINE="$2"; shift 2 ;;
    -w) SEMAINES="$2"; shift 2 ;;
    -T) TURBO="$2"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    -h|--help) sed -n '2,29p' "$0"; exit 0 ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done

# 0. Charge de la VM d'abord : une mesure sous charge ne vaut rien. Un run
#    llvmpipe pousse lui-même la charge à ~10-15 (16 cœurs, rendu multi-fil) :
#    enchaînés, les runs se gêneraient → on attend la décroissance (≤ 120 s).
charge() { cut -d' ' -f1 /proc/loadavg; }
for _ in $(seq 24); do
  awk -v c="$(charge)" 'BEGIN { exit !(c > 4) }' || break
  read -rt 5 <> <(:) || true
done
uptime
awk -v c="$(charge)" 'BEGIN { exit !(c > 4) }' && echo "⚠️  charge VM $(charge) > 4 : mesure peu fiable." >&2

vm_verifier
if [ "$BUILD" = 1 ]; then vm_build; fi
vm_xvfb ":${PERF_DISPLAY:-96}"

# 1. Godot temps réel en arrière-plan ; on lit son journal jusqu'à SAUT+N relevés.
SORTIE=/tmp/perf_symbiose; rm -rf "$SORTIE"; mkdir -p "$SORTIE"; LOG="$SORTIE/godot.log"
ARGS=(--capture-banc="$BANC" --capture-zoom="$ZOOM")
[ -n "$CENTRE" ] && ARGS+=(--capture-centre="$CENTRE")
[ -n "$CACHER" ] && ARGS+=(--capture-cacher="$CACHER")
[ -n "$GRAINE" ] && ARGS+=(--capture-seed="$GRAINE")
[ -n "$SEMAINES" ] && ARGS+=(--capture-semaines="$SEMAINES")
[ -n "$TURBO" ] && ARGS+=(--capture-turbo="$TURBO")
DISPLAY="$ECRAN" LIBGL_ALWAYS_SOFTWARE=1 "$GODOT" --path "$DEPOT" \
  --rendering-driver opengl3 --resolution 1920x1080 --print-fps \
  -- "${ARGS[@]}" >"$LOG" 2>&1 &
GPID=$!
trap 'kill $GPID 2>/dev/null || true; kill $XPID 2>/dev/null || true' EXIT

FIN=$((SECONDS + DELAI))
while [ "$(grep -c '^\[perf\]' "$LOG" || true)" -lt $((SAUT + N)) ]; do
  kill -0 $GPID 2>/dev/null || { echo "Godot s'est arrêté (cf. $LOG)" >&2; exit 1; }
  [ $SECONDS -lt $FIN ] || { echo "délai $DELAI s dépassé (cf. $LOG)" >&2; exit 1; }
  read -rt 1 <> <(:) || true
done
kill $GPID 2>/dev/null || true

# 2. Moyenne des N relevés après le saut (FPS = 1000 / ms moyen, pas moyenne des FPS).
grep '^\[perf\]' "$LOG" | sed -n "$((SAUT + 1)),$((SAUT + N))p" | awk -v banc="$BANC" \
  -v zoom="$ZOOM" -v cacher="${CACHER:-—}" '
  { for (i = 2; i <= NF; i++) { split($i, kv, "="); v[kv[1]] += kv[2]
      if (kv[1] == "max" && kv[2] + 0 > pire + 0) pire = kv[2] + 0 }
    n++ }
  END { ms = v["ms"] / n
        printf "banc %s ×%s masqué %s : FPS %.1f (frame %.1f ms) [n=%d relevés de 1 s] · draw calls %.0f · objets %.0f · primitives %.0f · pire frame %.0f ms · gels>250ms %d\n",
               banc, zoom, cacher, 1000 / ms, ms, n, v["draw"] / n, v["obj"] / n, v["prim"] / n, pire, v["gels"] }'
