#!/usr/bin/env bash
# SYMBIOSE — mesure du SEUIL DE VISIBILITÉ des signes (INFO-BULLE DU VIVANT ②).
# Lance le banc world/WorldView.BancSeuil.cs sous Xvfb (sans Movie Maker : le banc
# relit lui-même l'écran) et résume, par cause et par palier, la plus petite
# intensité qui change au moins un pixel de l'écran par rapport à l'état sain.
#
# USAGE : mesure_seuil.sh [-b BANC] [-c X,Y] [-w SEMAINES] [-p] [-x CAUSE] [--no-build]
#   -b monde (défaut smoke) · -c point visé cm (témoin = plante la plus proche)
#   -w semaines de warmup · -p palette SNES ON (F11) · -x une seule cause (défaut toutes)
#   -P CAUSE,I,FICHIER.png : pose seule ×4 + info-bulle, recadrage PNG (captures ⑥)
# Sortie : journal complet dans $SORTIE/godot.log, résumé à l'écran.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../../../../../tools/lib_vm_godot.sh"
BANC=smoke CENTRE="" SEM="" PAL="" CAUSE=toutes POSE="" BUILD=1
SORTIE="${SORTIE:-/tmp/mesure_seuil}"
while [ $# -gt 0 ]; do
  case "$1" in
    -b) BANC="$2"; shift 2 ;;  -c) CENTRE="$2"; shift 2 ;;
    -w) SEM="$2"; shift 2 ;;   -p) PAL=1; shift ;;
    -x) CAUSE="$2"; shift 2 ;; -P) POSE="$2"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done
vm_verifier
if [ "$BUILD" = 1 ]; then vm_build; fi
vm_xvfb ":${CAPTURE_DISPLAY:-96}"
mkdir -p "$SORTIE"
# Vent nul + vie macro / météo masquées : seule la témoin change d'une image à l'autre.
ARGS=(--capture-banc="$BANC" --capture-vent=0 --capture-cacher=MacroLife,ForagerLayer,Weather,Carpophores)
[ -n "$CENTRE" ] && ARGS+=(--capture-centre="$CENTRE")
[ -n "$SEM" ] && ARGS+=(--capture-semaines="$SEM")
[ -n "$PAL" ] && ARGS+=(--capture-palette=1)
if [ -n "$POSE" ]; then
  ARGS+=(--capture-seuil-pose="${POSE%,*}" --capture-seuil-png="${POSE##*,}")
else
  ARGS+=(--capture-seuil="$CAUSE")
fi
DISPLAY="$ECRAN" LIBGL_ALWAYS_SOFTWARE=1 "$GODOT" --path "$DEPOT" \
  --rendering-driver opengl3 --resolution 1920x1080 --fixed-fps 10 \
  -- "${ARGS[@]}" >"$SORTIE/godot.log" 2>&1 || true
grep '^\[Seuil\]' "$SORTIE/godot.log" | grep -v ' i=' || true
# Résumé : seuil = plus petite intensité > 0 avec px > 0 ; bruit = 2ᵉ i=0.
grep -o '\[Seuil\] [a-z_]* ×[0-9.]* i=[0-9.]* px=-\?[0-9]*' "$SORTIE/godot.log" \
  | sed 's/i=//; s/px=//' | LC_ALL=C awk '
  { k=$2" "$3; i=$4+0; px=$5+0
    if (!(k in vu)) { vu[k]=1; ordre[++n]=k; nz[k]=0; s[k]="> 0.5" }
    if (i==0) { if (nz[k]++ == 1) bruit[k]=px }
    else if (px>0 && s[k]=="> 0.5") s[k]=$4 }
  END { for (j=1;j<=n;j++) printf "%-26s seuil %-6s (bruit %s px)\n", ordre[j], s[ordre[j]], bruit[ordre[j]] }'
