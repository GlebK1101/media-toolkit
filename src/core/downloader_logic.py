# src/core/downloader_logic.py
import yt_dlp
import os
import time
import gc
import subprocess
import sys
import re

class YtLogger:
    def __init__(self, log_callback, stop_callback=None):
        self.log_func = log_callback
        self.stop_callback = stop_callback 

    def debug(self, msg):
        if any(x in msg for x in ["has already been downloaded", "File is already existing", "already exists"]):
            self.log_func(f"⚠️ Skipped: File already exists.", replace=False)
            self.log_func("-"*80, replace=False)
            if self.stop_callback:
                self.stop_callback(reason="exists")

    def warning(self, msg):
        if "JavaScript runtime" in msg or "Only deno is enabled" in msg:
            return
        self.log_func(f"⚠️ Warning: {msg}", replace=False)
        self.log_func("-"*80, replace=False)

    def error(self, msg):
        self.log_func(f"❌ Error: {msg}", replace=False)
        self.log_func("-"*80, replace=False)


class DownloadLogic:
    # Константы для временных расширений
    TEMP_EXTENSIONS = ('.ytdl', '.temp', '.frag')
    
    def __init__(self, log_callback):
        self.log = log_callback
        self.ffmpeg_path = os.path.abspath(os.path.join("bin"))
        self.is_cancelled = False
        self.skip_remaining = False
        self.download_phase = 1  # 1=Video, 2=Audio, 3=Merge
        self.mode = 'video'
        self.keep_sound = True
        self.active_save_path = None
        self.pre_existing_files = set()

    def stop_download(self):
        self.is_cancelled = True

    def _notify_stop(self, reason):
        if reason == "exists":
            self.skip_remaining = True

    def _format_size(self, bytes_val):
        if not bytes_val: 
            return "0.00"
        return f"{bytes_val / 1024 / 1024:.2f}"

    def _kill_ffmpeg_processes(self):
        try:
            cmd = ['taskkill', '/F', '/IM', 'ffmpeg.exe'] if sys.platform == 'win32' else ['pkill', '-9', 'ffmpeg']
            subprocess.run(cmd, capture_output=True, timeout=5)
        except Exception:
            pass

    def _get_progress_prefix(self):
        if self.mode == 'audio':
            return "Downloading Audio:"
        elif self.mode == 'video' and self.keep_sound:
            if self.download_phase == 1:
                return "Downloading Video Track:"
            elif self.download_phase == 2:
                return "Downloading Audio Track:"
        return "Downloading Video:"

    def progress_hook(self, d):
        if self.is_cancelled:
            raise ValueError("DownloadCancelled")

        status = d.get('status')
        
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            percent = (downloaded / total * 100) if total else 0
            
            prefix = self._get_progress_prefix()
            msg = f"{prefix} {percent:.1f}% | Size: {self._format_size(total)} MiB | Speed: {self._format_size(speed)} MiB/s"
            self.log(msg, replace=True)

        elif status == 'finished':
            if self.mode == 'video' and self.keep_sound:
                if self.download_phase == 1:
                    self.log("✅ Done. Fetching Audio track...", replace=True)
                    self.download_phase = 2
                elif self.download_phase == 2:
                    self.log("✅ Done. Merging Video and Audio...", replace=True)
                    self.download_phase = 3 
            else:
                self.log("✅ Done. Finalizing...", replace=True)

    def _is_temp_file(self, filename):
        return (filename.endswith(".part") or 
                ".part" in filename or 
                any(filename.endswith(ext) for ext in self.TEMP_EXTENSIONS))

    def _cleanup_files(self, final_file=None):
        if not self.active_save_path or not os.path.exists(self.active_save_path):
            return

        self._kill_ffmpeg_processes()
        gc.collect()
        time.sleep(0.5)
        
        for attempt in range(5):
            time.sleep(0.5 + (attempt * 0.5))
            
            try:
                current_files = set(os.listdir(self.active_save_path))
                new_files = current_files - self.pre_existing_files
                deleted_count = 0
                
                for f_name in new_files:
                    full_path = os.path.join(self.active_save_path, f_name)
                    
                    # Не удаляем финальный файл
                    if final_file:
                        try:
                            if os.path.samefile(full_path, final_file):
                                continue
                        except (OSError, ValueError):
                            pass
                    
                    # Удаляем только временные файлы
                    if self._is_temp_file(f_name):
                        try:
                            if os.path.exists(full_path):
                                if sys.platform == 'win32':
                                    try:
                                        os.chmod(full_path, 0o777)
                                    except:
                                        pass
                                
                                os.remove(full_path)
                                deleted_count += 1
                        except OSError:
                            pass
                
                # Выход если временных файлов больше нет
                remaining = set(os.listdir(self.active_save_path)) - self.pre_existing_files
                has_parts = any(".part" in f for f in remaining)
                
                if not has_parts or (deleted_count == 0 and attempt > 1):
                    break
            except Exception:
                pass

    def _extract_video_title_from_url(self, url):
        # Метод 1: YouTube ID
        youtube_patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be/([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                return f"Video_{match.group(1)}"
            
        twitter_pattern = r'(?:twitter\.com|x\.com)/[^/]+/status/(\d+)'
        match = re.search(twitter_pattern, url)
        if match:
            return f"X_Video_{match.group(1)}"
        
        # Метод 2: Последняя часть URL
        try:
            url_parts = url.rstrip('/').split('/')
            if url_parts:
                last_part = url_parts[-1].split('?')[0].split('&')[0]
                if last_part and len(last_part) > 3:
                    return last_part
        except:
            pass
        
        return "Unknown Title"

    def _build_ydl_opts(self, save_path, filename, overwrite, quality, video_ext, audio_ext):
        ydl_opts = {
            'ffmpeg_location': self.ffmpeg_path,
            'paths': {'home': save_path},
            'progress_hooks': [self.progress_hook],
            'quiet': True,
            'no_warnings': True,
            'logger': YtLogger(self.log, self._notify_stop),
            'overwrites': overwrite,     
            'force_overwrites': overwrite,
            'outtmpl': f"{filename}.%(ext)s" if filename else "%(title)s.%(ext)s",
            'cookiefile': ('cookies.txt') 
        }

        if self.mode == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            post_proc = {'key': 'FFmpegExtractAudio', 'preferredcodec': audio_ext}
            if audio_ext == 'mp3':
                post_proc['preferredquality'] = '192'
            ydl_opts['postprocessors'] = [post_proc]
        
        elif self.mode == 'video':
            height_rule = f"[height<={quality[:-1]}]" if quality != 'Best' else ""
            video_rule = f"bestvideo{height_rule}[vcodec!*=av01]"
            
            if self.keep_sound:
                if video_ext == 'mp4':
                    ydl_opts['format'] = f"{video_rule}+bestaudio[ext=m4a]/{video_rule}+bestaudio/best"
                    ydl_opts['merge_output_format'] = 'mp4'
                elif video_ext == 'webm':
                    # пытаемся найти webm-дорожки и если их нет, берем лучшие доступные
                    ydl_opts['format'] = f"{video_rule}[ext=webm]+bestaudio[ext=webm]/{video_rule}+bestaudio/best"
                    # сливаем в контейнер MKV, чтобы избежать краша
                    ydl_opts['merge_output_format'] = 'mkv'
                    # корректно конвертируем итог в webm
                    ydl_opts['postprocessors'] =[{'key': 'FFmpegVideoConvertor', 'preferedformat': 'webm'}]
                    # это будет реально долго, но хоть как то.
                else:
                    ydl_opts['format'] = f"{video_rule}+bestaudio/best"
                    ydl_opts['merge_output_format'] = video_ext
            else:
                ydl_opts['format'] = video_rule
                ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': video_ext}]
        
        return ydl_opts

    def _get_final_filename(self, info, ydl, audio_ext, video_ext):
        if 'requested_downloads' in info:
            return info['requested_downloads'][0]['filepath']
        
        final_filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(final_filename)
        
        if self.mode == 'audio':
            return f"{base}.{audio_ext}"
        elif self.mode == 'video' and self.keep_sound:
            return f"{base}.{video_ext}"
        
        return final_filename

    def run_download(self, params):
        self.is_cancelled = False
        self.skip_remaining = False
        
        url = params['url']
        
        if "x.com/" in url or "twitter.com/" in url:
            url = url.replace("x.com/", "twitter.com/") 
            if "?" in url:
                url = url.split("?")[0]
        
        save_path = params['path'] or os.path.join(os.getcwd(), "_output\\downloads")
        filename = params['filename']
        quality = params['quality']
        video_ext = params['video_ext']
        audio_ext = params['audio_ext']
        self.mode = params['mode']
        self.keep_sound = params['keep_video_sound']
        overwrite = params['overwrite'] 
        
        self.active_save_path = save_path
        self.download_phase = 1

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        try:
            self.pre_existing_files = set(os.listdir(save_path))
        except:
            self.pre_existing_files = set()

        self.log("Fetching info...", replace=True)
        
        video_title = "Unknown Title"
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'logger': YtLogger(lambda x, r=False: None)}) as ydl_info:
                info_dict = ydl_info.extract_info(url, download=False)
                video_title = info_dict.get('title', url)
        except Exception:
            video_title = self._extract_video_title_from_url(url)

        type_str = "Video" if self.mode == 'video' else "Audio"
        
        if self.mode == 'video':
            snd_str = "Sound: ON" if self.keep_sound else "Sound: OFF"
            settings_str = f"{video_ext}, {quality}, {snd_str}"
        else:
            q_str = "192kbps" if audio_ext == 'mp3' else "Native"
            settings_str = f"{audio_ext}, {q_str}"

        self.log(f"{type_str}: {video_title}  |  Format: [{settings_str}]", replace=False)
        self.log(f"Downloading to: [{save_path}]", replace=False)
        self.log("Starting download...", replace=True)

        # Проверка существования файла (избегаем лишних запросов к серверу)
        expected_ext = video_ext if self.mode == 'video' else audio_ext
        
        # указал имя - проверяем его
        if filename:
            full_path = os.path.join(save_path, f"{filename}.{expected_ext}")
            if os.path.exists(full_path) and not overwrite:
                self.log(f"⚠️ Skipped: File already exists.")
                self.log("-"*80, replace=False)
                return
        # Если имя не указано - пытаемся использовать video_title
        elif video_title and video_title != "Unknown Title" and not video_title.startswith("Video_"):
            # Очищаем название от недопустимых символов для имени файла
            safe_title = "".join(c for c in video_title if c not in r'\/:*?"<>|').strip()
            full_path = os.path.join(save_path, f"{safe_title}.{expected_ext}")
            if os.path.exists(full_path) and not overwrite:
                self.log(f"⚠️ Skipped: File already exists.")
                self.log("-"*80, replace=False)
                return
        
        # Если файл существует и overwrite=True, сообщаем об этом
        if filename and os.path.exists(os.path.join(save_path, f"{filename}.{expected_ext}")) and overwrite:
            self.log(f"ℹ️File exists. Overwriting...")

        # Настройки и запуск
        ydl_opts = self._build_ydl_opts(save_path, filename, overwrite, quality, video_ext, audio_ext)
        ydl = None
        final_filename = None
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                except yt_dlp.utils.DownloadError as e:
                    if self.skip_remaining or "already exists" in str(e): 
                        return 
                    raise e
                
                if self.skip_remaining: 
                    return

                final_filename = self._get_final_filename(info, ydl, audio_ext, video_ext)

            # Вывод результата
            if final_filename and os.path.exists(final_filename):
                size_bytes = os.path.getsize(final_filename)
                filename_only = os.path.basename(final_filename)
                
                prefix = "✅ Done. Finalizing..."
                if self.mode == 'video' and self.keep_sound:
                    prefix = "✅ Done. Merging Video and Audio..."
                
                success_msg = f"{prefix} SUCCESS! \nSaved to {filename_only} [{self._format_size(size_bytes)} MiB]"
                self.log(success_msg, replace=False) 
                self.log("-"*80, replace=False)
                
                if ydl:
                    del ydl
                gc.collect()
                self._cleanup_files(final_file=final_filename)

        except ValueError as ve:
            if "DownloadCancelled" in str(ve):
                self.log("🛑 Download CANCELLED.")
                self.log("-"*80, replace=False)
                
                if ydl: 
                    del ydl
                gc.collect()
                self._cleanup_files()
            else:
                self.log(f"❌ Error: {str(ve)}")
                self.log("-"*80, replace=False)
        
        except yt_dlp.utils.DownloadError:
            if ydl:
                del ydl
            gc.collect()
            self._cleanup_files()
        
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            self.log("-"*80, replace=False)
            
            if ydl:
                del ydl
            gc.collect()
            self._cleanup_files()