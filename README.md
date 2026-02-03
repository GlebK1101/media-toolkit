# Media Toolkit

**Media Toolkit** is a universal desktop application built with Python (tkinter) that combines essential tools for everyday media file processing.

The application was created to consolidate routine tasks into a single convenient interface: video downloading, format conversion, compression, trimming, and merging. Under the hood, the program acts as a GUI wrapper for two powerful tools: **yt-dlp** and **FFmpeg**.

## Project Structure

The application architecture follows a modular principle, clearly separating the graphical interface (frontend) from the logic (backend).

```text
folder/
├── bin/                       # External tools folder (dependencies)
│   ├── ffmpeg.exe             # Binary for video/audio processing
│   ├── ffprobe.exe            # Binary for metadata analysis
│   └── ffplay.exe             # Used for previewing in the editor
│
├── src/                       # Application source code
│   │
│   ├── core/                  # CORE: Pure logic (backend)
│   │   ├── __init__.py
│   │   ├── compressor_logic.py # Compression logic (CRF control, resolution)
│   │   ├── converter_logic.py  # Conversion logic (Smart Stream Copy)
│   │   ├── downloader_logic.py # yt-dlp wrapper with progress hooks
│   │   ├── editor_logic.py     # Waveform processing, trimming, and preview
│   │   └── merger_logic.py     # Merging logic (concat demuxer / filter complex)
│   │
│   ├── tabs/                  # INTERFACE: Tabs (frontend)
│   │   ├── __init__.py
│   │   ├── base_tab.py         # Base class (shared console, threading)
│   │   ├── about_tab.py        # In-app documentation
│   │   ├── compressor_tab.py   # Compression UI (Single/Batch)
│   │   ├── converter_tab.py    # Conversion UI (Single/Batch)
│   │   ├── downloader_tab.py   # Downloader UI
│   │   ├── editor_tab.py       # Visual editor (Timeline, Canvas)
│   │   └── merger_tab.py       # Queue manager for file merging
│   │
│   ├── utils/                 # UTILITIES
│   │   ├── __init__.py
│   │   ├── ffmpeg_utils.py     # FFmpeg binary search and validation
│   │   ├── theme.py            # Styling (colors, fonts, ttk styles)
│   │   └── updater.py          # Auto-update script for yt-dlp via pip
│   │
│   └── main.py                # ENTRY POINT: Initialization and startup
│
├── requirements.txt           # List of Python dependencies
└── README.md                  # Documentation
```

## Features and Module Specifics

The main architectural feature is multithreading. Each tab runs its tasks in a separate thread, ensuring the interface remains responsive even during heavy video rendering. A built-in console is implemented everywhere to provide real-time log feedback to the user.

### 1. Downloader
A convenient graphical wrapper over the `yt-dlp` library. The module allows downloading content in two modes: Full Video (where the program downloads video and audio streams in maximum quality and merges them) or Audio Extraction only.

Attention to detail:
*   **Duplicate Protection:** The program remembers URLs currently in progress "on the fly". You cannot accidentally start downloading the same video twice. (Unfortunately, this check does not allow you to download audio and video from the same link at the same time).
*   **File Check:** If a file with the same name already exists in the destination folder, the download will be skipped (unless the overwrite option is explicitly enabled) to save your time and bandwidth.
*   **Auto-Update:** On every startup, the program quietly checks for a fresh version of `yt-dlp` and updates it, so you don't have to worry about YouTube algorithm changes.
*   **Cancel Button:** Pressing this cancels all download processes and deletes temporary files. (A file ending in `f616.[format].part` sometimes refuses to be deleted. This isn't a problem. In this case, simply close the program and delete the file manually).

### 2. Converter
A tool for changing containers and codecs. It supports both single file operations and Batch folder processing.

Implemented with "Smart Logic":
*   If you try to convert a file to the same format (e.g., MKV -> MKV), the program won't re-encode the video but will use `Stream Copy`. This happens instantly and without quality loss.
*   When changing formats, pre-configured optimal presets (H.264 for video, AAC/LAME for audio) are applied, balancing size and quality.
*   Source overwrite protection is present: the program will not allow you to start conversion if the input and output files are identical, preventing source corruption.

### 3. Compressor
A module for reducing video file size based on the **CRF** (Constant Rate Factor) parameter. Instead of guessing the bitrate, you simply move the slider from 0 (Lossless) to 51 (minimum quality) to choose the desired balance.

Features:
*   Support for changing resolution (Resize) directly during compression.
*   Batch mode: compress the weight of an entire video folder at once.
*   Safety: if no save path is selected, the program will create a `compressed` subfolder itself to avoid mixing originals and compressed versions. Source overwrite protection is also implemented.

### 4. Editor / Cutter
A full-fledged trimming tool. Unlike simple cutters, here you see a visualization of the sound wave (waveform), allowing you to cut video with surgical precision — by sound peaks or pauses.

*   **Interface:** Timeline with zoom support (mouse wheel) and panning (Right Click).
*   **Preview:** Built-in player allows you to listen and view the selected section before exporting.
*   **Technical Nuance:** Many editors simply cut the stream (`copy`), often causing black frames or desync at the beginning of the video because the cut doesn't hit a keyframe (I-frame). We took a different path: the editor uses fast re-encoding (`preset ultrafast`) with timestamp reset. This guarantees the video starts exactly at the millisecond you selected.

### 5. Merger
A tool for joining multiple files into one long track. Works with both video and pure audio.

*   **File Queue:** A convenient list where you can reorder clips.
*   **Smart Fitting:** If you try to merge videos of different sizes (e.g., 1080p and 720p (You can add other permissions in the code if necessary)), the program automatically brings them to a common denominator, adding black bars (padding) where necessary so the final video doesn't "jump".
*   **Audio Background:** When merging audio files, you can add a static image to create a video file output.

---

## Codec Configuration (Developer Guide)

The code comes with balanced FFmpeg settings suitable for most tasks. However, if you need to change codecs, bitrate, or quality presets, it is easy to do.

For easy navigation through the code, use Search (Ctrl+F) with the special markers listed below.
If the line text does not fit on the screen, use Word Wrap (Alt+Z in VS Code). [Ctrl+Shift+P: toggle word wrap]

#### 1. Conversion (`src/core/converter_logic.py`)
Search marker: `-(Settings)-`
This block (method `run_convert`) contains the codec selection logic.
*   You can change `crf_value` (default 23-28) to adjust quality.
*   To speed up encoding, you can change `preset` from `slow` to `fast` or `ultrafast`.
*   Audio bitrate is also set here (e.g., `-b:a 128k`).

#### 2. Compression (`src/core/compressor_logic.py`)
Search marker: `-(Settings)-`
(Method `run_compress`).
*   This defines the CRF slider logic.
*   Note the settings for `.webm` — it uses the VP9 codec, which works differently than H.264.

#### 3. Editor (`src/core/editor_logic.py`)
Search marker: `-(Settings)-`
(Method `run_cut`).
*   Parameters for re-encoding the cut fragment are set here.
*   **Important:** We use flags `-c:v libx264` and `-preset ultrafast`. If you want to cut without re-encoding (instant but less precise), replace them with `-c:v copy`.
*   **Audio:** If you remove the volume filter and set `-c:a copy`, the sound will be copied as is, but the volume slider in the interface will stop affecting the result.

#### 4. Merger (`src/core/merger_logic.py`)
Search marker: `-(Settings)-`
(Method `run_merge`).
*   The block is divided into `VIDEO MODE` and `AUDIO MODE`.
*   Video mode uses a complex `filter_complex` for scaling and padding. Be careful when editing it.
*   Here you can change the quality of the final merge by adjusting `-crf` and `-preset` parameters.

---

## Installation and Launch

1.  **Requirements:**
    *   Python 3.12+ (Project tested on Python 3.14). Download it from the [official website](https://www.python.org/downloads/).
    *   Install required libraries:
        ```bash
        pip install -r requirements.txt
        ```
2.  **FFmpeg:**
    *   FFmpeg is required for the program to work. Download it from the [official website](https://ffmpeg.org/download.html).
    *   Place `ffmpeg.exe`, `ffprobe.exe` (and `ffplay.exe` for the editor) in the `bin/` folder in the project root.
    *   *Alternative:* Ensure FFmpeg is installed on your system and added to the PATH environment variable. (And don't forget to restart your computer for the system paths to work.)
3.  **Launch:**
    ```bash
    python src/main.py
    ```