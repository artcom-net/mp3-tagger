"""mp3 module.

This module contains the main class-interface for data access ID3 tags
and helper functions.

"""


import os

from stat import S_IWRITE

from mp3_tagger.id3 import ID3FrameStream, ID3FrameV2, VERSION_2, VERSION_BOTH
from mp3_tagger.exceptions import MP3OpenFileError, TagSetError


def val_getter(func):
    """Decorator getter."""

    def wrapper(self):
        attr = func.__name__
        tags = self._get_tags(attr)
        if len(tags) == 1:
            tags = tags[0].value
        return func(self, tags)
    return wrapper


def val_setter(func):
    """Decorator setter."""

    def wrapper(self, val):
        attr = func.__name__
        if attr == 'genre' and self._tag_version is VERSION_BOTH:
            raise TagSetError('Genre tag not supports multiple version set')
        tags = self._get_tags(attr)
        v2_null = len(tags) == 0 and self._tag_version is VERSION_2
        v2_null_both = self._tag_version is VERSION_BOTH and (
            len(tags) in (0, 1)
        )
        if v2_null or v2_null_both:
            frame = ID3FrameV2.from_str(attr, val, self.id3_version)
            self._frame_stream.frames.append(frame)
            tags.append(frame.tags)
        for tag in tags:
            tag.value = val
        self._frame_stream.update_frames()
        return func(self, val)
    return wrapper


def val_deleter(func):
    """Decorator deleter."""

    def wrapper(self):
        attr = func.__name__
        tags = self._get_tags(attr)
        for tag in tags:
            del tag.value
        self._frame_stream.update_frames()
        return func(self)
    return wrapper


class MP3File(object):
    """Class - based interface to ID3."""

    _tag_version = VERSION_BOTH

    def __init__(self, path):
        """Initial instance.

        :param path: path to mp3 file.

        """
        self.path = path
        self._frame_stream = ID3FrameStream(self.open())
        self.id3_version = self._frame_stream.get_id3_version()
        self._tags = self._frame_stream.get_tags()

    def open(self):
        """Reads file.

        :return: byte string.

        """
        if self.path.endswith('.mp3'):
            try:
                stream = open(self.path, 'r+b')
            except PermissionError:
                os.chmod(self.path, S_IWRITE)
                stream = open(self.path, 'r+b')
        else:
            raise MP3OpenFileError('File must be MP3 format')
        data = stream.read()
        stream.close()
        return data

    @staticmethod
    def _filter_title(tags, title):
        """Filter tags by title.

        :param tags: list of tags;
        :param title: tag title;
        :return: filtered list.

        """
        return list(
            filter(lambda tag: getattr(tag, 'title') == title, tags)
        )

    def _filter_version(self):
        """Filter tags by version.

        :return: filtered list.

        """
        return list(
            filter(lambda tag: isinstance(tag, self._tag_version), self._tags)
        )

    def _get_tags(self, title):
        """Used by decorators."""

        return self._filter_title(self._filter_version(), title)

    def get_tags(self):
        """Get tags.

        :return: dict.

        """
        tags_dict = {}
        tags = self._filter_version()
        try:
            for class_ in self._tag_version:
                ver_dict = {}
                tmp_dict = {}
                for tag in tags:
                    if isinstance(tag, class_):
                        tmp_dict[tag.title] = tag.value
                ver_dict[class_.__name__] = tmp_dict.copy()
                tags_dict.update(ver_dict.copy())
                ver_dict.clear()
                tmp_dict.clear()
        except TypeError:
            for tag in tags:
                tags_dict.update(tag.to_dict())
        return tags_dict

    def save(self):
        """Writes updated data to file."""

        data = self._frame_stream.update_stream()
        with open(self.path, 'wb') as out_stream:
            out_stream.write(data)

    @classmethod
    def set_version(cls, version):
        """Changes tag version for set/get/del methods.
        Available values: id3.VERSION_1, id3.VERSION_2, id3.VERSION_BOTH.

        """

        if version in VERSION_BOTH or version is VERSION_BOTH:
            cls._tag_version = version
        else:
            raise ValueError('Incorrect version value (may be: id3.VERSION_1, '
                             'id3.VERSION_2 or id3.VERSION_BOTH).')

    @property
    @val_getter
    def artist(self, val):
        return val

    @property
    @val_getter
    def album(self, val):
        return val

    @property
    @val_getter
    def song(self, val):
        return val

    @property
    @val_getter
    def track(self, val):
        return val

    @property
    @val_getter
    def comment(self, val):
        return val

    @property
    @val_getter
    def genre(self, val):
        return val

    @property
    @val_getter
    def year(self, val):
        return val

    @property
    @val_getter
    def band(self, val):
        return val

    @property
    @val_getter
    def composer(self, val):
        return val

    @property
    @val_getter
    def copyright(self, val):
        return val

    @property
    @val_getter
    def url(self, val):
        return val

    @property
    @val_getter
    def publisher(self, val):
        return val

    @artist.setter
    @val_setter
    def artist(self, val):
        pass

    @album.setter
    @val_setter
    def album(self, val):
        pass

    @song.setter
    @val_setter
    def song(self, val):
        pass

    @track.setter
    @val_setter
    def track(self, val):
        pass

    @comment.setter
    @val_setter
    def comment(self, val):
        pass

    @genre.setter
    @val_setter
    def genre(self, val):
        pass

    @year.setter
    @val_setter
    def year(self, val):
        pass

    @band.setter
    @val_setter
    def band(self, val):
        pass

    @composer.setter
    @val_setter
    def composer(self, val):
        pass

    @copyright.setter
    @val_setter
    def copyright(self, val):
        pass

    @url.setter
    @val_setter
    def url(self, val):
        pass

    @publisher.setter
    @val_setter
    def publisher(self, val):
        pass

    @artist.deleter
    @val_deleter
    def artist(self):
        pass

    @album.deleter
    @val_deleter
    def album(self):
        pass

    @song.deleter
    @val_deleter
    def song(self):
        pass

    @track.deleter
    @val_deleter
    def track(self):
        pass

    @comment.deleter
    @val_deleter
    def comment(self):
        pass

    @genre.deleter
    @val_deleter
    def genre(self):
        pass

    @year.deleter
    @val_deleter
    def year(self):
        pass

    @band.deleter
    @val_deleter
    def band(self):
        pass

    @composer.deleter
    @val_deleter
    def composer(self):
        pass

    @copyright.deleter
    @val_deleter
    def copyright(self):
        pass

    @url.deleter
    @val_deleter
    def url(self):
        pass

    @publisher.deleter
    @val_deleter
    def publisher(self):
        pass

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self.path)

    def __repr__(self):
        return self.__str__()
