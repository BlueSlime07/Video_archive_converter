#!/usr/bin/env python3

from pathlib import Path
import sys
import subprocess
import shutil

CRF = 20
PRESET = "slow"

RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
RESET   = "\033[0m"

VIDEO_EXTENSIONS = {
    ".3gp",
    ".asf",
    ".avi",
    ".flv",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mts",
    ".mxf",
    ".ogm",
    ".rm",
    ".rmvb",
    ".ts",
    ".vob",
    ".webm",
    ".wmv",
}

TMP_DIR = Path("/tmp/video-archive-converter")
TMP_FILE = TMP_DIR / "recoded.mkv"

def cerr(*args):
    print(*args,file=sys.stderr)

def scan_files(input_dir: Path) -> list[Path]:
    """
    Return a list containing every file inside input_dir recursively.
    """

    files = []

    for path in input_dir.rglob("*"):
        if path.is_file():
            files.append(path)

    return files

def filter_videos(files: list[Path]) -> list[Path]:
    """
    Keep only video files.
    """

    videos = []

    for file in files:
        if file.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(file)

    return videos

def create_output_directory(input_dir: Path) -> Path:
    """
    Create the output directory next to the input directory.

    Example:
        Movies -> Movies.fs
    """

    output_dir = input_dir.parent / f"{input_dir.name}.fs"

    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir

def get_output_path(
    input_dir: Path,
    output_dir: Path,
    video: Path,
) -> Path:
    """
    Build the output path while preserving the directory structure.

    Example:

        Input:
            /media/Movies

        File:
            /media/Movies/Action/Avatar.mkv

        Output:
            /media/Movies.fs/Action/Avatar.mkv
    """

    relative_path = video.relative_to(input_dir)

    output_path = output_dir / relative_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    return output_path

def encode_video(input_file: Path, tmp_file: Path) -> bool:
    """
    Encode one video into the temporary file.

    Returns:
        True  -> success
        False -> ffmpeg failed
    """

    tmp_file.parent.mkdir(parents=True, exist_ok=True)

    if tmp_file.exists():
        tmp_file.unlink()

    command = [
        "ffmpeg",

        "-hide_banner",

        "-y",

        "-i",
        str(input_file),

        "-map",
        "0:v:0",

        "-c:v",
        "libx264",

        "-preset",
        PRESET,

        "-crf",
        str(CRF),

        "-vf",
        "scale=-2:720",

        "-pix_fmt",
        "yuv420p",

        str(tmp_file),
    ]

    result = subprocess.run(
        command,
        check=False,
        )

    return result.returncode == 0

def mux_video(tmp_file: Path, original_file: Path, output_file: Path,) -> bool:
    """
    Merge encoded video with all non-video streams from the original file.
    """
    if output_file.exists():output_file.unlink()
    command = [

        "mkvmerge",

        "-o",
        str(output_file),

        str(tmp_file),

        "--no-video",

        str(original_file),
    ]
    result = subprocess.run(
        command,
        check=False,
        )

    return result.returncode == 0


def main():

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_directory>")
        sys.exit(1)

    input_dir = Path(sys.argv[1]).resolve()

    if not input_dir.exists():
        cerr(f"{RED}Error: '{input_dir}' does not exist.{RESET}")
        sys.exit(1)

    if not input_dir.is_dir():
        cerr(f"{RED}Error: '{input_dir}' is not a directory.{RESET}")
        sys.exit(1)
    
    if shutil.which("ffmpeg") is None:
        cerr(f"{RED}ffmpeg not found.{RESET}")
        sys.exit(1)

    if shutil.which("mkvmerge") is None:
        cerr(f"{RED}mkvmerge not found{RESET}")
        sys.exit(1)

    files = scan_files(input_dir)
    success = 0
    failed = 0
    failed_files=[]

    print(f"{BLUE}Found {len(files)} file(s).{RESET}")

    videos = filter_videos(files)
    print(f"{BLUE}Found {len(videos)} video(s).{RESET}")
    output_dir = create_output_directory(input_dir)
    print(f"{BLUE}output directory: {output_dir}{RESET}")
    print()

    for index, video in enumerate(videos, start=1):

        output_path = get_output_path(
            input_dir,
            output_dir,
            video,
        )
        print(f"{YELLOW}\n\n[{index}/{len(videos)}] {video.relative_to(input_dir)}\n\n{RESET}")

        if not encode_video(video, TMP_FILE):
            cerr(f"{RED}Failed to encode: {video}{RESET}")
            failed+=1
            failed_files.append(video.relative_to(input_dir))
            continue
        if not mux_video(TMP_FILE, video, output_path):
            cerr(f"{RED}Failed to mux: {video}{RESET}")
            failed+=1
            failed_files.append(video.relative_to(input_dir))
            continue
        success+=1

    if TMP_FILE.exists():TMP_FILE.unlink()
    print(f"\n\n{GREEN}Done.\nSuccess: {success}{RESET}{RED}\nFailed: {failed}{RESET}")
    if failed:
        cerr(f"{RED}Failed file:{RESET}")
        for file in failed_files:
            cerr(f"\t{file}")

if __name__ == "__main__":
    main()