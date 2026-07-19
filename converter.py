#!/usr/bin/env python3

from pathlib import Path
import sys
import subprocess
import shutil
import hashlib
import pickle as pk

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

def scan_files(input_dir: Path) -> list[Path]:
    """
    Return a list containing every file inside input_dir recursively.
    """

    files = []

    for path in input_dir.rglob("*"):
        if path.is_file():
            files.append(path)

    return files

def split_files(files: list[Path], videos: list[Path], other_files: list[Path]) -> None:
    """
    Split files into videos and non-video files.
    """

    for file in files:
        if file.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(file)
        else:
            other_files.append(file)


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

        "-i", str(input_file),

        "-map", "0:v:0",

        "-c:v", "libx264",

        "-preset", PRESET,

        "-crf", str(CRF),

        "-vf", "scale=-2:720",

        "-pix_fmt", "yuv420p",

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

def copy_other_files(other_files: list[Path], input_dir: Path, output_dir: Path, state:dict, state_file:Path, state_file_temp:Path)->None:
    """
    It copies all files that are not videos.
    """
    if not other_files:
        print_info("\tNo additional files to copy.")
        return
    
    total = len(other_files)
    success = 0
    failed = 0
    failed_files = []

    print_info(f"\t{total} File(s) need to be copied.")

    for index, file in enumerate(other_files,start=1):
        output_path = get_output_path(
            input_dir,
            output_dir,
            file,
        )
        
        try:
            print_status(f"\t[{index}/{total}] Copying {file.relative_to(input_dir.parent)}")
            shutil.copy2(file,output_path)
            print()
            success+=1
            state["output_others"].append(file.relative_to(input_dir))
            f = state_file_temp.open('wb')
            pk.dump(state, f)
            f.close()
            shutil.copy2(state_file_temp,state_file)
            state_file_temp.unlink()
        except OSError as e:
            print_error(f"\terror to copy {file} to {output_path}")
            print_error(f"\terror: \n{e}")
            failed+=1
            failed_files.append(file)
            state["copy_failed"].append(file.relative_to(input_dir))
            f = state_file_temp.open('wb')
            pk.dump(state, f)
            f.close()
            shutil.copy2(state_file_temp,state_file)
            state_file_temp.unlink()
    print_success(f"\tCopy Done.")
    print_success(f"\tSuccess: {success}")
    print_red(f"\tFailed: {failed}")
    if failed:
        for file in failed_files:
            print_error(f"\t\t{file.relative_to(input_dir.parent)}")

def get_file_hash(filepath: Path, chunk_size: int = 8192) -> str:
    """for geting hash of files"""
    sha256 = hashlib.sha256()
    with filepath.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def del_in_list(In:list,for_remove:list):
    for i in for_remove:
        if i in In:
            In.remove(i)
    

def main():

    if len(sys.argv) < 2:
        print_error(f"Invalid input.\ntry: {sys.argv[0]} --help")
        sys.exit(1)

    if("-h" in sys.argv or "--help" in sys.argv):
        print(f"Usag: {sys.argv[0]} <input_directory> options")
    input_dir = Path(sys.argv[1]).resolve()

    if not input_dir.exists():
        print_error(f"Error: '{input_dir}' does not exist.")
        sys.exit(1)

    if not input_dir.is_dir():
        print_error(f"Error: '{input_dir}' is not a directory.")
        sys.exit(1)
    
    if shutil.which("ffmpeg") is None:
        print_error(f"ffmpeg not found.")
        sys.exit(1)

    if shutil.which("mkvmerge") is None:
        print_error(f"mkvmerge not found")
        sys.exit(1)
    print_title("scanning directory..")
    files = scan_files(input_dir)
    success = 0
    failed = 0
    failed_files = []

    print_info(f"Found {len(files)} file(s).")
    other_files: list[Path] = []
    videos: list[Path] = []
    split_files(files,videos,other_files)
    print_info(f"Found {len(videos)} video(s).")
    output_dir = create_output_directory(input_dir)
    print_info(f"output directory: {output_dir}")
    print()

    state=dict()
    state_dir = output_dir / ".video_converter"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "state"
    state_file_temp = state_dir / "state_tmp"

    print_title("search in state file.")
    if not state_file.exists():
        print_info("state file not found.")
        print_cyan(f"making state file in {state_file.relative_to(output_dir.parent)}")
        state["state_version"]=1
        state["input_directory"]=input_dir
        state["output_directory"]=output_dir
        state["input_videos"]=dict()
        for i in videos:
            state["input_videos"][i.relative_to(input_dir)] = get_file_hash(i)
        state["input_others"]=dict()
        for i in other_files:
            state["input_others"][i.relative_to(input_dir)] = get_file_hash(i)
        state["output_videos"]=[]
        state["output_others"]=[]
        state["encode_failed"]=[]
        state["copy_failed"]=[]
        file = state_file.open("wb")
        pk.dump(state,file=file)
        file.close()
    else:
        print_info(f"state file found in {state_file}")
        file = state_file.open("rb")
        pk.load(state,file=file)
        file.close()
        state["input_directory"]=input_dir
        state["output_directory"]=output_dir
        for_del_in_videos:list[Path]=[]
        for_del_in_others:list[Path]=[]
        for video in videos:
            if not video.relative_to(input_dir) in state["input_videos"].keys():
                state["input_videos"][video.relative_to(input_dir)] = get_file_hash(video)
            else:
                file_hash = get_file_hash(video)
                if state["input_videos"][video.relative_to(input_dir)] == file_hash and video.relative_to(input_dir) in state["output_videos"]:
                    for_del_in_videos.append(file)
                else:
                    state["input_videos"][video.relative_to(input_dir)] = get_file_hash(video)
                    continue

        for file in other_files:
            if not file.relative_to(input_dir) in state["input_others"].keys():
                state["input_others"][file.relative_to(input_dir)] = get_file_hash(file)
            else:
                file_hash = get_file_hash(file)
                if state["input_others"][file.relative_to(input_dir)] == file_hash and file.relative_to(input_dir) in state["output_others"]:
                    for_del_in_others.append(file)
                else:
                    state["input_others"][file.relative_to(input_dir)] = get_file_hash(file)
                    continue
        del_in_list(videos,for_del_in_videos)
        del_in_list(other_files,for_del_in_others)
            
    for index, video in enumerate(videos, start=1):

        output_path = get_output_path(
            input_dir,
            output_dir,
            video,
        )
        print_status(f"\n[{index}/{len(videos)}] {video.relative_to(input_dir)}\n")

        if not encode_video(video, TMP_FILE):
            print_error(f"Failed to encode: {video}")
            failed+=1
            failed_files.append(video.relative_to(input_dir))
            state['encode_failed'].append(video)
            file = state_file_temp.open("wb")
            pk.dump(state,file)
            file.close()
            shutil.copy2(state_file_temp,state_file)
            state_file_temp.unlink(missing_ok=True)
            continue
        if not mux_video(TMP_FILE, video, output_path):
            print_error(f"Failed to mux: {video}")
            failed+=1
            failed_files.append(video.relative_to(input_dir))
            state['encode_failed'].append(video)
            file = state_file_temp.open("wb")
            pk.dump(state,file)
            file.close()
            shutil.copy2(state_file_temp,state_file)
            state_file_temp.unlink(missing_ok=True)
            continue
        success+=1
        state["output_videos"].append(video.relative_to(input_dir))
        file = state_file_temp.open("wb")
        pk.dump(state,file)
        file.close()
        shutil.copy2(state_file_temp,state_file)
        state_file_temp.unlink(missing_ok=True)
    
    print_cyan(f"Copying other files...")
    copy_other_files(other_files,input_dir,output_dir,state,state_file,state_file_temp)
    
    if TMP_FILE.exists():TMP_FILE.unlink()

    print_success(f"done.\nSuccess: {success}")
    print_red(f"Faild: {failed}")

    if failed:
        print_error(f"Failed file:")
        for file in failed_files:
            print_error(f"\t{file}")

if __name__ == "__main__":
    main()