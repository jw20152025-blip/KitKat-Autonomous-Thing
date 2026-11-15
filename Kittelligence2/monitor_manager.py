from __future__ import annotations

import ctypes
import os
import random
from ctypes import wintypes


class MonitorManager:
    """Enumerates Windows displays in virtual-desktop coordinates."""

    def __init__(self):
        self._monitors = []
        self.refresh()

    def refresh(self):
        monitors = []
        if os.name == "nt":
            try:
                class RECT(ctypes.Structure):
                    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

                class MONITORINFO(ctypes.Structure):
                    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT),
                                ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]

                user32 = ctypes.windll.user32
                callback_type = ctypes.WINFUNCTYPE(
                    wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
                    ctypes.POINTER(RECT), wintypes.LPARAM
                )

                def collect(handle, _dc, _rect, _data):
                    info = MONITORINFO()
                    info.cbSize = ctypes.sizeof(MONITORINFO)
                    if user32.GetMonitorInfoW(handle, ctypes.byref(info)):
                        r = info.rcMonitor
                        monitors.append({
                            "left": int(r.left), "top": int(r.top),
                            "right": int(r.right), "bottom": int(r.bottom),
                        })
                    return True

                callback = callback_type(collect)
                user32.EnumDisplayMonitors(None, None, callback, 0)
            except Exception:
                monitors = []

        if not monitors:
            if os.name == "nt":
                user32 = ctypes.windll.user32
                left, top = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
                width, height = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
                monitors = [{"left": left, "top": top, "right": left + width,
                             "bottom": top + height}]
            else:
                monitors = [{"left": 0, "top": 0, "right": 1920, "bottom": 1080}]
        self._monitors = monitors
        return list(monitors)

    @property
    def monitors(self):
        return list(self._monitors)

    def choose_position(self, width, height, margin=24, preferred=None):
        monitors = self._monitors or self.refresh()
        if preferred is not None and 0 <= preferred < len(monitors):
            candidates = [(preferred, monitors[preferred])]
        else:
            candidates = list(enumerate(monitors))
        index, rect = candidates[random.randrange(len(candidates))]
        max_x = max(rect["left"] + margin, rect["right"] - width - margin)
        max_y = max(rect["top"] + margin, rect["bottom"] - height - margin)
        return index, (
            random.randint(rect["left"] + margin, max_x),
            random.randint(rect["top"] + margin, max_y),
        )

    def clamp_to_nearest_monitor(self, x, y, width, height, margin=0):
        monitors = self._monitors or self.refresh()
        best = None
        best_distance = None
        for index, rect in enumerate(monitors):
            min_x, max_x = rect["left"] + margin, rect["right"] - width - margin
            min_y, max_y = rect["top"] + margin, rect["bottom"] - height - margin
            cx = max(min_x, min(max_x, x))
            cy = max(min_y, min(max_y, y))
            distance = (cx - x) ** 2 + (cy - y) ** 2
            if best_distance is None or distance < best_distance:
                best_distance, best = distance, (index, cx, cy)
        return best
