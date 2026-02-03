# src/core/editor_logic.py
import os
import subprocess
import sys
import numpy as np
import re

class EditorLogic:
    def __init__(self, log_callback):
        self.log = log_callback
        self.preview_process = None
        self.process = None
        
        project_root = os.getcwd()
        local_bin = os.path.join(project_root, "bin")
        exe_ext = ".exe" if sys.platform == "win32" else ""
        
        self.ffmpeg_path = os.path.join(local_bin, f"ffmpeg{exe_ext}")
        self.ffplay_path = os.path.join(local_bin, f"ffplay{exe_ext}")
        self.ffprobe_path = os.path.join(local_bin, f"ffprobe{exe_ext}")
        
        if not os.path.exists(self.ffmpeg_path): self.ffmpeg_path = "ffmpeg"
        if not os.path.exists(self.ffplay_path): self.ffplay_path = "ffplay"
        if not os.path.exists(self.ffprobe_path): self.ffprobe_path = "ffprobe"

    def _get_startup_info(self):
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return si
        return None

    def get_duration(self, file_path):
        cmd = [self.ffprobe_path, "-v", "error", "-show_entries", 
               "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=self._get_startup_info())
            return float(result.stdout.strip())
        except:
            return 0.0

    def get_waveform_exact(self, file_path):
        target_sr = 10000 
        cmd = [
            self.ffmpeg_path, "-i", file_path, "-ac", "1", "-ar", str(target_sr),   
            "-map", "0:a", "-c:a", "pcm_s16le", "-f", "s16le", "-"
        ]
        
        self.log("ℹ️Building waveform...", replace=False)
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, 
                bufsize=10**7, startupinfo=self._get_startup_info()
            )
            raw_data, _ = process.communicate()
            audio_data = np.frombuffer(raw_data, dtype=np.int16)
            
            if len(audio_data) == 0: return np.array([]), 0.0
            
            real_duration = len(audio_data) / target_sr
            max_val = float(np.max(np.abs(audio_data)))
            if max_val == 0: max_val = 1.0
            norm_data = np.abs(audio_data) / max_val
            
            return norm_data, real_duration
            
        except Exception as e:
            self.log(f"❌ Error: {e}", replace=False)
            return np.array([]), 0.0

    def start_preview(self, input_path, start, end, volume=1.0, loop=False):
        self.stop_preview()
        cmd = [self.ffplay_path, "-nodisp", "-autoexit", "-hide_banner"]
        cmd.extend(["-ss", str(start)])
        
        filters = []
        if abs(volume - 1.0) > 0.01: filters.append(f"volume={volume}")
        if filters: cmd.extend(["-af", ",".join(filters)])
            
        if loop: cmd.extend(["-loop", "0"])
            
        duration = end - start
        if duration > 0: cmd.extend(["-t", str(duration)])
        cmd.append(input_path)
        
        try:
            self.preview_process = subprocess.Popen(cmd, startupinfo=self._get_startup_info())
        except Exception as e:
            self.log(f"❌ Preview error: {e}")
            self.log("-" * 80, replace=False)

    def stop_preview(self):
        if self.preview_process:
            try: self.preview_process.kill()
            except: pass
            self.preview_process = None

    def _parse_time_to_seconds(self, time_str):
        try:
            # HH:MM:SS.ms
            parts = time_str.split(':')
            h = int(parts[0])
            m = int(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        except:
            return 0.0

    def cancel(self):
        self.is_cancelled = True
        if self.process:
            self.log("🛑 Stopping process...", replace=False)
            try:
                self.process.kill()
            except:
                pass
    
    def run_cut(self, params):
        self.is_cancelled = False
        in_path = params['input_path']
        out_path = params['output_path']
        start = params['start']
        end = params['end']
        volume = params['volume']
        overwrite = params['overwrite']
        
        # Проверка на совпадение входного и выходного файла
        if os.path.abspath(in_path) == os.path.abspath(out_path):
            self.log("❌ Error: Input and Output files cannot be the same!", replace=False)
            self.log("Please change the output name or folder.", replace=False)
            self.log("-" * 80, replace=False)
            return

        if os.path.exists(out_path) and not overwrite:
            self.log("ℹ️File exists. Overwrite OFF.", replace=False)
            self.log("-" * 80, replace=False)
            return

        _, ext = os.path.splitext(out_path)
        ext = ext.lower()

        cmd = [self.ffmpeg_path, "-y"]
        cmd.extend(["-ss", str(start)])
        cmd.extend(["-t", str(end - start)])
        cmd.extend(["-i", in_path])
        
        # Audio Volume filter
        if abs(volume - 1.0) > 0.01:
            cmd.extend(["-af", f"volume={volume}"])
        
        # -(Settings)-
        # Audio Codecs
        if ext == '.mp3': cmd.extend(["-c:a", "libmp3lame", "-q:a", "2"])
        elif ext == '.m4a': cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        elif ext == '.wav': cmd.extend(["-c:a", "pcm_s16le"])
        elif ext == '.flac': cmd.extend(["-c:a", "flac"])
        elif ext == '.ogg': cmd.extend(["-c:a", "libvorbis", "-q:a", "6"])
        elif ext == '.webm': cmd.extend(["-c:a", "libvorbis", "-q:a", "6"])
        else: cmd.extend(["-c:a", "aac", "-b:a", "192k"])
            
        # Video Handling
        video_containers = ['.mp4', '.mkv', '.mov', '.avi', '.webm', '.flv', '.wmv']
        
        # point:video_cut  это своеобразная метка для навигации
        if ext in video_containers:
            # вот тут у нас возникает интересный момент! 
            # Видеофайл не хранит каждый кадр как полноценную картинку. 
            # Он хранит один полный кадр (I-frame или ключевой кадр) раз в несколько секунд, 
            # а остальные кадры --- это просто информация о том, что изменилось по сравнению с предыдущим.
            # Рассмотрим на примере: пытаемся сделать обрезку с 30.5 секунды. FFmpeg ищет ближайший ключевой кадр. Допустим, он находится на 28.0 секунде.
            # FFmpeg вынужден начать видеопоток с 28.0 секунды (иначе картинка рассыпется), но аудио он режет честно с 30.5.
            # Итог: Видео начинается раньше звука. Плеер пытается это компенсировать: он "морозит" первый кадр или показывает черный экран эти 2.5 секунды, 
            # пока аудио не догонит видео по времени. Отсюда рассинхрон и странная длительность.
            # Может вы этого и не заметите на коротких видео, но на длинных для экономии места ключевые кадры ставят реже (раз в 5-10 секунд). Шанс не попасть в разрез увеличивается.
            # -----------------------
            # cmd.extend(["-c:v", "copy"]) # поэтому эту строку комментируем и используем альтернативу ниже
            # -----------------------
            # Вместо copy используем перекодирование для точности
            # -preset ultrafast: максимально быстрое кодирование (жертвуем размером ради скорости)
            # -crf 23: стандартное качество (лично я не особо различаю 23 и ~30). Чем меньше поставито (до 51 включительно), тем меньше размер выходного файла.
            # -max_muxing_queue_size 1024: помогает избежать ошибок буфера на длинных видео
            cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-max_muxing_queue_size", "1024"])
            # Сбрасываем таймстампы, чтобы избежать черных экранов в начале
            cmd.extend(["-avoid_negative_ts", "make_zero"])
            # Если что, то видео будет начинаться ровно с выбранной миллисекунды. 
            # Так как мы используем -ss перед входом, перекодироваться будет только вырезанный кусок, а не весь фильм, так что должно быть приемлемо.
            # -----------------------
        else:
            cmd.append("-vn") 
        
        cmd.append(out_path)
        
        self.log(f"ℹ️Saving: {os.path.basename(out_path)}", replace=False)
        self.log(f"ℹ️Range: {start:.2f}-{end:.2f}s | Vol: {volume}", replace=False)
        
        try:
            self.process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace',
                startupinfo=self._get_startup_info()
            )
            
            total_duration = end - start
            
            while True:
                if self.is_cancelled:
                    self.process.kill()
                    self.log("🛑 Cancelled.")
                    if os.path.exists(out_path):
                        try: os.remove(out_path)
                        except: pass
                    return

                line = self.process.stderr.readline()
                if not line and self.process.poll() is not None: break
                
                # Progress parsing
                if "time=" in line:
                    match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line)
                    if match and total_duration > 0:
                        current_seconds = self._parse_time_to_seconds(match.group(1))
                        percent = (current_seconds / total_duration) * 100
                        self.log(f"Processing: {percent:.1f}%", replace=True)

            if self.process.returncode == 0:
                self.log(f"✅ Success!", replace=False)
                self.log("-" * 80, replace=False)
            else:
                self.log("❌ Error.", replace=False)
                self.log("-" * 80, replace=False)
                
        except Exception as e:
            self.log(f"❌ Exception: {e}", replace=False)
            self.log("-" * 80, replace=False)
        finally:
            self.process = None