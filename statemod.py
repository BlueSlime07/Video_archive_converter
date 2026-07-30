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
    
def state_validate(state_file:Path)->int:
    with state_file.open('r',encoding='utf-8') as file:
        state:dict = json.load(file)

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
            
def state_fix(state_file:Path,
              state_file_temp:Path,
              ) -> int:
    result = FixError.NotFoundError
    if state_file_temp.exists():
        try:
            with state_file_temp.open('r', encoding='utf-8') as file:
                json.load(file)
            os.replace(state_file_temp,state_file)
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

def merg_whit_scan(state:dict[str:dict[Path:str]],
                   state_file:Path,
                state_file_temp:Path,
                input_dir:Path,
                output_dir:Path,
                videos:set[Path],
                other_files:set[Path],
                   ) -> None:
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
    
    state["input_videos"].difference_update(for_del_in_videos_history)
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
        if not(state["output_directory"]/file in videos or (state["output_directory"]/file.with_suffix(".mkv") in videos) if VIDEO_EXTENSIONS[file.suffix.lower()] != ContainerPolicy.MP4_FAMILY else False):
            for_del.add(file)
    
    state["output_videos"].difference_update(for_del)
    for_del.clear()
    
    for file in state["output_others"]:
        if not state["output_directory"]/file in others:
            for_del.add(file)
    state["output_others"].difference_update(for_del)
    
    state_write(state,state_file,state_file_temp)
    