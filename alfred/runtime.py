"""Réglage ciblé du processus interactif, sans changer le plan d'alimentation."""
import sys


def prefer_interactive_cpu():
    """Windows HighQoS : désactiver le throttling EXECUTION_SPEED pour Alfred.

    Ce n'est ni une priorité haute, ni une affinité imposée. Sur les CPU hybrides,
    cela évite le placement économe d'un service vocal sans fenêtre au premier plan.
    Une plate-forme ne proposant pas l'API garde simplement son comportement habituel.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class PowerThrottling(ctypes.Structure):
            _fields_ = [("Version", wintypes.ULONG), ("ControlMask", wintypes.ULONG),
                        ("StateMask", wintypes.ULONG)]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.SetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                                ctypes.c_void_p, wintypes.DWORD]
        kernel.SetProcessInformation.restype = wintypes.BOOL
        # PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1 ; EXECUTION_SPEED = 1.
        # ControlMask=1, StateMask=0 est l'opt-out HighQoS documenté par Microsoft.
        state = PowerThrottling(1, 1, 0)
        return bool(kernel.SetProcessInformation(kernel.GetCurrentProcess(), 4,
                                                 ctypes.byref(state), ctypes.sizeof(state)))
    except (AttributeError, OSError):
        return False
