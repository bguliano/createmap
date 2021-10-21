import os
from concurrent.futures import ThreadPoolExecutor
from itertools import chain


class PathManager:
    def __init__(self, path):
        self.path = path
        self._directories = []
        self.folders = []
        self.files = []
        self.exts = {}
        with ThreadPoolExecutor() as executor:
            e = executor.map(self.createmap, os.walk(path))
        self._directories = list(e)
        self.folders = list(chain(*[item.folders for item in self._directories]))
        self.files = list(chain(*[item.files for item in self._directories]))

    def createmap(self, vals):
        dirs = [os.path.join(vals[0], item) for item in vals[1]]
        files = [os.path.join(vals[0], item) for item in vals[2]]
        d = Directory(vals[0])
        d.add_both(dirs, files)
        return d

    @property
    def directories(self):
        return self.folders


class Directory:
    def __init__(self, path):
        self.path = path
        self.folders = []
        self.files = []

    def add_both(self, dirs, files):
        self.folders.extend(dirs)
        self.files.extend(files)
