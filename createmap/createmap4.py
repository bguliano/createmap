import os


class PathManager:
    def __init__(self, path):
        self.path = path
        self._directories = []
        self.folders = []
        self.files = []
        self.exts = {}
        for root, dirs, files in os.walk(path):
            self._directories.append(Directory(root))
            for folder in dirs:
                self._directories[-1].add_folder(os.path.join(root, folder))
                self.folders.append(os.path.join(root, folder))
            for file in files:
                self._directories[-1].add_file(os.path.join(root, file))
                self.files.append(os.path.join(root, file))

    @property
    def directories(self):
        return self.folders


class Directory:
    def __init__(self, path):
        self.path = path
        self.folders = []
        self.files = []

    def add_folder(self, path):
        self.folders.append(path)

    def add_file(self, path):
        self.files.append(path)
