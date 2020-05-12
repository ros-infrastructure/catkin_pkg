import functools
import os
import shutil
import tempfile


class temporary_directory(object):

    def __init__(self, prefix=''):
        self.prefix = prefix

    def __enter__(self):
        self.original_cwd = os.getcwd()
        self.temp_path = tempfile.mkdtemp(prefix=self.prefix)
        os.chdir(self.temp_path)
        return self.temp_path

    def __exit__(self, exc_type, exc_value, traceback):
        # in Windows, current directory needs to be changed back to release the file handle.
        if self.original_cwd and os.path.exists(self.original_cwd):
            os.chdir(self.original_cwd)
        if self.temp_path and os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)


def in_temporary_directory(f):
    @functools.wraps(f)
    def decorated(*args, **kwds):
        with temporary_directory() as directory:
            try:
                from inspect import getfullargspec as getargspec
            except ImportError:
                from inspect import getargspec
            # If it takes directory of kwargs and kwds does already have
            # directory, inject it
            if 'directory' not in kwds and 'directory' in getargspec(f)[0]:
                kwds['directory'] = directory
            return f(*args, **kwds)
    decorated.__name__ = f.__name__
    return decorated
