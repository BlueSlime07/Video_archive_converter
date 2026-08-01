from enum import IntEnum,auto
from pathlib import Path
from dataclasses import dataclass

class ContainerPolicy(IntEnum):
    """
    Container format classification policy for video files.

    Categorizes video containers based on their compatibility with
    the native workflow and encoding requirements.

    Members:
        MKV: Matroska container - fully supported native format.
        MP4_FAMILY: MP4, M4V, MOV, etc. - widely compatible containers.
        WEBM: WebM container - web-optimized but limited codec support.
        PROFESSIONAL: Professional/studio containers (e.g., MXF) - may contain
                     production metadata not preserved by this tool.
        LEGACY: Legacy/obsolete containers - outside native workflow scope.
    """
    MKV = auto()
    MP4_FAMILY = auto()
    WEBM = auto()
    PROFESSIONAL = auto()
    LEGACY = auto()

class ControlModes:
    """
    Global configuration flags and settings for the application.

    This class holds all runtime configuration options that control the
    behavior of the encoding workflow. Flags are typically set via
    command-line arguments using flag_handler().

    Attributes:
        COPY (bool): Enable file copying (default: True).
        FORCE_MKV (bool): Force conversion to MKV container (default: False).
        IN_PLACE (bool): Process files in their original location.
                        Overrides COPY and disables it (default: False).
        FINISH_NOTIFICATION (bool): Play notification sound when done (default: False).
        JUST_REFRESH (bool): Only refresh the state without processing (default: False).
        IS_OUTPUT_DIR_SET (bool): Flag indicating if output directory was specified.
        OUTPUT_DIR (Path): Custom output directory path (if set).
    """
    def __init__(self):
        self.COPY=True
        self.FORCE_MKV = False
        self.IN_PLACE = False
        self.FINISH_NOTIFICATION = False 
        self.JUST_REFRESH = False
        self.IS_OUTPUT_DIR_SET = False
        self.OUTPUT_DIR = Path()

flag_control = ControlModes()

class FixError(IntEnum):
    """
    Error codes for state file validation, fixing, and recovery operations.

    These codes are returned by state validation and recovery functions to
    indicate the outcome of operations on state files.

    Members:
        NotFoundError: State file does not exist or cannot be located.
        NoError: Operation completed successfully with no issues.
        StateDamaged: State file exists but is corrupted or unreadable.
        StateNotSupported: State file version or format is not supported.
        SchemaError: State structure is invalid (missing required fields or wrong types).
        SemanticError: State content has logical errors (invalid values or relationships).
    """
    NotFoundError = auto()
    NoError = auto()
    StateDamaged = auto()
    StateNotSupported = auto()
    SchemaError = auto()
    SemanticError = auto()

@dataclass
class ProgressState:
    """
    Runtime state tracking for encoding progress.

    This dataclass holds all real-time metrics and status information
    during the video encoding process. Values are updated continuously
    by the encoding worker and displayed by the progress bar.

    Attributes:
        progress (str): Current progress status ('continue', 'end', 'force_down').
        frame (int): Number of frames encoded so far.
        fps (float): Current frames per second encoding speed.
        speed (str): Speed as string with 'x' suffix (e.g., '1.5x').
        speed_f (float): Speed factor as float (1.0 = real-time).
        total_size (int): Total size of output file in bytes.
        out_time_ms (int): Encoded duration in milliseconds.
        out_time_s (float): Encoded duration in seconds.
        return_code (int | None): Exit code from encoder process (None if not finished).
    """
    progress:str = 'continue'

    frame:int = 0
    fps:float = 0.0
    speed:str = '0x'
    speed_f:float = 1.0

    total_size:int = 0

    out_time_ms:int = 0
    out_time_s:float = 0.0

    return_code: int|None = None

progress_state = ProgressState()