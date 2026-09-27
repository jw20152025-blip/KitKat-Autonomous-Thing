import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import tkinter as tk
from tkinter import messagebox


# ============================================================
# KITTELLIGENCE UPDATER
# ============================================================

CURRENT_VERSION = "1.1.0"

# Change this to your GitHub repository.
GITHUB_OWNER = "YOUR_GITHUB_USERNAME"
GITHUB_REPO = "YOUR_KITTELLIGENCE_REPO"

# ------------------------------------------------------------
# TEST MODE
# ------------------------------------------------------------
# True = pretend an update exists without contacting GitHub.
# False = use real GitHub Releases.
TEST_MODE = True

TEST_VERSION = "1.0.1"


def version_tuple(version):
    version = version.lower().replace("v", "").strip()

    parts = version.split(".")

    numbers = []

    for part in parts:
        number = ""

        for character in part:
            if character.isdigit():
                number += character
            else:
                break

        numbers.append(
            int(number or 0)
        )

    while len(numbers) < 3:
        numbers.append(0)

    return tuple(numbers[:3])


def is_newer(version):
    return (
        version_tuple(version)
        > version_tuple(CURRENT_VERSION)
    )


def get_latest_release():
    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Kittelligence-Updater"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=10
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        )


def find_installer(release):
    assets = release.get(
        "assets",
        []
    )

    for asset in assets:

        name = asset.get(
            "name",
            ""
        )

        if name.lower().endswith(
            ".exe"
        ):

            if (
                "setup" in name.lower()
                or "installer" in name.lower()
            ):
                return asset.get(
                    "browser_download_url"
                )

    return None


def ask_update(version):
    root = tk.Tk()

    root.withdraw()

    result = messagebox.askyesno(
        "Kittelligence Update",
        (
            "🐱 Kittelligence has an update!\n\n"
            f"Current version: {CURRENT_VERSION}\n"
            f"New version: {version}\n\n"
            "Update now?"
        )
    )

    root.destroy()

    return result


def download_installer(url):
    temp_directory = tempfile.gettempdir()

    installer_path = os.path.join(
        temp_directory,
        "KittelligenceUpdate.exe"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Kittelligence-Updater"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        data = response.read()

    with open(
        installer_path,
        "wb"
    ) as file:

        file.write(data)

    return installer_path


def run_installer(installer_path):

    subprocess.Popen(
        [installer_path],
        close_fds=True
    )


def check_for_update():

    # ========================================================
    # LOCAL TEST MODE
    # ========================================================

    if TEST_MODE:

        if not is_newer(
            TEST_VERSION
        ):
            return False

        if not ask_update(
            TEST_VERSION
        ):
            return False

        messagebox.showinfo(
            "Updater Test",
            (
                "TEST MODE WORKS! 🐱\n\n"
                f"Detected fake version {TEST_VERSION}.\n\n"
                "No installer was downloaded."
            )
        )

        return True

    # ========================================================
    # REAL GITHUB UPDATE
    # ========================================================

    try:

        release = get_latest_release()

        latest_version = release.get(
            "tag_name",
            ""
        )

        if not latest_version:
            return False

        if not is_newer(
            latest_version
        ):
            return False

        installer_url = find_installer(
            release
        )

        if not installer_url:

            messagebox.showwarning(
                "Kittelligence Update",
                (
                    "A new version was found, "
                    "but no installer was found "
                    "in the GitHub release."
                )
            )

            return False

        if not ask_update(
            latest_version
        ):
            return False

        installer_path = download_installer(
            installer_url
        )

        run_installer(
            installer_path
        )

        return True

    except Exception as error:

        print(
            f"[Updater] Update check failed: {error}"
        )

        return False


if __name__ == "__main__":

    check_for_update()