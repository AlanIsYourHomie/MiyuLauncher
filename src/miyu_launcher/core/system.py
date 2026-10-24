from __future__ import annotations

import ctypes
import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class SystemInfo:
    operating_system: str
    release: str
    architecture: str
    machine: str
    processor: str
    total_ram_gb: float | None


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _get_total_ram_gb() -> float | None:
    if platform.system() != "Windows":
        return None

    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(_MemoryStatusEx)

    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None

    return round(status.ullTotalPhys / (1024 ** 3), 2)


def get_system_info() -> SystemInfo:
    """Return basic information about the computer running MiyuLauncher."""
    return SystemInfo(
        operating_system=platform.system(),
        release=platform.release(),
        architecture=platform.architecture()[0],
        machine=platform.machine() or "Unknown",
        processor=platform.processor() or "Unknown",
        total_ram_gb=_get_total_ram_gb(),
    )
