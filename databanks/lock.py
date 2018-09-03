
from flock import Flock, LOCK_EX


class FileLock:
    def __init__(self, path):
        self._path = path

    def __enter__(self):
        self._fp = open(self._path, 'w')
        self._fl = Flock(self._fp, LOCK_EX)
        return self._fl.__enter__()

    def __exit__(self, type, value, traceback):
        self._fl.__exit__(type, value, traceback)
        self._fp.close()
