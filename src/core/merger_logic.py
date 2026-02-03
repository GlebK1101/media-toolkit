# src/core/merger_logic.py
import os
import subprocess
import sys
import json
import re

class MergerLogic:
    def __init__(self, log_callback):
        self.log = log_callback
        self.active_processes = []
        self.is_cancelled = False
        
        project_root = os.getcwd()
        local_bin = os.path.join(project_root, "bin")
        exe_ext = ".exe" if sys.platform == "win32" else ""
        
        self.ffmpeg_path = os.path.join(local_bin, f"ffmpeg{exe_ext}")
        self.ffprobe_path = os.path.join(local_bin, f"ffprobe{exe_ext}")
        
        if not os.path.exists(self.ffmpeg_path): self.ffmpeg_path = "ffmpeg"
        if not os.path.exists(self.ffprobe_path): self.ffprobe_path = "ffprobe"

    def _get_startup_info(self):
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return si
        return None

    def cancel(self):
        self.is_cancelled = True
        for p in self.active_processes:
            try:
                p.kill()
            except:
                pass
        self.active_processes.clear()

    def probe_file(self, file_path):
        cmd = [
            self.ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', startupinfo=self._get_startup_info())
            data = json.loads(res.stdout)
            
            duration = float(data['format'].get('duration', 0))
            has_video = any(s['codec_type'] == 'video' for s in data.get('streams', []))
            has_audio = any(s['codec_type'] == 'audio' for s in data.get('streams', []))
            size_bytes = os.path.getsize(file_path)
            
            return {
                'duration': duration, 
                'has_video': has_video, 
                'has_audio': has_audio,
                'size': size_bytes
            }
        except Exception as e:
            self.log(f"❌ Probe error {os.path.basename(file_path)}: {e}")
            self.log("-" * 80, replace=False)
            return None

    def _parse_time_to_seconds(self, time_str):
        try:
            parts = time_str.split(':')
            h = int(parts[0])
            m = int(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        except:
            return 0.0
    
    def _format_size(self, size_bytes):
        if size_bytes < 1024: return f"{size_bytes} B"
        elif size_bytes < 1024**2: return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024**3: return f"{size_bytes/(1024**2):.2f} MB"
        else: return f"{size_bytes/(1024**3):.2f} GB"

    def run_merge(self, params):
        self.is_cancelled = False 
        current_cancelled = False 
        
        files = params['files']
        out_path = params['output_path']
        mode = params['mode']
        overwrite = params['overwrite']
             
        fps = params.get('fps', 30)
        res_str = params.get('resolution', '1920x1080')
        crf = params.get('crf', 23)
        bg_image = params.get('bg_image', '')

        if not files:
            self.log("⚠️ No files to merge.")
            self.log("-" * 80, replace=False)
            return

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        if os.path.exists(out_path) and not overwrite:
            self.log(f"ℹ️File exists: {os.path.basename(out_path)}", replace=False)
            self.log("-" * 80, replace=False)
            return

        self.log(f"ℹ️Merging {len(files)} files -> {os.path.basename(out_path)}", replace=False)

        # Analyze inputs
        inputs_info = []
        total_duration = 0.0
        
        for f in files:
            info = self.probe_file(f)
            if not info:
                self.log(f"⚠️ Skipped invalid file: {os.path.basename(f)}")
                continue
            info['path'] = f
            inputs_info.append(info)
            total_duration += info['duration']

        if not inputs_info:
            return

        try:
            w_target, h_target = map(int, res_str.lower().split('x'))
        except:
            w_target, h_target = 1920, 1080

        # Build FFmpeg command
        cmd = [self.ffmpeg_path, "-y"]
        
        for info in inputs_info:
            cmd.extend(["-i", info['path']])

        bg_input_index = -1
        if mode == 'video' and bg_image and os.path.exists(bg_image):
            cmd.extend(["-loop", "1", "-i", bg_image])
            bg_input_index = len(inputs_info)

        filter_complex = []
        
        # -(Settings)-
        # --- VIDEO MODE ---
        if mode == 'video':
            for i, info in enumerate(inputs_info):
                dur = info['duration']
                if info['has_video']:
                    filter_complex.append(
                        f"[{i}:v]scale={w_target}:{h_target}:force_original_aspect_ratio=decrease,"
                        f"pad={w_target}:{h_target}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{i}];"
                    )
                elif bg_input_index >= 0:
                    filter_complex.append(
                        f"[{bg_input_index}:v]trim=duration={dur},setpts=PTS-STARTPTS,"
                        f"scale={w_target}:{h_target}:force_original_aspect_ratio=decrease,"
                        f"pad={w_target}:{h_target}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{i}];"
                    )
                else:
                    filter_complex.append(f"color=s={w_target}x{h_target}:d={dur}:r={fps}[v{i}];")

                if info['has_audio']:
                    filter_complex.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}];")
                else:
                    filter_complex.append(f"anullsrc=d={dur}:cl=stereo:r=44100[a{i}];")

            concat_parts = "".join([f"[v{i}][a{i}]" for i in range(len(inputs_info))])
            filter_complex.append(f"{concat_parts}concat=n={len(inputs_info)}:v=1:a=1[outv][outa]")
            
            cmd.extend(["-filter_complex", "".join(filter_complex)])
            cmd.extend(["-map", "[outv]", "-map", "[outa]"])
            cmd.append("-shortest")
            cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", str(crf)])
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        # --- AUDIO MODE ---
        else:
            for i, info in enumerate(inputs_info):
                if info['has_audio']:
                    filter_complex.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}];")
                else:
                    dur = info['duration']
                    filter_complex.append(f"anullsrc=d={dur}:cl=stereo:r=44100[a{i}];")
            
            concat_parts = "".join([f"[a{i}]" for i in range(len(inputs_info))])
            filter_complex.append(f"{concat_parts}concat=n={len(inputs_info)}:v=0:a=1[outa]")

            cmd.extend(["-filter_complex", "".join(filter_complex)])
            cmd.extend(["-map", "[outa]"])
            cmd.extend(["-vn", "-c:a", "libmp3lame", "-q:a", "2"])

        cmd.append(out_path)
        
        # Execution
        process = None
        try:
            process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace',
                bufsize=1, 
                startupinfo=self._get_startup_info()
            )
            
            self.active_processes.append(process)
            
            for line in process.stderr:
                if self.is_cancelled:
                    current_cancelled = True
                    process.kill()
                    break

                if "time=" in line:
                    match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line)
                    if match and total_duration > 0:
                        current_seconds = self._parse_time_to_seconds(match.group(1))
                        percent = (current_seconds / total_duration) * 100
                        self.log(f"Processing [{os.path.basename(out_path)}] {percent:.1f}%", replace=True)

            process.wait()

            if current_cancelled or self.is_cancelled:
                self.log(f"🛑 Cancelled: {os.path.basename(out_path)}")
                if os.path.exists(out_path):
                    try: os.remove(out_path)
                    except: pass
                return

            if process.returncode == 0:
                final_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                self.log(f"✅ Done: {os.path.basename(out_path)} [{self._format_size(final_size)}]", replace=False)
                self.log("-" * 80, replace=False)
            else:
                self.log(f"❌ Error merging {os.path.basename(out_path)}", replace=False)
                self.log("-" * 80, replace=False)
                
        except Exception as e:
            self.log(f"❌ Exception: {e}", replace=False)
            self.log("-" * 80, replace=False)
        finally:
            if process and process in self.active_processes:
                self.active_processes.remove(process)