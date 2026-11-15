from __future__ import annotations

import json
import hashlib
import subprocess
import tempfile
import threading
import urllib.request
from pathlib import Path
from tkinter import messagebox


OWNER = "jw20152025-blip"
REPO = "KitKat-Autonomous-Thing"
RELEASE_API = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"


def version_tuple(value):
    parts = str(value).lstrip("v").split(".")
    return tuple(int("".join(c for c in p if c.isdigit()) or 0) for p in parts[:3])


class UpdateManager:
    def __init__(self, root, current_version):
        self.root = root
        self.current_version = current_version
        self.checking = False

    def check(self, manual=False):
        if self.checking:
            return
        self.checking = True

        def worker():
            try:
                request = urllib.request.Request(
                    RELEASE_API,
                    headers={"User-Agent": "Kittelligence-Updater"},
                )
                with urllib.request.urlopen(request, timeout=12) as response:
                    release = json.loads(response.read().decode("utf-8"))

                latest = release.get("tag_name", "")
                assets = release.get("assets", [])
                installer = next(
                    (a for a in assets if a.get("name", "").lower().endswith(".exe")),
                    None,
                )
                error = None
                if not latest:
                    error = "The latest GitHub release has no version tag."
                elif version_tuple(latest) <= version_tuple(self.current_version):
                    error = "You already have the latest version."
                elif installer is None:
                    error = "A newer release exists, but it has no Windows installer attached."

                self.root.after(
                    0,
                    lambda: self._finish_check(manual, latest, installer, error),
                )
            except Exception as exc:
                error_text = str(exc)
                self.root.after(
                    0,
                    lambda message=error_text: self._finish_check(
                        manual, "", None, f"Could not check GitHub: {message}"
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_check(self, manual, latest, installer, error):
        self.checking = False
        if error:
            if manual:
                messagebox.showinfo("Kittelligence updates", error)
            return

        if not messagebox.askyesno(
            "Kittelligence update",
            f"Version {latest} is available. Download and start the installer?\n\n"
            "Your saved memory will be kept.",
        ):
            return

        threading.Thread(
            target=self._download_and_launch,
            args=(installer,),
            daemon=True,
        ).start()

    def _download_and_launch(self, asset):
        try:
            url = asset["browser_download_url"]
            filename = Path(tempfile.gettempdir()) / asset["name"]
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Kittelligence-Updater"},
            )
            digest = hashlib.sha256()
            with urllib.request.urlopen(request, timeout=60) as response, filename.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    digest.update(chunk)

            expected = asset.get("digest")
            if (
                expected
                and expected.startswith("sha256:")
                and digest.hexdigest().lower() != expected.split(":", 1)[1].lower()
            ):
                filename.unlink(missing_ok=True)
                raise ValueError(
                    "The downloaded installer failed its SHA-256 integrity check."
                )

            subprocess.Popen([str(filename)], cwd=str(filename.parent))
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Kittelligence",
                    "Installer started. Close Kittelligence when the installer asks you to.",
                ),
            )
        except Exception as exc:
            error_text = str(exc)
            self.root.after(
                0,
                lambda message=error_text: messagebox.showerror(
                    "Kittelligence update failed", message
                ),
            )
