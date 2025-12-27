import os
import shutil
import urllib.request
import zipfile
import pathlib
import stat

# Configuration
UV_VERSION = "latest"  # or specific version like "0.5.11"
UV_PLATFORM = "x86_64-pc-windows-msvc"
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
OUTPUT_ZIP_NAME = "gogma-artian-weapons-reroll-automation"


def clean_dist():
    """Removes the existing dist directory."""
    if DIST_DIR.exists():
        print(f"Cleaning existing dist directory: {DIST_DIR}")
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()


def download_file(url, dest_path):
    """Downloads a file from a URL to a destination path."""
    print(f"Downloading: {url} -> {dest_path}")
    with urllib.request.urlopen(url) as response, open(dest_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


def setup_uv():
    """Downloads uv and its license."""
    uv_dir = DIST_DIR / "uv"
    uv_dir.mkdir()

    # Download uv
    # Assuming latest for now, can be pinned.
    # The URL pattern for GitHub releases assets:
    base_url = "https://github.com/astral-sh/uv/releases/latest/download"
    uv_zip_url = f"{base_url}/uv-{UV_PLATFORM}.zip"
    uv_zip_path = uv_dir / "uv.zip"

    try:
        download_file(uv_zip_url, uv_zip_path)
    except Exception as e:
        print(f"Failed to download uv: {e}")
        return

    # Extract uv.exe
    print("Extracting uv.exe...")
    with zipfile.ZipFile(uv_zip_path, "r") as zip_ref:
        # The zip usually contains a folder named uv-x86_64-pc-windows-msvc/uv.exe
        # We need to find uv.exe
        for file in zip_ref.namelist():
            if file.endswith("uv.exe"):
                # Extract to a temp location then move, or read and write
                source = zip_ref.open(file)
                target = open(uv_dir / "uv.exe", "wb")
                with source, target:
                    shutil.copyfileobj(source, target)
                break

    # Clean up zip
    uv_zip_path.unlink()

    # Download License (MIT)
    license_url = "https://raw.githubusercontent.com/astral-sh/uv/main/LICENSE-MIT"
    download_file(license_url, uv_dir / "LICENSE-MIT")


def copy_project_files():
    """Copies source code and config files."""
    print("Copying project files...")

    # src directory
    # src directory
    shutil.copytree(
        PROJECT_ROOT / "src",
        DIST_DIR / "src",
        ignore=shutil.ignore_patterns("bonus_reroller"),
    )

    # Files to copy
    files_to_copy = [
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "main.py",
        "config.toml",  # Assuming config.toml is in root or src, user path indicated src/skill_reroller/config.toml but implementation plan said root?
        # Let's check where config.toml is. It is in src/skill_reroller/config.toml in the active document metadata.
        # But usually there might be a root one? Let's assume we copy what's needed.
        # If config.toml is NOT in root, we don't copy it to root unless the app expects it there.
        # The user metadata says: c:\Users\yuuho\Projects\gogma-artian-weapons-reroll-automation\src\skill_reroller\config.toml
        # So it's inside src. We already copied src.
        # Only copy if it exists in root.
    ]

    for filename in files_to_copy:
        src_file = PROJECT_ROOT / filename
        if src_file.exists():
            shutil.copy(src_file, DIST_DIR / filename)
        else:
            print(f"Warning: {filename} not found in project root, skipping.")

    # Note: data directory
    # User requested to exclude logs, output, and videos, but keep sample images.
    data_dir = PROJECT_ROOT / "data"
    if data_dir.exists():
        shutil.copytree(
            data_dir,
            DIST_DIR / "data",
            ignore=shutil.ignore_patterns("logs", "output", "*.mp4", "*.avi"),
        )


def create_run_bat():
    """Creates the startup script in scripts/run_skill_reroller.bat (repo compliant)."""
    print("Creating scripts/run_skill_reroller.bat...")

    scripts_dir = DIST_DIR / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Path to uv needs to go up one level since we are in scripts/
    # %~dp0 is scripts/, .. goes to root, then uv/uv.exe
    bat_content = (
        "@echo off\n"
        'cd /d "%~dp0\\.."\n'
        '"%~dp0\\..\\uv\\uv.exe" run main.py\n'
        "if %errorlevel% neq 0 pause\n"
    )

    with open(scripts_dir / "run_skill_reroller.bat", "w") as f:
        f.write(bat_content)


def create_notices():
    """Creates ThirdPartyNotices.txt."""
    print("Creating ThirdPartyNotices.txt...")
    notices = (
        "Third Party Notices\n"
        "===================\n\n"
        "This software includes the following third-party software:\n\n"
        "1. uv\n"
        "   - Website: https://github.com/astral-sh/uv\n"
        "   - License: MIT License / Apache License 2.0\n"
        "   - Copyright (c) 2024 Astral Software Inc.\n"
        "   - The full license text can be found in the 'uv/LICENSE-MIT' file.\n\n"
        "2. PaddleOCR dependencies (downloaded at runtime)\n"
        "   - Please refer to https://github.com/PaddlePaddle/PaddleOCR for details.\n"
    )
    with open(DIST_DIR / "ThirdPartyNotices.txt", "w", encoding="utf-8") as f:
        f.write(notices)


def create_zip():
    """Zips the dist directory."""
    zip_filename = f"{OUTPUT_ZIP_NAME}.zip"
    zip_path = PROJECT_ROOT / zip_filename
    print(f"Creating ZIP archive: {zip_path}")

    shutil.make_archive(str(PROJECT_ROOT / OUTPUT_ZIP_NAME), "zip", DIST_DIR)
    print(f"Done! Distribution created at: {zip_path}")


def main():
    clean_dist()
    setup_uv()
    copy_project_files()
    create_run_bat()
    create_notices()
    create_zip()


if __name__ == "__main__":
    main()
