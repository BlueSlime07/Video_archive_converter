from pathlib import Path
import pickle as pk
import json
import os

from functions import *

INPUT_MAPS = (
    "input_videos",
    "input_others",
)
OUTPUT_SETS = (
    "output_videos",
    "output_others",
    "encode_failed",
    "copy_failed",
)
LAST_STATE_VERSION = 2

def state_update_v1_to_v2(state_file:Path,
                          state_file_temp:Path,
                          ):
    """
    Update state file from version 1 to version 2 format.

    Reads the old state file, converts it to the new format with proper
    structure and JSON serialization, then replaces the old file.

    Version 2 changes:
        - Adds "state_version" field
        - Converts Path objects to string paths (.as_posix())
        - Uses JSON format instead of pickle
        - Reorganizes data structure

    Args:
        state_file: Path to the main state file
        state_file_temp: Path to temporary state file

    Returns:
        FixError.NoError on success, FixError.StateNotSupported if state
        cannot be loaded or is corrupted.

    Note:
        This function handles:
        - Recovery from temporary file if it exists
        - Pickle/JSON format conversion
        - Safe file replacement with atomic operations
        - Cleanup of old files on success
    """
    if state_file_temp.exists():
        try:
            with state_file_temp.open('rb') as file:
                pk.load(file)
            os.replace(state_file_temp, state_file)
        except (
            pk.UnpicklingError,
            EOFError,
            OSError,
            NotImplementedError,
        ):
            state_file_temp.unlink()

    try:
        with state_file.open('rb') as file:
            state = pk.load(file)

    except (
        pk.UnpicklingError,
        EOFError,
        OSError,
        NotImplementedError,
    ):
        return FixError.StateNotSupported

    state_temp = dict()
    
    state_temp["state_version"]=LAST_STATE_VERSION
    state_temp["input_directory"] = state["input_directory"].as_posix()
    state_temp["output_directory"] = state["output_directory"].as_posix()

    for key in INPUT_MAPS:
        state_temp[key]=dict()
        for i in state[key].keys():
            state_temp[key][i.as_posix()] = state[key][i]

    for key in OUTPUT_SETS:
        state_temp[key]=[]
        for i in state[key]:
            state_temp[key].append(i.as_posix())

    with state_file_temp.with_suffix('.json').open("w",encoding='utf-8') as file:
        json.dump(
            state_temp,
            file,
            indent=4,
            ensure_ascii=False,
            sort_keys=False,
                    )
        file.flush()
        os.fsync(file.fileno())
    os.replace(state_file_temp.with_suffix('.json'),state_file.with_suffix('.json'))
    state_file.unlink(missing_ok=True)
    state_file_temp.unlink(missing_ok=True)
    return FixError.NoError
    
def state_validate_dict(state:dict)->int:
    """
    Validate the structure and content of a state dictionary.

    Checks that all required keys exist, values have correct types,
    and the state version is compatible. Prints warnings for unknown
    keys and legacy state versions.

    Args:
        state: The state dictionary to validate.

    Returns:
        FixError.NoError if validation passes.
        FixError.SchemaError if structure is invalid.
        FixError.SemanticError if values have wrong types.

    Required keys:
        state_version, input_directory, output_directory,
        input_videos, input_others, output_videos, output_others,
        encode_failed, copy_failed
    """
    keys = set(state.keys())
    defult_keys = {"state_version","input_directory","output_directory","input_videos", "input_others","output_videos","output_others","encode_failed","copy_failed"}

    if len(keys - defult_keys)>0:
        print_warning("Warning: Unknown keys found in state file.")
        for key in keys - defult_keys:
            print_warning(f'\tUnknown key "{key}" ignored.')

    for key in defult_keys:
        if not key in keys:
            print_error(f"Missing required key: {key}")
            return FixError.SchemaError

    if state["state_version"] != LAST_STATE_VERSION:
        print_warning("Legecy state detected.\ntrying to fix it automaticly.")

    for key1 in INPUT_MAPS:
        if not isinstance(state[key1], dict):
            print_error(f'Value of "{key1}" must be an object.')
            return FixError.SchemaError
        for key2 in state[key1].keys():
            if not isinstance(key2, str):
                print_error(f'In "{key1}", this key is not a string: {key2}')
                return FixError.SemanticError

            if not isinstance(state[key1][key2], str):
                print_error(f'Invalid hash value in "{key1}".')
                return FixError.SemanticError

    for key in OUTPUT_SETS:
        if not isinstance(state[key], list):
            print_error(f'Value of "{key}" must be an array.')
            return FixError.SchemaError
        for i in state[key]:
            if not isinstance(i, str):
                print_error(f'This item from "{key}" is not a string')
                return FixError.SemanticError

    return FixError.NoError

def state_validate(state_file:Path)->int:
    """
    Load and validate a state file from disk.

    Reads the JSON state file and passes it to state_validate_dict()
    for structural validation.

    Args:
        state_file: Path to the JSON state file.

    Returns:
        Same as state_validate_dict(): FixError.NoError,
        FixError.SchemaError, or FixError.SemanticError.
    """
    with state_file.open('r',encoding='utf-8') as file:
        state:dict = json.load(file)
    return state_validate_dict(state)
            
def state_fix(state_file:Path,
              state_file_temp:Path,
              ) -> int:
    """
    Attempt to fix or recover a corrupted or legacy state file.

    This function handles multiple recovery scenarios:
        1. Valid temporary file exists → replace main state file
        2. Main state file is valid JSON → no action needed
        3. Main state file is corrupted → try to recover from backup
        4. Legacy v1 state file exists → convert to v2 format

    Args:
        state_file: Path to the main state file (.json)
        state_file_temp: Path to the temporary state file (.json)

    Returns:
        FixError.NoError if state is valid or successfully recovered.
        FixError.StateDamaged if state is corrupted and cannot be fixed.
        FixError.NotFoundError if no valid state file exists.

    Recovery priority:
        1. Temporary file (if valid) → replace main
        2. Main file (if valid) → keep as-is
        3. Corrupted main → try v1 backup conversion
        4. Legacy v1 file → convert to v2
    """
    result = FixError.NotFoundError
    if state_file_temp.exists():
        try:
            with state_file_temp.open('r', encoding='utf-8') as file:
                state = json.load(file)
            if state_validate_dict(state) == FixError.NoError:
                os.replace(state_file_temp,state_file)
                result = FixError.NoError
            else:
                state_file_temp.unlink()
                result = FixError.NoError
        except (json.JSONDecodeError, OSError):
            state_file_temp.unlink()
            result = FixError.NoError
            
    elif state_file.exists():
        try:
            with state_file.open('r', encoding='utf-8') as file:
                json.load(file)
            result = FixError.NoError
        except (json.JSONDecodeError, OSError):
            if state_file.with_suffix("").exists():
                result = state_update_v1_to_v2(state_file.with_suffix(''),state_file_temp.with_suffix(''))
            else:
                result = FixError.StateDamaged

    elif state_file_temp.with_suffix('').exists() or state_file.with_suffix('').exists():
        result = state_update_v1_to_v2(state_file.with_suffix(''),state_file_temp.with_suffix(''))

    return result

def state_read(state_file:Path) -> dict:
    """
    Read and deserialize a state file from disk.

    Loads the JSON state file and converts all string paths back to Path objects.
    This is the reverse operation of the state writing function.

    Args:
        state_file: Path to the JSON state file to read.

    Returns:
        A dictionary containing the complete state with:
            - state_version: int
            - input_directory: Path
            - output_directory: Path
            - input_videos: dict[Path, str] (file path → hash)
            - input_others: dict[Path, str] (file path → hash)
            - output_videos: set[Path]
            - output_others: set[Path]
            - encode_failed: set[Path]
            - copy_failed: set[Path]

    Note:
        This function assumes the state file is valid and properly formatted.
        Call state_validate() before using this function if validation is needed.
    """

    with state_file.open("r",encoding="utf-8") as file:
        state_temp = json.load(file)

    state = dict()
    state["state_version"] = state_temp["state_version"]
    state["input_directory"] = Path(state_temp["input_directory"])
    state["output_directory"] = Path(state_temp["output_directory"])

    for key in INPUT_MAPS:
        state[key] = dict()
        for i in state_temp[key].keys():
            state[key][Path(i)] = state_temp[key][i]

    for key in OUTPUT_SETS:
        state[key] = {Path(i) for i in state_temp[key]}
        
    return state


def state_write(state:dict,
                state_file:Path,
                state_file_temp:Path,
                ) -> None:
    """
    Write a state dictionary to a JSON file with atomic replacement.

    Converts all Path objects to string paths, serializes to JSON,
    and atomically replaces the target file using a temporary file.

    Args:
        state: The state dictionary to write (contains Path objects).
        state_file: The final destination path for the state file (.json).
        state_file_temp: Temporary file path used for atomic write operation.

    Note:
        This function performs an atomic write operation:
            1. Writes to a temporary file first
            2. Flushes and fsync() to ensure data is written to disk
            3. Atomically replaces the target file with os.replace()

        This prevents data corruption if the process is interrupted during writing.

    Structure of the output JSON:
        {
            "state_version": int,
            "input_directory": str,
            "output_directory": str,
            "input_videos": {str: str},  # path → hash
            "input_others": {str: str},  # path → hash
            "output_videos": [str, ...],  # sorted list of paths
            "output_others": [str, ...],  # sorted list of paths
            "encode_failed": [str, ...],  # sorted list of paths
            "copy_failed": [str, ...]     # sorted list of paths
        }
    """
    state_temp = dict()

    state_temp["state_version"]=state["state_version"]
    state_temp["input_directory"] = state["input_directory"].as_posix()
    state_temp["output_directory"] = state["output_directory"].as_posix()

    for key in INPUT_MAPS:
        state_temp[key]=dict()
        for i in state[key].keys():
            state_temp[key][i.as_posix()] = state[key][i]

    for key in OUTPUT_SETS:
        state_temp[key]=sorted(p.as_posix() for p in state[key])

    with state_file_temp.open("w",encoding='utf-8') as file:
        json.dump(
            state_temp,
            file,
            indent=4,
            ensure_ascii=False,
            sort_keys=False,
                  )
        file.flush()
        os.fsync(file.fileno())

    os.replace(state_file_temp, state_file)

def make_default(state:dict,
                 input_dir:Path,
                 output_dir:Path,
                 videos:list[Path],
                 other_files:list[Path],
                 )->None:
    """
    Initialize a state dictionary with default values for a new encoding job.

    Populates the state with version info, directory paths, and hashes of all
    input files. Output sets are initialized as empty sets.

    Args:
        state: The state dictionary to populate (modified in-place).
        input_dir: Root input directory path.
        output_dir: Root output directory path.
        videos: List of video file paths to process.
        other_files: List of non-video files to copy (e.g., subtitles, images).

    Note:
        - File paths are stored relative to input_dir as keys.
        - File hashes are computed using get_file_hash() for change detection.
        - All output sets are initialized as empty sets (will be populated later).
    """
    state["state_version"]=LAST_STATE_VERSION
    state["input_directory"]=input_dir
    state["output_directory"]=output_dir
    state["input_videos"]=dict()
    for i in videos:
        state["input_videos"][i.relative_to(input_dir)] = get_file_hash(i)
    state["input_others"]=dict()
    for i in other_files:
        state["input_others"][i.relative_to(input_dir)] = get_file_hash(i)
    state["output_videos"]=set()
    state["output_others"]=set()
    state["encode_failed"]=set()
    state["copy_failed"]=set()

def merge_whit_scan(state:dict[str:dict[Path:str]],
                   state_file:Path,
                state_file_temp:Path,
                input_dir:Path,
                output_dir:Path,
                videos:set[Path],
                other_files:set[Path],
                   ) -> None:
    """
    Merge current file system scan results with existing state.

    Updates the state by:
        1. Removing entries for files that no longer exist
        2. Adding new files with their hashes
        3. Skipping unchanged files that are already processed
        4. Updating hashes for modified files

    Args:
        state: The state dictionary to update (modified in-place).
        state_file: Path to the main state file (for writing).
        state_file_temp: Path to temporary state file (for writing).
        input_dir: Root input directory path.
        output_dir: Root output directory path.
        videos: Set of video files found in current scan.
        other_files: Set of non-video files found in current scan.

    Note:
        This function handles three scenarios for each file:
            - File removed: Remove from state and output sets
            - File new: Add to state with its hash
            - File unchanged & processed: Skip (remove from processing list)
            - File modified: Update hash and reprocess
    """
    
    state["input_directory"]=input_dir
    state["output_directory"]=output_dir
    for_del_in_videos:set[Path]=set()
    for_del_in_others:set[Path]=set()
    for_del_in_videos_history:set[Path]=set()
    for_del_in_others_history:set[Path]=set()

    for video in state["input_videos"].keys():
        if not input_dir/video in videos:
            for_del_in_videos_history.add(video)
    
    for file in state["input_others"].keys():
        if not input_dir/file in other_files:
            for_del_in_others_history.add(file)
    
    state["output_videos"].difference_update(for_del_in_videos_history)
    state["output_others"].difference_update(for_del_in_others_history)

    for video in videos:
        if not video.relative_to(input_dir) in state["input_videos"].keys():
            state["input_videos"][video.relative_to(input_dir)] = get_file_hash(video)
        else:
            file_hash = get_file_hash(video)
            if ((state["input_videos"][video.relative_to(input_dir)] == file_hash) if not flag_control.IN_PLACE else True) and (video.relative_to(input_dir) in state["output_videos"]):
                for_del_in_videos.add(video)
            else:
                state["input_videos"][video.relative_to(input_dir)] = file_hash
                continue
    
    for file in other_files:
        if not file.relative_to(input_dir) in state["input_others"].keys():
            state["input_others"][file.relative_to(input_dir)] = get_file_hash(file)
        else:
            file_hash = get_file_hash(file)
            if state["input_others"][file.relative_to(input_dir)] == file_hash and file.relative_to(input_dir) in state["output_others"]:
                for_del_in_others.add(file)
            else:
                state["input_others"][file.relative_to(input_dir)] = file_hash
                continue

    videos.difference_update(for_del_in_videos)
    other_files.difference_update(for_del_in_others)

    state_write(state,state_file,state_file_temp)

def state_refresh(state_file:Path,
                  state_file_temp:Path,
                  input_dir:Path,
                  )->dict:
    """
    Refresh the state file by synchronizing it with the current file system.

    This function scans both input and output directories, updates the state
    to reflect the current state of the file system, and writes the updated
    state back to disk.

    Operations performed:
        1. Reads the current state from disk
        2. Scans input directory for videos and other files
        3. Removes entries for files that no longer exist in input
        4. Scans output directory for processed files
        5. Removes entries for files that no longer exist in output
        6. Updates input/output directory paths
        7. Writes the refreshed state back to disk

    Args:
        state_file: Path to the main state file (.json)
        state_file_temp: Path to the temporary state file (.json)
        input_dir: Root input directory path (may have changed)

    Returns:
        The updated state dictionary after refresh.

    Note:
        This function handles:
            - Files deleted from input directory
            - Files deleted from output directory
            - Output videos with both original extension and .mkv extension
            - All state modifications are atomic (via state_write)
    """
    state:dict[str:dict] = state_read(state_file)
    
    state["state_version"]=LAST_STATE_VERSION
    state["input_directory"]=input_dir
    state["output_directory"]= create_output_directory(input_dir)

    files = scan_files(input_dir)
    videos:set[Path] = set()
    others:set[Path] = set()
    split_files(files,videos,others)
    for_del:set[Path]=set()

    for file in state["input_videos"].keys():
        if not input_dir/file in videos:
            for_del.add(file)
    
    for file in for_del:
        state["input_videos"].pop(file)
    for_del.clear()

    for file in state["input_others"].keys():
        if not input_dir/file in others:
            for_del.add(file)
    
    for file in for_del:
        state["input_others"].pop(file)
    for_del.clear()
    files.clear()
    videos.clear()
    others.clear()

    files = scan_files(state["output_directory"])
    split_files(files,videos,others)

    for file in state["output_videos"]:
        if not(state["output_directory"]/file in videos or state["output_directory"]/file.with_suffix(".mkv") in videos):
            for_del.add(file)
    
    state["output_videos"].difference_update(for_del)
    for_del.clear()
    
    for file in state["output_others"]:
        if not state["output_directory"]/file in others:
            for_del.add(file)
    state["output_others"].difference_update(for_del)
    
    state_write(state,state_file,state_file_temp)
    