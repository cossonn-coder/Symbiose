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
#     -b  monde/banc (défaut full)          -z  palier de zoom (défaut 0.5 ; ×4 avec -E)
#     -c  point visé en cm monde X,Y        -x  couches masquées par nom de nœud
#         (Ground Decor Objects MacroLife ForagerLayer Carpophores Couverture
#          Allelopathie Mulch Puddle Litter LeafLitter Snow Covers Weather Sky
#          Vignette — cf. world/WorldView.Couches.cs)
#     -k  relevés [perf] ignorés en tête (défaut 4)   -n  relevés moyennés (défaut 8)
#     -t  délai max total en s (défaut 300)  -S seed (défaut 42)  -w warmup semaines
#     -T  n semaines en TURBO pendant la mesure (gel hebdomadaire, D106 T4) : la
#         sortie ajoute la pire frame (max) et le total de frames > 250 ms (gels)
#     -E  BANC D'ÉTALONNAGE (PERF VUE ①, même scénario que la touche E du F5) :
#         mesure de E secondes au point de banc (semaine moteur fixe, ×4 au centre
#         du banc, 60 s/semaine) ; imprime le rapport complet (distribution des
#         images, postes CPU) au lieu de la moyenne [perf]. -z / -c remplacent zoom
#         et centre ; -x MacroLife masque la vie macro ; -O coupe les ombres.
#     -O  ombres coupées (comme la touche O)
#     -L  palette indexée coupée (F11) : mesure « avant » A/B — CASSÉ À L'ÉCRAN ③
#     -A  cadence PENDANT la mesure du banc E (PERF VUE ④) : 0 = turbo, s = s par
#         semaine (1 = défaut de test de Nico) ; absent = nominale 60 s/semaine
#     -V  vent imposé (force[,direction rad], 0 = calme) — comme --capture-vent
#     -W  semaine moteur du banc E (défaut 45 ; 67 = été an 2, cas de stress)
#     -R  monde rendu en PLEINE RÉSOLUTION 1920×1080 ×1 (mesure, PERF VUE ⑤)
#     -a  automate branché pendant tout le banc (FLUIDITÉ AN 2 ①) : ouvert = touche A
#         (onglet Automate affiché) ; ferme = branché puis panneau fermé
#     -3  BANC E EN 3 PHASES (FLUIDITÉ PC ①) : durées A,B,C en s (défaut 25,25,20) —
#         A normal / B rendu suspendu (steps seuls, ≥ 6) / C moteur en pause ; à
#         combiner avec -A (sinon aucun step en A/B). Implique -E (durée de A).
#     -P  BANC DE PARTAGE (FLUIDITÉ PC PARTAGE ②) : la phase A du banc 3 phases devient
#         4 sous-phases de P s (régulateur OFF/15 FPS × moteur BelowNormal/Normal) +
#         tableau côte à côte en fin de rapport. Implique -3 (défaut 25,25,20) ; sur la
#         VM le passage en Normal est refusé (nice) → rapporté « non applicable ».
#     -Z  BALAYAGE DE ZOOM (FLUIDITÉ PC LEVIERS ①) : ×0,5 → ×32 → ×0,5, Z s par palier
#         sur le point -c ; imprime le rapport des à-coups de zoom (même texte que la
#         touche Z du F5 : une ligne par changement + synthèse par paire de paliers).
#   Exemple : tools/perf_vm.sh -Z 4 -S 1521550718 -w 90 -c 1650,950 -t 900
#   Exemple : tools/perf_vm.sh -3 25,25,20 -A 1 -W 90 -S 1521550718 -t 900
#   Exemple : tools/perf_vm.sh -3 25,25,20 -P 20 -A 1 -W 90 -S 1521550718 -t 900
#   Exemple : tools/perf_vm.sh -z 0.5 -x Ground
#   Exemple : tools/perf_vm.sh -E 20 -z 4 -x MacroLife -O
#   Journal complet : /tmp/perf_symbiose/godot.log
set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib_vm_godot.sh"   # DEPOT GODOT XROOT + vm_*
BANC=full ZOOM="" CENTRE="" CACHER="" SAUT=4 N=8 DELAI=300 GRAINE="" SEMAINES="" TURBO="" BUILD=1 BANC_E="" OMBRES="" BANC_W="" CADENCE="" VENT="" PLEINE="" AUTOMATE="" TROIS="" BALAYAGE="" PARTAGE=""

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
    -E) BANC_E="$2"; shift 2 ;;
    -O) OMBRES=0; shift ;;
    -L) SANSLUT=1; shift ;;
    -W) BANC_W="$2"; shift 2 ;;
    -A) CADENCE="$2"; shift 2 ;;
    -V) VENT="$2"; shift 2 ;;
    -R) PLEINE=1; shift ;;
    -a) AUTOMATE="$2"; shift 2 ;;
    -3) TROIS="$2"; BANC_E="${2%%,*}"; shift 2 ;;
    -Z) BALAYAGE="$2"; shift 2 ;;
    -P) PARTAGE="$2"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    -h|--help) sed -n '2,55p' "$0"; exit 0 ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done
# -P implique le banc 3 phases (durées par défaut si -3 absent).
if [ -n "$PARTAGE" ] && [ -z "$TROIS" ]; then TROIS=25,25,20; BANC_E=25; fi

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

[ -z "$ZOOM" ] && [ -z "$BANC_E" ] && ZOOM=0.5   # banc E : ×4 du scénario par défaut
vm_verifier
if [ "$BUILD" = 1 ]; then vm_build; fi
vm_xvfb ":${PERF_DISPLAY:-96}"

# 1. Godot temps réel en arrière-plan ; on lit son journal jusqu'à SAUT+N relevés.
SORTIE=/tmp/perf_symbiose; rm -rf "$SORTIE"; mkdir -p "$SORTIE"; LOG="$SORTIE/godot.log"
ARGS=(--capture-banc="$BANC")
# Banc E : zoom/centre ne valent qu'au CADRAGE (l'avance turbo reste à ×0,5, comme au F5).
if [ -n "$BANC_E" ]; then Z=banc-zoom C=banc-centre; else Z=zoom C=centre; fi
[ -n "$ZOOM" ] && ARGS+=(--capture-$Z="$ZOOM")
[ -n "$CENTRE" ] && ARGS+=(--capture-$C="$CENTRE")
[ -n "$CACHER" ] && ARGS+=(--capture-cacher="$CACHER")
[ -n "$GRAINE" ] && ARGS+=(--capture-seed="$GRAINE")
[ -n "$SEMAINES" ] && ARGS+=(--capture-semaines="$SEMAINES")
[ -n "$TURBO" ] && ARGS+=(--capture-turbo="$TURBO")
[ -n "$BANC_E" ] && ARGS+=(--capture-etalonnage="$BANC_E")
[ -n "$OMBRES" ] && ARGS+=(--capture-ombres=0)
[ -n "${SANSLUT:-}" ] && ARGS+=(--capture-lut=0)
[ -n "$BANC_W" ] && ARGS+=(--capture-banc-semaine="$BANC_W")
[ -n "$CADENCE" ] && ARGS+=(--capture-banc-cadence="$CADENCE")
[ -n "$VENT" ] && ARGS+=(--capture-vent="$VENT")
[ -n "$PLEINE" ] && ARGS+=(--capture-pleine-res=1)
[ -n "$AUTOMATE" ] && ARGS+=(--capture-banc-automate="$AUTOMATE")
[ -n "$TROIS" ] && ARGS+=(--capture-banc-3phases="$TROIS")
[ -n "$PARTAGE" ] && ARGS+=(--capture-banc-partage="$PARTAGE")
[ -n "$BALAYAGE" ] && ARGS+=(--capture-zoom-balayage="$BALAYAGE")
DISPLAY="$ECRAN" LIBGL_ALWAYS_SOFTWARE=1 "$GODOT" --path "$DEPOT" \
  --rendering-driver opengl3 --resolution 1920x1080 --print-fps \
  -- "${ARGS[@]}" >"$LOG" 2>&1 &
GPID=$!
trap 'kill $GPID 2>/dev/null || true; kill $XPID 2>/dev/null || true' EXIT

FIN=$((SECONDS + DELAI))
# Banc d'étalonnage : on attend le marqueur de fin, puis on imprime le rapport.
if [ -n "$BANC_E" ]; then
  until grep -q '^\[banc\] FIN' "$LOG"; do
    kill -0 $GPID 2>/dev/null || { echo "Godot s'est arrêté (cf. $LOG)" >&2; exit 1; }
    [ $SECONDS -lt $FIN ] || { echo "délai $DELAI s dépassé (cf. $LOG)" >&2; exit 1; }
    read -rt 1 <> <(:) || true
  done
  sed -n '/^\[banc\] DEBUT/,/^\[banc\] FIN/p' "$LOG"
  exit 0
fi
# Balayage de zoom : idem, marqueurs [zoom] (WorldView.ZoomJournal.cs).
if [ -n "$BALAYAGE" ]; then
  until grep -q '^\[zoom\] FIN' "$LOG"; do
    kill -0 $GPID 2>/dev/null || { echo "Godot s'est arrêté (cf. $LOG)" >&2; exit 1; }
    [ $SECONDS -lt $FIN ] || { echo "délai $DELAI s dépassé (cf. $LOG)" >&2; exit 1; }
    read -rt 1 <> <(:) || true
  done
  sed -n '/^\[zoom\] DEBUT/,/^\[zoom\] FIN/p' "$LOG"
  exit 0
fi
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
