# SYMBIOSE — tools/lib_vm_godot.sh (sprint RENDU VISIBLE T1 — factorisation)
# Amorçage COMMUN des bancs VM sans écran : tools/capture_vm.sh (PNG, Movie
# Maker) et tools/perf_vm.sh (FPS temps réel). Fichier SOURCÉ (`. lib_vm_godot.sh`),
# pas exécuté : il pose des variables et des fonctions dans le script appelant.
# Dépendances hors dépôt et réinstallation : cf. en-tête de tools/capture_vm.sh.

DEPOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="${GODOT:-$HOME/opt/godot/Godot_v4.6-stable_mono_linux_x86_64/Godot_v4.6-stable_mono_linux.x86_64}"
XROOT="${XROOT:-$HOME/opt/xvfb/root}"

# Godot + Xvfb présents ? (sortie en erreur sinon)
vm_verifier() {
  [ -x "$GODOT" ] || { echo "Godot absent : $GODOT" >&2; exit 1; }
  [ -x "$XROOT/usr/bin/Xvfb-patched" ] || { echo "Xvfb absent : $XROOT" >&2; exit 1; }
}

# Build C# (filet de compilation) — Godot lance les DLL compilées.
vm_build() {
  PATH="$HOME/.dotnet:$PATH" dotnet build "$DEPOT/Symbiose.csproj" -nologo -v q >/dev/null
}

# Xvfb sur l'écran virtuel $1 (ex. :97), tué à la sortie du script appelant.
# Pose ECRAN et XPID. Xvfb cherche `xkbcomp` dans un chemin COMPILÉ : la copie
# `Xvfb-patched` pointe /tmp/xk, qu'on (re)crée ici (/tmp vidé au reboot).
vm_xvfb() {
  export LD_LIBRARY_PATH="$XROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  mkdir -p /tmp/xk && ln -sf "$XROOT/usr/bin/xkbcomp" /tmp/xk/xkbcomp
  ECRAN="$1"
  "$XROOT/usr/bin/Xvfb-patched" "$ECRAN" -screen 0 1920x1080x24 -nolisten tcp >/tmp/xk/xvfb$ECRAN.log 2>&1 &
  XPID=$!
  trap 'kill $XPID 2>/dev/null || true' EXIT
  for _ in $(seq 50); do [ -e "/tmp/.X11-unix/X${ECRAN#:}" ] && break; read -rt 0.1 <> <(:) || true; done
}
