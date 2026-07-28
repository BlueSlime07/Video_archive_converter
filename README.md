# Video Archive Converter

A simple, predictable, and reliable video archive converter for Linux.

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
* Preserves:

  * Audio tracks
  * Subtitle tracks
  * Attachments (MKV)
  * Track language
  * Track names
  * Default/Forced flags
* Supports automatic resume using a state file
* Processes one file at a time to reduce disk usage
* Displays conversion progress
* Reports failed files at the end

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

The suffix `.fs` stands for **For Server**.

The original directory structure is preserved.

---

## Command Line Options

| Option              | Description                                        |
| ------------------- | -------------------------------------------------- |
| `-h`, `--help`      | Show help information                              |
| `-n`, `--no-copy`   | Do not copy non-video files                        |
| `-f`, `--force-mkv` | Convert unsupported containers to MKV              |
| `-i`, `--in-place`  | Replace original files after successful conversion |
| `-r`, `--refresh`   | Refresh the state file                             |

---

## Requirements

* Python 3.11+
* FFmpeg
* FFprobe
* MKVToolNix
* GPAC (MP4Box)

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
converter.py /path/to/Movies
```

Convert unsupported containers to MKV:

```bash
converter.py Movies --force-mkv
```

Replace original files:

```bash
converter.py Movies --in-place
```

Skip copying non-video files:

```bash
converter.py Movies --no-copy
```

Refresh the state file:

```bash
converter.py Movies --refresh
```

---

## Encoding Settings

| Setting      | Value           |
| ------------ | --------------- |
| Video Codec  | H.264 (libx264) |
| Resolution   | 720p            |
| Pixel Format | yuv420p         |
| Preset       | Configurable    |
| CRF          | Configurable    |

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

---

## License

MIT License
