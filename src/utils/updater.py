# src/utils/updater.py
import subprocess
import sys
from importlib.metadata import version, PackageNotFoundError

def get_current_version(package_name="yt-dlp"):
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "Not installed"

def update_yt_dlp(log_callback=None):
    package = "yt-dlp"
    current_ver = get_current_version(package)
    
    if log_callback:
        log_callback(f"Checking for updates... (Current: {current_ver})", replace=False)
    
    try:
        # Запускаем обновление
        # --disable-pip-version-check убирает желтые предупреждения самого pip
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package, "--disable-pip-version-check"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(result.stderr)

        if "Requirement already satisfied" in result.stdout:
            if log_callback:
                log_callback(f"{package} is up to date.", replace=False)
        else:
            new_ver = get_current_version(package)
            if log_callback:
                log_callback(f"Updated successfully to {new_ver}!", replace=False)
                
    except Exception as e:
        if log_callback:
            log_callback(f"Update check failed: {str(e)}", replace=False)