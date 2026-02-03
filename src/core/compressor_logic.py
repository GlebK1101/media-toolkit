# src/core/compressor_logic.py
import os
import subprocess
import re
import sys

class CompressorLogic:
    def __init__(self, log_callback):
        self.log = log_callback
        self.process = None
        self.is_cancelled = False
        
        project_root = os.getcwd()
        local_bin = os.path.join(project_root, "bin")
        exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        self.ffmpeg_path = os.path.join(local_bin, exe_name)
        
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = "ffmpeg"

    def stop_process(self):
        self.is_cancelled = True
        if self.process:
            self.log("🛑 Stopping compression process...", replace=False)
            try:
                self.process.kill()
            except:
                pass

    def _get_file_size_str(self, path):
        try:
            size = os.path.getsize(path) / (1024 * 1024)
            return f"[{size:.2f} MiB]"
        except:
            return "[? MiB]"

    def _get_duration(self, file_path):
        cmd = [self.ffmpeg_path, "-i", file_path]
        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.\d+", result.stderr)
            if match:
                h, m, s = map(int, match.groups())
                return h * 3600 + m * 60 + s
        except:
            pass
        return 0

    def _parse_time_to_seconds(self, time_str):
        try:
            parts = time_str.split(':')
            h = int(parts[0])
            m = int(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        except:
            return 0

    def run_compress(self, params):
        self.is_cancelled = False
        input_path = params['input_path']
        output_folder = params['output_folder']
        crf_value = params['crf']
        resolution = params['resolution']
        output_name = params.get('output_name', '')
        overwrite = params.get('overwrite', False)
        
        batch_mode = params.get('batch_mode', False)
        batch_current = params.get('batch_current', 0)
        batch_total = params.get('batch_total', 0)

        if not os.path.exists(input_path):
            self.log(f"❌ Error: Input file not found: {input_path}", replace=False)
            self.log("-" * 80, replace=False)
            return

        src_filename = os.path.basename(input_path)
        src_name_no_ext, src_ext = os.path.splitext(src_filename)
        src_ext_lower = src_ext.lower()
        
        if output_name:
            final_name_no_ext = output_name
        else:
            final_name_no_ext = src_name_no_ext

        output_path = os.path.join(output_folder, f"{final_name_no_ext}{src_ext}")

        if not os.path.exists(output_folder):
            try: os.makedirs(output_folder)
            except: pass

        # --- ЛОГИРОВАНИЕ ---
        input_size_str = self._get_file_size_str(input_path)
        res_str = f"Res: {resolution}" if resolution != "Original" else "Res: Original"
        params_str = f"CRF: {crf_value} | {res_str}"

        if batch_mode:
            self.log(f"[{batch_current}/{batch_total}]", replace=False)
            self.log(f"Compressing: {src_filename} {input_size_str}", replace=False)
            self.log(f"Settings: {params_str}", replace=False)
        else:
            self.log(f"Compressing: {src_filename} {input_size_str}", replace=False)
            self.log(f"Settings: {params_str}", replace=False)
            self.log(f"Folder: {output_folder}", replace=False)

        # --- ЗАЩИТА ОТ ПЕРЕЗАПИСИ САМОГО СЕБЯ ---
        if os.path.abspath(input_path) == os.path.abspath(output_path):
            self.log("""❌ CRITICAL ERROR: Input and Output paths are identical!
    Cannot overwrite source file during compression.
    Please change output folder or filename.""", replace=False)
            self.log("-" * 80, replace=False)
            return

        if os.path.exists(output_path) and not overwrite:
            self.log(f"⚠️ Skipped: File exists (Overwrite OFF).", replace=False)
            self.log("-" * 80, replace=False)
            return

        total_duration = self._get_duration(input_path)

        # Команда FFmpeg
        cmd = [self.ffmpeg_path, "-y", "-i", input_path]
        
        # -(Settings)-
        if src_ext_lower == '.webm':
            # WebM не поддерживает H.264/AAC. Используем VP9/Opus.
            # Для VP9 CRF работает так же (0-63), но нам нужно добавить -b:v 0, чтобы включить режим CRF.
            cmd.extend(["-c:v", "libvpx-vp9", "-crf", str(int(crf_value)), "-b:v", "0"])
            # Аудио для WebM
            cmd.extend(["-c:a", "libopus"])
        
        elif src_ext_lower == '.gif':
            # GIF - особый случай, его нельзя сжать через CRF x264
            self.log("⚠️ GIF compression not supported in this mode.", replace=False)
            return
        
        else:
            # Для всего остального (mp4, mkv, avi, mov, flv...) используем H.264 (лучшая совместимость)
            # Внимание: Если исходник AVI или WMV, запись в них H.264 может быть нестабильной, но FFmpeg обычно справляется. 
            cmd.extend(["-c:v", "libx264", "-crf", str(int(crf_value)), "-preset", "medium"])
            # Аудио
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        # Разрешение
        if resolution != "Original":
            height = resolution.replace('p', '')
            # scale=-2:HEIGHT сохраняет пропорции
            cmd.extend(["-vf", f"scale=-2:{height}"])

        cmd.append(output_path)

        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            self.process = subprocess.Popen(
                cmd, 
                stderr=subprocess.PIPE, 
                stdout=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo
            )

            while True:
                if self.is_cancelled:
                    self.process.kill()
                    self.log("🛑 Compression cancelled.", replace=False)
                    self.log("-" * 80, replace=False)
                    if os.path.exists(output_path):
                        try: os.remove(output_path)
                        except: pass
                    return

                line = self.process.stderr.readline()
                if not line and self.process.poll() is not None:
                    break
                
                if line and "time=" in line:
                    match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line)
                    if match and total_duration > 0:
                        current_seconds = self._parse_time_to_seconds(match.group(1))
                        percent = (current_seconds / total_duration) * 100
                        self.log(f"Processing: {percent:.1f}%", replace=True)

            if self.process.returncode == 0:
                out_size_str = self._get_file_size_str(output_path)
                final_name = os.path.basename(output_path)
                
                if batch_mode:
                    self.log(f"✅ Success.", replace=True)
                else:
                    self.log(f"✅ Success: {final_name} {out_size_str}", replace=True)
                
                self.log("-" * 80, replace=False)
            else:
                if not self.is_cancelled:
                    self.log(f"❌ FFmpeg Error. Format/Codec mismatch?", replace=False)
                    self.log("-" * 80, replace=False)
        
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", replace=False)
            self.log("-" * 80, replace=False)
        finally:
            self.process = None

    def run_batch(self, params):
        input_folder = params['input_folder']
        output_folder = params['output_folder']
        crf = params['crf']
        resolution = params['resolution']
        overwrite = params.get('overwrite', False)
        
        if not os.path.exists(input_folder):
            self.log("❌ Error: Input folder not found.", replace=False)
            self.log("-" * 80, replace=False)
            return

        # РАСШИРЕННЫЙ СПИСОК ФАЙЛОВ
        supported_exts = (
            '.mp4', '.mkv', '.avi', '.webm', '.mov', '.m4v', 
            '.flv', '.wmv', '.3gp', '.mpg', '.mpeg', '.ts', '.m2ts', '.vob'
        )
        files = [f for f in os.listdir(input_folder) if f.lower().endswith(supported_exts)]
        
        if not files:
            self.log("⚠️ No supported video files found.", replace=False)
            self.log("-" * 80, replace=False)
            return

        # Проверка на совпадение папок (так как расширение сохраняется, это фатально)
        if os.path.abspath(input_folder) == os.path.abspath(output_folder):
            self.log("""❌ BATCH ERROR: Input and Output folders are identical!
    Compressor preserves file extensions (e.g. .mp4 -> .mp4).
    Saving to the same folder would overwrite source files.
    Please select a different output folder.""", replace=False)
            self.log("-" * 80, replace=False)
            return

        self.log(f"ℹ️Starting batch compression for {len(files)} files...", replace=False)
        self.log("-" * 80, replace=False)

        for i, filename in enumerate(files):
            if self.is_cancelled:
                self.log("🛑 Batch processing stopped.", replace=False)
                self.log("-" * 80, replace=False)
                break
            
            file_params = {
                'input_path': os.path.join(input_folder, filename),
                'output_folder': output_folder,
                'output_name': '', 
                'crf': crf,
                'resolution': resolution,
                'overwrite': overwrite,
                'batch_mode': True,
                'batch_current': i + 1,
                'batch_total': len(files)
            }
            
            self.run_compress(file_params)
            
        if not self.is_cancelled:
            self.log("✅ All files processed!", replace=False)
            self.log("-" * 80, replace=False)