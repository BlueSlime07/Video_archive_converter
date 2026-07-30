from enum import IntEnum,auto

class ContainerPolicy(IntEnum):
    MKV = auto()
    MP4_FAMILY = auto()
    WEBM = auto()
    PROFESSIONAL = auto()
    LEGACY = auto()

class ControlModes:
    def __init__(self):
        self.COPY=True
        self.FORCE_MKV = False
        self.IN_PLACE = False
        self.FINISH_NOTIFICATION = False 

flag_control = ControlModes()

class FixError(IntEnum):
    NotFoundError = auto()
    NoError = auto()
    StateDamaged = auto()
    StateNotSupported = auto()
    SchemaError = auto()
    SemanticError = auto()
    