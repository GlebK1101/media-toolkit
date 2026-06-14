# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-05-07
*(Commit: age-restricted videos from X)*

### Added

#### [FEAT-001] Support for Age-Restricted Videos (X / Twitter)
**Problem:**
The application was unable to download age-restricted or sensitive media from X (formerly Twitter) and other platforms. Because the underlying `yt-dlp` tool was executing requests as an anonymous guest, the servers blocked access to any 18+ content.

**Technical Explanation:**
To bypass age restrictions, platforms require the download request to come from an authenticated user session. Previously, the application did not pass any session data to the media servers.

**Solution:**
Integrated the `cookiefile` parameter into `ydl_opts` inside `src/core/downloader_logic.py`. 
The application now checks for and reads a local `cookies.txt` file. If a user exports their browser session cookies (including the `auth_token` for X) into this file, `yt-dlp` will authenticate as that user, seamlessly bypassing age restrictions and expanding download capabilities.

---

## [1.0.2] - 2026-06-14

### Added
#### [FEAT-002] SQLite Database Integration for Metadata Logging
**Description:**
Added a new "Database" tab allowing users to automatically log metadata from YouTube downloads directly into an SQLite database.

**Features:**
- **Dynamic Schema:** Automatically adds new columns to existing tables without breaking the database if the user selects new metadata checkboxes mid-session.
- **Extensive Metadata:** Supports logging 20+ fields including title, URLs, channel info, views, likes, custom notes, file paths, selected download quality, and final calculated file size.
- **Visual Order Customization:** Users can rearrange the column layout for the database directly from the UI using Up/Down buttons.
- **Safety First:** Includes a daily auto-backup feature (`backups/` folder) triggered on the first write of the day, and a duplicate prevention toggle based on `video_url`.
- **External Viewer Recommendation:** Recommended using [DB Browser for SQLite](https://sqlitebrowser.org/dl/) to view and manage the generated databases.


## [1.0.1] - 2026-02-04

### Fixed

#### [FIX-001] Audio Preview Offset (Synchronization Issue)
**Problem:**
When using the **Editor/Cutter** tab to preview a **video file**, a synchronization issue occurred during playback controls. If the user paused the playback and then resumed it, the audio would not start exactly where the cursor was. Instead, it often "jumped back" by 1-3 seconds, repeating a part of the audio that had already been played.

**Technical Explanation:**
Even though we were only listening to audio (`-nodisp`), the player (`ffplay`) was still trying to synchronize with the video stream. Video files use "Keyframes" which appear only once every few seconds. When attempting to seek to a specific timestamp (e.g., 30.5s), the player snapped back to the nearest Keyframe (e.g., 28.0s), dragging the audio back with it.

**Solution:**
Modified the `start_preview` method in `src/core/editor_logic.py`:
1.  **Added `-vn` flag:** Explicitly tells FFmpeg to ignore the video stream. Since we don't display video in the preview anyway, this forces the player to focus only on the audio stream, which allows for millisecond-precise seeking without snapping to video keyframes.
2.  **Switched to `atrim` filter:** Replaced standard seek (`-ss`) with the `atrim` filter for mathematical cutting precision.
3.  **Reset Timestamps:** Added `asetpts=PTS-STARTPTS` to reset the internal clock.

**Code Change:**
```python
def start_preview(self, input_path, start, end, volume=1.0, loop=False):
    self.stop_preview()
    
    # Added "-vn" to ignore video stream (prevents keyframe snapping)
    cmd = [self.ffplay_path, "-nodisp", "-vn", "-autoexit", "-hide_banner"]

    # Switched to 'atrim' for precise audio cutting
    filters = [f"atrim=start={start}:end={end},asetpts=PTS-STARTPTS"]
    
    if abs(volume - 1.0) > 0.01: filters.append(f"volume={volume}")
    if filters: cmd.extend(["-af", ",".join(filters)])
        
    if loop: cmd.extend(["-loop", "0"])
        
    cmd.append(input_path)
    
    # ... process execution ...
```
**Result:**

Video Files: Pausing and resuming now works instantly and precisely. There is no more "looping" or repeating of the last few seconds.
