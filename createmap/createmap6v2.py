import os
from queue import Queue
from threading import Thread, Lock
from time import time


class AlreadyMappedException(Exception):
    pass


class AlreadyFormattedException(Exception):
    pass


class NotMappedException(Exception):
    pass


class PathManager:
    def __init__(self, path):
        self.path = path

        self.queue = Queue()
        self.ext_queue = Queue()
        self.format_queue = Queue()

        self.file_lock = Lock()
        self.folder_lock = Lock()

        self._folders = []
        self._files = []
        self._exts = {}

        self._formatted_dict = {'folder': FolderCollection(), 'ext': ExtCollection()}

        self.mapped = False
        self.formatted = False
        self.home_dir = None

    def createmap(self, threads: int = 8, output: bool = True):
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

    def unmap(self):
        self._folders = []
        self._files = []
        self._exts = {}
        self.mapped = False

    @property
    def folders(self):
        if self.formatted:
            return self._formatted_dict['folder']
        else:
            return self._folders

    @property
    def files(self):
        if self.formatted:
            return self._formatted_dict['file']
        else:
            return self._files

    @property
    def exts(self):
        if self.formatted:
            return self._formatted_dict['ext']
        else:
            return self._exts

    def format(self, threads=8, output=True):
        # Format should only happen once
        if self.formatted:
            raise AlreadyFormattedException

        start_time = time()

        for i in range(threads):
            worker = FormatWorker(self.format_queue, self)
            worker.daemon = True
            worker.start()

        for folder in self._folders:
            self.format_queue.put((folder, 'folder'))
        for file in self._files:
            self.format_queue.put((file, 'file'))
        for ext in self._exts.items():
            self.format_queue.put((ext, 'ext'))

        self.format_queue.join()

        if output:
            print(f'Took {time() - start_time} seconds')
        self.formatted = True

    def unformat(self):
        raise NotImplemented
        # for collection in self._formatted_dict.values():
        #     pass

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

    def add_formatted(self, obj, path_type):
        if obj is not None:
            self._formatted_dict[path_type].add(obj)


class PathWorker(Thread):
    def __init__(self, queue, manager):
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
    def __init__(self, queue, manager):
        Thread.__init__(self)
        self.queue = queue
        self.manager = manager

    def run(self):
        while True:
            file = self.queue.get()
            self.manager.add_ext(os.path.splitext(file)[1][1:], file)
            self.queue.task_done()


class FormatWorker(Thread):
    def __init__(self, queue, manager):
        Thread.__init__(self)
        self.queue = queue
        self.manager = manager

    def run(self):
        while True:
            path, path_type = self.queue.get()
            f = None
            if path_type == 'folder':
                f = Folder(path)
            elif path_type == 'file':
                f = File(path)
            elif path_type == 'ext':
                f = Ext(*path)
            self.manager.add_formatted(f, path_type)
            self.queue.task_done()


class Collection:
    def __init__(self):
        self._lock = Lock()
        self._collection = []

    def __repr__(self):
        return self._collection

    def __contains__(self, i):
        return i in self._collection

    def __len__(self):
        return len(self._collection)

    def add(self, path):
        with self._lock:
            self._collection.append(path)

    def get(self, name, default=None):
        for item in self._collection:
            if item.name == name:
                return item
        return default

    def list(self):
        for item in self._collection:
            print(item)


class FolderCollection(Collection):
    def __init__(self):
        super().__init__()


class FileCollection(Collection):
    def __init__(self):
        super().__init__()


class ExtCollection(Collection):
    def __init__(self):
        super().__init__()


class Folder:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)

    @property
    def contents(self):
        result = []
        for (path, folders, files) in os.walk(self.path):
            result.extend(folders)
            result.extend(files)
            break
        return result

    def __len__(self):
        return len(self.contents)

    def open(self):
        os.system(f'explorer "{self.path}"')


class File:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.ext = os.path.splitext(path)[1][1:]

    def open_in_explorer(self):
        os.system(f'explorer /select,"{self.path}"')

    def open(self):
        os.system(self.path)


class Ext:
    def __init__(self, ext, contents):
        self.ext = ext
        self.name = ext
        self.contents = contents
        for (i, file) in enumerate(contents):
            self.contents[i] = File(file)

    def __len__(self):
        return len(self.contents)
