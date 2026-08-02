from classes import *

CRF = 22
PRESET = "ultrafast"

PROGRESS_BAR_WIDTH = 32

RED      = "\033[31m"        # Error
GREEN    = "\033[32m"        # Success
YELLOW   = "\033[33m"        # Notice
ORANGE   = "\033[38;5;208m"  # Warning
BLUE     = "\033[34m"        # Info
CYAN     = "\033[36m"        # Hint
MAGENTA  = "\033[35m"        # Debug
RESET    = "\033[0m"

VIDEO_EXTENSIONS = {
    ".mkv":ContainerPolicy.MKV,

    ".mp4":ContainerPolicy.MP4_FAMILY,
    ".m4v":ContainerPolicy.MP4_FAMILY,
    ".mov":ContainerPolicy.MP4_FAMILY,
    ".3gp":ContainerPolicy.MP4_FAMILY,

    ".webm":ContainerPolicy.WEBM,

    ".mxf":ContainerPolicy.PROFESSIONAL,
    ".m2ts":ContainerPolicy.PROFESSIONAL,
    ".mts":ContainerPolicy.PROFESSIONAL,

    ".avi":ContainerPolicy.LEGACY,
    ".asf":ContainerPolicy.LEGACY,
    ".flv":ContainerPolicy.LEGACY,
    ".mpeg":ContainerPolicy.LEGACY,
    ".mpg":ContainerPolicy.LEGACY,
    ".rm":ContainerPolicy.LEGACY,
    ".rmvb":ContainerPolicy.LEGACY,
    ".vob":ContainerPolicy.LEGACY,
    ".ogm":ContainerPolicy.LEGACY,
    ".ts":ContainerPolicy.LEGACY,
    ".wmv":ContainerPolicy.LEGACY,
}

APP_NAME = "video-archive-converter"
APP_VERSION = "1.1.0"