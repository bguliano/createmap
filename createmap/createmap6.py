import os
from queue import Queue
from threading import Thread, Lock
from time import time
from typing import List, Callable, Union
import pickle
from pathlib import Path
from humanize import naturalsize


class AlreadyMappedException(Exception):
    pass


class NotMappedException(Exception):
    pass


class PathManager:
    def __init__(self, path: Union[str, Path], auto_map: bool = True):
        if isinstance(path, Path):
            self.path = str(path)
        else:
            self.path = path

        self.queue = Queue()
        self.ext_queue = Queue()

        self.file_lock = Lock()
        self.folder_lock = Lock()

        self.folders = []
        self.files = []
        self.exts = {}

        self.mapped = False
        self.home_dir = None

        if auto_map:
            self.createmap()

    def __repr__(self):
        return self.path

    def __str__(self):
        return self.path

    def createmap(self, threads: int = 8, output: bool = False, inline: bool = True):
        # Map should only be created once
        if self.mapped:
            raise AlreadyMappedException

        start_time = time()

        for i in range(round(threads / 2)):
            worker = PathWorker(self.queue, self)
            worker.daemon = True
            worker.start()
        self.queue.put(self.path)

        for i in range(round(threads / 2)):
            worker = ExtWorker(self.ext_queue, self)
            worker.daemon = True
            worker.start()

        self.queue.join()
        self.ext_queue.join()

        if output:
            print(f'Took {time() - start_time} seconds')
            print(f'Found {len(self.folders)} folders, {len(self.files)} files, and {len(self.exts.keys())} extensions')
        self.mapped = True

        if inline:
            return self

    def unmap(self):
        self.folders = []
        self.files = []
        self.exts = {}
        self.mapped = False

    def _get_filepath(self, filename: str):
        return os.path.join(Path.home() if self.home_dir is None else self.home_dir, filename)

    def export_map_summary(self, filename: str, number: bool = True):
        if self.mapped:
            with open(self._get_filepath(filename), 'w') as f:
                f.write(f'Folders found: {len(self.folders)}')
                for (i, folder) in enumerate(self.folders):
                    f.write(f'\n{i + 1 if number else ""}: {folder}')
                f.write(f'\n\nFiles found: {len(self.files)}')
                for (i, file) in enumerate(self.files):
                    f.write(f'\n{i + 1 if number else ""}: {file}')
                f.write(f'\n\nExtensions found: {len(self.exts)}')
                for (key, value) in self.exts.items():
                    f.write(f'\n.{key} - {len(value)} files')
                    for (i, file) in enumerate(value):
                        f.write(f'\n\t{i + 1 if number else ""}: {file}')
        else:
            raise NotMappedException

    def export_map(self, filename: str):
        if self.mapped:
            with open(self._get_filepath(filename), 'wb') as f:
                payload = [
                    self.folders,
                    self.files,
                    self.exts
                ]
                pickle.dump(payload, f)
        else:
            raise NotMappedException

    def import_map(self, filepath: str):
        if self.mapped:
            raise AlreadyMappedException
        else:
            with open(filepath, 'rb') as f:
                self.folders, self.files, self.exts = pickle.load(f)
            self.mapped = True

    def export_exts(self, filename: str, number: bool = False):
        if self.mapped:
            with open(self._get_filepath(filename), 'w') as f:
                for (key, value) in self.exts.items():
                    f.write(f'\n.{key} - {len(value)} files')
                    for (i, file) in enumerate(value):
                        f.write(f'\n\t{str(i + 1) + ": " if number else ""}{file}')
        else:
            raise NotMappedException

    def export_list(self, list: List[str], filename: str, number: bool = False):
        with open(self._get_filepath(filename), 'w') as f:
            for (i, item) in enumerate(list):
                f.write(f'{str(i + 1) + ": " if number else ""}{item}\n')

    def get_exts(self, *exts: str, case_sensitive: bool = False) -> List[str]:
        result = []
        for ext in exts:
            if ext.startswith('.'):
                ext = ext[1:]
            if case_sensitive:
                result.extend(self.exts.get(ext, []))
            else:
                result.extend(self.exts.get(ext.lower(), []))
                result.extend(self.exts.get(ext.upper(), []))
        return result

    def export_condition(self, condition: Callable[[str], bool], filename: str, number: bool = False):
        result = []
        for file in self.files:
            if condition(file):
                result.append(file)
        self.export_list(result, filename, number)

    @property
    def total_bytes(self):
        return sum([os.path.getsize(file) for file in self.files])

    @staticmethod
    def open_file(filename: str):
        os.system(filename)

    @staticmethod
    def open_file_in_explorer(filename: str):
        os.system(f'explorer /select,"{filename}"')

    @staticmethod
    def size_of(filename: str, _print: bool = False, binary: bool = False) -> int:
        size = os.path.getsize(filename)
        if _print:
            print(naturalsize(size), binary)
        else:
            return size

    def add_folders(self, paths):
        paths = list(paths)
        with self.folder_lock:
            self.folders.extend(paths)
            for item in paths:
                self.queue.put(item)

    def add_files(self, paths):
        paths = list(paths)
        with self.file_lock:
            self.files.extend(paths)
        for item in paths:
            self.ext_queue.put(item)

    def add_ext(self, ext, file):
        if ext in self.exts:
            self.exts[ext].append(file)
        else:
            self.exts[ext] = [file]


class PathWorker(Thread):
    def __init__(self, queue: Queue, manager: PathManager):
        Thread.__init__(self)
        self.queue = queue
        self.manager = manager

    def run(self):
        while True:
            directory = self.queue.get()
            for (path, folders, files) in os.walk(directory):
                self.manager.add_files(os.path.join(path, file) for file in files)
                self.manager.add_folders(os.path.join(path, folder) for folder in folders)
                break
            self.queue.task_done()


class ExtWorker(Thread):
    def __init__(self, queue: Queue, manager: PathManager):
        Thread.__init__(self)
        self.queue = queue
        self.manager = manager

    def run(self):
        while True:
            file = self.queue.get()
            self.manager.add_ext(os.path.splitext(file)[1][1:], file)
            self.queue.task_done()
