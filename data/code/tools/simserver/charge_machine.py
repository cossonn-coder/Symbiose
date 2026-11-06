"""
SYMBIOSE — tools/simserver/charge_machine.py
Qui d'autre que le moteur occupait le processeur pendant un tick ?

📖 D127 : au PC, les pires ticks passent un tiers à la moitié de leur durée à
ATTENDRE (durée murale − CPU du moteur). Le moteur tourne en `BelowNormal` : tout
processus normal passe devant. Pour nommer ce qui prend le processeur, la sonde
relève deux compteurs CUMULÉS, avant et après le tick :

  - `temps_machine()` : (occupé, total) en secondes-cœur, tous cœurs confondus.
    occupé / total sur la durée du tick = charge de la machine (100 % = tous les
    cœurs pleins).
  - `cpu_processus(pid)` : CPU consommé par un autre processus. On l'applique au
    PARENT du moteur, c'est-à-dire Godot (`SimBridge` lance le moteur lui-même).

Le reste, occupé − moteur − Godot, est la part des « autres processus » (antivirus,
navigateur, mise à jour…).

Deux implémentations sans dépendance : Windows par `ctypes` (`GetSystemTimes`,
`GetProcessTimes`), Linux par `/proc`. Ailleurs, ou en cas d'échec, `None` : le
rapport affiche alors simplement une ligne de moins.

Golden NEUTRE : rien ici n'est lu par la simulation.
"""
from __future__ import annotations

import ctypes
import os
import sys

_TICKS_WINDOWS = 1e-7   # FILETIME : unités de 100 ns


def _filetime_s(ft) -> float:
    return ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) * _TICKS_WINDOWS


if sys.platform == "win32":
    from ctypes import wintypes

    _k32 = ctypes.windll.kernel32
    _k32.OpenProcess.restype = wintypes.HANDLE
    _ACCES_LECTURE = 0x1000   # PROCESS_QUERY_LIMITED_INFORMATION : sans droit admin

    def temps_machine() -> tuple[float, float] | None:
        """(occupé, total) cumulés en secondes-cœur. Sous Windows, `kernel` inclut
        déjà le temps d'inactivité : occupé = kernel + user − idle."""
        idle, kern, user = (wintypes.FILETIME() for _ in range(3))
        if not _k32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern),
                                   ctypes.byref(user)):
            return None
        total = _filetime_s(kern) + _filetime_s(user)
        return total - _filetime_s(idle), total

    def cpu_processus(pid: int) -> float | None:
        h = _k32.OpenProcess(_ACCES_LECTURE, False, pid)
        if not h:
            return None
        try:
            t = [wintypes.FILETIME() for _ in range(4)]   # création, fin, noyau, user
            if not _k32.GetProcessTimes(h, *(ctypes.byref(x) for x in t)):
                return None
            return _filetime_s(t[2]) + _filetime_s(t[3])
        finally:
            _k32.CloseHandle(h)

else:
    try:
        _HZ = os.sysconf("SC_CLK_TCK")
    except (AttributeError, ValueError, OSError):
        _HZ = 100

    def temps_machine() -> tuple[float, float] | None:
        """Ligne `cpu` de /proc/stat : idle et iowait comptent comme inactifs."""
        try:
            with open("/proc/stat") as f:
                v = [int(x) for x in f.readline().split()[1:]]
        except (OSError, ValueError):
            return None
        total = sum(v[:8])   # user nice system idle iowait irq softirq steal
        return (total - v[3] - v[4]) / _HZ, total / _HZ

    def cpu_processus(pid: int) -> float | None:
        """Champs 14-15 (utime, stime) de /proc/<pid>/stat. Le nom du processus
        peut contenir des espaces : on découpe après la dernière parenthèse."""
        try:
            with open(f"/proc/{pid}/stat") as f:
                champs = f.read().rsplit(")", 1)[1].split()
        except (OSError, IndexError):
            return None
        return (int(champs[11]) + int(champs[12])) / _HZ


def releve() -> tuple:
    """Instantané à prendre au début et à la fin du tick."""
    return temps_machine(), cpu_processus(os.getppid())


def bilan(avant: tuple, apres: tuple, cpu_moteur_s: float) -> dict | None:
    """Charge pendant le tick. `None` si un compteur manque."""
    (m0, g0), (m1, g1) = avant, apres
    if m0 is None or m1 is None:
        return None
    occupe, total = m1[0] - m0[0], m1[1] - m0[1]
    if total <= 0:
        return None
    godot = None if g0 is None or g1 is None else g1 - g0
    autres = occupe - cpu_moteur_s - (godot or 0.0)
    return {"charge_pct": round(100.0 * occupe / total),
            "coeurs": os.cpu_count(),
            "godot_ms": None if godot is None else round(godot * 1000.0),
            "autres_ms": round(max(0.0, autres) * 1000.0)}
