"""id3 module.

This module contains classes describing objects which are essentially
byte strings. The structure is as follows: frames, depending on version,
contain the tags and meta data, frames are within the abstract
container class - ID3FrameStream and they also managed.

"""

import re
import struct

from mp3_tagger.genres import GENRES
from mp3_tagger.exceptions import TagSetError, FrameInitError


__all__ = ['ID3FrameStream', 'VERSION_1', 'VERSION_2', 'VERSION_BOTH']


class ID3Tag(object):
    """Base class for ID3TagV1 and ID3TagV2."""

    def __init__(self, title, bytes_, encoding):
        """Initial instance.

        :param title: tag name;
        :param bytes_: byte string;
        :param encoding: defined in ENCODING dict.

        """
        self.title = title
        self.bytes_ = bytes_
        self.encoding = encoding
        self.replace_bytes = None

    @property
    def value(self):
        """Tag value getter."""

        val = self._unpack_bytes()
        if self.title == 'genre' and isinstance(val, int):
            try:
                val = GENRES[val]
            except KeyError:
                val = None
        val = val if val else None
        return val

    @value.setter
    def value(self, value):
        """Tag value setter."""
        self.replace_bytes = value

    def update_attr(self):
        """Update byte values."""

        self.bytes_ = self.replace_bytes
        self.replace_bytes = None

    def _unpack_bytes(self):
        """Stub method."""

    def to_dict(self):
        return {self.title: self.value}

    def __str__(self):
        return '%s(%s:%s)' % (self.__class__.__name__, self.title, self.value)

    def __repr__(self):
        return self.__str__()


class ID3TagV1(ID3Tag):
    """This class describing the tags of the first version ID3."""

    ENCODE = 'UTF-8'

    def __init__(self, title, bytes_):
        super(ID3TagV1, self).__init__(title, bytes_, ID3TagV1.ENCODE)
        self._len = len(bytes_)

    @ID3Tag.value.setter
    def value(self, value):
        """Tag value setter."""

        if self.title == 'genre':
            try:
                value = int(value)
            except ValueError:
                raise TagSetError('Genre value for ID3TagV1 must be int')
        ID3Tag.value.fset(self, self._pack_bytes(value))

    @value.deleter
    def value(self):
        """After marking remove the tag is not removed from the frame,
        just its value is set to zero. When call the property will be return
        None.

        """
        val = 255 if self.title == 'genre' else 0
        ID3Tag.value.fset(self, self._pack_bytes(val))

    def _pack_bytes(self, value):
        """Packaging data.

        :param value: payload data;
        :return: byte string.

        """
        if self.title in ('track', 'genre') or value in (0, 255):
            value = int(value)
            val = struct.pack('>B', value)
        else:
            val = str(value).encode()
        while len(val) != self._len:
            if len(val) < self._len:
                val += b'\x00'
            else:
                val = val[:-1]
        return val

    def _unpack_bytes(self):
        """Gets payload."""

        if self.title in ('track', 'genre'):
            val = struct.unpack('>B', self.bytes_)[0]
        else:
            try:
                val = self.bytes_.decode()
            except UnicodeDecodeError:
                val = self.bytes_.decode('CP1251')
            if '\x00' in val:
                val = val.replace('\x00', '')
        return val


class ID3TagV2(ID3Tag):
    """This class describes the tags of the second version of ID3:
    2.2, 2.3, 2.4.

    """
    def __init__(self, title, bytes_, encoding):
        super(ID3TagV2, self).__init__(title, bytes_, encoding)
        self.to_remove = False
        self.to_insert = False

    @ID3Tag.value.setter
    def value(self, value):
        """Tag value setter."""

        if self.title == 'comment':
            bytes_ = b'eng' + value.encode(self.encoding)
        else:
            try:
                bytes_ = value.encode(self.encoding)
            except AttributeError:
                bytes_ = str(value).encode(self.encoding)
        ID3Tag.value.fset(self, bytes_)

    @value.deleter
    def value(self):
        """Marked for later removal of the tag and frame."""

        self.to_remove = True

    def _unpack_bytes(self):
        """Gets payload."""

        val = None
        try:
            val = self.bytes_.decode(self.encoding)
        except UnicodeDecodeError:
            if self.title == 'comment':
                val = self.bytes_[3:].decode(self.encoding)
                val = val.replace('\x00', '')
        if self.title == 'genre':
            try:
                val = int(val)
            except ValueError:
                if re.match(r'\w+', val):
                    pass
                else:
                    val = int(re.search(r'\d+', val).group(0))
        return val

# Versions for filter tags.
VERSION_1 = ID3TagV1
VERSION_2 = ID3TagV2
VERSION_BOTH = (ID3TagV1, ID3TagV2)


class ID3Frame(object):
    """Base frame class for ID3FrameV1 and ID3FrameV2."""

    def __init__(self, bytes_):
        self.bytes_ = bytes_
        self.replace_bytes = None
        self.title = None
        self.tags = None

    def update(self, bytes_):
        if bytes_ != self.bytes_:
            self.replace_bytes = bytes_

    def __str__(self):
        title = self.title.decode() if isinstance(self.title, bytes) \
            else self.title
        return '%s(%s:%s)' % (self.__class__.__name__, title, self.tags)

    def __repr__(self):
        return self.__str__()


class ID3FrameV1(ID3Frame):
    """The class describes a frame with a header TAG,
     that contains tags ID3TagV1.

     """

    OFFSET = {
        'song': (3, 30),
        'artist': (33, 30),
        'album': (63, 30),
        'year': (93, 4),
        'comment': (97, 28),
        'null_byte': (125, 1),
        'track': (126, 1),
        'genre': (127, 1)
    }

    def __init__(self, bytes_):
        super(ID3FrameV1, self).__init__(bytes_)
        self.tags = []
        self.title = 'TAG'
        for tag_title in self.OFFSET:
            offset, len_ = self.OFFSET[tag_title]
            tag_bytes = self.bytes_[offset:offset + len_]
            if tag_title != 'null_byte':
                tag = ID3TagV1(tag_title, tag_bytes)
                self.tags.append(tag)

    def update(self, *args):
        """Updates byte string from tags."""

        bytes_ = b'TAG'
        for tag in self.tags:
            if tag.title == 'track':
                bytes_ += b'\x00'
            if tag.replace_bytes:
                bytes_ += tag.replace_bytes
                tag.update_attr()
            else:
                bytes_ += tag.bytes_
        super(ID3FrameV1, self).update(bytes_)

    def __getattr__(self, attr):
        if attr in ('to_remove', 'to_insert'):
            return False


class ID3FrameV2(ID3Frame):
    """This class describes frames of the second version ID3.

    Available frames are listed in FRAMES dict.

    """

    HEADER_LEN = 10

    FRAMES = {
        'TPE1': 'artist',
        'TPE2': 'band',
        'TALB': 'album',
        'TIT2': 'song',
        'TRCK': 'track',
        'TCON': 'genre',
        'TCOM': 'composer',
        'TCOP': 'copyright',
        'COMM': 'comment',
        'TYER': 'year',
        'TORY': 'year',
        'TDRC': 'year',
        'TPUB': 'publisher',
        'WXXX': 'url'
    }

    OFFSET = {
        'title': (0, 4),
        'data_len': (4, 8),
        'flags': (8, 10),
    }

    ENCODING = {
        0: 'ISO-8859-1',
        1: 'UTF-16',
        2: 'UTF-16BE',
        3: 'UTF-8'
    }

    def __init__(self, bytes_):
        """Initial instance.

        The difference from the first version of the frame that this frame
        contains the header, meta data and the tag.

        """
        super(ID3FrameV2, self).__init__(bytes_)
        self.title = None
        self.data_len = None
        self.flags = None
        self.to_remove = False
        self.to_insert = False
        for meta, offset in self.OFFSET.items():
            setattr(self, meta, self.bytes_[offset[0]:offset[1]])
        self.encoding = self.bytes_[self.HEADER_LEN:self.HEADER_LEN + 1]
        tag_title = self.FRAMES[self.title.decode()]
        encode_index = struct.unpack('>B', self.encoding)[0]
        if encode_index in self.ENCODING:
            tag_encode = self.ENCODING[encode_index]
            self.tags = ID3TagV2(
                tag_title, self.bytes_[self.HEADER_LEN + 1:], tag_encode
            )
        else:
            raise FrameInitError

    def update(self, *args):
        """Updates byte string from tags."""

        if self.tags.replace_bytes:
            b_str = b''
            self.data_len = self._get_data_len(
                self.tags.replace_bytes, self.encoding
            )
            for meta in (self.title, self.data_len, self.flags, self.encoding):
                b_str += meta
            bytes_ = b_str + self.tags.replace_bytes
            self.tags.update_attr()
            super(ID3FrameV2, self).update(bytes_)
        elif self.tags.to_remove:
            self.to_remove = True
        elif self.tags.to_insert:
            self.to_insert = True
            self.tags.to_insert = False

    @staticmethod
    def _get_data_len(bytes_, encoding):
        """Packs four byte string which defines the payload length."""

        len_ = len(encoding + bytes_)
        return struct.pack('>i', len_)

    @classmethod
    def from_str(cls, title, val, version):
        """Creates an instance of the data payload."""

        if title in cls.FRAMES.values():
            for frame_title, tag_title in cls.FRAMES.items():
                if title == 'year':
                    frame_title = 'TDRC'
                    break
                if title == tag_title:
                    break
            else:
                raise TagSetError("Tag %s can't be set" % title)
            if title == 'url':
                encoding_byte = b'\x00'
            else:
                encoding_byte = b'\x03' if version == '2.4' else b'\x01'
            encoding = cls.ENCODING[struct.unpack('>B', encoding_byte)[0]]
            if title == 'comment':
                data = b'eng' + val.encode(encoding)
            else:
                data = val.encode(encoding)
            data_len = cls._get_data_len(data, encoding_byte)
            bytes_ = b'' + frame_title.encode()
            for field in (data_len, b'\x00\x00', encoding_byte, data):
                if isinstance(field, str):
                    field = field.encode(encoding)
                bytes_ += field
        else:
            raise TagSetError("Tag %s can't be set" % title)
        frame_obj = cls(bytes_)
        frame_obj.tags.to_insert = True
        return frame_obj

    def __del__(self):
        del self.tags


class ID3FrameStream(object):
    """The class is a container of frames."""

    def __init__(self, bytes_):
        """Initial instance.

        :param bytes_: bytes from file.

        """
        self.bytes_ = bytes_
        self.frames = []

    def _get_frames(self):
        """Gets list all frames."""

        if not self.frames:
            self.frames += self._parse_frames()
        return self.frames

    def update_stream(self):
        """Updates, changes or deletes frames in bytes_ attribute."""

        for frame in self._get_changed_frame():
            if frame.to_remove:
                self.bytes_ = self.bytes_.replace(frame.bytes_, b'')
                self.frames.remove(frame)
                del frame
                continue
            elif frame.to_insert:
                self._insert_frame(frame)
                continue
            self.bytes_ = self.bytes_.replace(
                frame.bytes_, frame.replace_bytes
            )
            frame.bytes_ = frame.replace_bytes
            frame.replace_bytes = None
        return self.bytes_

    def _get_changed_frame(self):
        """Gets list of changed frames."""

        self.update_frames()
        return list(
            filter(lambda frame:
                   frame.replace_bytes or frame.to_remove or frame.to_insert,
                   self.frames)
        )

    def update_frames(self):
        """Updates byte value for all frames."""

        for frame in self.frames:
            frame.update()

    def get_tags(self):
        """Returns list of ID3TagV1 and ID3TagV2 instances."""

        tags = []
        for frame in self._get_frames():
            tags_ = frame.tags
            if isinstance(tags_, list):
                tags += tags_
            else:
                tags.append(tags_)
        return tags

    def _parse_frames(self):
        """Frames parser."""

        frames = []
        for frame_title in ID3FrameV2.FRAMES:
            try:
                frame_start = self.bytes_.index(frame_title.encode())
            except ValueError:
                frame_start = None
            if frame_start:
                start, end = ID3FrameV2.OFFSET['data_len']
                data_len = self.bytes_[frame_start + start:frame_start + end]
                data_len = struct.unpack('>i', data_len)[0]
                location = (frame_start,
                            frame_start + ID3FrameV2.HEADER_LEN + data_len)
                frame_bytes = self.bytes_[location[0]:location[1]]
                if frame_bytes:
                    try:
                        frame = ID3FrameV2(frame_bytes)
                    except FrameInitError:
                        pass
                    else:
                        frames.append(frame)
        old_frame = ID3FrameV1(self.bytes_[-128:])
        frames.append(old_frame)
        return frames

    def get_id3_version(self):
        """Returns ID3 version value."""

        if self.bytes_[:3] == b'ID3':
            subversion = struct.unpack('>2B', self.bytes_[3:5])[0]
            version = '2.%d' % subversion
        else:
            version = '1.1'
        return version

    def _insert_frame(self, frame):
        """Inserts frame after ID3 header."""

        self.bytes_ = self.bytes_[:10] + frame.bytes_ + self.bytes_[10:]
