import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


# ============================================================
# CONFIG
# ============================================================

CURRENT_VERSION = "1.0.0"

GITHUB_OWNER = "jw20152025-blip"
GITHUB_REPO = "KitKat-Autonomous-Thing"

RELEASES_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)


# ============================================================
# VERSION
# ============================================================

def normalize_version(version):

    version = str(version).strip()

    if version.lower().startswith("v"):
        version = version[1:]

    parts = version.split(".")

    numbers = []

    for part in parts:

        number = ""

        for character in part:

            if character.isdigit():
                number += character
            else:
                break

        if number:
            numbers.append(
                int(number)
            )
        else:
            numbers.append(0)

    while len(numbers) < 3:
        numbers.append(0)

    return tuple(numbers[:3])


def is_newer_version(
    latest,
    current
):

    return (
        normalize_version(latest)
        > normalize_version(current)
    )


# ============================================================
# GITHUB
# ============================================================

def get_latest_release():

    request = urllib.request.Request(
        RELEASES_API,
        headers={
            "User-Agent":
                "KitKat-Autonomous-Thing-Updater"
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=10
        ) as response:

            data = response.read()

            return json.loads(data)

    except Exception as error:

        print(
            f"[Updater] GitHub check failed: {error}"
        )

        return None


# ============================================================
# FIND INSTALLER
# ============================================================

def find_installer(release):

    assets = release.get(
        "assets",
        []
    )

    installers = []

    for asset in assets:

        name = str(
            asset.get(
                "name",
                ""
            )
        ).lower()

        if name.endswith(".exe"):

            installers.append(
                asset
            )

    if not installers:
        return None

    # Prefer obvious installer/setup names.
    for asset in installers:

        name = asset["name"].lower()

        if (
            "setup" in name
            or "installer" in name
            or "install" in name
        ):

            return asset

    return installers[0]


# ============================================================
# DOWNLOAD
# ============================================================

def download_installer(asset):

    download_url = asset.get(
        "browser_download_url"
    )

    if not download_url:
        return None

    filename = asset.get(
        "name",
        "KitKatUpdate.exe"
    )

    temp_directory = tempfile.gettempdir()

    installer_path = Path(
        temp_directory
    ) / filename

    request = urllib.request.Request(
        download_url,
        headers={
            "User-Agent":
                "KitKat-Autonomous-Thing-Updater"
        }
    )

    try:

        print(
            "[Updater] Downloading update..."
        )

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            with open(
                installer_path,
                "wb"
            ) as file:

                while True:

                    chunk = response.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    file.write(chunk)

        print(
            f"[Updater] Downloaded to: "
            f"{installer_path}"
        )

        return installer_path

    except Exception as error:

        print(
            f"[Updater] Download failed: {error}"
        )

        try:

            if installer_path.exists():
                installer_path.unlink()

        except Exception:
            pass

        return None


# ============================================================
# RUN INSTALLER
# ============================================================

def launch_installer(installer_path):

    try:

        print(
            "[Updater] Launching installer..."
        )

        subprocess.Popen(
            [
                str(installer_path)
            ],
            cwd=str(
                installer_path.parent
            )
        )

        return True

    except Exception as error:

        print(
            f"[Updater] Could not launch installer: "
            f"{error}"
        )

        return False


# ============================================================
# UPDATE PROMPT
# ============================================================

def ask_to_update(
    current_version,
    latest_version
):

    root = tk.Tk()

    root.withdraw()

    try:

        result = messagebox.askyesno(
            "KitKat Update",
            (
                "A new version of KitKat is available!\n\n"
                f"Current version: {current_version}\n"
                f"New version: {latest_version}\n\n"
                "Would you like to update now?"
            )
        )

    finally:

        root.destroy()

    return result


# ============================================================
# MAIN UPDATE CHECK
# ============================================================

def check_for_update():

    print(
        "[Updater] Checking for updates..."
    )

    release = get_latest_release()

    # No GitHub release yet.
    if release is None:

        print(
            "[Updater] No release available."
        )

        return False

    # GitHub can return a draft/prerelease depending
    # on how the release is configured.
    if release.get(
        "draft",
        False
    ):

        print(
            "[Updater] Latest release is a draft."
        )

        return False

    latest_version = release.get(
        "tag_name"
    )

    if not latest_version:

        print(
            "[Updater] Release has no version tag."
        )

        return False

    print(
        f"[Updater] Current version: "
        f"{CURRENT_VERSION}"
    )

    print(
        f"[Updater] Latest version: "
        f"{latest_version}"
    )

    if not is_newer_version(
        latest_version,
        CURRENT_VERSION
    ):

        print(
            "[Updater] Already up to date."
        )

        return False

    installer = find_installer(
        release
    )

    if installer is None:

        print(
            "[Updater] Update exists, "
            "but no .exe installer was found."
        )

        return False

    installer_name = installer.get(
        "name",
        "Unknown"
    )

    print(
        f"[Updater] Installer found: "
        f"{installer_name}"
    )

    if not ask_to_update(
        CURRENT_VERSION,
        latest_version
    ):

        print(
            "[Updater] User declined update."
        )

        return False

    installer_path = download_installer(
        installer
    )

    if installer_path is None:

        messagebox.showerror(
            "KitKat Update",
            "The update could not be downloaded."
        )

        return False

    if not launch_installer(
        installer_path
    ):

        messagebox.showerror(
            "KitKat Update",
            "The installer could not be started."
        )

        return False

    print(
        "[Updater] Update installer started."
    )

    return True


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    updated = check_for_update()

    if updated:

        print(
            "[Updater] Update started."
        )

    else:

        print(
            "[Updater] No update started."
        )