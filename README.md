## A simple, predictable, and reliable video archive converter.

# Video Converter

A simple video archive converter for Linux.

The goal of this project is to convert every video inside a directory into a standardized format suitable for long-term storage and media servers such as Jellyfin.

The program recursively scans an input directory, re-encodes every video to H.264 720p using FFmpeg, then rebuilds the final container using MKVToolNix (mkvmerge) so that non-video streams from the original file are preserved.

## Features

- Recursive directory scanning
- Preserves the original directory structure
- Creates the output directory next to the source directory
- Encodes every video to H.264 (libx264)
- Scales video to 720p
- Uses CRF encoding
- Uses mkvmerge to preserve non-video streams
- Processes one file at a time
- Displays progress during conversion
- Reports failed files at the end

## Output Directory

If the input directory is

```
Movies/
```

the output directory will be

```
Movies.fs/
```

`.fs` stands for **For Server**.

The directory structure inside the output directory is preserved.

## Requirements

- Python 3
- FFmpeg
- MKVToolNix

On Arch Linux:

```bash
sudo pacman -Sy ffmpeg mkvtoolnix
```

## Usage

```bash
python converter.py /path/to/Movies
```
or better
```bash
converter.py /path/to/Movies
```

Example:

```bash
python converter.py "/mnt/media/Movies"
```

## Current Encoding Settings

Video codec:

```
libx264
```

Preset:

```
slow
```

CRF:

```
20
```

Resolution:

```
720p
```

Pixel format:

```
yuv420p
```

## Project Goals

This project focuses on:

- reducing archive size
- preserving playback compatibility
- preserving useful container data
- keeping the implementation simple and maintainable

The project intentionally avoids unnecessary complexity during early development.

## Current Status

This is an early development version.

The encoding pipeline is functional, but additional testing with different media collections is still required.

## License

MIT
