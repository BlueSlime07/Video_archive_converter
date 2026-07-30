import sys
from pathlib import Path
import subprocess
import shutil
import hashlib
import os
import time

from config import *

def print_info(*orgs):
    print(BLUE,end="")
    print(*orgs,end="")
    print(RESET)

def print_success(*orgs):
    print(GREEN,end="")
    print(*orgs,end="")
    print(RESET)

def print_status(*orgs):
    print(YELLOW,end="")
    print(*orgs,end="")
    print(RESET)

def print_title(*orgs):
    print(MAGENTA,end="")
    print(*orgs,end="")
    print(RESET)

def print_cyan(*orgs):
    print(CYAN,end="")
    print(*orgs,end="")
    print(RESET)

def print_error(*orgs):
    print(RED,end="",file=sys.stderr)
    print(*orgs,end="", file=sys.stderr)
    print(RESET, file=sys.stderr)

def print_red(*orgs):
    print(RED,end="")
    print(*orgs,end="")
    print(RESET)

def print_warning(*orgs):
    print(ORANGE,end="")
    print(*orgs,end="")
    print(RESET)

def scan_files(input_dir: Path) -> set[Path]:
    """
    Return a set containing every file inside input_dir recursively.
    """

    files = set()

    for path in input_dir.rglob("*"):
        if path.is_file():
            files.add(path)

    return files

def split_files(files: set[Path], videos: set[Path], other_files: set[Path]) -> None:
    """
    Split files into videos and non-video files.
    """

    for file in files:
        if file.suffix.lower() in VIDEO_EXTENSIONS.keys():
            videos.add(file)
        else:
            other_files.add(file)


def create_output_directory(input_dir: Path) -> Path:
    """
    Create the output directory next to the input directory.

    Example:
        Movies -> Movies.fs
    """
    if flag_control.IN_PLACE:
        return input_dir

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

        "-i", str(input_file),

        "-map", "0:v:0",

        "-c:v", "libx264",

        "-preset", PRESET,

        "-crf", str(CRF),

        "-vf", "scale=-2:720",

        "-pix_fmt", "yuv420p",

#        "-progress", "pipe:1",

        str(tmp_file),
    ]

    result = subprocess.run(
        command,
        check=False,
        )

    return result.returncode == 0

def get_video_track_id(path: Path) -> int | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=id",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return int(result.stdout.strip(), 0)
    except (subprocess.SubprocessError, ValueError):
        return None

def mux_video(tmp_file: Path, original_file: Path, output_file: Path,) -> bool:
    """
    Create the final output container by combining the encoded video
    with the original non-video streams.
    """
    policy = VIDEO_EXTENSIONS.get(original_file.suffix.lower())

    if flag_control.FORCE_MKV and (policy != ContainerPolicy.MP4_FAMILY):
        policy = ContainerPolicy.MKV

    match policy:
        case ContainerPolicy.MKV:
            if output_file.exists() and not flag_control.IN_PLACE:output_file.unlink()
            tmp_output = original_file.parent / (original_file.name + ".tmp.mkv")
            command = [

                "mkvmerge",

                "-o",
                str(output_file) if not flag_control.IN_PLACE else str(tmp_output),

                str(tmp_file),

                "--no-video",

                str(original_file),
            ]
            result = subprocess.run(
                    command,
                    check=False,
                    )
            
        case ContainerPolicy.MP4_FAMILY:
            if output_file.exists() and not flag_control.IN_PLACE: output_file.unlink()

            tmp_output = original_file.parent / (original_file.name + ".tmp.mp4")
            target = tmp_output if flag_control.IN_PLACE else output_file

            try:
                shutil.copy2(original_file,target)
            except OSError:
                return False
            
            track_id = get_video_track_id(target)
            if track_id is None:
                return False
            
            command = [
                "MP4Box",

                "-rem", str(track_id),
                
                "-add", f"{tmp_file}#video",
                
                str(target),
            ]
            result = subprocess.run(
                    command,
                    check=False,
                    )
            
        case _:
            raise AssertionError(f"Unsupported native container: {policy}")

    if flag_control.IN_PLACE and result.returncode != 0:
        tmp_output.unlink(missing_ok=True)

    if flag_control.IN_PLACE and result.returncode == 0:
        try:
            os.replace(tmp_output,original_file)
        except OSError:
            tmp_output.unlink(missing_ok=True)
            return False
        tmp_output.unlink(missing_ok=True)

    return result.returncode == 0

def handle_non_native(input_dir:Path, input_file:Path, output_file: Path) -> bool:
    try:    
        if flag_control.COPY and not flag_control.FORCE_MKV:shutil.copy2(input_file,output_file)

    except OSError:
        return False
    
    policy = VIDEO_EXTENSIONS.get(input_file.suffix.lower())
    
    print_red(input_file.relative_to(input_dir))

    match policy:
        case ContainerPolicy.WEBM:
            print_info("WebM container detected.\n")
            print_warning("H.264 video cannot be stored in a standards-compliant WebM container.\n")
        
        case ContainerPolicy.PROFESSIONAL:
            print_info("Professional container detected.\n")
            print_warning("This container may contain production metadata that this tool does not preserve.\n")

        case ContainerPolicy.LEGACY:
            print_info("Legacy container detected.\n")
            print_warning("This legacy container is outside the scope of the native workflow.\n")
        
    if flag_control.COPY:print_status("The original file was copied without modification.")
    else:print_status("The file was skipped.")
    print_cyan("Use --force-mkv if you want to convert it to MKV.")
    
    return True

def get_file_hash(filepath: Path,
                  chunk_size:int = 8192,
                  ) -> str:
    """for geting hash of files"""
    sha256 = hashlib.sha256()
    with filepath.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def ask_delete_state(state_file:Path, exit_cod:int):
    chose = input("Delete it and rebuild it? [y/N] ")
    if chose in ("","N","n"):
        sys.exit(exit_cod)
    elif chose in ('Y','y'):
        state_file.unlink()

def finish_notification():
    print('\a',end='',flush=True)
    time.sleep(0.13)
    print('\a',end='',flush=True)
    time.sleep(0.26)
    print('\a',end='',flush=True)
    time.sleep(0.13)
    print('\a',end='',flush=True)