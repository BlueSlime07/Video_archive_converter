from pathlib import Path
import sys
import subprocess
import shutil
import hashlib
import pickle as pk

def get_file_hash(filepath: Path,
                  chunk_size:int = 8192,
                  ) -> str:
    """for geting hash of files"""
    sha256 = hashlib.sha256()
    with filepath.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def del_in_list(In:list,for_remove:list):
    remove_set = set(for_remove)
    In[:] = [x for x in In if x not in remove_set]

def state_read(state_file:Path,
               state_file_temp:Path,
               ) -> dict:
    if state_file_temp.exists():
        shutil.copy2(state_file_temp, state_file)
    with state_file.open('rb') as file:
        state = pk.load(file)
    return state


def state_write(state:dict,
                state_file:Path,
                state_file_temp:Path,
                ) -> None:
    with state_file_temp.open('wb') as file:
        pk.dump(state,file)
        file.close()
    shutil.copy2(state_file_temp, state_file)
    state_file_temp.unlink()

def make_default(state:set,
                 input_dir:Path,
                 output_dir:Path,
                 videos:list[Path],
                 other_files:list[Path],
                 )->None:

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

def merg_whit_scan(state:dict,
                   state_file:Path,
                state_file_temp:Path,
                input_dir:Path,
                output_dir:Path,
                videos:list[Path],
                other_files:list[Path],
                
                   ) -> None:
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
                for_del_in_videos.append(video)
            else:
                state["input_videos"][video.relative_to(input_dir)] = file_hash
                continue

    for file in other_files:
        if not file.relative_to(input_dir) in state["input_others"].keys():
            state["input_others"][file.relative_to(input_dir)] = get_file_hash(file)
        else:
            file_hash = get_file_hash(file)
            if state["input_others"][file.relative_to(input_dir)] == file_hash and file.relative_to(input_dir) in state["output_others"]:
                for_del_in_others.append(file)
            else:
                state["input_others"][file.relative_to(input_dir)] = file_hash
                continue
    del_in_list(videos,for_del_in_videos)
    del_in_list(other_files,for_del_in_others)