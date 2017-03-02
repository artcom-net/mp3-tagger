from .mp3 import MP3File
from .id3 import ID3FrameStream, VERSION_1, VERSION_2, VERSION_BOTH
from .exceptions import MP3OpenFileError, TagSetError, FrameInitError


__version__ = '1.0'
