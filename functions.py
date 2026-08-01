import sys
from pathlib import Path
import subprocess
import shutil
import hashlib
import os
import time
import threading

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
    Create output directory next to input directory (e.g., Movies -> Movies.fs).
    If output directory is set via flag_control, uses that instead.
    If IN_PLACE is enabled, returns input_dir without creating anything.
    """
    if flag_control.IN_PLACE:
        return input_dir

    if flag_control.IS_OUTPUT_DIR_SET:
        output_dir = flag_control.OUTPUT_DIR
    else:
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

def progress_bar(full_time:float|None)->None:
    """
    Display a real-time progress bar during video encoding.

    Shows encoding progress, FPS, speed, elapsed time, ETA, frame count, and file size.
    Adapts layout based on terminal width (full mode if >= 85 columns, otherwise compact mode).
    If full_time is None or 0, shows progress without ETA/percentage.

    Args:
        full_time: Total duration of the video in seconds.
    """
    units = ('KB','MB','GB','TB')
    if full_time is not None and full_time > 0:
        try:
            runner=0
            if shutil.get_terminal_size().columns >= 85:
                ###  FULL
                last_down = 2
                print('\n\n\033[?25l',end='\033[2A')
                while runner<2 and progress_state.progress != "force_down":
                        if runner>0:
                            progress_state.out_time_ms = full_time *1_000_000
                            progress_state.out_time_s = full_time
                        fill = int(progress_state.out_time_s / full_time * PROGRESS_BAR_WIDTH)
                        print("\r\033[k Encoding: ["+fill*'█'+(PROGRESS_BAR_WIDTH - fill)*'░'+f"]  {int(progress_state.out_time_s/full_time*100):>3d}%  ⚡ {progress_state.fps:<8.2f} fps │  {progress_state.speed_f:<4.2f}x",end='\033[B')
                        size = progress_state.total_size
                        n = 0
                        size =round(size / 1024, 1)
                        while size>1024:
                            n+=1
                            size = round(size / 1024, 1)

                        if progress_state.speed_f > 0:
                            ETA_s = int((full_time-progress_state.out_time_s)//progress_state.speed_f)
                        else:
                            ETA_s = 359999
                        if ETA_s <0:ETA_s=0

                        print(f"\r\033[k Elapsed: {int(progress_state.out_time_s)//3600:02d}:{int(progress_state.out_time_s)//60%60:02d}:{int(progress_state.out_time_s)%60:02d}  │  ETA: {ETA_s//3600:02d}:{ETA_s//60%60:02d}:{ETA_s%60:02d}  │  Frames: {progress_state.frame:<6,d}  │  Size: {size:<6.1f} {units[n]}",end='\033[A',flush=True)
                        time.sleep(0.1)
                        if progress_state.progress == 'end':
                            runner+=1
            else:
                ###   COMPACT
                last_down = 8
                print("Encoding:")
                
                print(8*'\n'+"\033[?25l",end='\033[8A')
                while runner<2 and progress_state.progress != "force_down":
                    if runner>0:
                        progress_state.out_time_ms = full_time *1_000_000
                        progress_state.out_time_s = full_time
                    fill = int(progress_state.out_time_s / full_time * 20)
                    print("\r\033[K["+(fill)*'█'+(20-fill)*'░'+']',end='\033[2B')
                    print(f"\r\033[kProgress: {int(progress_state.out_time_s/full_time*100):>3d}%",end='\033[B')
                    print(f"\r\033[kElapsed : {int(progress_state.out_time_s)//3600:02d}:{int(progress_state.out_time_s)//60%60:02d}:{int(progress_state.out_time_s)%60:02d}",end='\033[B')

                    if progress_state.speed_f > 0:
                        ETA_s = int((full_time-progress_state.out_time_s)//progress_state.speed_f)
                    else:
                        ETA_s = 359999
                    if ETA_s <0:ETA_s=0

                    print(f"\r\033[kETA     : {ETA_s//3600:02d}:{ETA_s//60%60:02d}:{ETA_s%60:02d}",end='\033[B')
                    print(f"\r\033[kFPS     : {progress_state.fps:<8.2f}",end='\033[B')
                    print(f"\r\033[kSpeed   : {progress_state.speed_f:<4.2f}x",end='\033[B')
                    print(f"\r\033[kFrames  : {progress_state.frame:<6,d}",end='\033[B')
                    size = progress_state.total_size
                    n = 0
                    size =round(size / 1024, 1)
                    while size>1024:
                        n+=1
                        size = size/1024
                    print(f"\r\033[kSize    : {size:<6.1f} {units[n]}",end='\033[8A',flush=True)
                    time.sleep(0.1)
                    if progress_state.progress == 'end':
                        runner+=1
            
                    

        finally:
            print(f'\033[{last_down}B\033[?25h\n')
    else:
        try:
            ###   NO_DURATION
            runner = 0

            print("Encoding:  ⚠ Duration unavailable\n")
            print("\n\n\n\n\n\033[?25l",end='\033[5A')
            while runner<2 and progress_state.progress != "force_down":
                print(f"\r\033[k Elapsed: {int(progress_state.out_time_s)//3600:02d}:{int(progress_state.out_time_s)//60%60:02d}:{int(progress_state.out_time_s)%60:02d}",end='\033[B')
                print(f"\r\033[k Frames : {progress_state.frame:<6,d}",end='\033[B')
                print(f"\r\033[k FPS    : {progress_state.fps:<8.2f}",end='\033[B')
                print(f"\r\033[k Speed  : {progress_state.speed_f:<4.2f}x",end='\033[B')
                size = progress_state.total_size
                n = 0
                size =round(size / 1024, 1)
                while size>1024:
                    n+=1
                    size = size/1024
                print(f"\r\033[k Size   : {size:<6.1f} {units[n]}",end='\033[4A',flush=True)
                time.sleep(0.1)
                if progress_state.progress == 'end':
                    runner+=1
                
        finally:
            print('\033[5B\033[?25h')

def get_video_time(video:Path) -> float|None:
    """
    Get video duration in seconds using ffprobe.

    Tries multiple ffprobe methods (stream duration first, then format duration).
    Returns None if duration cannot be determined.

    Args:
        video: Path to the video file.

    Returns:
        Video duration in seconds, or None if unavailable.
    """
    methods:tuple[tuple[str,...],...] =(
        (
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries',
            'stream=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            str(video),
        ),

        (
            'ffprobe',
            '-v', 'error',
            '-show_entries',
            'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            str(video),
        ),

    )
    for method in methods: 
        try:        
            result = subprocess.run(
                method,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout and result.stdout.strip() != 'N/A':
                return float(result.stdout.strip())
        except (subprocess.SubprocessError, ValueError):
            continue
    else:
        return None
    
    

def encode_video(input_file: Path, tmp_file: Path) -> bool:
    """
    Encode one video into the temporary file and update progress state.

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

        "-progress", "pipe:1",

        '-nostats',

        str(tmp_file),
    ]
    reset_progress_state()
    bar = threading.Thread(target=progress_bar,args=(get_video_time(input_file),))
    
    result = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1

        )

    bar.start()

    try:    
        while progress_state.progress =='continue':
            line = result.stdout.readline()
            key, value = str(line).strip().split('=',1)
            match key:
                case 'progress':
                    progress_state.progress=value

                case 'frame':
                    progress_state.frame=int(value)

                case 'fps':
                    progress_state.fps=float(value)

                case 'total_size':
                    progress_state.total_size=int(value)

                case 'out_time_ms':
                    progress_state.out_time_ms=int(value)
                    progress_state.out_time_s=float(int(value)/1000000)

                case 'speed':
                    progress_state.speed=value
                    progress_state.speed_f=float(value.strip()[:-1])
    except:
        progress_state.progress = 'force_down'
        result.terminate()
        bar.join()
        raise

    result.wait()
    bar.join()

    progress_state.return_code=result.returncode

    if result.returncode !=0:
        print(result.stderr.read())
    return result.returncode == 0

def get_video_track_id(path: Path) -> int | None:
    """
    Get the video track ID from a video file using ffprobe.

    Returns None if the track ID cannot be determined.

    Args:
        path: Path to the video file.

    Returns:
        Video track ID (e.g., 0x100), or None if unavailable.
    """
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
    """
    Handle non-native video containers (WebM, Professional, Legacy).

    Copies the file if COPY flag is enabled and FORCE_MKV is not set.
    Prints appropriate warnings based on container type.

    Args:
        input_dir: Root input directory (for relative path display).
        input_file: Source video file path.
        output_file: Destination path for copied file.

    Returns:
        True if handled successfully, False if copy operation failed.
    """
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
    """Play a beep pattern to notify when encoding is complete."""
    print('\a',end='',flush=True)
    time.sleep(0.13)
    print('\a',end='',flush=True)
    time.sleep(0.26)
    print('\a',end='',flush=True)
    time.sleep(0.13)
    print('\a',end='',flush=True)

def reset_progress_state():
    """Reset progress state to default values."""
    progress_state.progress = 'continue'

    progress_state.frame = 0
    progress_state.fps = 0.0
    progress_state.speed = '0x'
    progress_state.speed_f = 1.0

    progress_state.total_size = 0

    progress_state.out_time_ms = 0
    progress_state.out_time_s = 0.0

    progress_state.return_code = None

def flag_handler():
    """
    Parse command-line arguments and configure program behavior.

    Supported flags:
        -n, --no-copy       : Disable file copying (default is copy)
        -f, --force-mkv     : Force conversion to MKV container
        -i, --in-place      : Process files in their original location (disables copy)
        -b, --notification  : Enable finish notification sound
        -r, --refresh       : Refresh mode (just refresh the display)
        -o, --output <dir>  : Specify custom output directory

    Exit codes:
        51 : Invalid argument detected
        26 : Conflicting options (--in-place and --output used together)

    Note:
        If --in-place and --output are both used, the program will beep 5 times
        with decreasing intervals before exiting with code 26 to alert the user.

    ⚠️ Terminal Alert Warning:
        If you have configured your terminal to flash the screen instead of beeping
        (e.g., "Visual Bell" in some terminal emulators), be aware that in a dark
        environment, a sudden white flash can be startling or uncomfortable for
        your eyes. Consider using headphones or adjusting your terminal settings
        if you are sensitive to light flashes.
    """
    args = sys.argv

    skip_args = 0

    for index in range(2,len(args)):
        i = args[index]
        if skip_args>0:
            skip_args -= 1
            continue

        elif i in ("--no-copy", '-n'):
            flag_control.COPY = False

        elif i in ("--force-mkv" , "-f"):
            flag_control.FORCE_MKV = True

        elif i in ("--in-place", '-i'):
            flag_control.IN_PLACE = True
            flag_control.COPY = False

        elif i in ('--notification', '-b'):
            flag_control.FINISH_NOTIFICATION = True

        elif i in ("--refresh", '-r'):
            flag_control.JUST_REFRESH = True

        elif i in ("--output", '-o'):
            flag_control.IS_OUTPUT_DIR_SET = True
            flag_control.OUTPUT_DIR = Path(args[index+1]).resolve()
            skip_args +=1

        else:
            print_error(f"Invalid argument detected: {i}")
            sys.exit(51)

    if flag_control.IN_PLACE and flag_control.IS_OUTPUT_DIR_SET:
        delta = 1
        for i in range(5):
            print('\a',end='',flush=True)
            time.sleep(delta)
            delta /= 1.5

        print_error("You can't use both --in-place and --output together.")
        sys.exit(26)