#!/usr/bin/env python3

from pathlib import Path
import shutil
import sys

from functions import *
import statemod as st

def copy_other_files(other_files: list[Path], input_dir: Path, output_dir: Path, state:dict, state_file:Path, state_file_temp:Path)->None:
    """
    It copies all files that are not videos.
    """
    if not flag_control.COPY:
        print_info("\tCopying of non-video files is disabled.")
        return
    
    if not other_files:
        print_info("\tNo additional files to copy.")
        return
    
    total = len(other_files)
    success = 0
    failed = 0
    failed_files:set[Path] = set()

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
            state["output_others"].add(file.relative_to(input_dir))
            st.state_write(state, state_file, state_file_temp)
            
        except OSError as e:
            print_error(f"\terror to copy {file} to {output_path}")
            print_error(f"\terror: \n{e}")
            failed+=1
            failed_files.add(file)
            state["copy_failed"].add(file.relative_to(input_dir))
            st.state_write(state, state_file, state_file_temp)

    print_success(f"\tCopy Done.")
    print_success(f"\tSuccess: {success}")
    print_red(f"\tFailed: {failed}")
    if failed:
        for file in failed_files:
            print_error(f"\t\t{file.relative_to(input_dir.parent)}")

def main():

    if len(sys.argv) < 2:
        print_error(f"Invalid input.\ntry: {APP_NAME} --help")
        sys.exit(1)

    if("-h" in sys.argv or "--help" in sys.argv):
        print(f"""Video Archive Converter

Convert video archives to H.264 720p while preserving audio, subtitles,
attachments and container metadata whenever possible.

Usage:
    {APP_NAME} <input_directory> [OPTIONS]

Options:
    -h, --help
        Show this help message and exit.

    -n, --no-copy
        Do not copy non-video files.

    -f, --force-mkv
        Convert unsupported containers to MKV.
        Native MKV and MP4-family containers are not affected.

    -i, --in-place
        Replace the original files after a successful conversion.
        Files are processed using temporary files to reduce the risk
        of data loss.
        Implies --no-copy.

    -r, --refresh
        Refresh the state file by removing entries for files that no
        longer exist in the input or output directories.
    
    -b, --notification
        bell alart at the end.

Behavior:
    • MKV:
        Replace only the video track while preserving audio,
        subtitles and attachments.

    • MP4 family (.mp4, .m4v, .mov, .3gp):
        Replace only the video track.

    • Other containers:
        They are copied unchanged unless --force-mkv is specified.

Output:
    Default:
        <input_directory>.fs/

    --in-place:
        Original files are replaced after successful processing.

Requirements:
    ffmpeg
    ffprobe
    mkvmerge
    MP4Box

Examples:
    {APP_NAME} Movies

    {APP_NAME} Movies --force-mkv

    {APP_NAME} Movies --no-copy

    {APP_NAME} Movies --in-place

    {APP_NAME} Movies --refresh
    {APP_NAME} Movies --notification
""")
        sys.exit(0)
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

    if shutil.which("ffprobe") is None:
        print_error(f"ffprobe not found")
        sys.exit(1)

    if shutil.which("MP4Box") is None:
        print_error(f"MP4Box not found")
        sys.exit(1)

    if "--no-copy" in sys.argv or "-n" in sys.argv:
        flag_control.COPY = False
    if "--force-mkv" in sys.argv or "-f" in sys.argv:
        flag_control.FORCE_MKV = True
    if "--in-place" in sys.argv or '-i' in sys.argv:
        flag_control.IN_PLACE = True
        flag_control.COPY = False
    if '--notification' in sys.argv or '-b' in sys.argv:
        flag_control.FINISH_NOTIFICATION = True

    print_title("scanning directory..")
    files = scan_files(input_dir)
    success = 0
    failed = 0
    failed_files = set()

    print_info(f"Found {len(files)} file(s).")
    other_files: set[Path] = set()
    videos: set[Path] = set()
    split_files(files,videos,other_files)
    print_info(f"Found {len(videos)} video(s).")
    output_dir = create_output_directory(input_dir)
    print_info(f"output directory: {output_dir}")
    print()

    TMP_DIR = Path("/tmp/video-archive-converter")
    try:
        TMP_DIR.mkdir(parents=True,exist_ok=True)
        test = TMP_DIR/".test_write"
        test.touch()
        test.unlink()
    except OSError:
        TMP_DIR = output_dir/".tmp/video-archive-converter"
        TMP_DIR.mkdir(parents=True,exist_ok=True)
    TMP_FILE = TMP_DIR / "recoded.mkv"

    state=dict()
    state_dir = output_dir / ".video_converter"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "state.json"
    state_file_temp = state_dir / "state_tmp.json"

    if "--refresh" in sys.argv or '-r' in sys.argv:
        st.state_refresh(state_file,state_file_temp,input_dir)
        exit(0)

    print_title("Checking for state file...")

    result = st.state_fix(state_file,state_file_temp)
    if result == FixError.NoError:
        result = st.state_validate(state_file)

    match result:
        case FixError.NoError:
            pass
        case FixError.NotFoundError:
            pass

        case FixError.StateDamaged:
            print_error("State file is corrupted.")
            ask_delete_state(state_file, 1)

        case FixError.StateNotSupported:
            print_error("The legacy state file cannot be read. It may be corrupted or created on an incompatible operating system.")
            ask_delete_state(state_file.with_suffix(''), 2)

        case FixError.SchemaError:
            print_error("Unsupported state file schema detected.")
            ask_delete_state(state_file, 3)

        case FixError.SemanticError:
            print_error("Invalid value detected in the state file.")
            ask_delete_state(state_file, 4)

    if not state_file.exists():
        print_info("state file not found.")
        print_cyan(f"Creating state file at {state_file.relative_to(output_dir.parent)}")
        st.make_default(state,
                              input_dir,
                              output_dir,
                              videos,
                              other_files,
                              )
        st.state_write(state,state_file,state_file_temp)
    else:
        print_info(f"State file found at {state_file}")
        st.state_refresh(state_file,state_file_temp,input_dir)
        state = st.state_read(state_file)
        
        st.merg_whit_scan(state,
                                state_file,
                                state_file_temp,
                                input_dir,
                                output_dir,
                                videos,
                                other_files,
                                )

    for index, video in enumerate(videos, start=1):

        output_path = get_output_path(
            input_dir,
            output_dir,
            video,
        )
    
        print_status(f"\n[{index}/{len(videos)}] {video.relative_to(input_dir)}\n")

        if flag_control.FORCE_MKV:
            if not (VIDEO_EXTENSIONS.get(output_path.suffix.lower()) in (ContainerPolicy.MKV,ContainerPolicy.MP4_FAMILY)):
                if output_path.exists() and not flag_control.IN_PLACE:output_path.unlink()
                elif flag_control.IN_PLACE:
                    tmp_hash = state["input_videos"][video.relative_to(input_dir)]
                    state["input_videos"].pop(video.relative_to(input_dir))

                    os.rename(video,video.with_suffix(".mkv"))
                    video = video.with_suffix('.mkv')

                    state["input_videos"][video.relative_to(input_dir)] = tmp_hash

                output_path = output_path.with_suffix(".mkv")
                print_info(f"Converting {video.relative_to(input_dir)} to MKV")

        if VIDEO_EXTENSIONS.get(output_path.suffix.lower()) in (ContainerPolicy.MKV,ContainerPolicy.MP4_FAMILY):
            if not encode_video(video, TMP_FILE):
                print_error(f"Failed to encode: {video}")
                failed+=1
                failed_files.add(video.relative_to(input_dir))
                state['encode_failed'].add(video.relative_to(input_dir))
                st.state_write(state, state_file, state_file_temp)
                continue
            if not mux_video(TMP_FILE, video, output_path):
                print_error(f"Failed to mux: {video}")
                failed+=1
                failed_files.add(video.relative_to(input_dir))
                state['encode_failed'].add(video.relative_to(input_dir))
                st.state_write(state, state_file, state_file_temp)
                continue
            else:
                state["output_videos"].add((video.with_suffix('.mkv') if (flag_control.IN_PLACE and flag_control.FORCE_MKV and not VIDEO_EXTENSIONS[video.suffix] in (ContainerPolicy.MKV, ContainerPolicy.MP4_FAMILY)) else video).relative_to(input_dir))
                st.state_write(state, state_file, state_file_temp)
            
        else:
            if not handle_non_native(input_dir,video,output_path):
                print_error(f"Failed to copy: {video}")
                failed+=1
                failed_files.add(video.relative_to(input_dir))
                state["copy_failed"].add(video.relative_to(input_dir))
                st.state_write(state, state_file, state_file_temp)
                continue
        success+=1
        
    print_success(f"done.\nSuccess: {success}")
    print_red(f"Failed: {failed}")

    if failed:
        print_error(f"Failed file:")
        for file in failed_files:
            print_error(f"\t{file}")
    
    print_cyan(f"Copying other files...")
    copy_other_files(other_files,input_dir,output_dir,state,state_file,state_file_temp)
    
    if TMP_FILE.exists():TMP_FILE.unlink()
    if flag_control.FINISH_NOTIFICATION:
        finish_notification()

if __name__ == "__main__":
    main()
