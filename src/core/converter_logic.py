# src/core/converter_logic.py
import os
import subprocess
import re
import sys
import time

class ConverterLogic:
    def __init__(self, log_callback):
        self.log = log_callback
        self.process = None
        self.is_cancelled = False
        
        # Поиск ffmpeg
        project_root = os.getcwd()
        local_bin = os.path.join(project_root, "bin")
        exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        self.ffmpeg_path = os.path.join(local_bin, exe_name)
        
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = "ffmpeg"

    def stop_conversion(self):
        self.is_cancelled = True
        if self.process:
            self.log("ℹ️Stopping conversion process...", replace=False)
            try:
                self.process.terminate()  # Сначала пробуем мягкое завершение
                time.sleep(0.5)
                if self.process.poll() is None:
                    self.process.kill()  # Если не помогло - жёсткое
            except Exception as e:
                self.log(f"❌ Error stopping process: {e}", replace=False)
                self.log("-"*80, replace=False)

    def _get_file_size_str(self, path):
        try:
            size = os.path.getsize(path) / (1024 * 1024)
            return f"[{size:.2f} MiB]"
        except Exception:
            return "[? MiB]"
    
    def _get_duration(self, file_path):
        cmd = [self.ffmpeg_path, "-i", file_path]
        try:
            result = subprocess.run(
                cmd, 
                stderr=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                text=True, 
                encoding='utf-8', 
                errors='replace',
                timeout=10  # Таймаут для избежания зависания
            )
            match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.\d+", result.stderr)
            if match:
                h, m, s = map(int, match.groups())
                return h * 3600 + m * 60 + s
        except Exception as e:
            self.log(f"⚠️ Warning: Could not get duration: {e}", replace=False)
            self.log("-"*80, replace=False)
        return 0

    
    def _parse_time_to_seconds(self, time_str):
        try:
            parts = time_str.split(':')
            h = int(parts[0])
            m = int(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        except Exception:
            return 0

    def run_convert(self, params):
        self.is_cancelled = False
        input_path = params['input_path']
        output_folder = params['output_folder']
        target_ext = params['format']
        output_name = params.get('output_name', '')
        overwrite = params.get('overwrite', False)
        
        # Параметры для батч-режима (для логов)
        batch_mode = params.get('batch_mode', False)
        batch_current = params.get('batch_current', 0)
        batch_total = params.get('batch_total', 0)

        # Проверка существования входного файла
        if not os.path.exists(input_path):
            self.log(f"❌ Error: Input file not found: {input_path}", replace=False)
            self.log("-" * 80, replace=False)
            return

        # Имя исходного файла
        src_filename = os.path.basename(input_path)
        src_ext = os.path.splitext(src_filename)[1]
        
        # ================= PRE-CONVERSION ANALYSIS =================
        LOSSY_VIDEO = {'.mp4', '.avi', '.webm', '.mov'}

        src_ext = src_ext.lower()
        target_ext = target_ext.lower()

        # 1. Конвертация "в самого себя"
        if src_ext == target_ext:
            self.log("ℹ️Info: Same format detected. Stream copy will be used (no quality loss).", replace=False)
            
        # 2. Потенциальная деградация (lossy → lossy, но формат меняется)
        elif src_ext in LOSSY_VIDEO and target_ext in LOSSY_VIDEO:
            self.log("⚠️ Warning: lossy → lossy conversion. Quality degradation expected.", replace=False)
        
        # Определение имени выходного файла
        if output_name:
            name_no_ext = output_name
        else:
            name_no_ext = os.path.splitext(src_filename)[0]

        # Создаем папку вывода
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                self.log(f"❌ Error creating folder: {e}", replace=False)
                self.log("-" * 80, replace=False)
                return

        output_path = os.path.join(output_folder, f"{name_no_ext}{target_ext}")
        
        # --- ЛОГИКА ОБНАРУЖЕНИЕ (ШАПКА) ---
        input_size_str = self._get_file_size_str(input_path)

        if batch_mode:
            self.log(f"[{batch_current}/{batch_total}]", replace=False)
            self.log(f"Converting: {src_filename} {input_size_str}", replace=False)
            self.log(f"Format: {src_ext} ---> {target_ext}", replace=False)
        else:
            self.log(f"Converting: {src_filename} {input_size_str}", replace=False)
            self.log(f"Format: {src_ext} ---> {target_ext}", replace=False)
            self.log(f"Folder: {output_folder}", replace=False)

        # Проверка существования выходного файла
        if os.path.exists(output_path):
            if not overwrite:
                self.log(f"⚠️ Skipped: File exists (Overwrite OFF).", replace=False)
                self.log("-" * 80, replace=False)
                return
            else:
                # Проверяем, не тот ли это же самый файл
                if os.path.abspath(input_path) == os.path.abspath(output_path):
                    self.log(f"⚠️ Skipped: Input and output are the same file.", replace=False)
                    self.log("-" * 80, replace=False)
                    return
                # Удаляем существующий файл перед конвертацией
                try:
                    os.remove(output_path)
                except Exception as e:
                    self.log(f"❌ Error removing existing file: {e}", replace=False)
                    self.log("-" * 80, replace=False)
                    return

        # Получаем длительность
        total_duration = self._get_duration(input_path)

        # Команда FFmpeg
        cmd = [self.ffmpeg_path, "-y", "-i", input_path]

        # ================= SMART CONVERSION LOGIC =================

        # определяем: тот же формат или нет
        same_format = src_ext.lower() == target_ext.lower()
        
        # -(Settings)-
        # ---------- AUDIO ONLY ----------
        if target_ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
            cmd.append("-vn")

            if same_format:
                # аудио ---> аудио, формат тот же --- просто копируем
                cmd.extend(["-c:a", "copy"])
            else:
                if target_ext == '.mp3':
                    cmd.extend(["-c:a", "libmp3lame", "-q:a", "2"])   # V0 approximately 190 kbps
                elif target_ext == '.m4a':
                    cmd.extend(["-c:a", "aac", "-b:a", "128k"])
                elif target_ext == '.wav':
                    cmd.extend(["-c:a", "pcm_s16le"])
                elif target_ext == '.flac':
                    cmd.extend(["-c:a", "flac"])
                elif target_ext == '.ogg':
                    cmd.extend(["-c:a", "libvorbis", "-q:a", "6"])

        # ---------- VIDEO ----------
        elif target_ext in ['.mp4', '.mkv', '.avi', '.webm', '.mov']:

            if same_format:
                # видео ---> видео, формат тот же --- STREAM COPY
                cmd.extend([
                    "-c:v", "copy",
                    "-c:a", "copy"
                ])

                # оптимизация mp4/mov
                if target_ext in ['.mp4', '.mov']:
                    cmd.extend(["-movflags", "+faststart"])

            else:
                # НАСТРОЙКИ СЖАТИЯ
                # Чем выше CRF, тем меньше размер и хуже качество.
                # CRF 23 = Стандарт.
                # CRF 28 = Оптимально для хранения (меньше вес).
                crf_value = "28" 
                preset_val = "slow" # <--- medium (быстро) или slow (компактно)

                if target_ext in ['.mp4', '.mov']:
                    cmd.extend([
                        "-c:v", "libx264",
                        "-preset", preset_val,
                        "-crf", crf_value,        
                        "-profile:v", "high",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "128k",            # 128k достаточно для большинства
                        "-movflags", "+faststart"
                    ])

                elif target_ext == '.mkv':
                    cmd.extend([
                        "-c:v", "libx264",
                        "-preset", preset_val,
                        "-crf", crf_value,
                        "-c:a", "aac",
                        "-b:a", "128k"
                    ])

                elif target_ext == '.webm':
                    cmd.extend([
                        "-c:v", "libvpx-vp9",
                        "-crf", "35",  # Для VP9 шкала другая, 35-40 оптимально для веса
                        "-b:v", "0",
                        "-c:a", "libopus",
                        "-b:a", "96k"  # Opus отличный даже на 96k
                    ])

                elif target_ext == '.avi':
                    # ВАЖНО: Мы используем libx264 в AVI. 
                    # Это нестандартно, но эффективно для размера.
                    cmd.extend([
                        "-c:v", "libx264",
                        "-preset", preset_val,
                        "-crf", crf_value,
                        "-profile:v", "baseline", # Для AVI лучше baseline для совместимости
                        "-level", "3.0",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "libmp3lame",     # MP3 совместимее для AVI
                        "-q:a", "4"               # VBR качество (~160kbps), экономит место в тишине
                    ])
                    
                elif target_ext == '.mp4':
                    cmd.extend([
                        "-c:v", "libx264",
                        "-preset", "slow",
                        "-crf", "21",
                        "-tune", "film",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-movflags", "+faststart"
                    ])

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

            # Чтение прогресса
            last_percent = -1
            while True:
                if self.is_cancelled:
                    self.process.terminate()
                    time.sleep(0.5)
                    if self.process.poll() is None:
                        self.process.kill()
                    self.log("🛑 Conversion cancelled.", replace=False)
                    self.log("-" * 80, replace=False)
                    # Удаляем незавершённый файл
                    if os.path.exists(output_path):
                        try: 
                            os.remove(output_path)
                        except: 
                            pass
                    return

                line = self.process.stderr.readline()
                if not line and self.process.poll() is not None:
                    break
                
                # Обновление прогресса
                if line and "time=" in line:
                    match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line)
                    if match and total_duration > 0:
                        current_seconds = self._parse_time_to_seconds(match.group(1))
                        percent = min((current_seconds / total_duration) * 100, 100)
                        # Обновляем только при изменении процента
                        if int(percent) != last_percent:
                            self.log(f"Processing: {percent:.1f}%", replace=True)
                            last_percent = int(percent)

            # Проверка результата
            if self.process.returncode == 0:
                out_size_str = self._get_file_size_str(output_path)
                final_name = os.path.basename(output_path)
                
                if batch_mode:
                    self.log(f"✅ Success. {out_size_str}", replace=True)
                else:
                    self.log(f"✅ Success: {final_name} {out_size_str}", replace=True)
                
                self.log("-" * 80, replace=False)
            else:
                if not self.is_cancelled:
                    self.log(f"❌ FFmpeg Error (code {self.process.returncode}).", replace=False)
                    self.log("-" * 80, replace=False)
        
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", replace=False)
            self.log("-" * 80, replace=False)
        finally:
            self.process = None

    def run_batch(self, params):
        input_folder = params['input_folder']
        output_folder = params['output_folder']
        target_ext = params['format']
        overwrite = params.get('overwrite', False)
        
        if not os.path.exists(input_folder):
            self.log("❌ Input folder not found.", replace=False)
            self.log("-" * 80, replace=False)
            return

        supported_exts = ('.mp4', '.mkv', '.avi', '.webm', '.mov', '.mp3', '.wav', '.m4a', '.flac', '.ogg')
        
        # Собираем файлы
        try:
            files = [f for f in os.listdir(input_folder) if f.lower().endswith(supported_exts)]
        except Exception as e:
            self.log(f"❌ Error reading folder: {e}", replace=False)
            self.log("-" * 80, replace=False)
            return
        
        if not files:
            self.log("⚠️ No supported media files found in folder.", replace=False)
            self.log("-" * 80, replace=False)
            return

        self.log(f"ℹ️Starting batch conversion for {len(files)} file(s)...", replace=False)
        self.log("-" * 80, replace=False)

        for i, filename in enumerate(files):
            if self.is_cancelled:
                self.log("🛑 Batch processing stopped by user.", replace=False)
                self.log("-" * 80, replace=False)
                break
            
            file_params = {
                'input_path': os.path.join(input_folder, filename),
                'output_folder': output_folder,
                'format': target_ext,
                'output_name': '',  # В батче имя оставляем оригинальным
                'overwrite': overwrite,
                'batch_mode': True,
                'batch_current': i + 1,
                'batch_total': len(files)
            }
            
            self.run_convert(file_params)
            
            if self.is_cancelled:
                break
            
        if not self.is_cancelled:
            self.log("✅ Batch conversion completed!", replace=False)
            self.log("-" * 80, replace=False)