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
        if self.temp_path and os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)
        if self.original_cwd and os.path.exists(self.original_cwd):
            os.chdir(self.original_cwd)


def in_temporary_directory(f):
    @functools.wraps(f)
    def decorated(*args, **kwds):
        with temporary_directory() as directory:
            from inspect import getargspec
            # If it takes directory of kwargs and kwds does already have
            # directory, inject it
            if 'directory' not in kwds and 'directory' in getargspec(f)[0]:
                kwds['directory'] = directory
            return f(*args, **kwds)
    decorated.__name__ = f.__name__
    return decorated

class temporary_file():

    def __init__(self):
        pass

    def __enter__(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        return self.temp_file

    def __exit__(self, exc_type, exc_value, traceback):
        if self.temp_file and os.path.exists(self.temp_file.name):
            self.temp_file.close()
            os.remove(self.temp_file.name)