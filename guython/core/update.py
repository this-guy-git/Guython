import requests
import re
import os
import platform
import subprocess
from guython.core.constants import VERSION


def strip_build(v):
    return re.match(r"v?(\d+\.\d+\.\d+)", v).group(1)

ver = f"v{strip_build(VERSION)}"

def detect_platform():
    os_name = platform.system()
    if os_name == "Windows":
        return "windows"
    elif os_name == "Linux":
        return "linux"
    else:
        return "unsupported"

def check_for_updates():
    current_version = strip_build(VERSION)
    user_os = detect_platform()

    if user_os == "unsupported":
        print("Your OS is not supported for auto-updating.")
        return

    try:
        if user_os == "windows":
            api_url = "https://api.github.com/repos/this-guy-git/Guython/releases/latest"
        elif user_os == "linux":
            api_url = "https://api.github.com/repos/this-guy-git/guython-deb/releases/latest"

        res = requests.get(api_url)
        release = res.json()
        tag_name = release.get("tag_name", "")
        latest_version = strip_build(tag_name)

        if latest_version > current_version:
            print(f"\nGuython update available: {tag_name} (you have {ver})")

            installer_url = None
            installer_name = None

            for asset in release.get("assets", []):
                asset_name = asset["name"]

                if user_os == "windows" and asset_name.startswith("guythonInstaller") and asset_name.endswith(".exe"):
                    installer_url = asset["browser_download_url"]
                    installer_name = asset_name
                    break
                elif user_os == "linux" and asset_name == "guython-deb.deb":
                    installer_url = asset["browser_download_url"]
                    installer_name = asset_name
                    break

            if not installer_url:
                print("Could not find a compatible installer in the release assets.")
                return

            while True:
                prompt = input("Would you like to download and install the update? (y/n): ").strip().lower()
                if prompt == "y":
                    print(f"Downloading {installer_name}...")
                    with requests.get(installer_url, stream=True) as r:
                        with open(installer_name, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)

                    print("Running installer...")
                    if user_os == "windows":
                        subprocess.Popen([installer_name], shell=True)
                    elif user_os == "linux":
                        subprocess.run(["sudo", "dpkg", "-i", installer_name])
                        subprocess.run(["guython"])

                    break
                elif prompt == "n":
                    print("\0")
                    break
                else:
                    print("Invalid option. Please enter 'y' or 'n'.")
    except Exception as e:
        print("Update check failed:", e)

if __name__ == "__main__":
    check_for_updates()
