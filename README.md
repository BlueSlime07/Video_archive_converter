# Video Archive Converter

Video Archive Converter is a cross-platform command-line tool that converts video collections into space-efficient H.264 archives while preserving audio tracks, subtitles, attachments, and stream metadata.

Designed for long-running conversions with automatic resume support and optimized for media servers such as Jellyfin.

Video Archive Converter recursively scans a directory, converts supported videos to **H.264 720p** using FFmpeg, and rebuilds the final container while preserving non-video streams whenever possible.

The project is designed for building standardized video archives suitable for media servers such as Jellyfin or for long-term personal storage.

---

## Features

* Recursive directory scanning
* Preserves the original directory structure
* Creates a separate output directory by default
* Optional in-place conversion
* Encodes video using **H.264 (libx264)**
* Resizes video to **720p**
* CRF-based encoding
* Real-time encoding progress bar with FPS, speed, elapsed time, ETA, output size and frame count.
* Automatically adapts to small terminals (e.g. Termux) with a compact progress view.
* Gracefully falls back when video duration is unavailable.
* Preserves:

  * Audio tracks
  * Subtitle tracks
  * Attachments (MKV)
  * Track language
  * Track names
  * Default/Forced flags
* Supports automatic resume with automatic state validation and recovery
* Processes one file at a time to reduce disk usage
* Displays conversion progress
* Reports failed files at the end
* Optional audible notification when processing finishes
* Automatic resume after interruption
* JSON-based state file
* Built-in live progress display
* Cross-platform (Linux / Windows)
* Optional completion notification
* Custom output directory

---

## Supported Containers

### Native containers

These containers are processed while preserving their non-video streams.

| Container | Status    |
| --------- | --------- |
| MKV       | Supported |
| MP4       | Supported |
| M4V       | Supported |
| MOV       | Supported |
| 3GP       | Supported |

### Other containers

The following containers are copied without modification by default:

* AVI
* ASF
* FLV
* MPEG
* MPG
* RM
* RMVB
* VOB
* OGM
* TS
* WMV
* WebM
* MXF
* M2TS
* MTS

Use `--force-mkv` if you want to convert these containers into MKV.

---

## Output Directory

By default the program creates a new directory next to the source directory.

Example:

```
Movies/
```

becomes

```
Movies.fs/
```
or
```
video_converter Movies --output /mnt/archive
```
become
```
/mnt/archive
```

The suffix `.fs` stands for **For Server**.

The original directory structure is preserved.

---

## Command Line Options

| Option                 | Description                                                |
| ---------------------- | ---------------------------------------------------------- |
| `-h`, `--help`         | Show help information                                      |
| `-n`, `--no-copy`      | Do not copy non-video files                                |
| `-f`, `--force-mkv`    | Convert unsupported containers to MKV                      |
| `-i`, `--in-place`     | Replace original files after successful conversion         |
| `-r`, `--refresh`      | Refresh the state file                                     |
| `-b`,  `--notification`| Play a terminal bell notification when processing finishes |

---

## Progress Display

Video Archive Converter replaces FFmpeg's default progress output with a cleaner
real-time interface showing:

- Encoding progress
- FPS
- Encoding speed
- Elapsed time
- Estimated remaining time (ETA)
- Encoded frame count
- Output file size

When the source duration is unavailable, the program automatically switches to
an alternative display that still reports all available information.

---

## State File

The converter stores its progress in a UTF-8 encoded JSON state file inside the output directory.

If the conversion is interrupted, the program resumes from the last successful file on the next run.

This allows interrupted conversions to continue without reprocessing files that have already been completed.

On startup the converter automatically:

- validates the state file
- recovers from temporary state files after interrupted executions
- migrates supported legacy state files to the current format
- detects corrupted state files and asks before removing them

The `--refresh` option synchronizes the state file with the current contents of the input directory.

---

## Requirements

* Python 3.11+
* FFmpeg
* FFprobe
* MKVToolNix
* GPAC (MP4Box)

  ---

### Debian

Before installing the Video Archive Converter package, make sure all required dependencies are available on your system.

In particular, verify that `gpac` (which provides `MP4Box`) is installed.

```bash
sudo apt install gpac
```

If your Debian release does not provide the `gpac` package in its official repositories, install GPAC using a method appropriate for your distribution before installing Video Archive Converter.

---

### Fedora

FFmpeg is required for video conversion.

Fedora does not include FFmpeg in the default repositories.
Install RPM Fusion before installing Video Archive Converter:

```bash
sudo dnf install \
https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
```
Then retry to install video-archive-converter.

---

### Arch Linux
Download last version on release page and run:

```bash
sudo pacman -U ./video-archive-converter*.pkg.tar.zst
```

---

## Arch Linux (AUR)

Install with any AUR helper.

### Using yay

```bash
yay -S video-archive-converter
```

### Using paru

```bash
paru -S video-archive-converter
```

The package depends on:

* Python
* FFmpeg
* MKVToolNix
* GPAC (MP4Box)

These dependencies will be installed automatically by the package manager.

---

## Termux

> **Requirements**
>
> * Termux **GitHub** or **F-Droid** version
> * **x11-repo** enabled
>
> The Google Play version of Termux is **not supported**.

Enable the X11 repository:

```bash
pkg install x11-repo
pkg update
```

Then install Video Archive Converter:

```bash
curl -fsSL https://raw.githubusercontent.com/BlueSlime07/Video_archive_converter/refs/heads/main/termux/video-archive-converter_termux_installer.sh | bash
```

The installer will automatically:

* Download the latest Termux package
* Install it
* Remove temporary files

Run:

```bash
video-archive-converter --help
```

---

## Usage

Convert an entire directory:

```bash
video-archive-converter /path/to/Movies
```
Save converted files into a custom directory:
```bash
video-archive-converter Movies -o <directory>
```

Convert unsupported containers to MKV:

```bash
video-archive-converter Movies --force-mkv
```

Replace original files:

```bash
video-archive-converter Movies --in-place
```

Skip copying non-video files:

```bash
video-archive-converter Movies --no-copy
```

Refresh the state file:

```bash
video-archive-converter Movies --refresh
```
Play a terminal bell notification when processing finishes:

```bash
video-archive-converter ~/Videos --notification
```

---

## Encoding Settings

| Setting      | Value           |
| ------------ | --------------- |
| Video Codec  | H.264 (libx264) |
| Resolution   | 720p            |
| Pixel Format | yuv420p         |
| Preset       | slow (default)  |
| CRF          | 22 (default)    |

---

## State File

The converter stores its progress in a state file located inside the output directory.

This allows interrupted conversions to continue without reprocessing files that have already been completed.

The `--refresh` option updates the state file when files have been added, removed, or renamed.

---

## Design Goals

The project focuses on:

* Predictable behavior
* Safe file handling
* Reliable long-running conversions
* Simple implementation
* Low memory usage
* Media server compatibility
* Crash-resistant operation

---

## License

MIT License
