# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.contrib.staticfiles.storage import CachedFilesMixin
from django.core.files.base import File
from django.core.files.storage import get_storage_class
import os

from boto.utils import parse_ts
from require.storage import OptimizedFilesMixin
from storages.backends.s3boto import S3BotoStorage


# From https://github.com/jezdez/django_compressor/issues/100
class ForgivingFile(File):
    def _get_size(self):
        if not hasattr(self, '_size'):
            if hasattr(self.file, 'size'):
                self._size = self.file.size
            elif hasattr(self.file, 'name') and os.path.exists(self.file.name):
                self._size = os.path.getsize(self.file.name)
            elif hasattr(self.file, 'tell') and hasattr(self.file, 'seek'):
                pos = self.file.tell()
                self.file.seek(0, os.SEEK_END)
                self._size = self.file.tell()
                self.file.seek(pos)
            else:
                raise AttributeError("Unable to determine the file's size.")
        return self._size

    def _set_size(self, size):
        self._size = size

    size = property(_get_size, _set_size)

    def chunks(self, chunk_size=None):
        """
        Read the file and yield chucks of ``chunk_size`` bytes (defaults to
        ``UploadedFile.DEFAULT_CHUNK_SIZE``).
        """
        if not chunk_size:
            chunk_size = self.DEFAULT_CHUNK_SIZE

        if hasattr(self, 'seek'):
            self.seek(0)

        while True:
            data = self.read(chunk_size)
            if not data:
                break
            yield data


class CachedS3BotoStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class('compressor.storage.CompressorFileStorage')()

    def save(self, name, content):
        content = ForgivingFile(content)
        name = super(CachedS3BotoStorage, self).save(name, content)
        self.local_storage._save(name, content)
        return name

    def modified_time(self, name):
        name = self._normalize_name(self._clean_name(name))
        entry = self.entries.get(name)
        if entry is None:
            entry = self.bucket.get_key(self._encode_name(name))
        # Parse the last_modified string to a local datetime object.
        return parse_ts(entry.last_modified)


class FixedStorageMixin(object):
    def url(self, name, **kwargs):
        url = super(FixedStorageMixin, self).url(name, **kwargs)
        if name.endswith('/') and not url.endswith('/'):
            url += '/'
        return url

class CachedRootS3BotoStorage(OptimizedFilesMixin, FixedStorageMixin, CachedS3BotoStorage):
    "S3 storage backend that sets the static bucket."
    def __init__(self, *args, **kwargs):
        kwargs['location'] = 'static'
        super(CachedRootS3BotoStorage, self).__init__(*args, **kwargs)

class StaticRootS3BotoStorage(CachedRootS3BotoStorage):
    "This doesn't gzip css files because they need to be read by compressor to compress them"
    gzip_content_types = (
        'application/javascript',
        'application/x-javascript',
    )

class MediaRootS3BotoStorage(FixedStorageMixin, S3BotoStorage):
    "S3 storage backend that sets the media bucket."
    def __init__(self, *args, **kwargs):
        super(MediaRootS3BotoStorage, self).__init__(location='media',
                                              *args, **kwargs)
        