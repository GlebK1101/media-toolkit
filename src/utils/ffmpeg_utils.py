# src/utils/ffmpeg_utils.py
import os
import shutil
import sys

def get_binary_path(binary_name):
    project_root = os.getcwd()
    local_bin = os.path.join(project_root, "bin")
    
    # Добавляем .exe для Windows
    if sys.platform == "win32" and not binary_name.endswith(".exe"):
        binary_name += ".exe"
    
    # Проверяем bin/
    local_path = os.path.join(local_bin, binary_name)
    if os.path.exists(local_path):
        return os.path.abspath(local_path)
        
    # Проверяем PATH
    global_path = shutil.which(binary_name)
    if global_path:
        return global_path
        
    return None

def check_ffmpeg(log_callback=None):
    ffmpeg = get_binary_path("ffmpeg")
    ffprobe = get_binary_path("ffprobe")
    ffplay = get_binary_path("ffplay")

    missing = []
    if not ffmpeg: missing.append("ffmpeg")
    if not ffprobe: missing.append("ffprobe")
    
    if log_callback:
        if not missing:
            log_callback(f"FFmpeg/Probe found.", replace=False)
            return True
        else:
            log_callback(f"❌ Critical: Missing {', '.join(missing)}", replace=False)
            return False
    return (len(missing) == 0)